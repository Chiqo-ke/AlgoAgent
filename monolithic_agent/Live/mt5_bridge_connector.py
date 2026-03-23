"""
MT5 Bridge Connector
====================
Drop-in replacement for MT5Connector that talks to the mt5_bridge.py
Flask server running inside Wine instead of calling the MetaTrader5
Python package directly (which is Windows-only).

Usage:
    from mt5_bridge_connector import MT5BridgeConnector as MT5Connector

All public methods match the original MT5Connector API exactly so no other
file in the Live module needs to change.
"""
import logging
import time
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import LiveConfig, MT5Constants

logger = logging.getLogger("LiveTrader.MT5BridgeConnector")

# ── Default bridge URL (localhost only, never exposed externally) ─────────────
BRIDGE_URL = "http://127.0.0.1:5555"


class MT5ConnectionError(Exception):
    """Raised when the MT5 bridge connection fails."""


class MT5BridgeConnector:
    """
    Mirrors the public API of the original MT5Connector but communicates
    with the mt5_bridge.py Flask server running inside Wine.

    Architecture:
        Linux Python  ──HTTP──>  mt5_bridge.py (Wine Python 3.11)
                                      │ named-pipe / shared memory
                                 terminal64.exe (Wine)
                                      │ TCP
                                 Broker server
    """

    def __init__(self, config: LiveConfig, bridge_url: str = BRIDGE_URL):
        self.config = config
        self.bridge_url = bridge_url.rstrip("/")
        self.is_connected = False
        self.account_info: Optional[Dict] = None
        self.terminal_info: Optional[Dict] = None
        self.last_terminal_status_issue: Optional[str] = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5

        # HTTP session with retry logic
        self._session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.5,
                      status_forcelist=[500, 502, 503, 504])
        self._session.mount("http://", HTTPAdapter(max_retries=retry))

        logger.info("MT5BridgeConnector initialised  bridge=%s", self.bridge_url)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get(self, path: str, params: Optional[Dict] = None,
             timeout: int = 30) -> Optional[Dict]:
        try:
            r = self._session.get(f"{self.bridge_url}{path}",
                                  params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.ConnectionError:
            logger.error("Bridge unreachable at %s — is mt5_bridge running?",
                         self.bridge_url)
            return None
        except Exception as e:
            logger.error("GET %s failed: %s", path, e)
            return None

    def _post(self, path: str, json_body: Optional[Dict] = None,
              timeout: int = 30) -> Optional[Dict]:
        try:
            r = self._session.post(f"{self.bridge_url}{path}",
                                   json=json_body or {}, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.ConnectionError:
            logger.error("Bridge unreachable at %s — is mt5_bridge running?",
                         self.bridge_url)
            return None
        except Exception as e:
            logger.error("POST %s failed: %s", path, e)
            return None

    def _bridge_alive(self) -> bool:
        """Return True if the bridge HTTP server responds to /health."""
        try:
            r = self._session.get(f"{self.bridge_url}/health", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def _describe_terminal_trading_issue(
        self,
        terminal_info: Optional[Dict[str, Any]] = None,
        account_info: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Return an actionable explanation when MT5 is connected but not permitted
        to execute live orders from the client terminal / external API.
        """
        if self.config.dry_run:
            self.last_terminal_status_issue = None
            return None

        terminal = terminal_info or self.terminal_info or self._get("/terminal_info")
        account = account_info or self.account_info or self._get("/account_info")

        issues = []
        if terminal:
            if terminal.get("trade_allowed") is False:
                issues.append("terminal Algo Trading is disabled")
            if terminal.get("tradeapi_disabled") is True:
                issues.append("terminal blocks external Python/API trading")

        if account:
            if account.get("trade_allowed") is False:
                issues.append("broker account trading is disabled")
            if account.get("trade_expert") is False:
                issues.append("broker account expert/API trading is disabled")

        if not issues:
            self.last_terminal_status_issue = None
            return None

        flags = []
        if terminal:
            flags.append(
                "terminal.trade_allowed=%s terminal.tradeapi_disabled=%s"
                % (terminal.get("trade_allowed"), terminal.get("tradeapi_disabled"))
            )
        if account:
            flags.append(
                "account.trade_allowed=%s account.trade_expert=%s"
                % (account.get("trade_allowed"), account.get("trade_expert"))
            )

        issue_text = (
            f"MT5 is connected but not allowed to place live orders: {', '.join(issues)}. "
            "Enable 'Algo Trading' and uncheck 'Disable automatic trading via external Python API' "
            "in MT5 (Tools -> Options -> Expert Advisors), then restart the MT5 terminal and bridge service. "
            + (" ".join(flags) if flags else "")
        ).strip()
        self.last_terminal_status_issue = issue_text
        return issue_text

    # ── Public API (matches MT5Connector exactly) ─────────────────────────────

    def initialize(self) -> bool:
        """
        Initialize MT5 via the bridge:
          1. Call /initialize on the bridge (starts MT5 terminal connection)
          2. Call /login with broker credentials
          3. Fetch terminal + account info
        """
        logger.info("Initialising MT5 via bridge ...")

        # Wait up to 30 s for the bridge to be alive
        for attempt in range(10):
            if self._bridge_alive():
                break
            logger.warning("Bridge not ready yet, waiting … (%d/10)", attempt + 1)
            time.sleep(3)
        else:
            logger.error("MT5 bridge did not become reachable within 30 s")
            return False

        try:
            # Step 1 – initialise MT5 terminal inside Wine.
            # Skip /initialize if bridge already reports initialised=true to avoid
            # the race condition where concurrent sessions call /initialize, which
            # triggers mt5.shutdown() + reinit and briefly sets _initialised=False,
            # causing /login calls from other sessions to get a 503.
            health = self._get("/health")
            already_initialised = health and health.get("initialised") is True
            init_in_progress = health and health.get("init_in_progress") is True
            if already_initialised:
                logger.info("Bridge already initialised (health check) — skipping /initialize")
            elif init_in_progress:
                logger.info("Bridge auto-init in progress — waiting for it to complete ...")
                # Poll until initialised or timeout (up to 3 minutes)
                for _ in range(18):  # 18 × 10s = 3 min
                    time.sleep(10)
                    health = self._get("/health")
                    if health and health.get("initialised") is True:
                        logger.info("Bridge auto-init completed")
                        break
                else:
                    logger.error("Bridge auto-init did not complete within 3 minutes")
                    return False
            else:
                init_payload: Dict[str, Any] = {"timeout": self.config.mt5_timeout}
                if self.config.mt5_path:
                    init_payload["path"] = self.config.mt5_path

                resp = self._post("/initialize", init_payload, timeout=90)
                if resp is None:
                    logger.error("Bridge /initialize failed: no response")
                    return False
                # 202 means auto-init is in progress — retry on next cycle
                if isinstance(resp, dict) and resp.get("retry_after"):
                    logger.info("Bridge /initialize: init in progress, will retry (retry_after=%ss)",
                                resp.get("retry_after"))
                    return False
                if resp.get("status") != "initialised":
                    logger.error("Bridge /initialize failed: %s", resp)
                    return False
                logger.info("MT5 initialised  version=%s", resp.get("version"))

            # Step 2 – login (skip in dry_run mode, or when bridge is already
            # authenticated and no credentials are provided in this process)
            if not self.config.dry_run:
                if not self.config.mt5_login or not self.config.mt5_password:
                    # Bridge manages its own persistent session; no re-login needed
                    logger.info("Bridge mode: no credentials in env — using existing bridge session")
                else:
                    login_resp = self._post("/login", {
                        "login":    self.config.mt5_login,
                        "password": self.config.mt5_password,
                        "server":   self.config.mt5_server,
                    }, timeout=60)

                    if not login_resp or login_resp.get("status") != "logged_in":
                        logger.error("Bridge /login failed: %s", login_resp)
                        return False

                    self.account_info = login_resp.get("account")
                    logger.info("MT5 login OK  account=%s  server=%s",
                                self.account_info.get("login"),
                                self.account_info.get("server"))
            else:
                logger.info("DRY_RUN: skipping MT5 login")

            # Step 3 – fetch terminal info
            self.terminal_info = self._get("/terminal_info")
            if not self.account_info:
                self.account_info = self._get("/account_info")

            terminal_issue = self._describe_terminal_trading_issue(
                terminal_info=self.terminal_info,
                account_info=self.account_info,
            )
            if terminal_issue:
                logger.error("MT5 terminal is not ready for live trading: %s", terminal_issue)
                self.is_connected = False
                return False

            self.is_connected = True
            self.reconnect_attempts = 0

            logger.info("✓ MT5 bridge connection established")
            if self.account_info:
                logger.info("  Account : %s — %s",
                            self.account_info.get("login"),
                            self.account_info.get("server"))
                logger.info("  Balance : $%.2f", self.account_info.get("balance", 0))
                logger.info("  Equity  : $%.2f", self.account_info.get("equity", 0))
            return True

        except Exception as e:
            logger.error("initialize() exception: %s", e, exc_info=True)
            return False

    def shutdown(self):
        """Gracefully shut down the MT5 connection via bridge."""
        if self.is_connected:
            logger.info("Shutting down MT5 connection via bridge ...")
            self._post("/shutdown")
            self.is_connected = False
            logger.info("✓ MT5 bridge connection closed")

    def reconnect(self) -> bool:
        """Attempt to re-establish the connection (exponential back-off).

        When max_reconnect_attempts is exhausted the counter is reset so the
        live-trader loop will keep retrying indefinitely (spaced by the loop
        sleep) rather than giving up permanently after 5 failures.
        """
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            # Bridge may be slow to initialise after a cold start — reset so
            # the next loop iteration tries again instead of stopping forever.
            logger.warning(
                "Max reconnect attempts (%d) reached — resetting counter to "
                "allow continued retries once the bridge comes back",
                self.max_reconnect_attempts,
            )
            self.reconnect_attempts = 0
            return False

        self.reconnect_attempts += 1
        wait = min(2 ** self.reconnect_attempts, 60)
        logger.warning("Reconnect attempt %d/%d in %ds …",
                       self.reconnect_attempts,
                       self.max_reconnect_attempts, wait)
        time.sleep(wait)

        self._post("/shutdown")
        self.is_connected = False
        return self.initialize()

    def check_connection(self) -> bool:
        """Return True if the bridge is reachable and MT5 is initialised."""
        if not self.is_connected:
            return False
        info = self._get("/account_info")
        if info is None or "error" in info:
            logger.warning("Connection check failed: %s", info)
            self.is_connected = False
            return False
        self.account_info = info
        return True

    def ensure_connected(self) -> bool:
        """Check connection; reconnect if necessary."""
        if self.check_connection():
            return True
        logger.warning("Connection lost — attempting reconnect …")
        return self.reconnect()

    # ── Account / Symbol ──────────────────────────────────────────────────────

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        if not self.ensure_connected():
            return None
        data = self._get("/account_info")
        if not data or "error" in data:
            return None
        # Return only the keys the rest of the system expects
        return {
            "login":        data.get("login"),
            "trade_mode":   data.get("trade_mode"),
            "leverage":     data.get("leverage"),
            "balance":      data.get("balance"),
            "equity":       data.get("equity"),
            "profit":       data.get("profit"),
            "margin":       data.get("margin"),
            "margin_free":  data.get("margin_free"),
            "margin_level": data.get("margin_level"),
            "currency":     data.get("currency"),
            "server":       data.get("server"),
            "company":      data.get("company"),
        }

    def get_terminal_info(self) -> Optional[Dict[str, Any]]:
        if not self.ensure_connected():
            return None
        data = self._get("/terminal_info")
        if not data or "error" in data:
            return None
        self.terminal_info = data
        return data

    def get_terminal_trading_issue(self) -> Optional[str]:
        """Public helper for callers that want an actionable live-trading diagnosis."""
        return self._describe_terminal_trading_issue()

    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        if not self.ensure_connected():
            return None
        data = self._get("/symbol_info", {"symbol": symbol})
        if not data or "error" in data:
            return None
        return {
            "name":                 data.get("name"),
            "bid":                  data.get("bid"),
            "ask":                  data.get("ask"),
            "last":                 data.get("last"),
            "volume":               data.get("volume_min"),
            "volume_min":           data.get("volume_min"),
            "volume_max":           data.get("volume_max"),
            "volume_step":          data.get("volume_step"),
            "trade_contract_size":  data.get("trade_contract_size"),
            "trade_tick_size":      data.get("trade_tick_size"),
            "trade_tick_value":     data.get("trade_tick_value"),
            "point":                data.get("point"),
            "digits":               data.get("digits"),
            "spread":               data.get("spread"),
            "trade_mode":           data.get("trade_mode"),
            "currency_base":        data.get("currency_base"),
            "currency_profit":      data.get("currency_profit"),
            "currency_margin":      data.get("currency_margin"),
        }

    # ── Positions & Orders ────────────────────────────────────────────────────

    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.ensure_connected():
            return []
        params = {"symbol": symbol} if symbol else {}
        data = self._get("/positions_get", params)
        if data is None or "error" in (data if isinstance(data, dict) else {}):
            return []
        return data  # list of dicts already

    def get_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.ensure_connected():
            return []
        params = {"symbol": symbol} if symbol else {}
        data = self._get("/orders_get", params)
        if data is None or "error" in (data if isinstance(data, dict) else {}):
            return []
        return data

    # ── Order Execution ───────────────────────────────────────────────────────

    def check_order(self, request_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.ensure_connected():
            return None
        terminal_issue = self._describe_terminal_trading_issue()
        if terminal_issue:
            logger.error("Blocking order_check: %s", terminal_issue)
            return {
                "retcode": 10027,
                "comment": terminal_issue,
                "retcode_message": MT5Constants.get_retcode_message(10027),
            }
        logger.info("order_check request: %s", request_dict)
        result = self._post("/order_check", request_dict)
        if not result or "error" in result:
            logger.error("order_check failed: %s", result)
            return None
        return result

    def send_order(self, request_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.ensure_connected():
            logger.error("Cannot send order: not connected")
            return None

        if self.config.dry_run:
            logger.info("DRY_RUN: would send order: %s", request_dict)
            return {
                "retcode":          10008,
                "retcode_message":  "TRADE_RETCODE_DONE",
                "deal":             999999,
                "order":            999999,
                "volume":           request_dict.get("volume", 0),
                "price":            request_dict.get("price", 0),
                "comment":          "DRY_RUN",
                "request_id":       0,
            }

        terminal_issue = self._describe_terminal_trading_issue()
        if terminal_issue:
            logger.error("Blocking order_send: %s", terminal_issue)
            return {
                "retcode": 10027,
                "retcode_message": MT5Constants.get_retcode_message(10027),
                "comment": terminal_issue,
            }

        logger.info("Sending order via bridge: action=%s  symbol=%s  volume=%s",
                    request_dict.get("action"), request_dict.get("symbol"),
                    request_dict.get("volume"))

        result = self._post("/order_send", request_dict, timeout=60)
        if not result or "error" in result:
            logger.error("order_send failed: %s", result)
            return None

        retcode = result.get("retcode")
        result["retcode_message"] = MT5Constants.get_retcode_message(retcode)

        if MT5Constants.is_success(retcode):
            logger.info("✓ Order executed  deal=#%s  order=#%s",
                        result.get("deal"), result.get("order"))
        else:
            logger.error("✗ Order failed  retcode=%s (%s)",
                         retcode, result["retcode_message"])
        return result

    def get_last_error(self) -> tuple:
        data = self._get("/last_error") or {}
        return (data.get("code", -1), data.get("description", "unknown"))

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self):
        if not self.initialize():
            raise MT5ConnectionError("Failed to initialise MT5 bridge connection")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

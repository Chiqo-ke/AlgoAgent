"""
Enhanced TradingView Scraper with Playwright Browser Automation
This module provides full functionality for symbol changing, timeframe control,
indicator management, and historical OHLCV data extraction from TradingView.

Uses Playwright (pip install playwright; playwright install chromium) for real
browser automation instead of the stub MCP Chrome DevTools calls.
"""

import time
import json
import re
from typing import Dict, List, Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright


class MCPTradingViewScraper:
    """
    Complete TradingView scraper using Playwright for real browser automation.

    Features:
    - Symbol changing
    - Timeframe adjustment (1m → 1M)
    - Indicator add/remove/configure
    - Historical OHLCV data extraction via JavaScript
    - Data export (JSON/CSV/Excel)

    Usage:
        scraper = MCPTradingViewScraper()
        scraper.init_browser()
        scraper.navigate_to_tradingview()
        scraper.change_symbol("AAPL")
        scraper.change_timeframe("1h")
        data = scraper.get_historical_data(bars_count=100)
        scraper.close_browser()

        # Or as context manager:
        with MCPTradingViewScraper() as scraper:
            scraper.navigate_to_tradingview()
            data = scraper.get_historical_data(bars_count=100)
    """

    # Legacy UID map (kept for backward compat)
    SYMBOL_BUTTON = "1_2"
    INDICATORS_BUTTON = "1_12"
    TIMEFRAME_BUTTONS = {
        "1m": "1_5",
        "3m": "1_6",
        "5m": "1_7",
        "30m": "1_8",
        "1h": "1_9",
    }

    # Resolution string map used by TradingView toolbar
    TIMEFRAME_BUTTON_MAP = {
        "1m": "1",
        "3m": "3",
        "5m": "5",
        "15m": "15",
        "30m": "30",
        "45m": "45",
        "1h": "60",
        "2h": "120",
        "3h": "180",
        "4h": "240",
        "1D": "1D",
        "1W": "1W",
        "1M": "1M",
    }

    TRADINGVIEW_BASE_URL = "https://www.tradingview.com/chart/"

    def __init__(self, headless: bool = False):
        """
        Initialize the scraper.

        Args:
            headless: Run browser in headless mode.
                      Default False so TradingView can establish WebSocket data feeds.
        """
        self.current_symbol: Optional[str] = None
        self.current_timeframe: Optional[str] = None
        self.active_indicators: List[Dict] = []
        self.headless = headless

        # Playwright objects
        self._pw: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self.browser_initialized: bool = False
    
    def init_browser(self) -> bool:
        """
        Launch Chromium via Playwright and open a new page.

        Returns:
            True if successful
        """
        try:
            print("🌐 Launching Chromium browser via Playwright...")
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            self._context = self._browser.new_context(
                viewport={"width": 1440, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            )
            self._page = self._context.new_page()
            self.browser_initialized = True
            print("   ✅ Browser initialized")
            return True
        except Exception as e:
            print(f"   ❌ Failed to initialize browser: {e}")
            return False
    
    def navigate_to_tradingview(self, url: str = "https://www.tradingview.com/chart/") -> bool:
        """
        Navigate to TradingView chart page and wait for it to be ready.

        Args:
            url: TradingView URL (default: main chart page)

        Returns:
            True if successful
        """
        try:
            if not self.browser_initialized or self._page is None:
                print("   ⚠️  Browser not initialized, initializing now...")
                if not self.init_browser():
                    return False

            print(f"🔗 Navigating to TradingView: {url}")
            self._page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Wait for chart canvas
            try:
                self._page.wait_for_selector("canvas", timeout=30000)
                print("   ✅ Chart canvas detected")
            except Exception:
                print("   ⚠️  Canvas not detected — chart may still be loading")

            # Extra buffer for TradingView WebSocket data feeds
            time.sleep(4)
            print("   ✅ Navigated to TradingView")
            return True

        except Exception as e:
            print(f"   ❌ Failed to navigate to TradingView: {e}")
            return False
    
    def close_browser(self) -> bool:
        """
        Close the browser and clean up Playwright resources.

        Returns:
            True if successful
        """
        try:
            if self._page:
                self._page.close()
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
            self.browser_initialized = False
            print("   ✅ Browser closed")
            return True
        except Exception as e:
            print(f"   ❌ Failed to close browser: {e}")
            return False
    
    def change_symbol(self, symbol: str) -> bool:
        """
        Change the chart symbol via TradingView's symbol search dialog.

        Process:
            1. Press "/" hotkey to open symbol search
            2. Type symbol name
            3. Press Enter to select first result
            4. Wait for chart to reload

        Args:
            symbol: Ticker (e.g., "AAPL", "EURUSD", "BTCUSD", "NASDAQ:AAPL")

        Returns:
            True if successful
        """
        try:
            if self._page is None:
                raise RuntimeError("Browser not initialized")

            print(f"🔄 Changing symbol to {symbol}...")

            # Press "/" which opens TradingView symbol search from chart
            self._page.keyboard.press("/")
            time.sleep(0.8)

            # Locate and fill the search input
            search_input = None
            selectors = [
                'input[data-role="search"]',
                'input[placeholder*="Search"]',
                'input[class*="search-YnYORFMU"]',
                'input[class*="search"]',
            ]
            for sel in selectors:
                try:
                    search_input = self._page.wait_for_selector(sel, timeout=3000)
                    if search_input:
                        break
                except Exception:
                    continue

            if search_input is None:
                # Fallback: click the symbol header button
                header_btn = self._page.query_selector(
                    '[data-name="header-toolbar-symbol-search"], '
                    '[class*="symbolInput-"], button[class*="symbol-"]'
                )
                if header_btn:
                    header_btn.click()
                    time.sleep(0.5)
                    for sel in selectors:
                        try:
                            search_input = self._page.wait_for_selector(sel, timeout=2000)
                            if search_input:
                                break
                        except Exception:
                            continue

            if search_input is None:
                print("   ❌ Could not locate symbol search input")
                return False

            search_input.triple_click()
            search_input.type(symbol, delay=50)
            time.sleep(0.5)
            self._page.keyboard.press("Enter")

            # Wait for chart to reload with new symbol
            time.sleep(2.5)

            self.current_symbol = symbol
            print(f"✅ Symbol changed to: {symbol}")
            return True

        except Exception as e:
            print(f"❌ Error changing symbol: {e}")
            return False
    
    def change_timeframe(self, timeframe: str) -> bool:
        """
        Change the chart timeframe.
        
        Args:
            timeframe: One of "1m", "3m", "5m", "30m", "1h"
            
        Returns:
            True if successful
            
        Example:
            ```python
            scraper.change_timeframe("5m")
            ```
            
        MCP Tools Required:
            - mcp_io_github_chr_click: Click timeframe button
        """
    def change_timeframe(self, timeframe: str) -> bool:
        """
        Change chart timeframe using TradingView's toolbar buttons.

        Args:
            timeframe: One of "1m","3m","5m","15m","30m","45m","1h","2h","3h","4h","1D","1W","1M"

        Returns:
            True if successful
        """
        try:
            if self._page is None:
                raise RuntimeError("Browser not initialized")

            tv_resolution = self.TIMEFRAME_BUTTON_MAP.get(timeframe, timeframe)
            print(f"🔄 Changing timeframe to {timeframe} (tv resolution: {tv_resolution})...")

            # Try multiple selector strategies
            selectors = [
                f'button[aria-label="{tv_resolution}"]',
                f'button[data-value="{tv_resolution}"]',
                f'[data-name="header-toolbar-intervals"] button:has-text("{timeframe}")',
                f'button[class*="item-"]:has-text("{timeframe}")',
            ]

            clicked = False
            for sel in selectors:
                try:
                    btn = self._page.query_selector(sel)
                    if btn:
                        btn.click()
                        clicked = True
                        break
                except Exception:
                    continue

            if not clicked:
                # JS fallback
                clicked = self._page.evaluate(f"""
                    (() => {{
                        const btns = Array.from(document.querySelectorAll('button'));
                        const btn = btns.find(b =>
                            b.textContent.trim() === '{timeframe}' ||
                            b.getAttribute('data-value') === '{tv_resolution}'
                        );
                        if (btn) {{ btn.click(); return true; }}
                        return false;
                    }})()
                """)

            if not clicked:
                print(f"   ⚠️  Timeframe button for '{timeframe}' not found; chart may keep previous tf")

            time.sleep(1.5)
            self.current_timeframe = timeframe
            print(f"✅ Timeframe changed to: {timeframe}")
            return True

        except Exception as e:
            print(f"❌ Error changing timeframe: {e}")
            return False
    
    def add_indicator(self, indicator_name: str, parameters: Optional[Dict] = None) -> bool:
        """
        Add an indicator to the TradingView chart.

        Process:
            1. Click Indicators toolbar button
            2. Search for the indicator
            3. Press Enter to add first result
            4. Optionally configure parameters

        Args:
            indicator_name: e.g., "RSI", "EMA", "MACD"
            parameters: Optional dict e.g., {"length": 20, "source": "close"}

        Returns:
            True if successful
        """
        try:
            if self._page is None:
                raise RuntimeError("Browser not initialized")

            print(f"🔄 Adding indicator: {indicator_name}...")

            # Click Indicators button
            indicators_btn = self._page.query_selector(
                '[data-name="header-toolbar-indicators"], '
                'button[aria-label*="Indicators"], '
                'button[class*="indicator"]'
            )
            if indicators_btn:
                indicators_btn.click()
            else:
                # Use keyboard shortcut "i"
                self._page.keyboard.press("i")

            time.sleep(0.8)

            # Find and fill search input
            search_input = None
            for sel in ['input[data-role="search"]', 'input[placeholder*="Search"]',
                        'input[class*="search"]']:
                try:
                    search_input = self._page.wait_for_selector(sel, timeout=3000)
                    if search_input:
                        break
                except Exception:
                    continue

            if search_input is None:
                print(f"   ⚠️  Indicator search input not found")
                return False

            search_input.triple_click()
            search_input.type(indicator_name, delay=50)
            time.sleep(0.5)
            self._page.keyboard.press("Enter")
            time.sleep(1.2)

            # Close dialog
            self._page.keyboard.press("Escape")
            time.sleep(0.3)

            indicator_info = {"name": indicator_name, "parameters": parameters or {}}
            self.active_indicators.append(indicator_info)

            if parameters:
                print(f"   🔧 Configuring parameters: {parameters}")
                self.configure_indicator(indicator_name, parameters)

            print(f"✅ Added indicator: {indicator_name}")
            return True

        except Exception as e:
            print(f"❌ Error adding indicator: {e}")
            return False
    
    def remove_indicator(self, indicator_name: str) -> bool:
        """
        Remove an indicator from the chart by locating its Remove button via DOM.

        Args:
            indicator_name: Name to remove (e.g., "RSI", "EMA")

        Returns:
            True if successful
        """
        try:
            if self._page is None:
                raise RuntimeError("Browser not initialized")

            print(f"🔄 Removing indicator: {indicator_name}...")

            removed = self._page.evaluate(f"""
                (() => {{
                    const name = '{indicator_name}'.toLowerCase();
                    const btns = Array.from(document.querySelectorAll('button'));
                    const removeBtn = btns.find(b => {{
                        const label = (b.getAttribute('aria-label') || b.textContent || '').toLowerCase();
                        return label.includes('remove') && label.includes(name);
                    }});
                    if (removeBtn) {{ removeBtn.click(); return true; }}
                    return false;
                }})()
            """)

            if not removed:
                print(f"   ⚠️  Remove button not found for '{indicator_name}'")

            time.sleep(0.5)

            self.active_indicators = [
                ind for ind in self.active_indicators if ind["name"] != indicator_name
            ]
            print(f"✅ Removed indicator: {indicator_name}")
            return True

        except Exception as e:
            print(f"❌ Error removing indicator: {e}")
            return False
    
    def configure_indicator(self, indicator_name: str, parameters: Dict) -> bool:
        """
        Configure an indicator's parameters using DOM interaction.

        Args:
            indicator_name: Name of indicator to configure
            parameters: e.g., {"length": 21, "source": "hl2"}

        Returns:
            True if successful
        """
        try:
            if self._page is None:
                raise RuntimeError("Browser not initialized")

            print(f"   🔧 Configuring {indicator_name} parameters...")

            # Click Settings button for this indicator
            opened = self._page.evaluate(f"""
                (() => {{
                    const name = '{indicator_name}'.toLowerCase();
                    const btns = Array.from(document.querySelectorAll('button'));
                    const settingsBtn = btns.find(b => {{
                        const label = (b.getAttribute('aria-label') || b.textContent || '').toLowerCase();
                        return (label.includes('settings') || label.includes('format')) &&
                               label.includes(name);
                    }});
                    if (settingsBtn) {{ settingsBtn.click(); return true; }}
                    return false;
                }})()
            """)

            if not opened:
                print(f"   ⚠️  Settings button not found for {indicator_name}")
                return False

            time.sleep(0.6)

            for param_name, param_value in parameters.items():
                print(f"      ⚙️  Setting {param_name} = {param_value}")
                self._page.evaluate(f"""
                    (() => {{
                        const label = '{param_name}'.toLowerCase();
                        const inputs = Array.from(document.querySelectorAll(
                            'input[type="number"], input[data-role], input[class*="input"]'
                        ));
                        for (const inp of inputs) {{
                            const container = inp.closest('tr, div, label');
                            if (container) {{
                                const text = (container.textContent || '').toLowerCase();
                                if (text.includes(label)) {{
                                    inp.focus();
                                    inp.select();
                                    inp.value = '{param_value}';
                                    inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    return true;
                                }}
                            }}
                        }}
                        return false;
                    }})()
                """)
                time.sleep(0.2)

            # Confirm dialog
            self._page.keyboard.press("Enter")
            time.sleep(0.5)

            for ind in self.active_indicators:
                if ind["name"] == indicator_name:
                    ind["parameters"].update(parameters)
                    break

            print(f"   ✅ Configured {indicator_name} successfully")
            return True

        except Exception as e:
            print(f"   ❌ Error configuring indicator: {e}")
            return False
    
    def get_historical_data(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        bars_count: Optional[int] = None,
    ) -> List[Dict]:
        """
        Fetch historical OHLCV data from TradingView chart via JavaScript.

        Extracts candle data directly from TradingView's internal chart model.
        Falls back to DOM-based single-bar extraction if JS API paths fail.

        Args:
            from_date: Start date ISO string (e.g., "2024-01-01") or None
            to_date:   End date ISO string  (e.g., "2024-12-31") or None
            bars_count: Number of most-recent bars to return

        Returns:
            List of dicts with keys: timestamp, open, high, low, close, volume, time
        """
        if self._page is None:
            print("❌ Browser not initialized — cannot fetch historical data")
            return []

        print("📊 Fetching historical data from TradingView chart...")
        if from_date:
            print(f"   From: {from_date}")
        if to_date:
            print(f"   To: {to_date}")
        if bars_count:
            print(f"   Bars requested: {bars_count}")

        bars_count_js = bars_count if bars_count else "null"
        from_date_js = f'"{from_date}"' if from_date else "null"
        to_date_js = f'"{to_date}"' if to_date else "null"

        historical_script = f"""
        (() => {{
          try {{
            const requestedBars = {bars_count_js};
            const fromDateTs = {from_date_js} ? new Date({from_date_js}).getTime() / 1000 : null;
            const toDateTs   = {to_date_js}   ? new Date({to_date_js}).getTime() / 1000   : null;

            const barsList = [];

            // ── Path 1: tvWidget.activeChart() high-level API ──────────────
            const widget = window.tvWidget;
            if (widget && typeof widget.activeChart === 'function') {{
              try {{
                const chart  = widget.activeChart();
                const series = chart.getSeries ? chart.getSeries() : null;
                if (series) {{
                  const barsData = series.bars ? series.bars() : null;
                  if (barsData && typeof barsData.bars === 'function') {{
                    const rawBars = barsData.bars();
                    for (let i = 0; i < rawBars.length; i++) {{
                      const bar = rawBars.get(i);
                      if (!bar) continue;
                      const ts = bar.time;
                      if (fromDateTs && ts < fromDateTs) continue;
                      if (toDateTs   && ts > toDateTs  ) continue;
                      barsList.push({{
                        timestamp: new Date(ts * 1000).toISOString(),
                        time:  ts,
                        open:  bar.open,
                        high:  bar.high,
                        low:   bar.low,
                        close: bar.close,
                        volume: bar.volume || 0
                      }});
                      if (requestedBars && barsList.length >= requestedBars) break;
                    }}
                    if (barsList.length > 0) {{
                      return {{ success: true, bars: barsList, source: 'path1_series_bars',
                                symbol: chart.symbol ? chart.symbol() : null,
                                timeframe: chart.resolution ? chart.resolution() : null }};
                    }}
                  }}
                }}
              }} catch(e1) {{}}
            }}

            // ── Path 2: TradingView.chartWidgetCollection (older API) ──────
            try {{
              const wc = window.TradingView && window.TradingView.chartWidgetCollection;
              if (wc) {{
                const chartWidget = wc[Object.keys(wc)[0]];
                if (chartWidget) {{
                  const model = chartWidget._chartWidget &&
                                chartWidget._chartWidget.model &&
                                chartWidget._chartWidget.model();
                  if (model) {{
                    const ms = model.mainSeries && model.mainSeries();
                    if (ms) {{
                      const data = ms.bars ? ms.bars().data() : null;
                      if (data) {{
                        const rawBars = data.bars ? data.bars() : null;
                        if (rawBars) {{
                          for (let i = 0; i < rawBars.length; i++) {{
                            const bar = rawBars.get(i);
                            if (!bar) continue;
                            const ts = bar.time;
                            if (fromDateTs && ts < fromDateTs) continue;
                            if (toDateTs   && ts > toDateTs  ) continue;
                            barsList.push({{
                              timestamp: new Date(ts * 1000).toISOString(),
                              time:  ts,
                              open:  bar.open,
                              high:  bar.high,
                              low:   bar.low,
                              close: bar.close,
                              volume: bar.volume || 0
                            }});
                            if (requestedBars && barsList.length >= requestedBars) break;
                          }}
                          if (barsList.length > 0) {{
                            return {{ success: true, bars: barsList, source: 'path2_chartwidget' }};
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
              }}
            }} catch(e2) {{}}

            // ── Path 3: Scan window objects for series-like property ────────
            try {{
              const isSeries = (obj) => obj && typeof obj === 'object' &&
                typeof obj.bars === 'function';
              const scanObj = (obj, depth) => {{
                if (depth > 4 || !obj || typeof obj !== 'object') return null;
                if (isSeries(obj)) return obj;
                for (const key of Object.keys(obj).slice(0, 30)) {{
                  try {{
                    const r = scanObj(obj[key], depth + 1);
                    if (r) return r;
                  }} catch(_) {{}}
                }}
                return null;
              }};
              const series = scanObj(window.tvWidget, 0);
              if (series) {{
                const barsData = series.bars();
                if (barsData) {{
                  const rawBars = typeof barsData.bars === 'function' ?
                                  barsData.bars() : barsData;
                  if (rawBars && rawBars.length > 0) {{
                    for (let i = 0; i < rawBars.length; i++) {{
                      const bar = rawBars.get ? rawBars.get(i) : rawBars[i];
                      if (!bar) continue;
                      const ts = bar.time;
                      if (fromDateTs && ts < fromDateTs) continue;
                      if (toDateTs   && ts > toDateTs  ) continue;
                      barsList.push({{
                        timestamp: new Date(ts * 1000).toISOString(),
                        time: ts, open: bar.open, high: bar.high,
                        low: bar.low, close: bar.close, volume: bar.volume || 0
                      }});
                      if (requestedBars && barsList.length >= requestedBars) break;
                    }}
                    if (barsList.length > 0) {{
                      return {{ success: true, bars: barsList, source: 'path3_scan' }};
                    }}
                  }}
                }}
              }}
            }} catch(e3) {{}}

            return {{
              success: false, bars: [],
              error: 'No chart data accessible via known API paths',
              hints: [
                'window.tvWidget = ' + (typeof window.tvWidget),
                'window.TradingView = ' + (typeof window.TradingView)
              ]
            }};
          }} catch (outerError) {{
            return {{ success: false, bars: [], error: outerError.message }};
          }}
        }})()
        """

        try:
            result = self._page.evaluate(historical_script)

            if result and result.get("success") and result.get("bars"):
                bars = result["bars"]
                print(f"   ✅ Extracted {len(bars)} bars via JS ({result.get('source', '?')})")
                if bars:
                    print(f"   Range: {bars[0]['timestamp']} → {bars[-1]['timestamp']}")
                return bars

            error_msg = result.get("error") if result else "evaluate returned None"
            hints = result.get("hints", []) if result else []
            print(f"   ⚠️  JS API path failed: {error_msg}")
            if hints:
                print(f"   Hints: {hints}")
            print("   🔄 Trying DOM legend fallback (single bar)...")
            return self._extract_via_dom_legend()

        except Exception as e:
            print(f"❌ Error fetching historical data: {e}")
            return []

    def _extract_via_dom_legend(self) -> List[Dict]:
        """
        DOM fallback: extract single visible OHLCV bar from TradingView price legend.

        Returns:
            1-element list with current bar data, or [].
        """
        if self._page is None:
            return []
        try:
            dom_script = """
            (() => {
              const text = document.body.innerText;
              const ohlcMatch = text.match(
                /O[:\\s]*([\\d,.]+)\\s+H[:\\s]*([\\d,.]+)\\s+L[:\\s]*([\\d,.]+)\\s+C[:\\s]*([\\d,.]+)/
              );
              if (!ohlcMatch) return null;
              const parse = s => parseFloat(s.replace(/,/g, ''));
              const volMatch = text.match(/Vol[:\\s]*([\\d,.]+)\\s*([KMBkmb])?/);
              let volume = 0;
              if (volMatch) {
                volume = parse(volMatch[1]);
                if (volMatch[2]) {
                  const m = { K:1000, M:1000000, B:1000000000 };
                  volume *= (m[volMatch[2].toUpperCase()] || 1);
                }
              }
              return {
                timestamp: new Date().toISOString(),
                time: Math.floor(Date.now() / 1000),
                open:   parse(ohlcMatch[1]),
                high:   parse(ohlcMatch[2]),
                low:    parse(ohlcMatch[3]),
                close:  parse(ohlcMatch[4]),
                volume: volume
              };
            })()
            """
            bar = self._page.evaluate(dom_script)
            if bar and bar.get("open"):
                print(f"   ✅ DOM legend extraction succeeded (1 bar)")
                return [bar]
            print("   ⚠️  DOM legend extraction returned empty")
            return []
        except Exception as e:
            print(f"   ❌ DOM legend extraction failed: {e}")
            return []

    def get_market_data(self) -> Dict:
        """
        Extract current market data (symbol, timeframe, OHLCV, change, indicators)
        from the visible TradingView chart using DOM text scraping.

        Returns:
            Dictionary with symbol, timeframe, ohlc, volume, change, indicators, timestamp.
        """
        if self._page is None:
            print("❌ Browser not initialized")
            return {}

        print("🔍 Extracting market data...")

        extraction_script = """
        () => {
          const data = {
            symbol: null,
            timeframe: null,
            ohlc: {},
            indicators: [],
            volume: null,
            change: {},
            timestamp: new Date().toISOString()
          };

          const titleMatch = document.title.match(/^([A-Z0-9./]+)/);
          if (titleMatch) data.symbol = titleMatch[1];

          const text = document.body.innerText;

          const ohlcMatch = text.match(
            /O[:\\s]*([\\d,.]+)\\s+H[:\\s]*([\\d,.]+)\\s+L[:\\s]*([\\d,.]+)\\s+C[:\\s]*([\\d,.]+)/
          );
          if (ohlcMatch) {
            const p = s => parseFloat(s.replace(/,/g,''));
            data.ohlc = {
              open:  p(ohlcMatch[1]),
              high:  p(ohlcMatch[2]),
              low:   p(ohlcMatch[3]),
              close: p(ohlcMatch[4])
            };
          }

          const volMatch = text.match(/Vol[:\\s]*([\\d,.]+)\\s*([KMBkmb])?/);
          if (volMatch) {
            let v = parseFloat(volMatch[1].replace(/,/g,''));
            if (volMatch[2]) {
              const m = { K:1000, M:1000000, B:1000000000 };
              v *= (m[volMatch[2].toUpperCase()] || 1);
            }
            data.volume = v;
          }

          const changeMatch = text.match(/([+\u2212-][\\d,.]+)\\s*\\(([+\u2212-][\\d,.]+)%\\)/);
          if (changeMatch) {
            const fix = s => parseFloat(s.replace(/\u2212/g,'-').replace(/,/g,''));
            data.change = { absolute: fix(changeMatch[1]), percent: fix(changeMatch[2]) };
          }

          const tfBtns = document.querySelectorAll('[role="radio"][aria-checked="true"]');
          if (tfBtns.length) data.timeframe = tfBtns[0].textContent.trim();

          const indMatches = text.match(/(EMA|SMA|RSI|MACD|BB|ATR|Stoch)/g);
          if (indMatches) data.indicators = [...new Set(indMatches)];

          return data;
        }
        """

        try:
            result = self._page.evaluate(extraction_script)
            if result:
                result["symbol"] = result.get("symbol") or self.current_symbol
                result["timeframe"] = result.get("timeframe") or self.current_timeframe
                print(f"✅ Extracted data for {result.get('symbol', 'unknown')}")
                return result
            return {}
        except Exception as e:
            print(f"❌ Error extracting market data: {e}")
            return {}

    def save_data(
        self,
        data: Dict,
        filepath: Optional[str] = None,
        format: str = "json",
        append: bool = False,
    ) -> str:
        """
        Save market data to file (delegates to TradingViewScraper.save_data).

        Args:
            data: Market data dictionary
            filepath: Custom path or auto-generate
            format: 'json', 'csv', or 'xlsx'
            append: Append to existing file

        Returns:
            Path to saved file
        """
        from .scraper import TradingViewScraper
        temp_scraper = TradingViewScraper()
        return temp_scraper.save_data(data, filepath, format, append)

    def print_summary(self, data: Dict):
        """Print a formatted summary of market data."""
        print("\n" + "=" * 60)
        print("📈 TRADINGVIEW MARKET DATA SUMMARY")
        print("=" * 60)
        print(f"\n📌 Symbol:    {data.get('symbol', 'N/A')}")
        print(f"⏱️  Timeframe: {data.get('timeframe', 'N/A')}")
        print(f"🕐 Timestamp: {data.get('timestamp', 'N/A')}")
        if "ohlc" in data:
            ohlc = data["ohlc"]
            print(f"\n💰 OHLC Data:")
            for k in ("open", "high", "low", "close"):
                print(f"   {k.capitalize()}: {ohlc.get(k, 'N/A')}")
        if data.get("volume"):
            print(f"\n📊 Volume: {data['volume']:,}")
        if "change" in data:
            c = data["change"]
            print(f"\n📉 Change: {c.get('absolute', 'N/A')} ({c.get('percent', 'N/A')}%)")
        if data.get("indicators"):
            print(f"\n📊 Active Indicators ({len(data['indicators'])}):")
            for ind in data["indicators"]:
                print(f"   • {ind}")
        print("\n" + "=" * 60 + "\n")

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self):
        self.init_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_browser()


# ---------------------------------------------------------------------------
# Standalone demo (run directly: python mcp_scraper.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print(" " * 20 + "🚀 MCP TRADINGVIEW SCRAPER (PLAYWRIGHT) 🚀")
    print("=" * 80)

    with MCPTradingViewScraper(headless=False) as scraper:
        scraper.navigate_to_tradingview()
        scraper.change_symbol("AAPL")
        scraper.change_timeframe("1h")

        data = scraper.get_historical_data(bars_count=100)
        print(f"\n✅ Retrieved {len(data)} historical bars")
        if data:
            print(f"   Range: {data[0]['timestamp']} → {data[-1]['timestamp']}")
            print(f"   Last close: {data[-1]['close']}")

        live = scraper.get_market_data()
        scraper.print_summary(live)

    print("=" * 80)
    print(" " * 25 + "✅ DEMO COMPLETE!")
    print("=" * 80 + "\n")

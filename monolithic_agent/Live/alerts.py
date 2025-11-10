"""
Alert System - Send notifications for important events
"""
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger('LiveTrader.Alerts')


class AlertSystem:
    """
    Send alerts via webhook, Telegram, or other channels
    """
    
    def __init__(self, config):
        """
        Initialize alert system
        
        Args:
            config: Live trading configuration
        """
        self.config = config
        self.enabled = config.enable_alerts
        self.webhook_url = config.alert_webhook_url
        self.telegram_bot_token = config.telegram_bot_token
        self.telegram_chat_id = config.telegram_chat_id
        
        if self.enabled:
            logger.info("Alert system enabled")
            if self.webhook_url:
                logger.info(f"  Webhook: {self.webhook_url[:30]}...")
            if self.telegram_bot_token:
                logger.info("  Telegram: configured")
    
    def send_alert(
        self, 
        message: str, 
        severity: str = 'INFO',
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Send alert through configured channels
        
        Args:
            message: Alert message
            severity: Severity level (INFO, WARNING, ERROR, CRITICAL)
            details: Optional additional details
        """
        if not self.enabled:
            return
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Format message
        formatted_message = self._format_message(message, severity, timestamp, details)
        
        # Send via webhook
        if self.webhook_url:
            self._send_webhook(formatted_message, severity)
        
        # Send via Telegram
        if self.telegram_bot_token and self.telegram_chat_id:
            self._send_telegram(formatted_message, severity)
    
    def _format_message(
        self, 
        message: str, 
        severity: str, 
        timestamp: str,
        details: Optional[Dict[str, Any]]
    ) -> str:
        """Format alert message"""
        emoji = {
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🚨'
        }.get(severity, '')
        
        formatted = f"{emoji} **{severity}** - {timestamp}\n\n{message}"
        
        if details:
            formatted += "\n\n**Details:**\n"
            for key, value in details.items():
                formatted += f"  • {key}: {value}\n"
        
        return formatted
    
    def _send_webhook(self, message: str, severity: str):
        """Send alert via webhook"""
        try:
            payload = {
                'text': message,
                'severity': severity,
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug("Alert sent via webhook")
            else:
                logger.warning(f"Webhook alert failed: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    def _send_telegram(self, message: str, severity: str):
        """Send alert via Telegram"""
        try:
            # Convert Markdown to Telegram format
            telegram_message = message.replace('**', '*')
            
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': telegram_message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.debug("Alert sent via Telegram")
            else:
                logger.warning(f"Telegram alert failed: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
    
    def alert_startup(self):
        """Send startup alert"""
        self.send_alert(
            "Live Trader started",
            severity='INFO',
            details={
                'Mode': 'DRY RUN' if self.config.dry_run else 'LIVE',
                'Strategy': self.config.strategy_id,
                'Symbols': ', '.join(self.config.symbols)
            }
        )
    
    def alert_shutdown(self, summary: Dict[str, Any]):
        """Send shutdown alert with summary"""
        self.send_alert(
            "Live Trader shutdown",
            severity='INFO',
            details=summary
        )
    
    def alert_trade_executed(self, symbol: str, side: str, volume: float, price: float):
        """Alert on trade execution"""
        self.send_alert(
            f"Trade executed: {side} {volume} {symbol} @ {price:.5f}",
            severity='INFO'
        )
    
    def alert_position_closed(self, symbol: str, profit: float):
        """Alert on position closure"""
        severity = 'INFO' if profit >= 0 else 'WARNING'
        emoji = '📈' if profit >= 0 else '📉'
        
        self.send_alert(
            f"{emoji} Position closed: {symbol} - P/L: ${profit:.2f}",
            severity=severity
        )
    
    def alert_error(self, error_message: str, details: Optional[Dict[str, Any]] = None):
        """Alert on error"""
        self.send_alert(
            f"Error: {error_message}",
            severity='ERROR',
            details=details
        )
    
    def alert_kill_switch(self, reason: str):
        """Alert on kill switch activation"""
        self.send_alert(
            f"🚨 KILL SWITCH ACTIVATED: {reason}",
            severity='CRITICAL'
        )
    
    def alert_daily_limit_reached(self, limit_type: str, details: Dict[str, Any]):
        """Alert when daily limit is reached"""
        self.send_alert(
            f"Daily {limit_type} limit reached - trading paused",
            severity='WARNING',
            details=details
        )


# Example usage
if __name__ == "__main__":
    from config import LiveConfig
    
    config = LiveConfig()
    config.enable_alerts = True
    
    alerts = AlertSystem(config)
    
    # Test alerts
    alerts.alert_startup()
    alerts.alert_trade_executed('EURUSD', 'BUY', 0.01, 1.0950)
    alerts.alert_position_closed('EURUSD', 25.50)
    
    print("✓ Alert system test completed")

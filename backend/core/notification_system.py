"""
Notification System
Sends alerts via multiple channels when circuit breaker triggers
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

from core.circuit_breaker import IssueRecord, CircuitState
from utils.logger import setup_logger

logger = setup_logger(__name__)


class NotificationChannel(str, Enum):
    """Notification channels"""
    LOG = "log"
    EMAIL = "email"
    SMS = "sms"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    DASHBOARD = "dashboard"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class NotificationSystem:
    """
    Multi-channel notification system for circuit breaker events
    """
    
    def __init__(self):
        self.enabled_channels = {
            NotificationChannel.LOG: True,
            NotificationChannel.DASHBOARD: True,
            NotificationChannel.EMAIL: False,  # Configure in production
            NotificationChannel.SMS: False,
            NotificationChannel.TELEGRAM: False,
            NotificationChannel.WEBHOOK: False
        }
        
        # Configuration
        self.email_config = {}
        self.sms_config = {}
        self.telegram_config = {}
        self.webhook_urls = []
        
        # Dashboard notifications (stored for real-time display)
        self.dashboard_notifications: List[Dict] = []
        self.max_dashboard_notifications = 50
    
    async def send_alert(
        self,
        issue: IssueRecord,
        priority: NotificationPriority = NotificationPriority.WARNING
    ):
        """Send alert through configured channels"""
        
        message = self._format_message(issue, priority)
        
        # Send to enabled channels
        tasks = []
        
        if self.enabled_channels[NotificationChannel.LOG]:
            tasks.append(self._send_log(message, priority))
        
        if self.enabled_channels[NotificationChannel.DASHBOARD]:
            tasks.append(self._send_dashboard(message, issue, priority))
        
        if self.enabled_channels[NotificationChannel.EMAIL]:
            tasks.append(self._send_email(message, priority))
        
        if self.enabled_channels[NotificationChannel.SMS]:
            tasks.append(self._send_sms(message, priority))
        
        if self.enabled_channels[NotificationChannel.TELEGRAM]:
            tasks.append(self._send_telegram(message, priority))
        
        if self.enabled_channels[NotificationChannel.WEBHOOK]:
            tasks.append(self._send_webhook(message, issue, priority))
        
        # Execute all notifications concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def _format_message(self, issue: IssueRecord, priority: NotificationPriority) -> str:
        """Format notification message"""
        
        emoji_map = {
            CircuitState.ALERT: "⚠️",
            CircuitState.THROTTLE: "🟡",
            CircuitState.HALT: "🔴",
            CircuitState.SHUTDOWN: "☠️"
        }
        
        emoji = emoji_map.get(issue.severity, "ℹ️")
        
        message = f"""
{emoji} AI TRADING SIGMA - Circuit Breaker Alert

Priority: {priority.upper()}
State: {issue.severity.upper()}
Issue: {issue.issue_type}
Time: {issue.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Details:
{self._format_details(issue.details)}

Action Required: {'IMMEDIATE' if priority == NotificationPriority.EMERGENCY else 'Monitor'}
"""
        return message.strip()
    
    def _format_details(self, details: Dict) -> str:
        """Format issue details"""
        lines = []
        for key, value in details.items():
            if isinstance(value, float):
                lines.append(f"  • {key}: {value:.2f}")
            else:
                lines.append(f"  • {key}: {value}")
        return "\n".join(lines)
    
    # ========================================================================
    # CHANNEL IMPLEMENTATIONS
    # ========================================================================
    
    async def _send_log(self, message: str, priority: NotificationPriority):
        """Send to log file"""
        if priority == NotificationPriority.EMERGENCY:
            logger.critical(message)
        elif priority == NotificationPriority.CRITICAL:
            logger.error(message)
        elif priority == NotificationPriority.WARNING:
            logger.warning(message)
        else:
            logger.info(message)
    
    async def _send_dashboard(
        self,
        message: str,
        issue: IssueRecord,
        priority: NotificationPriority
    ):
        """Send to dashboard (stored for real-time display)"""
        notification = {
            'id': f"notif_{datetime.utcnow().timestamp()}",
            'timestamp': datetime.utcnow().isoformat(),
            'priority': priority,
            'severity': issue.severity,
            'issue_type': issue.issue_type,
            'message': message,
            'details': issue.details,
            'read': False
        }
        
        self.dashboard_notifications.append(notification)
        
        # Keep only recent notifications
        if len(self.dashboard_notifications) > self.max_dashboard_notifications:
            self.dashboard_notifications = self.dashboard_notifications[-self.max_dashboard_notifications:]
        
        logger.debug(f"Dashboard notification added: {notification['id']}")
    
    async def _send_email(self, message: str, priority: NotificationPriority):
        """Send email notification"""
        # TODO: Implement email sending
        # This would use SMTP or email service (e.g., SendGrid, AWS SES)
        logger.info(f"Email notification (not configured): {priority}")
        pass
    
    async def _send_sms(self, message: str, priority: NotificationPriority):
        """Send SMS notification"""
        # TODO: Implement SMS sending
        # This would use SMS service (e.g., Twilio, AWS SNS)
        logger.info(f"SMS notification (not configured): {priority}")
        pass
    
    async def _send_telegram(self, message: str, priority: NotificationPriority):
        """Send Telegram notification"""
        # TODO: Implement Telegram bot
        # This would use Telegram Bot API
        logger.info(f"Telegram notification (not configured): {priority}")
        pass
    
    async def _send_webhook(
        self,
        message: str,
        issue: IssueRecord,
        priority: NotificationPriority
    ):
        """Send webhook notification"""
        # TODO: Implement webhook POST
        # This would HTTP POST to configured URLs
        logger.info(f"Webhook notification (not configured): {priority}")
        pass
    
    # ========================================================================
    # CONFIGURATION
    # ========================================================================
    
    def enable_channel(self, channel: NotificationChannel):
        """Enable notification channel"""
        self.enabled_channels[channel] = True
        logger.info(f"Notification channel enabled: {channel}")
    
    def disable_channel(self, channel: NotificationChannel):
        """Disable notification channel"""
        self.enabled_channels[channel] = False
        logger.info(f"Notification channel disabled: {channel}")
    
    def configure_email(self, smtp_host: str, smtp_port: int, from_email: str, to_emails: List[str]):
        """Configure email notifications"""
        self.email_config = {
            'smtp_host': smtp_host,
            'smtp_port': smtp_port,
            'from_email': from_email,
            'to_emails': to_emails
        }
        self.enable_channel(NotificationChannel.EMAIL)
    
    def configure_telegram(self, bot_token: str, chat_ids: List[str]):
        """Configure Telegram notifications"""
        self.telegram_config = {
            'bot_token': bot_token,
            'chat_ids': chat_ids
        }
        self.enable_channel(NotificationChannel.TELEGRAM)
    
    def add_webhook_url(self, url: str):
        """Add webhook URL"""
        self.webhook_urls.append(url)
        self.enable_channel(NotificationChannel.WEBHOOK)
    
    # ========================================================================
    # DASHBOARD API
    # ========================================================================
    
    def get_dashboard_notifications(self, limit: int = 20) -> List[Dict]:
        """Get recent dashboard notifications"""
        return self.dashboard_notifications[-limit:]
    
    def mark_notification_read(self, notification_id: str):
        """Mark notification as read"""
        for notif in self.dashboard_notifications:
            if notif['id'] == notification_id:
                notif['read'] = True
                break
    
    def clear_dashboard_notifications(self):
        """Clear all dashboard notifications"""
        self.dashboard_notifications = []


# Global instance
notification_system = NotificationSystem()


# Export
__all__ = ['NotificationSystem', 'notification_system', 'NotificationPriority', 'NotificationChannel']

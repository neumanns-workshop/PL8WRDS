"""
Alerting and notification system for monitoring events.
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import httpx
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..core.config import get_settings
from .logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class Alert:
    """Alert data structure."""
    id: str
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    component: str
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        if self.acknowledged_at:
            data['acknowledged_at'] = self.acknowledged_at.isoformat()
        data['severity'] = self.severity.value
        data['status'] = self.status.value
        return data


class AlertRule:
    """Alert rule configuration."""
    
    def __init__(self, 
                 name: str,
                 condition: callable,
                 severity: AlertSeverity,
                 component: str,
                 cooldown_seconds: int = 300,  # 5 minutes
                 auto_resolve: bool = False,
                 resolve_condition: Optional[callable] = None):
        self.name = name
        self.condition = condition
        self.severity = severity
        self.component = component
        self.cooldown_seconds = cooldown_seconds
        self.auto_resolve = auto_resolve
        self.resolve_condition = resolve_condition
        self.last_triggered = 0
        self.active_alerts: Set[str] = set()


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""
    
    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
    
    @abstractmethod
    async def send_notification(self, alert: Alert) -> bool:
        """Send notification for an alert. Returns True if successful."""
        pass
    
    @abstractmethod
    async def send_test_notification(self) -> bool:
        """Send a test notification. Returns True if successful."""
        pass


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel."""
    
    def __init__(self, name: str = "email", enabled: bool = None):
        super().__init__(name, enabled if enabled is not None else settings.monitoring.alert_email_enabled)
        self.smtp_host = settings.monitoring.smtp_host
        self.smtp_port = settings.monitoring.smtp_port
        self.smtp_username = settings.monitoring.smtp_username
        self.smtp_password = settings.monitoring.smtp_password
        self.smtp_use_tls = settings.monitoring.smtp_use_tls
        self.from_address = settings.monitoring.alert_email_from
        self.to_addresses = settings.monitoring.alert_email_to
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send email notification."""
        if not self.enabled or not self.to_addresses:
            return False
        
        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = self.from_address
            message["To"] = ", ".join(self.to_addresses)
            message["Subject"] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            # Create email body
            body = self._create_email_body(alert)
            message.attach(MIMEText(body, "html"))
            
            # Send email
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=self.smtp_use_tls
            ) as server:
                if self.smtp_username and self.smtp_password:
                    await server.login(self.smtp_username, self.smtp_password)
                
                await server.send_message(message)
            
            logger.info(f"Email alert sent successfully", alert_id=alert.id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert", alert_id=alert.id, error=str(e))
            return False
    
    async def send_test_notification(self) -> bool:
        """Send test email."""
        test_alert = Alert(
            id="test-alert",
            title="Test Alert",
            description="This is a test alert to verify email notifications are working.",
            severity=AlertSeverity.LOW,
            status=AlertStatus.ACTIVE,
            component="test",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        return await self.send_notification(test_alert)
    
    def _create_email_body(self, alert: Alert) -> str:
        """Create HTML email body."""
        severity_color = {
            AlertSeverity.LOW: "#28a745",
            AlertSeverity.MEDIUM: "#ffc107", 
            AlertSeverity.HIGH: "#fd7e14",
            AlertSeverity.CRITICAL: "#dc3545"
        }.get(alert.severity, "#6c757d")
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: {severity_color}; border-bottom: 2px solid {severity_color}; padding-bottom: 10px;">
                    🚨 {alert.title}
                </h2>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Severity:</strong> <span style="color: {severity_color}; font-weight: bold;">{alert.severity.value.upper()}</span></p>
                    <p><strong>Component:</strong> {alert.component}</p>
                    <p><strong>Status:</strong> {alert.status.value.upper()}</p>
                    <p><strong>Created:</strong> {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    {f'<p><strong>Correlation ID:</strong> {alert.correlation_id}</p>' if alert.correlation_id else ''}
                </div>
                
                <div style="margin: 20px 0;">
                    <h3>Description</h3>
                    <p>{alert.description}</p>
                </div>
                
                {self._format_metadata(alert.metadata) if alert.metadata else ''}
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
                
                <p style="font-size: 12px; color: #6c757d;">
                    This alert was generated by PL8WRDS Monitoring System.
                    Service: {settings.monitoring.service_name} v{settings.monitoring.service_version}
                </p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format metadata as HTML."""
        if not metadata:
            return ""
        
        html = "<div style='margin: 20px 0;'><h3>Additional Information</h3><ul>"
        for key, value in metadata.items():
            html += f"<li><strong>{key}:</strong> {value}</li>"
        html += "</ul></div>"
        return html


class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel using webhooks."""
    
    def __init__(self, name: str = "slack", enabled: bool = None):
        super().__init__(name, enabled if enabled is not None else settings.monitoring.alert_slack_enabled)
        self.webhook_url = settings.monitoring.slack_webhook_url
        self.channel = settings.monitoring.slack_channel
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send Slack notification."""
        if not self.enabled or not self.webhook_url:
            return False
        
        try:
            # Create Slack message
            payload = self._create_slack_payload(alert)
            
            # Send to Slack
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10
                )
                response.raise_for_status()
            
            logger.info(f"Slack alert sent successfully", alert_id=alert.id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert", alert_id=alert.id, error=str(e))
            return False
    
    async def send_test_notification(self) -> bool:
        """Send test Slack message."""
        test_alert = Alert(
            id="test-alert",
            title="Test Alert",
            description="This is a test alert to verify Slack notifications are working.",
            severity=AlertSeverity.LOW,
            status=AlertStatus.ACTIVE,
            component="test",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        return await self.send_notification(test_alert)
    
    def _create_slack_payload(self, alert: Alert) -> Dict[str, Any]:
        """Create Slack webhook payload."""
        severity_emoji = {
            AlertSeverity.LOW: "ℹ️",
            AlertSeverity.MEDIUM: "⚠️",
            AlertSeverity.HIGH: "🔥",
            AlertSeverity.CRITICAL: "🚨"
        }.get(alert.severity, "❓")
        
        severity_color = {
            AlertSeverity.LOW: "good",
            AlertSeverity.MEDIUM: "warning",
            AlertSeverity.HIGH: "danger",
            AlertSeverity.CRITICAL: "danger"
        }.get(alert.severity, "warning")
        
        attachment = {
            "color": severity_color,
            "title": f"{severity_emoji} {alert.title}",
            "text": alert.description,
            "fields": [
                {
                    "title": "Severity",
                    "value": alert.severity.value.upper(),
                    "short": True
                },
                {
                    "title": "Component", 
                    "value": alert.component,
                    "short": True
                },
                {
                    "title": "Status",
                    "value": alert.status.value.upper(),
                    "short": True
                },
                {
                    "title": "Created",
                    "value": alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
                    "short": True
                }
            ],
            "footer": f"PL8WRDS Monitoring | {settings.monitoring.service_name}",
            "ts": int(alert.created_at.timestamp())
        }
        
        # Add correlation ID if available
        if alert.correlation_id:
            attachment["fields"].append({
                "title": "Correlation ID",
                "value": alert.correlation_id,
                "short": False
            })
        
        # Add metadata fields
        if alert.metadata:
            for key, value in alert.metadata.items():
                attachment["fields"].append({
                    "title": key.replace("_", " ").title(),
                    "value": str(value),
                    "short": True
                })
        
        payload = {
            "channel": self.channel,
            "attachments": [attachment]
        }
        
        return payload


class WebhookNotificationChannel(NotificationChannel):
    """Generic webhook notification channel."""
    
    def __init__(self, name: str = "webhook", enabled: bool = None):
        super().__init__(name, enabled if enabled is not None else settings.monitoring.alert_webhook_enabled)
        self.webhook_url = settings.monitoring.alert_webhook_url
        self.timeout = settings.monitoring.alert_webhook_timeout
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send webhook notification."""
        if not self.enabled or not self.webhook_url:
            return False
        
        try:
            # Create payload
            payload = {
                "event_type": "alert",
                "alert": alert.to_dict(),
                "service": {
                    "name": settings.monitoring.service_name,
                    "version": settings.monitoring.service_version,
                    "environment": "development" if settings.is_development else "production"
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Send webhook
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
            
            logger.info(f"Webhook alert sent successfully", alert_id=alert.id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send webhook alert", alert_id=alert.id, error=str(e))
            return False
    
    async def send_test_notification(self) -> bool:
        """Send test webhook."""
        test_alert = Alert(
            id="test-alert",
            title="Test Alert",
            description="This is a test alert to verify webhook notifications are working.",
            severity=AlertSeverity.LOW,
            status=AlertStatus.ACTIVE,
            component="test",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        return await self.send_notification(test_alert)


class AlertManager:
    """Manages alerts, rules, and notifications."""
    
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_rules: List[AlertRule] = []
        self.notification_channels: List[NotificationChannel] = []
        self.alert_history: List[Alert] = []
        self.max_history_size = 1000
        
        self._setup_notification_channels()
        self._setup_default_alert_rules()
    
    def _setup_notification_channels(self):
        """Set up notification channels."""
        if settings.monitoring.alert_email_enabled:
            self.notification_channels.append(EmailNotificationChannel())
        
        if settings.monitoring.alert_slack_enabled:
            self.notification_channels.append(SlackNotificationChannel())
        
        if settings.monitoring.alert_webhook_enabled:
            self.notification_channels.append(WebhookNotificationChannel())
    
    def _setup_default_alert_rules(self):
        """Set up default alert rules."""
        
        # High error rate alert
        self.add_alert_rule(AlertRule(
            name="high_error_rate",
            condition=lambda metrics: self._check_error_rate(metrics),
            severity=AlertSeverity.HIGH,
            component="api",
            cooldown_seconds=300
        ))
        
        # Service unavailable alert
        self.add_alert_rule(AlertRule(
            name="service_unavailable",
            condition=lambda health: self._check_service_health(health),
            severity=AlertSeverity.CRITICAL,
            component="health",
            cooldown_seconds=60
        ))
        
        # High response time alert
        self.add_alert_rule(AlertRule(
            name="high_response_time",
            condition=lambda metrics: self._check_response_time(metrics),
            severity=AlertSeverity.MEDIUM,
            component="performance",
            cooldown_seconds=600
        ))
        
        # Model failure alert
        self.add_alert_rule(AlertRule(
            name="ml_model_failure",
            condition=lambda metrics: self._check_model_health(metrics),
            severity=AlertSeverity.HIGH,
            component="ml_model",
            cooldown_seconds=300
        ))
    
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.alert_rules.append(rule)
    
    def add_notification_channel(self, channel: NotificationChannel):
        """Add a notification channel."""
        self.notification_channels.append(channel)
    
    async def create_alert(self, 
                          title: str,
                          description: str,
                          severity: AlertSeverity,
                          component: str,
                          metadata: Optional[Dict[str, Any]] = None,
                          correlation_id: Optional[str] = None) -> Alert:
        """Create and process a new alert."""
        
        # Create alert
        alert_id = f"{component}_{int(time.time())}_{hash(title) % 10000}"
        now = datetime.now(timezone.utc)
        
        alert = Alert(
            id=alert_id,
            title=title,
            description=description,
            severity=severity,
            status=AlertStatus.ACTIVE,
            component=component,
            created_at=now,
            updated_at=now,
            metadata=metadata,
            correlation_id=correlation_id
        )
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self._add_to_history(alert)
        
        # Send notifications
        await self._send_notifications(alert)
        
        # Log alert creation
        logger.error(
            f"Alert created: {title}",
            alert_id=alert_id,
            severity=severity.value,
            component=component,
            correlation_id=correlation_id
        )
        
        return alert
    
    async def resolve_alert(self, alert_id: str, resolved_by: str = "system") -> bool:
        """Resolve an active alert."""
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now(timezone.utc)
        alert.updated_at = datetime.now(timezone.utc)
        
        # Update metadata
        if alert.metadata is None:
            alert.metadata = {}
        alert.metadata["resolved_by"] = resolved_by
        
        # Remove from active alerts
        del self.active_alerts[alert_id]
        
        # Send resolution notification
        await self._send_notifications(alert)
        
        logger.info(
            f"Alert resolved: {alert.title}",
            alert_id=alert_id,
            resolved_by=resolved_by
        )
        
        return True
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an active alert."""
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.updated_at = datetime.now(timezone.utc)
        
        # Update metadata
        if alert.metadata is None:
            alert.metadata = {}
        alert.metadata["acknowledged_by"] = acknowledged_by
        
        logger.info(
            f"Alert acknowledged: {alert.title}",
            alert_id=alert_id,
            acknowledged_by=acknowledged_by
        )
        
        return True
    
    async def check_alert_rules(self, context: Dict[str, Any]):
        """Check all alert rules against current context."""
        now = time.time()
        
        for rule in self.alert_rules:
            try:
                # Check cooldown
                if now - rule.last_triggered < rule.cooldown_seconds:
                    continue
                
                # Check condition
                if rule.condition(context):
                    # Create alert
                    await self.create_alert(
                        title=f"{rule.name.replace('_', ' ').title()} Alert",
                        description=f"Alert rule '{rule.name}' has been triggered",
                        severity=rule.severity,
                        component=rule.component,
                        metadata={"rule_name": rule.name}
                    )
                    
                    rule.last_triggered = now
                
                # Check for auto-resolution
                elif rule.auto_resolve and rule.resolve_condition and rule.active_alerts:
                    if rule.resolve_condition(context):
                        # Resolve active alerts for this rule
                        for alert_id in list(rule.active_alerts):
                            await self.resolve_alert(alert_id, "auto_resolution")
                            rule.active_alerts.remove(alert_id)
                
            except Exception as e:
                logger.error(f"Error checking alert rule {rule.name}", error=str(e))
    
    async def _send_notifications(self, alert: Alert):
        """Send notifications through all enabled channels."""
        for channel in self.notification_channels:
            if channel.enabled:
                try:
                    await channel.send_notification(alert)
                except Exception as e:
                    logger.error(
                        f"Failed to send notification via {channel.name}",
                        alert_id=alert.id,
                        error=str(e)
                    )
    
    def _add_to_history(self, alert: Alert):
        """Add alert to history."""
        self.alert_history.append(alert)
        
        # Trim history if too large
        if len(self.alert_history) > self.max_history_size:
            self.alert_history = self.alert_history[-self.max_history_size:]
    
    def _check_error_rate(self, metrics: Dict[str, Any]) -> bool:
        """Check if error rate is too high."""
        # This would integrate with your metrics system
        # For now, this is a placeholder
        error_rate = metrics.get("error_rate", 0)
        return error_rate > 0.05  # 5% error rate threshold
    
    def _check_service_health(self, health: Dict[str, Any]) -> bool:
        """Check if service is unhealthy."""
        return health.get("status") == "unhealthy"
    
    def _check_response_time(self, metrics: Dict[str, Any]) -> bool:
        """Check if response time is too high."""
        avg_response_time = metrics.get("avg_response_time", 0)
        return avg_response_time > 2.0  # 2 second threshold
    
    def _check_model_health(self, metrics: Dict[str, Any]) -> bool:
        """Check if ML model is failing."""
        model_errors = metrics.get("model_errors", 0)
        return model_errors > 5  # More than 5 model errors
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history."""
        return self.alert_history[-limit:]
    
    async def test_notifications(self) -> Dict[str, bool]:
        """Test all notification channels."""
        results = {}
        
        for channel in self.notification_channels:
            try:
                success = await channel.send_test_notification()
                results[channel.name] = success
            except Exception as e:
                logger.error(f"Failed to test {channel.name} channel", error=str(e))
                results[channel.name] = False
        
        return results


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
#!/usr/bin/env python3
"""
Real-time Notification System for Student Success Prediction

Provides real-time monitoring and alerting for at-risk students with:
- Risk threshold monitoring and early warning alerts
- WebSocket-based real-time notifications to teachers/staff
- Email/SMS integration for critical alerts
- Customizable alert rules and escalation policies
- Parent/guardian communication workflows

Key Features:
- Real-time risk score monitoring
- Configurable alert thresholds (High Risk: >70%, Critical: >85%)
- Multi-channel notifications (in-app, email, SMS)
- Alert acknowledgment and resolution tracking
- Automated intervention recommendations
"""

import asyncio
import json
import logging
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    RISK_INCREASE = "risk_increase"
    RISK_THRESHOLD = "risk_threshold"  
    ATTENDANCE_DROP = "attendance_drop"
    GRADE_DECLINE = "grade_decline"
    ENGAGEMENT_DROP = "engagement_drop"
    INTERVENTION_NEEDED = "intervention_needed"

@dataclass
class StudentAlert:
    alert_id: str
    student_id: str
    student_name: str
    alert_type: AlertType
    alert_level: AlertLevel
    risk_score: float
    previous_risk_score: float
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False
    assignee: Optional[str] = None
    intervention_recommended: bool = False

@dataclass
class NotificationRule:
    rule_id: str
    name: str
    alert_types: List[AlertType]
    risk_threshold: float
    enabled: bool = True
    channels: List[str] = None  # ['websocket', 'email', 'sms']
    recipients: List[str] = None
    escalation_time: Optional[int] = None  # minutes

class RealTimeNotificationSystem:
    def __init__(self):
        self.active_alerts: Dict[str, StudentAlert] = {}
        self.notification_rules: List[NotificationRule] = []
        self.websocket_connections: Set = set()
        self.alert_history: List[StudentAlert] = []
        self.student_risk_cache: Dict[str, float] = {}
        
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        
        # Initialize default notification rules
        self.setup_default_rules()
        
        logger.info("🔔 Real-time notification system initialized")

    def setup_default_rules(self):
        """Set up default notification rules for common scenarios"""
        default_rules = [
            NotificationRule(
                rule_id="high_risk_threshold",
                name="High Risk Student Alert",
                alert_types=[AlertType.RISK_THRESHOLD],
                risk_threshold=0.70,
                channels=['websocket', 'email'],
                escalation_time=30
            ),
            NotificationRule(
                rule_id="critical_risk_threshold", 
                name="Critical Risk Student Alert",
                alert_types=[AlertType.RISK_THRESHOLD],
                risk_threshold=0.85,
                channels=['websocket', 'email', 'sms'],
                escalation_time=15
            ),
            NotificationRule(
                rule_id="risk_increase",
                name="Risk Score Increase Alert",
                alert_types=[AlertType.RISK_INCREASE],
                risk_threshold=0.50,
                channels=['websocket'],
                escalation_time=60
            ),
            NotificationRule(
                rule_id="attendance_drop",
                name="Attendance Drop Alert", 
                alert_types=[AlertType.ATTENDANCE_DROP],
                risk_threshold=0.30,
                channels=['websocket', 'email'],
                escalation_time=45
            )
        ]
        
        self.notification_rules.extend(default_rules)
        logger.info(f"✅ Set up {len(default_rules)} default notification rules")

    async def monitor_student_risk(self, student_id: str, student_name: str, current_risk: float, 
                                  additional_data: Dict[str, Any] = None) -> List[StudentAlert]:
        """
        Monitor a student's risk score and generate alerts based on configured rules
        
        Args:
            student_id: Unique student identifier
            student_name: Student's display name
            current_risk: Current risk score (0.0 to 1.0)
            additional_data: Additional context (attendance, grades, engagement, etc.)
            
        Returns:
            List of generated alerts
        """
        generated_alerts = []
        previous_risk = self.student_risk_cache.get(student_id, 0.0)
        
        # Update risk cache
        self.student_risk_cache[student_id] = current_risk
        
        # Check for risk threshold alerts
        for rule in self.notification_rules:
            if not rule.enabled:
                continue
                
            if AlertType.RISK_THRESHOLD in rule.alert_types:
                if current_risk >= rule.risk_threshold and previous_risk < rule.risk_threshold:
                    alert = await self.create_risk_threshold_alert(
                        student_id, student_name, current_risk, previous_risk, rule, additional_data
                    )
                    generated_alerts.append(alert)
                    
            elif AlertType.RISK_INCREASE in rule.alert_types:
                risk_increase = current_risk - previous_risk
                if risk_increase >= 0.15 and current_risk >= rule.risk_threshold:  # 15% increase threshold
                    alert = await self.create_risk_increase_alert(
                        student_id, student_name, current_risk, previous_risk, additional_data
                    )
                    generated_alerts.append(alert)

        # Check for specific condition alerts (attendance, grades, engagement)
        if additional_data:
            condition_alerts = await self.check_condition_alerts(
                student_id, student_name, current_risk, additional_data
            )
            generated_alerts.extend(condition_alerts)
        
        # Process and broadcast alerts
        for alert in generated_alerts:
            await self.process_alert(alert)
            
        return generated_alerts

    async def create_risk_threshold_alert(self, student_id: str, student_name: str, 
                                        current_risk: float, previous_risk: float,
                                        rule: NotificationRule, additional_data: Dict) -> StudentAlert:
        """Create a risk threshold alert"""
        
        alert_level = AlertLevel.CRITICAL if current_risk >= 0.85 else AlertLevel.HIGH
        
        message = f"🚨 {student_name} has crossed the {rule.name.lower()} threshold"
        details = {
            'rule_triggered': rule.name,
            'threshold': rule.risk_threshold,
            'risk_increase': current_risk - previous_risk,
            'additional_data': additional_data or {}
        }
        
        alert = StudentAlert(
            alert_id=f"alert_{student_id}_{int(datetime.now().timestamp())}",
            student_id=student_id,
            student_name=student_name,
            alert_type=AlertType.RISK_THRESHOLD,
            alert_level=alert_level,
            risk_score=current_risk,
            previous_risk_score=previous_risk,
            message=message,
            details=details,
            timestamp=datetime.now(),
            intervention_recommended=current_risk >= 0.70
        )
        
        return alert

    async def create_risk_increase_alert(self, student_id: str, student_name: str,
                                       current_risk: float, previous_risk: float,
                                       additional_data: Dict) -> StudentAlert:
        """Create a risk increase alert"""
        
        risk_increase = current_risk - previous_risk
        alert_level = AlertLevel.HIGH if risk_increase >= 0.20 else AlertLevel.MEDIUM
        
        message = f"📈 {student_name}'s risk score increased significantly (+{risk_increase:.1%})"
        details = {
            'risk_increase': risk_increase,
            'additional_data': additional_data or {}
        }
        
        alert = StudentAlert(
            alert_id=f"alert_{student_id}_{int(datetime.now().timestamp())}",
            student_id=student_id,
            student_name=student_name,
            alert_type=AlertType.RISK_INCREASE,
            alert_level=alert_level,
            risk_score=current_risk,
            previous_risk_score=previous_risk,
            message=message,
            details=details,
            timestamp=datetime.now(),
            intervention_recommended=current_risk >= 0.60
        )
        
        return alert

    async def check_condition_alerts(self, student_id: str, student_name: str, 
                                   current_risk: float, data: Dict) -> List[StudentAlert]:
        """Check for specific condition-based alerts (attendance, grades, engagement)"""
        
        alerts = []
        
        # Attendance drop alert
        if 'attendance_rate' in data and data['attendance_rate'] < 0.75:
            alert = StudentAlert(
                alert_id=f"attendance_{student_id}_{int(datetime.now().timestamp())}",
                student_id=student_id,
                student_name=student_name,
                alert_type=AlertType.ATTENDANCE_DROP,
                alert_level=AlertLevel.HIGH if data['attendance_rate'] < 0.60 else AlertLevel.MEDIUM,
                risk_score=current_risk,
                previous_risk_score=current_risk,
                message=f"📅 {student_name} has low attendance: {data['attendance_rate']:.1%}",
                details={'attendance_rate': data['attendance_rate']},
                timestamp=datetime.now(),
                intervention_recommended=True
            )
            alerts.append(alert)
        
        # Grade decline alert
        if 'grade_trend' in data and data['grade_trend'] == 'declining':
            alert = StudentAlert(
                alert_id=f"grades_{student_id}_{int(datetime.now().timestamp())}",
                student_id=student_id,
                student_name=student_name,
                alert_type=AlertType.GRADE_DECLINE,
                alert_level=AlertLevel.MEDIUM,
                risk_score=current_risk,
                previous_risk_score=current_risk,
                message=f"📉 {student_name} shows declining grade trend",
                details={'grade_trend': data['grade_trend'], 'current_gpa': data.get('gpa', 'N/A')},
                timestamp=datetime.now(),
                intervention_recommended=True
            )
            alerts.append(alert)
        
        # Engagement drop alert
        if 'engagement_score' in data and data['engagement_score'] < 0.50:
            alert = StudentAlert(
                alert_id=f"engagement_{student_id}_{int(datetime.now().timestamp())}",
                student_id=student_id,
                student_name=student_name,
                alert_type=AlertType.ENGAGEMENT_DROP,
                alert_level=AlertLevel.MEDIUM,
                risk_score=current_risk,
                previous_risk_score=current_risk,
                message=f"📱 {student_name} has low engagement: {data['engagement_score']:.1%}",
                details={'engagement_score': data['engagement_score']},
                timestamp=datetime.now(),
                intervention_recommended=True
            )
            alerts.append(alert)
            
        return alerts

    async def process_alert(self, alert: StudentAlert):
        """Process and broadcast an alert through configured channels"""
        
        # Add to active alerts
        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)
        
        logger.info(f"🔔 Processing alert: {alert.message}")
        
        # Find applicable notification rules
        applicable_rules = [
            rule for rule in self.notification_rules 
            if rule.enabled and alert.alert_type in rule.alert_types
            and alert.risk_score >= rule.risk_threshold
        ]
        
        # Broadcast through configured channels
        for rule in applicable_rules:
            if 'websocket' in (rule.channels or []):
                await self.broadcast_websocket_alert(alert)
                
            if 'email' in (rule.channels or []) and self.email_user:
                await self.send_email_alert(alert, rule.recipients or [])
                
            # SMS integration would go here
            if 'sms' in (rule.channels or []):
                logger.info(f"📱 SMS alert would be sent for: {alert.message}")

    async def broadcast_websocket_alert(self, alert: StudentAlert):
        """Broadcast alert to all connected WebSocket clients"""
        
        alert_data = {
            'type': 'student_alert',
            'alert': asdict(alert),
            'timestamp': alert.timestamp.isoformat()
        }
        
        # Convert enum values to strings for JSON serialization
        alert_data['alert']['alert_type'] = alert.alert_type.value
        alert_data['alert']['alert_level'] = alert.alert_level.value
        alert_data['alert']['timestamp'] = alert.timestamp.isoformat()
        
        message = json.dumps(alert_data)
        
        # Broadcast to all connected clients
        disconnected_clients = set()
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected_clients.add(websocket)
        
        # Clean up disconnected clients
        self.websocket_connections -= disconnected_clients
        
        logger.info(f"📡 Broadcasted alert to {len(self.websocket_connections)} WebSocket clients")

    async def send_email_alert(self, alert: StudentAlert, recipients: List[str]):
        """Send email notification for alert"""
        
        if not self.email_user or not self.email_password:
            logger.warning("📧 Email credentials not configured - skipping email alert")
            return
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = ', '.join(recipients) if recipients else self.email_user
            msg['Subject'] = f"Student Alert: {alert.student_name} - {alert.alert_level.value.upper()}"
            
            # Create HTML email body
            html_body = f"""
            <html>
                <body>
                    <h2>🚨 Student Success Alert</h2>
                    <div style="border-left: 4px solid #ff6b6b; padding-left: 16px; margin: 16px 0;">
                        <h3>{alert.message}</h3>
                        <p><strong>Student:</strong> {alert.student_name}</p>
                        <p><strong>Alert Level:</strong> {alert.alert_level.value.upper()}</p>
                        <p><strong>Risk Score:</strong> {alert.risk_score:.1%}</p>
                        <p><strong>Previous Risk:</strong> {alert.previous_risk_score:.1%}</p>
                        <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    
                    {f'<p><strong>🎯 Intervention Recommended:</strong> Yes</p>' if alert.intervention_recommended else ''}
                    
                    <h4>Additional Details:</h4>
                    <pre>{json.dumps(alert.details, indent=2)}</pre>
                    
                    <p><em>This alert was generated by the Student Success Prediction System.</em></p>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
                
            logger.info(f"📧 Email alert sent for {alert.student_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send email alert: {e}")

    async def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Acknowledge an alert"""
        
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            self.active_alerts[alert_id].assignee = user_id
            
            # Broadcast acknowledgment
            await self.broadcast_alert_update(alert_id, 'acknowledged')
            
            logger.info(f"✅ Alert {alert_id} acknowledged by {user_id}")
            return True
            
        return False

    async def resolve_alert(self, alert_id: str, user_id: str, resolution_notes: str = None) -> bool:
        """Resolve an alert"""
        
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.assignee = user_id
            
            if resolution_notes:
                alert.details['resolution_notes'] = resolution_notes
                alert.details['resolved_by'] = user_id
                alert.details['resolved_at'] = datetime.now().isoformat()
            
            # Remove from active alerts
            # Keep a resolved copy in history; replace the corresponding history entry if exists
            resolved_copy = alert
            del self.active_alerts[alert_id]
            for i, hist_alert in enumerate(self.alert_history):
                if hist_alert.alert_id == alert_id:
                    self.alert_history[i] = resolved_copy
                    break
            else:
                self.alert_history.append(resolved_copy)
            
            # Broadcast resolution
            await self.broadcast_alert_update(alert_id, 'resolved')
            
            logger.info(f"✅ Alert {alert_id} resolved by {user_id}")
            return True
            
        return False

    async def broadcast_alert_update(self, alert_id: str, update_type: str):
        """Broadcast alert status updates to WebSocket clients"""
        
        update_data = {
            'type': 'alert_update',
            'alert_id': alert_id,
            'update_type': update_type,
            'timestamp': datetime.now().isoformat()
        }
        
        message = json.dumps(update_data)
        
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(message)
            except Exception:
                pass  # Handle in main broadcast method

    def add_websocket_connection(self, websocket):
        """Add a WebSocket connection for real-time notifications"""
        self.websocket_connections.add(websocket)
        logger.info(f"📡 WebSocket connected - {len(self.websocket_connections)} total connections")

    def remove_websocket_connection(self, websocket):
        """Remove a WebSocket connection"""
        self.websocket_connections.discard(websocket)
        logger.info(f"📡 WebSocket disconnected - {len(self.websocket_connections)} total connections")

    def get_active_alerts(self, student_id: str = None) -> List[StudentAlert]:
        """Get active alerts, optionally filtered by student"""
        
        alerts = list(self.active_alerts.values())
        
        if student_id:
            alerts = [alert for alert in alerts if alert.student_id == student_id]
            
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        return alerts

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get notification system statistics"""
        
        total_alerts = len(self.alert_history)
        active_alerts = len(self.active_alerts)
        
        # Count by alert level
        level_counts = {}
        for alert in self.alert_history:
            level = alert.alert_level.value
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # Count by alert type
        type_counts = {}
        for alert in self.alert_history:
            alert_type = alert.alert_type.value
            type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'resolved_alerts': total_alerts - active_alerts,
            'alert_levels': level_counts,
            'alert_types': type_counts,
            'websocket_connections': len(self.websocket_connections),
            'notification_rules': len(self.notification_rules),
            'students_monitored': len(self.student_risk_cache)
        }

# Global notification system instance
notification_system = RealTimeNotificationSystem()
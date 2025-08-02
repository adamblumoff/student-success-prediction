#!/usr/bin/env python3
"""
Real-time Notifications API Endpoints

Provides REST and WebSocket endpoints for the notification system:
- WebSocket connection for real-time alerts
- REST endpoints for alert management
- Notification rule configuration
- Alert acknowledgment and resolution
"""

from fastapi import APIRouter, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import json
import asyncio
from datetime import datetime

# Import our notification system
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from mvp.notifications import notification_system, AlertLevel, AlertType, StudentAlert, NotificationRule
from mvp.simple_auth import simple_auth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

def get_current_user(request: Request):
    """Simple authentication dependency"""
    auth_header = request.headers.get('authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        return simple_auth(credentials)
    
    raise HTTPException(status_code=401, detail="Authentication required")

# Request/Response Models
class StudentRiskUpdate(BaseModel):
    student_id: str = Field(..., description="Student identifier")
    student_name: str = Field(..., description="Student display name")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Current risk score (0.0-1.0)")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional context data")

class AlertAcknowledgment(BaseModel):
    alert_id: str = Field(..., description="Alert identifier")
    user_id: str = Field(..., description="User acknowledging the alert")

class AlertResolution(BaseModel):
    alert_id: str = Field(..., description="Alert identifier")
    user_id: str = Field(..., description="User resolving the alert")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")

class NotificationRuleCreate(BaseModel):
    name: str = Field(..., description="Rule name")
    alert_types: List[str] = Field(..., description="Alert types to monitor")
    risk_threshold: float = Field(..., ge=0.0, le=1.0, description="Risk threshold (0.0-1.0)")
    channels: List[str] = Field(default=['websocket'], description="Notification channels")
    recipients: Optional[List[str]] = Field(None, description="Email recipients")
    escalation_time: Optional[int] = Field(None, description="Escalation time in minutes")

# WebSocket endpoint for real-time notifications
@router.websocket("/notifications/ws")
async def websocket_notifications(websocket: WebSocket):
    """
    WebSocket endpoint for real-time student success notifications
    
    Provides live updates for:
    - New student alerts (risk threshold, attendance, grades)
    - Alert acknowledgments and resolutions
    - System status updates
    """
    await websocket.accept()
    notification_system.add_websocket_connection(websocket)
    
    try:
        # Send initial connection confirmation
        welcome_message = {
            'type': 'connection_established',
            'message': 'Connected to real-time notifications',
            'active_alerts': len(notification_system.get_active_alerts()),
            'timestamp': datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        # Send current active alerts
        active_alerts = notification_system.get_active_alerts()
        if active_alerts:
            for alert in active_alerts[:10]:  # Send last 10 active alerts
                alert_data = {
                    'type': 'student_alert',
                    'alert': {
                        'alert_id': alert.alert_id,
                        'student_id': alert.student_id,
                        'student_name': alert.student_name,
                        'alert_type': alert.alert_type.value,
                        'alert_level': alert.alert_level.value,
                        'risk_score': alert.risk_score,
                        'message': alert.message,
                        'timestamp': alert.timestamp.isoformat(),
                        'acknowledged': alert.acknowledged,
                        'intervention_recommended': alert.intervention_recommended
                    }
                }
                await websocket.send_text(json.dumps(alert_data))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (ping/pong, alert acknowledgments, etc.)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get('type') == 'ping':
                    await websocket.send_text(json.dumps({'type': 'pong', 'timestamp': datetime.now().isoformat()}))
                elif message.get('type') == 'acknowledge_alert':
                    alert_id = message.get('alert_id')
                    user_id = message.get('user_id', 'unknown')
                    if alert_id:
                        await notification_system.acknowledge_alert(alert_id, user_id)
                        
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        notification_system.remove_websocket_connection(websocket)

@router.post("/notifications/monitor")
async def monitor_student_risk(
    risk_update: StudentRiskUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Monitor student risk and trigger alerts if thresholds are exceeded
    
    This endpoint should be called whenever student risk scores are updated
    to enable real-time monitoring and alerting.
    """
    try:
        logger.info(f"🔍 Monitoring risk for {risk_update.student_name}: {risk_update.risk_score:.1%}")
        
        # Monitor student and generate alerts
        alerts = await notification_system.monitor_student_risk(
            student_id=risk_update.student_id,
            student_name=risk_update.student_name,
            current_risk=risk_update.risk_score,
            additional_data=risk_update.additional_data
        )
        
        return JSONResponse({
            'status': 'monitoring_active',
            'student_id': risk_update.student_id,
            'risk_score': risk_update.risk_score,
            'alerts_generated': len(alerts),
            'alerts': [
                {
                    'alert_id': alert.alert_id,
                    'alert_type': alert.alert_type.value,
                    'alert_level': alert.alert_level.value,
                    'message': alert.message,
                    'intervention_recommended': alert.intervention_recommended
                }
                for alert in alerts
            ],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error monitoring student risk: {e}")
        raise HTTPException(status_code=500, detail=f"Risk monitoring failed: {str(e)}")

@router.get("/notifications/alerts")
async def get_alerts(
    request: Request,
    student_id: Optional[str] = None,
    active_only: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """
    Get student alerts, optionally filtered by student ID
    
    Returns active alerts by default, or all alerts if active_only=false
    """
    try:
        if active_only:
            alerts = notification_system.get_active_alerts(student_id)
        else:
            # Get from history
            all_alerts = notification_system.alert_history
            if student_id:
                all_alerts = [alert for alert in all_alerts if alert.student_id == student_id]
            alerts = sorted(all_alerts, key=lambda x: x.timestamp, reverse=True)[:50]  # Last 50
        
        return JSONResponse({
            'alerts': [
                {
                    'alert_id': alert.alert_id,
                    'student_id': alert.student_id,
                    'student_name': alert.student_name,
                    'alert_type': alert.alert_type.value,
                    'alert_level': alert.alert_level.value,
                    'risk_score': alert.risk_score,
                    'previous_risk_score': alert.previous_risk_score,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat(),
                    'acknowledged': alert.acknowledged,
                    'resolved': alert.resolved,
                    'assignee': alert.assignee,
                    'intervention_recommended': alert.intervention_recommended,
                    'details': alert.details
                }
                for alert in alerts
            ],
            'total_count': len(alerts),
            'active_only': active_only,
            'filtered_by_student': student_id is not None
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@router.post("/notifications/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    acknowledgment: AlertAcknowledgment,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Acknowledge a student alert
    
    Acknowledging an alert indicates that a teacher/staff member has seen
    the alert and is taking appropriate action.
    """
    try:
        success = await notification_system.acknowledge_alert(alert_id, acknowledgment.user_id)
        
        if success:
            return JSONResponse({
                'status': 'acknowledged',
                'alert_id': alert_id,
                'acknowledged_by': acknowledgment.user_id,
                'timestamp': datetime.now().isoformat()
            })
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")

@router.post("/notifications/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolution: AlertResolution,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Resolve a student alert
    
    Resolving an alert indicates that the issue has been addressed
    and no further action is needed.
    """
    try:
        success = await notification_system.resolve_alert(
            alert_id, resolution.user_id, resolution.resolution_notes
        )
        
        if success:
            return JSONResponse({
                'status': 'resolved',
                'alert_id': alert_id,
                'resolved_by': resolution.user_id,
                'resolution_notes': resolution.resolution_notes,
                'timestamp': datetime.now().isoformat()
            })
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")

@router.get("/notifications/stats")
async def get_notification_stats(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Get notification system statistics
    
    Returns statistics about alerts, rules, and system health
    """
    try:
        stats = notification_system.get_alert_statistics()
        
        return JSONResponse({
            'notification_system_stats': stats,
            'system_health': {
                'status': 'healthy',
                'uptime': 'active',
                'last_alert': datetime.now().isoformat() if stats['total_alerts'] > 0 else None
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting notification stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.get("/notifications/rules")
async def get_notification_rules(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Get configured notification rules
    """
    try:
        rules = [
            {
                'rule_id': rule.rule_id,
                'name': rule.name,
                'alert_types': [alert_type.value for alert_type in rule.alert_types],
                'risk_threshold': rule.risk_threshold,
                'enabled': rule.enabled,
                'channels': rule.channels,
                'recipients': rule.recipients,
                'escalation_time': rule.escalation_time
            }
            for rule in notification_system.notification_rules
        ]
        
        return JSONResponse({
            'notification_rules': rules,
            'total_rules': len(rules),
            'enabled_rules': len([r for r in notification_system.notification_rules if r.enabled])
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting notification rules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get rules: {str(e)}")

@router.post("/notifications/rules")
async def create_notification_rule(
    rule_data: NotificationRuleCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new notification rule
    """
    try:
        # Convert string alert types to enum
        alert_types = []
        for alert_type_str in rule_data.alert_types:
            try:
                alert_types.append(AlertType(alert_type_str))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid alert type: {alert_type_str}")
        
        # Create new rule
        new_rule = NotificationRule(
            rule_id=f"rule_{int(datetime.now().timestamp())}",
            name=rule_data.name,
            alert_types=alert_types,
            risk_threshold=rule_data.risk_threshold,
            channels=rule_data.channels,
            recipients=rule_data.recipients,
            escalation_time=rule_data.escalation_time
        )
        
        notification_system.notification_rules.append(new_rule)
        
        return JSONResponse({
            'status': 'created',
            'rule_id': new_rule.rule_id,
            'message': f'Notification rule "{rule_data.name}" created successfully'
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating notification rule: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create rule: {str(e)}")

@router.get("/notifications/health")
async def notification_system_health():
    """
    Health check for the notification system
    """
    try:
        stats = notification_system.get_alert_statistics()
        
        return JSONResponse({
            'service': 'Real-time Notification System',
            'status': 'healthy',
            'features': [
                'Real-time WebSocket notifications',
                'Configurable alert thresholds',
                'Multi-channel notifications (WebSocket, Email)',
                'Alert acknowledgment and resolution',
                'Student risk monitoring',
                'Automated intervention recommendations'
            ],
            'statistics': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Notification system health check failed: {e}")
        return JSONResponse({
            'service': 'Real-time Notification System',
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status_code=500)
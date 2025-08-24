"""
Server-Sent Events (SSE) Notifications API

This module provides real-time notification capabilities for admin users through
Server-Sent Events. It manages user-specific event queues and handles both
payment and signup notifications.
"""

import json
import time
import threading
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from flask import Blueprint, Response, request, session, jsonify, current_app

# Create notifications blueprint
notifications_bp = Blueprint('notifications', __name__)

# Thread-safe event queue management
class NotificationManager:
    def __init__(self):
        self._admin_queues = defaultdict(lambda: deque(maxlen=100))  # Max 100 events per admin
        self._recent_notifications = deque(maxlen=50)  # Store last 50 notifications for 5 minutes
        self._lock = threading.RLock()
        self._recent_notification_window = 300  # 5 minutes in seconds
        
    def add_notification(self, admin_id, notification_data):
        """Add notification to specific admin's queue"""
        with self._lock:
            self._admin_queues[admin_id].append(notification_data)
    
    def get_notifications(self, admin_id):
        """Get and clear notifications for specific admin"""
        with self._lock:
            notifications = list(self._admin_queues[admin_id])
            self._admin_queues[admin_id].clear()
            return notifications
    
    def get_recent_notifications(self, admin_id):
        """Get recent notifications (last 5 minutes) for newly connected admin"""
        with self._lock:
            current_time = datetime.now(timezone.utc).timestamp()
            recent_notifications = []
            
            # Filter notifications from the last 5 minutes
            for notification in self._recent_notifications:
                server_timestamp = notification.get('server_timestamp', 0)
                if current_time - server_timestamp <= self._recent_notification_window:
                    recent_notifications.append(notification)
                    
            # Log only if we're in Flask app context
            try:
                current_app.logger.info(f"Found {len(recent_notifications)} recent notifications for admin {admin_id}")
            except RuntimeError:
                # Outside of Flask app context, skip logging
                pass
            return recent_notifications
    
    def cleanup_old_notifications(self):
        """Remove notifications older than 5 minutes from recent storage"""
        with self._lock:
            current_time = datetime.now(timezone.utc).timestamp()
            # Keep only notifications from the last 5 minutes
            valid_notifications = deque(maxlen=50)
            
            for notification in self._recent_notifications:
                server_timestamp = notification.get('server_timestamp', 0)
                if current_time - server_timestamp <= self._recent_notification_window:
                    valid_notifications.append(notification)
                    
            self._recent_notifications = valid_notifications
    
    def broadcast_to_admins(self, notification_data):
        """Broadcast notification to all admin users and store for recent retrieval"""
        try:
            with self._lock:
                # Add timestamp for recent notification tracking
                timestamped_notification = {
                    **notification_data,
                    'server_timestamp': datetime.now(timezone.utc).timestamp()
                }
                
                # Store in recent notifications with timestamp
                self._recent_notifications.append(timestamped_notification)
                
                # Broadcast to all connected admin queues
                for admin_id in list(self._admin_queues.keys()):
                    self._admin_queues[admin_id].append(timestamped_notification)
        except Exception as e:
            try:
                current_app.logger.error(f"Failed to broadcast notification: {e}")
            except RuntimeError:
                # Outside of Flask app context, use print for debugging
                print(f"Failed to broadcast notification: {e}")

# Global notification manager instance
notification_manager = NotificationManager()


@notifications_bp.route('/api/event-stream')
def event_stream():
    """
    SSE endpoint for real-time notifications
    Only accessible to admin users
    """
    # Check if user is admin
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    admin_id = session['admin']  # This is the admin email
    
    def generate():
        """Generate SSE events for the connected admin"""
        last_heartbeat = time.time()
        is_new_connection = True
        
        while True:
            current_time = time.time()
            
            try:
                # For new connections, send recent notifications first
                if is_new_connection:
                    recent_notifications = notification_manager.get_recent_notifications(admin_id)
                    for notification in recent_notifications:
                        yield f"data: {json.dumps(notification)}\n\n"
                    is_new_connection = False
                    
                # Get pending notifications
                notifications = notification_manager.get_notifications(admin_id)
                
                # Send notifications
                for notification in notifications:
                    yield f"data: {json.dumps(notification)}\n\n"
                
                # Send heartbeat every 30 seconds and cleanup old notifications
                if current_time - last_heartbeat >= 30:
                    heartbeat = {
                        'type': 'heartbeat',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    yield f"data: {json.dumps(heartbeat)}\n\n"
                    last_heartbeat = current_time
                    
                    # Cleanup old notifications periodically
                    notification_manager.cleanup_old_notifications()
                
                # Sleep briefly to prevent excessive CPU usage
                time.sleep(1)
                
            except GeneratorExit:
                # Client disconnected
                break
            except Exception as e:
                current_app.logger.error(f"SSE stream error for admin {admin_id}: {e}")
                error_event = {
                    'type': 'error',
                    'message': 'Stream error occurred',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                yield f"data: {json.dumps(error_event)}\n\n"
                break
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )


def emit_payment_notification(passport_data):
    """
    Emit payment notification to all admin users
    
    Args:
        passport_data: Passport object with payment information
    """
    try:
        from utils import get_gravatar_url
        
        notification = {
            'type': 'payment',
            'id': f"payment_{passport_data.id}_{int(time.time())}",
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'passport_id': passport_data.id,
                'user_name': passport_data.user.name if passport_data.user else 'Unknown',
                'email': passport_data.user.email if passport_data.user else 'unknown@example.com',
                'amount': float(passport_data.sold_amt) if passport_data.sold_amt else 0.0,
                'activity': passport_data.activity.name if passport_data.activity else 'Unknown Activity',
                'activity_id': passport_data.activity.id if passport_data.activity else None,
                'avatar': get_gravatar_url(passport_data.user.email if passport_data.user else 'unknown@example.com'),
                'paid_date': passport_data.paid_date.isoformat() if passport_data.paid_date else None
            }
        }
        
        # Broadcast to all admin users
        notification_manager.broadcast_to_admins(notification)
        
        current_app.logger.info(f"Payment notification emitted for passport {passport_data.id}")
        
    except Exception as e:
        current_app.logger.error(f"Failed to emit payment notification: {e}")


def emit_signup_notification(signup):
    """
    Emit signup notification to all admin users
    
    Args:
        signup: Signup object with registration information
    """
    try:
        from utils import get_gravatar_url
        from models import PassportType
        
        # Get passport type info if available
        passport_type = None
        if hasattr(signup, 'passport_type_id') and signup.passport_type_id:
            passport_type = PassportType.query.get(signup.passport_type_id)
        
        notification = {
            'type': 'signup',
            'id': f"signup_{signup.id}_{int(time.time())}",
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'signup_id': signup.id,
                'user_name': signup.user.name if signup.user else 'Unknown',
                'email': signup.user.email if signup.user else 'unknown@example.com',
                'phone': signup.user.phone_number if signup.user else '',
                'activity': signup.activity.name if signup.activity else 'Unknown Activity',
                'activity_id': signup.activity.id if signup.activity else None,
                'passport_type': passport_type.name if passport_type else 'Standard',
                'passport_type_price': float(passport_type.price_per_user) if passport_type else 0.0,
                'avatar': get_gravatar_url(signup.user.email if signup.user else 'unknown@example.com'),
                'created_at': signup.created_at.isoformat() if hasattr(signup, 'created_at') and signup.created_at else None
            }
        }
        
        # Broadcast to all admin users
        notification_manager.broadcast_to_admins(notification)
        
        current_app.logger.info(f"Signup notification emitted for signup {signup.id}")
        
    except Exception as e:
        current_app.logger.error(f"Failed to emit signup notification: {e}")


def broadcast_to_admins(notification_data):
    """
    Public function to broadcast notifications to all admin users
    
    Args:
        notification_data: Dictionary containing notification information
    """
    notification_manager.broadcast_to_admins(notification_data)


# Health check endpoint
@notifications_bp.route('/api/notifications/health')
def health_check():
    """Health check endpoint for SSE service"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'admin_id': session['admin']
    })

# Test notification endpoint
@notifications_bp.route('/api/notifications/test', methods=['POST'])
def test_notification():
    """Test endpoint to trigger a notification"""
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Create a test notification
    test_data = {
        'type': 'signup',
        'id': f"test_{int(time.time())}",
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'user_name': 'Test User',
        'user_email': 'test@example.com',
        'activity_name': 'Test Activity',
        'passport_type': 'Standard Pass'
    }
    
    # Add directly to the admin's queue
    admin_id = session['admin']
    notification_manager.add_notification(admin_id, test_data)
    
    return jsonify({'status': 'success', 'notification': test_data})
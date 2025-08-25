"""
Flask Request Logging Middleware
Provides comprehensive server-side timing analysis to complement client-side network monitoring.

Usage:
    from test.request_logger import RequestLogger
    
    app = Flask(__name__)
    request_logger = RequestLogger(app)
    
    # Or initialize later
    request_logger = RequestLogger()
    request_logger.init_app(app)
"""

import time
import json
import threading
import psutil
import os
from datetime import datetime, timedelta
from collections import defaultdict, deque
from functools import wraps
from flask import Flask, request, response, g
from sqlalchemy import event
from sqlalchemy.engine import Engine
import logging
import sys

class DatabaseQueryTracker:
    """Tracks database queries during request processing"""
    
    def __init__(self):
        self.query_count = 0
        self.query_time = 0.0
        self.queries = []
        self.connection_pool_size = 0
        
    def reset(self):
        self.query_count = 0
        self.query_time = 0.0
        self.queries = []
        self.connection_pool_size = 0

class RequestStats:
    """Thread-safe statistics collection"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self.total_requests = 0
        self.slow_requests = 0
        self.route_stats = defaultdict(lambda: {'count': 0, 'total_time': 0.0, 'max_time': 0.0, 'min_time': float('inf')})
        self.recent_requests = deque(maxlen=1000)  # Keep last 1000 requests
        self.error_requests = defaultdict(int)
        self.static_file_requests = 0
        
    def add_request(self, request_data):
        with self._lock:
            self.total_requests += 1
            
            route = request_data.get('route', 'unknown')
            duration = request_data.get('duration', 0.0)
            status_code = request_data.get('status_code', 200)
            
            # Track slow requests (>1 second)
            if duration > 1.0:
                self.slow_requests += 1
                
            # Track route statistics
            stats = self.route_stats[route]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['max_time'] = max(stats['max_time'], duration)
            stats['min_time'] = min(stats['min_time'], duration)
            
            # Track recent requests
            self.recent_requests.append(request_data)
            
            # Track error requests
            if status_code >= 400:
                self.error_requests[status_code] += 1
                
            # Track static file requests
            if request_data.get('is_static_file', False):
                self.static_file_requests += 1
    
    def get_summary(self):
        with self._lock:
            summary = {
                'total_requests': self.total_requests,
                'slow_requests': self.slow_requests,
                'slow_request_percentage': (self.slow_requests / max(self.total_requests, 1)) * 100,
                'static_file_requests': self.static_file_requests,
                'error_requests': dict(self.error_requests),
                'route_stats': {}
            }
            
            # Process route statistics
            for route, stats in self.route_stats.items():
                if stats['count'] > 0:
                    summary['route_stats'][route] = {
                        'count': stats['count'],
                        'avg_time': stats['total_time'] / stats['count'],
                        'max_time': stats['max_time'],
                        'min_time': stats['min_time'] if stats['min_time'] != float('inf') else 0,
                        'total_time': stats['total_time']
                    }
            
            return summary

class RequestLogger:
    """Comprehensive Flask request logging middleware"""
    
    def __init__(self, app=None, log_file='request_timings.log', json_file='request_analysis.json'):
        self.app = app
        self.log_file = log_file
        self.json_file = json_file
        self.stats = RequestStats()
        self.db_tracker = DatabaseQueryTracker()
        
        # Setup logging
        self.logger = logging.getLogger('request_logger')
        self.logger.setLevel(logging.INFO)
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter(
            '[REQUEST LOGGER] %(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with Flask app"""
        self.app = app
        
        # Setup SQLAlchemy event listeners for query tracking
        self._setup_database_tracking()
        
        # Register Flask hooks
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_appcontext(self._teardown_request)
        
        # Add route for getting statistics
        app.add_url_rule('/admin/request-stats', 'request_stats', self._get_stats_endpoint, methods=['GET'])
        app.add_url_rule('/admin/request-export', 'request_export', self._export_stats_endpoint, methods=['GET'])
        
        self.logger.info("Request logging middleware initialized")
    
    def _setup_database_tracking(self):
        """Setup SQLAlchemy event listeners for query tracking"""
        
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if hasattr(g, 'db_tracker'):
                g.db_tracker.queries.append({
                    'statement': statement[:200] + '...' if len(statement) > 200 else statement,
                    'start_time': time.time()
                })
        
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if hasattr(g, 'db_tracker') and g.db_tracker.queries:
                query = g.db_tracker.queries[-1]
                query_time = time.time() - query['start_time']
                query['duration'] = query_time
                g.db_tracker.query_count += 1
                g.db_tracker.query_time += query_time
                
                # Get connection pool info if available
                try:
                    if hasattr(conn.engine.pool, 'size'):
                        g.db_tracker.connection_pool_size = conn.engine.pool.size()
                except:
                    pass
    
    def _before_request(self):
        """Called before each request"""
        g.start_time = time.time()
        g.start_memory = self._get_memory_usage()
        g.db_tracker = DatabaseQueryTracker()
    
    def _after_request(self, response):
        """Called after each request"""
        try:
            end_time = time.time()
            duration = end_time - g.start_time
            end_memory = self._get_memory_usage()
            memory_delta = end_memory - g.start_memory
            
            # Get request information
            request_data = self._extract_request_data(duration, memory_delta, response)
            
            # Log the request
            self._log_request(request_data)
            
            # Add to statistics
            self.stats.add_request(request_data)
            
            # Warn about slow requests
            if duration > 1.0:
                self.logger.warning(f"SLOW REQUEST: {request.method} {request.path} took {duration:.2f}s")
            
            # Warn about static file serving
            if request_data.get('is_static_file', False):
                self.logger.warning(f"STATIC FILE SERVED BY FLASK: {request.path} - Consider using nginx/CDN")
            
            # Periodic statistics export
            if self.stats.total_requests % 100 == 0:
                self._export_statistics()
                
        except Exception as e:
            self.logger.error(f"Error in request logging: {e}")
        
        return response
    
    def _teardown_request(self, exception):
        """Called at the end of request context"""
        if exception:
            self.logger.error(f"Request ended with exception: {exception}")
    
    def _extract_request_data(self, duration, memory_delta, response):
        """Extract comprehensive request data"""
        
        # Determine if this is a static file request
        is_static_file = self._is_static_file_request(request.path)
        
        # Get route information
        route = self._get_route_name()
        
        # Calculate request/response sizes
        request_size = self._get_request_size()
        response_size = self._get_response_size(response)
        
        # Authentication information
        auth_info = self._get_auth_info()
        
        request_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'method': request.method,
            'path': request.path,
            'route': route,
            'duration': duration,
            'status_code': response.status_code,
            'request_size': request_size,
            'response_size': response_size,
            'memory_delta': memory_delta,
            'user_agent': request.headers.get('User-Agent', '')[:100],
            'remote_addr': request.remote_addr,
            'is_static_file': is_static_file,
            'auth_info': auth_info,
            'query_count': g.db_tracker.query_count if hasattr(g, 'db_tracker') else 0,
            'query_time': g.db_tracker.query_time if hasattr(g, 'db_tracker') else 0.0,
            'queries': g.db_tracker.queries if hasattr(g, 'db_tracker') else [],
            'connection_pool_size': g.db_tracker.connection_pool_size if hasattr(g, 'db_tracker') else 0,
            'referrer': request.referrer or '',
            'args': dict(request.args),
            'form_fields': len(request.form) if request.form else 0,
            'files_uploaded': len(request.files) if request.files else 0
        }
        
        return request_data
    
    def _is_static_file_request(self, path):
        """Determine if request is for a static file"""
        static_extensions = {'.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', '.woff2', '.ttf'}
        return any(path.lower().endswith(ext) for ext in static_extensions) or path.startswith('/static/')
    
    def _get_route_name(self):
        """Get the route name/endpoint"""
        try:
            if request.endpoint:
                return request.endpoint
            else:
                return request.path
        except:
            return 'unknown'
    
    def _get_request_size(self):
        """Calculate request size"""
        size = 0
        try:
            # Headers size (approximate)
            size += sum(len(k) + len(v) for k, v in request.headers.items())
            
            # Content length
            if request.content_length:
                size += request.content_length
            elif hasattr(request, 'data') and request.data:
                size += len(request.data)
                
        except:
            pass
        return size
    
    def _get_response_size(self, response):
        """Calculate response size"""
        try:
            if hasattr(response, 'content_length') and response.content_length:
                return response.content_length
            elif hasattr(response, 'data'):
                return len(response.data)
            else:
                return 0
        except:
            return 0
    
    def _get_auth_info(self):
        """Get authentication information"""
        auth_info = {
            'is_authenticated': False,
            'user_id': None,
            'auth_method': None
        }
        
        try:
            # Check session-based auth (adjust based on your auth implementation)
            from flask import session
            if 'user_id' in session:
                auth_info['is_authenticated'] = True
                auth_info['user_id'] = session.get('user_id')
                auth_info['auth_method'] = 'session'
            
            # Check for API key or token (adjust based on your auth implementation)
            if request.headers.get('Authorization'):
                auth_info['auth_method'] = 'token'
                
        except:
            pass
            
        return auth_info
    
    def _get_memory_usage(self):
        """Get current memory usage"""
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024  # MB
        except:
            return 0
    
    def _log_request(self, request_data):
        """Log request data"""
        log_message = (
            f"{request_data['method']} {request_data['path']} - "
            f"Status: {request_data['status_code']} - "
            f"Duration: {request_data['duration']:.3f}s - "
            f"DB Queries: {request_data['query_count']} ({request_data['query_time']:.3f}s) - "
            f"Memory: {request_data['memory_delta']:+.1f}MB - "
            f"Size: {request_data['request_size']}→{request_data['response_size']} bytes"
        )
        
        if request_data['duration'] > 1.0:
            self.logger.warning(f"SLOW: {log_message}")
        else:
            self.logger.info(log_message)
    
    def _export_statistics(self):
        """Export statistics to JSON file"""
        try:
            stats_summary = self.stats.get_summary()
            stats_summary['export_timestamp'] = datetime.utcnow().isoformat()
            stats_summary['uptime_minutes'] = (time.time() - self.stats.recent_requests[0]['timestamp'] if self.stats.recent_requests else 0) / 60
            
            # Add slowest routes
            if stats_summary['route_stats']:
                sorted_routes = sorted(
                    stats_summary['route_stats'].items(),
                    key=lambda x: x[1]['avg_time'],
                    reverse=True
                )
                stats_summary['slowest_routes'] = sorted_routes[:10]
                stats_summary['most_frequent_routes'] = sorted(
                    stats_summary['route_stats'].items(),
                    key=lambda x: x[1]['count'],
                    reverse=True
                )[:10]
            
            with open(self.json_file, 'w') as f:
                json.dump(stats_summary, f, indent=2)
                
            self.logger.info(f"Statistics exported to {self.json_file}")
            
        except Exception as e:
            self.logger.error(f"Error exporting statistics: {e}")
    
    def _get_stats_endpoint(self):
        """Endpoint to get current statistics"""
        try:
            from flask import jsonify
            stats = self.stats.get_summary()
            stats['recent_requests'] = list(self.stats.recent_requests)[-10:]  # Last 10 requests
            return jsonify(stats)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def _export_stats_endpoint(self):
        """Endpoint to trigger statistics export"""
        try:
            from flask import jsonify
            self._export_statistics()
            return jsonify({'message': f'Statistics exported to {self.json_file}'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_slow_requests(self, threshold=1.0, limit=50):
        """Get recent slow requests"""
        slow_requests = [
            req for req in self.stats.recent_requests
            if req.get('duration', 0) > threshold
        ]
        return sorted(slow_requests, key=lambda x: x.get('duration', 0), reverse=True)[:limit]
    
    def get_route_analysis(self, route=None):
        """Get detailed analysis for a specific route or all routes"""
        if route:
            return self.stats.route_stats.get(route, {})
        else:
            return dict(self.stats.route_stats)

# Convenience function for easy integration
def setup_request_logging(app, log_file='request_timings.log', json_file='request_analysis.json'):
    """
    Easy setup function for request logging
    
    Usage:
        from test.request_logger import setup_request_logging
        setup_request_logging(app)
    """
    return RequestLogger(app, log_file, json_file)

# Example usage and testing
if __name__ == '__main__':
    # This section can be used for testing the logger independently
    print("Request Logger Module")
    print("=====================")
    print("To use this middleware:")
    print("1. from test.request_logger import RequestLogger")
    print("2. request_logger = RequestLogger(app)")
    print("3. Or use setup_request_logging(app) for simple setup")
    print("\nFeatures:")
    print("- Comprehensive request timing")
    print("- Database query tracking")
    print("- Memory usage monitoring")
    print("- Static file detection")
    print("- Authentication tracking")
    print("- Statistics export")
    print("- Admin endpoints for monitoring")
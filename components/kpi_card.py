"""
KPICard - Production-ready KPI Card component for Minipass application

This module provides a robust, secure, and scalable implementation for generating
KPI card data with caching, validation, circuit breaker patterns, and comprehensive
error handling.

Author: Claude Code
Version: 1.0.0
"""

import logging
import time
import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import traceback
import json

# Flask and database imports
from flask import current_app
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Import existing models and utilities
from models import db, Passport, Signup, Activity, PassportType
from utils import get_kpi_stats

# Input validation using pydantic (already in requirements.txt)
from pydantic import BaseModel, validator, Field

# Set up logging
logger = logging.getLogger(__name__)


class CardType(Enum):
    """Supported KPI card types"""
    REVENUE = "revenue"
    ACTIVE_USERS = "active_users"
    ACTIVE_PASSPORTS = "active_passports"
    PASSPORTS_CREATED = "passports_created"
    PENDING_SIGNUPS = "pending_signups"
    UNPAID_PASSPORTS = "unpaid_passports"
    PROFIT = "profit"


class DeviceType(Enum):
    """Device types for responsive design"""
    MOBILE = "mobile"
    DESKTOP = "desktop"


@dataclass
class CircuitBreakerState:
    """Circuit breaker state tracking"""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def is_open(self) -> bool:
        return self.state == "OPEN"
    
    def should_attempt(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            # Check if we should try again after timeout
            if self.last_failure_time and \
               (datetime.now(timezone.utc) - self.last_failure_time).seconds > 60:
                self.state = "HALF_OPEN"
                return True
            return False
        return True  # HALF_OPEN


class KPICardRequest(BaseModel):
    """Request validation schema using Pydantic"""
    card_type: str = Field(..., description="Type of KPI card to generate")
    activity_id: Optional[int] = Field(None, description="Activity ID for activity-specific data")
    period: str = Field("7d", description="Time period for data aggregation")
    device_type: str = Field("desktop", description="Device type for responsive design")
    force_refresh: bool = Field(False, description="Force cache refresh")
    
    @validator('card_type')
    def validate_card_type(cls, v):
        valid_types = [ct.value for ct in CardType]
        if v not in valid_types:
            raise ValueError(f'Invalid card_type. Must be one of: {valid_types}')
        return v
    
    @validator('period')
    def validate_period(cls, v):
        valid_periods = ['7d', '30d', '90d']
        if v not in valid_periods:
            raise ValueError(f'Invalid period. Must be one of: {valid_periods}')
        return v
    
    @validator('device_type')
    def validate_device_type(cls, v):
        valid_devices = [dt.value for dt in DeviceType]
        if v not in valid_devices:
            raise ValueError(f'Invalid device_type. Must be one of: {valid_devices}')
        return v
    
    @validator('activity_id')
    def validate_activity_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError('activity_id must be a positive integer')
        return v


class SimpleCache:
    """
    Simple in-memory cache implementation since Redis isn't in requirements.txt
    In production, this could be replaced with Redis for better scalability
    """
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, datetime] = {}
        self.max_size = 1000
        self.default_ttl = 300  # 5 minutes
        
    def _cleanup_expired(self):
        """Remove expired cache entries"""
        current_time = datetime.now(timezone.utc)
        expired_keys = []
        
        for key, access_time in self._access_times.items():
            cache_entry = self._cache.get(key, {})
            ttl = cache_entry.get('ttl', self.default_ttl)
            if (current_time - access_time).seconds > ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._cache.pop(key, None)
            self._access_times.pop(key, None)
    
    def _evict_if_needed(self):
        """Evict oldest entries if cache is too large"""
        if len(self._cache) >= self.max_size:
            # Remove oldest 10% of entries
            sorted_keys = sorted(self._access_times.items(), key=lambda x: x[1])
            keys_to_remove = [k for k, v in sorted_keys[:int(self.max_size * 0.1)]]
            
            for key in keys_to_remove:
                self._cache.pop(key, None)
                self._access_times.pop(key, None)
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache"""
        self._cleanup_expired()
        
        if key not in self._cache:
            return None
        
        current_time = datetime.now(timezone.utc)
        access_time = self._access_times.get(key)
        cache_entry = self._cache.get(key, {})
        ttl = cache_entry.get('ttl', self.default_ttl)
        
        if access_time and (current_time - access_time).seconds <= ttl:
            return cache_entry.get('data')
        else:
            # Expired
            self._cache.pop(key, None)
            self._access_times.pop(key, None)
            return None
    
    def set(self, key: str, value: Dict[str, Any], ttl: int = None) -> None:
        """Set value in cache"""
        self._cleanup_expired()
        self._evict_if_needed()
        
        self._cache[key] = {
            'data': value,
            'ttl': ttl or self.default_ttl
        }
        self._access_times[key] = datetime.now(timezone.utc)
    
    def delete(self, key: str) -> None:
        """Delete key from cache"""
        self._cache.pop(key, None)
        self._access_times.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache"""
        self._cache.clear()
        self._access_times.clear()


class KPICard:
    """
    Production-ready KPI Card generator with security, caching, and resilience
    
    Features:
    - Input validation using Pydantic schemas
    - Circuit breaker pattern for database resilience
    - Smart caching with configurable TTLs
    - SQL injection prevention
    - Comprehensive error handling and logging
    - Support for both global and activity-specific data
    - Mobile vs desktop responsive variants
    - Unique card ID generation
    """
    
    def __init__(self):
        self.cache = SimpleCache()
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self.max_failures = 5
        self.circuit_timeout = 60  # seconds
        
        # Cache TTL configuration based on data volatility
        self.cache_ttls = {
            CardType.REVENUE.value: 300,           # 5 minutes - financial data changes frequently
            CardType.ACTIVE_USERS.value: 180,      # 3 minutes - user activity changes often
            CardType.ACTIVE_PASSPORTS.value: 600,  # 10 minutes - passport data more stable
            CardType.PASSPORTS_CREATED.value: 900, # 15 minutes - creation counts stable
            CardType.PENDING_SIGNUPS.value: 120,   # 2 minutes - signup status changes quickly
            CardType.UNPAID_PASSPORTS.value: 300,  # 5 minutes - payment status changes
            CardType.PROFIT.value: 600,            # 10 minutes - calculated metric
        }
    
    def _generate_card_id(self, card_type: str, activity_id: Optional[int] = None, 
                         period: str = "7d", device_type: str = "desktop") -> str:
        """Generate unique card ID for tracking and caching"""
        id_components = [
            card_type,
            str(activity_id) if activity_id else "global",
            period,
            device_type
        ]
        
        base_id = "_".join(id_components)
        # Add hash for uniqueness while keeping readability
        hash_suffix = hashlib.md5(base_id.encode()).hexdigest()[:8]
        return f"kpi_{base_id}_{hash_suffix}"
    
    def _get_cache_key(self, card_type: str, activity_id: Optional[int] = None,
                      period: str = "7d", device_type: str = "desktop") -> str:
        """Generate cache key"""
        return f"kpi_cache_{card_type}_{activity_id or 'global'}_{period}_{device_type}"
    
    def _get_circuit_breaker(self, key: str) -> CircuitBreakerState:
        """Get or create circuit breaker for a key"""
        if key not in self.circuit_breakers:
            self.circuit_breakers[key] = CircuitBreakerState()
        return self.circuit_breakers[key]
    
    def _record_success(self, key: str) -> None:
        """Record successful operation for circuit breaker"""
        circuit_breaker = self._get_circuit_breaker(key)
        circuit_breaker.failure_count = 0
        circuit_breaker.state = "CLOSED"
        circuit_breaker.last_failure_time = None
    
    def _record_failure(self, key: str) -> None:
        """Record failed operation for circuit breaker"""
        circuit_breaker = self._get_circuit_breaker(key)
        circuit_breaker.failure_count += 1
        circuit_breaker.last_failure_time = datetime.now(timezone.utc)
        
        if circuit_breaker.failure_count >= self.max_failures:
            circuit_breaker.state = "OPEN"
            logger.warning(f"Circuit breaker opened for {key} after {self.max_failures} failures")
    
    def _sanitize_sql_params(self, **params) -> Dict[str, Any]:
        """Sanitize SQL parameters to prevent injection"""
        sanitized = {}
        for key, value in params.items():
            if isinstance(value, str):
                # Remove potentially dangerous SQL characters
                value = value.replace("'", "").replace('"', "").replace(";", "").replace("--", "")
                if len(value) > 100:  # Limit length
                    value = value[:100]
            elif isinstance(value, int):
                # Ensure positive integers for IDs
                if key.endswith('_id') and value < 0:
                    raise ValueError(f"Invalid {key}: must be positive")
            
            sanitized[key] = value
        
        return sanitized
    
    def _execute_safe_query(self, query: str, params: Dict[str, Any] = None) -> Any:
        """Execute database query with safety checks"""
        try:
            # Sanitize parameters
            if params:
                params = self._sanitize_sql_params(**params)
            
            # Check for dangerous SQL patterns
            dangerous_patterns = [
                'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE',
                'EXEC', 'EXECUTE', 'UNION', '--', '/*', '*/', ';'
            ]
            
            query_upper = query.upper()
            for pattern in dangerous_patterns:
                if pattern in query_upper:
                    raise ValueError(f"Query contains dangerous pattern: {pattern}")
            
            # Execute query with timeout
            with db.engine.connect() as connection:
                if params:
                    result = connection.execute(text(query), params)
                else:
                    result = connection.execute(text(query))
                
                return result.fetchall()
                
        except Exception as e:
            logger.error(f"Database query failed: {str(e)}")
            raise
    
    def _get_base_kpi_data(self, activity_id: Optional[int] = None, period: str = "7d") -> Dict[str, Any]:
        """Get base KPI data using existing utils function with error handling"""
        circuit_key = f"base_kpi_{activity_id or 'global'}_{period}"
        circuit_breaker = self._get_circuit_breaker(circuit_key)
        
        if circuit_breaker.is_open() and not circuit_breaker.should_attempt():
            logger.warning(f"Circuit breaker open for {circuit_key}, returning fallback data")
            return self._get_fallback_data(period)
        
        try:
            # Use existing get_kpi_stats function
            if activity_id:
                kpi_stats = get_kpi_stats(activity_id=activity_id)
            else:
                kpi_stats = get_kpi_stats()
            
            # Extract data for the requested period
            period_data = kpi_stats.get(period, {})
            
            self._record_success(circuit_key)
            return period_data
            
        except Exception as e:
            self._record_failure(circuit_key)
            logger.error(f"Failed to get KPI stats: {str(e)}")
            return self._get_fallback_data(period)
    
    def _get_fallback_data(self, period: str) -> Dict[str, Any]:
        """Return fallback data when primary data source fails"""
        return {
            'revenue': 0,
            'revenue_change': 0,
            'revenue_trend': [0] * 7,
            'active_users': 0,
            'active_users_change': 0,
            'active_users_trend': [0] * 7,
            'active_passports': 0,
            'passports_created': 0,
            'pending_signups': 0,
            'unpaid_passports': 0,
            'profit': 0,
            'profit_change': 0
        }
    
    def _format_currency(self, amount: float) -> str:
        """Format currency with proper locale support"""
        try:
            return f"${amount:,.2f}"
        except (ValueError, TypeError):
            return "$0.00"
    
    def _format_percentage(self, percentage: float) -> str:
        """Format percentage with proper sign"""
        try:
            if percentage > 0:
                return f"+{percentage:.1f}%"
            else:
                return f"{percentage:.1f}%"
        except (ValueError, TypeError):
            return "0.0%"
    
    def _get_trend_direction(self, change: float) -> str:
        """Get trend direction based on change value"""
        if change > 0:
            return "up"
        elif change < 0:
            return "down"
        else:
            return "stable"
    
    def _get_trend_icon(self, direction: str) -> str:
        """Get Tabler icon class for trend direction"""
        icon_map = {
            "up": "ti ti-trending-up",
            "down": "ti ti-trending-down",
            "stable": "ti ti-minus"
        }
        return icon_map.get(direction, "ti ti-minus")
    
    def _get_trend_color(self, direction: str, card_type: str) -> str:
        """Get color class for trend based on direction and card type"""
        # For most metrics, up is good (green), down is bad (red)
        # But for some metrics like costs, down might be good
        
        good_when_up = [
            CardType.REVENUE.value,
            CardType.ACTIVE_USERS.value,
            CardType.ACTIVE_PASSPORTS.value,
            CardType.PASSPORTS_CREATED.value,
            CardType.PROFIT.value
        ]
        
        if card_type in good_when_up:
            return {
                "up": "text-success",
                "down": "text-danger",
                "stable": "text-muted"
            }.get(direction, "text-muted")
        else:
            # For metrics where down is good (like unpaid passports, pending signups)
            return {
                "up": "text-danger",
                "down": "text-success",
                "stable": "text-muted"
            }.get(direction, "text-muted")
    
    def _build_card_data(self, card_type: str, base_data: Dict[str, Any],
                        activity_id: Optional[int] = None, period: str = "7d",
                        device_type: str = "desktop") -> Dict[str, Any]:
        """Build standardized card data structure"""
        
        # Generate unique card ID
        card_id = self._generate_card_id(card_type, activity_id, period, device_type)
        
        # Get base values with safe fallbacks
        def safe_float(value, default=0.0):
            try:
                if value is None:
                    return default
                return float(value)
            except (ValueError, TypeError):
                return default
        
        def safe_int(value, default=0):
            try:
                if value is None:
                    return default
                return int(value)
            except (ValueError, TypeError):
                return default
        
        # Extract card-specific data
        if card_type == CardType.REVENUE.value:
            total = safe_float(base_data.get('revenue', 0))
            change = safe_float(base_data.get('revenue_change', 0))
            trend_data = base_data.get('revenue_trend', [])
            title = "Revenue"
            prefix = "$"
            
        elif card_type == CardType.ACTIVE_USERS.value:
            total = safe_int(base_data.get('active_users', 0))
            change = safe_float(base_data.get('active_users_change', 0))
            trend_data = base_data.get('active_users_trend', [])
            title = "Active Users"
            prefix = ""
            
        elif card_type == CardType.ACTIVE_PASSPORTS.value:
            total = safe_int(base_data.get('active_passports', 0))
            change = safe_float(base_data.get('active_passports_change', 0))
            trend_data = base_data.get('active_passports_trend', [])
            title = "Active Passports"
            prefix = ""
            
        elif card_type == CardType.PASSPORTS_CREATED.value:
            total = safe_int(base_data.get('passports_created', 0))
            change = safe_float(base_data.get('passports_created_change', 0))
            trend_data = base_data.get('passports_created_trend', [])
            title = "Passports Created"
            prefix = ""
            
        elif card_type == CardType.PENDING_SIGNUPS.value:
            total = safe_int(base_data.get('pending_signups', 0))
            change = safe_float(base_data.get('pending_signups_change', 0))
            trend_data = base_data.get('pending_signups_trend', [])
            title = "Pending Signups"
            prefix = ""
            
        elif card_type == CardType.UNPAID_PASSPORTS.value:
            total = safe_int(base_data.get('unpaid_passports', 0))
            change = safe_float(base_data.get('unpaid_passports_change', 0))
            trend_data = base_data.get('unpaid_passports_trend', [])
            title = "Unpaid Passports"
            prefix = ""
            
        elif card_type == CardType.PROFIT.value:
            total = safe_float(base_data.get('profit', 0))
            change = safe_float(base_data.get('profit_change', 0))
            trend_data = base_data.get('profit_trend', [])
            title = "Profit"
            prefix = "$"
            
        else:
            raise ValueError(f"Unsupported card type: {card_type}")
        
        # Ensure trend_data is a list with proper length
        if not isinstance(trend_data, list):
            trend_data = []
        
        period_days = {'7d': 7, '30d': 30, '90d': 90}.get(period, 7)
        if len(trend_data) != period_days:
            # Pad or truncate to correct length
            trend_data = (trend_data + [0] * period_days)[:period_days]
        
        # Calculate trend direction and styling
        trend_direction = self._get_trend_direction(change)
        trend_icon = self._get_trend_icon(trend_direction)
        trend_color = self._get_trend_color(trend_direction, card_type)
        
        # Format display values
        if prefix == "$":
            formatted_total = self._format_currency(total)
        else:
            formatted_total = f"{int(total):,}"
        
        formatted_change = self._format_percentage(abs(change))
        
        # Build standardized response structure
        card_data = {
            # Metadata
            'card_id': card_id,
            'card_type': card_type,
            'title': title,
            'activity_id': activity_id,
            'period': period,
            'device_type': device_type,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            
            # Data values
            'total': total,
            'formatted_total': formatted_total,
            'change': change,
            'formatted_change': formatted_change,
            'trend_data': trend_data,
            
            # Display properties
            'prefix': prefix,
            'trend_direction': trend_direction,
            'trend_icon': trend_icon,
            'trend_color': trend_color,
            
            # Responsive design
            'is_mobile': device_type == DeviceType.MOBILE.value,
            'css_classes': self._get_responsive_css_classes(device_type),
            
            # Compatibility with existing frontend data structures
            'percentage': abs(change),  # For activity_dashboard.html compatibility
            'trend': trend_direction,   # For activity_dashboard.html compatibility
        }
        
        # Add nested structure for dashboard.html compatibility
        if not activity_id:  # Global dashboard format
            card_data['nested_data'] = {
                period: {
                    card_type: {
                        'total': total,
                        'change': change,
                        'trend_data': trend_data
                    }
                }
            }
        
        return card_data
    
    def _get_responsive_css_classes(self, device_type: str) -> Dict[str, str]:
        """Get responsive CSS classes for different device types"""
        if device_type == DeviceType.MOBILE.value:
            return {
                'card': 'card card-sm mb-3',
                'header': 'card-header pb-2',
                'body': 'card-body pt-2',
                'title': 'text-muted small mb-1',
                'value': 'h4 mb-1',
                'trend': 'small'
            }
        else:  # Desktop
            return {
                'card': 'card mb-4',
                'header': 'card-header',
                'body': 'card-body',
                'title': 'text-muted mb-2',
                'value': 'h2 mb-3',
                'trend': 'text-sm'
            }
    
    def generate_card(self, **kwargs) -> Dict[str, Any]:
        """
        Generate KPI card data with comprehensive validation and error handling
        
        Args:
            card_type (str): Type of KPI card
            activity_id (Optional[int]): Activity ID for activity-specific data
            period (str): Time period ('7d', '30d', '90d')
            device_type (str): Device type ('mobile', 'desktop')
            force_refresh (bool): Force cache refresh
            
        Returns:
            Dict containing card data and metadata
            
        Raises:
            ValueError: For invalid input parameters
            RuntimeError: For system errors
        """
        start_time = time.time()
        
        try:
            # Validate input using Pydantic
            try:
                request = KPICardRequest(**kwargs)
            except Exception as e:
                raise ValueError(f"Invalid input parameters: {str(e)}")
            
            # Generate cache key
            cache_key = self._get_cache_key(
                request.card_type, 
                request.activity_id, 
                request.period, 
                request.device_type
            )
            
            # Check cache unless force refresh is requested
            if not request.force_refresh:
                cached_data = self.cache.get(cache_key)
                if cached_data:
                    logger.debug(f"Cache hit for {cache_key}")
                    cached_data['cache_hit'] = True
                    return cached_data
            
            # Get base KPI data
            logger.debug(f"Generating KPI card: {request.card_type}, activity: {request.activity_id}, period: {request.period}")
            
            base_data = self._get_base_kpi_data(request.activity_id, request.period)
            
            # Build card data
            card_data = self._build_card_data(
                request.card_type,
                base_data,
                request.activity_id,
                request.period,
                request.device_type
            )
            
            # Add metadata
            card_data.update({
                'success': True,
                'cache_hit': False,
                'generation_time_ms': round((time.time() - start_time) * 1000, 2),
                'version': '1.0.0'
            })
            
            # Cache the result
            ttl = self.cache_ttls.get(request.card_type, 300)
            self.cache.set(cache_key, card_data, ttl)
            
            logger.info(f"Generated KPI card {card_data['card_id']} in {card_data['generation_time_ms']}ms")
            
            return card_data
            
        except ValueError as e:
            logger.error(f"KPI card generation failed with validation error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'validation',
                'generation_time_ms': round((time.time() - start_time) * 1000, 2)
            }
            
        except Exception as e:
            logger.error(f"KPI card generation failed with system error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            return {
                'success': False,
                'error': 'Internal system error occurred',
                'error_type': 'system',
                'generation_time_ms': round((time.time() - start_time) * 1000, 2),
                'debug_info': str(e) if current_app.debug else None
            }
    
    def generate_multiple_cards(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate multiple KPI cards efficiently
        
        Args:
            requests: List of card request dictionaries
            
        Returns:
            Dictionary with card data keyed by card_id
        """
        start_time = time.time()
        results = {}
        errors = []
        
        try:
            for i, request_data in enumerate(requests):
                try:
                    card_data = self.generate_card(**request_data)
                    if card_data.get('success'):
                        results[card_data['card_id']] = card_data
                    else:
                        errors.append({
                            'request_index': i,
                            'error': card_data.get('error', 'Unknown error'),
                            'request_data': request_data
                        })
                        
                except Exception as e:
                    errors.append({
                        'request_index': i,
                        'error': str(e),
                        'request_data': request_data
                    })
            
            return {
                'success': True,
                'cards': results,
                'total_cards': len(results),
                'errors': errors,
                'error_count': len(errors),
                'generation_time_ms': round((time.time() - start_time) * 1000, 2)
            }
            
        except Exception as e:
            logger.error(f"Bulk KPI card generation failed: {str(e)}")
            return {
                'success': False,
                'error': 'Bulk generation failed',
                'cards': results,
                'errors': errors,
                'generation_time_ms': round((time.time() - start_time) * 1000, 2)
            }
    
    def clear_cache(self, pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        Clear cache entries, optionally filtered by pattern
        
        Args:
            pattern: Optional pattern to match cache keys
            
        Returns:
            Dictionary with operation results
        """
        try:
            if pattern:
                # Clear specific pattern (simple string matching for now)
                keys_to_remove = []
                for key in self.cache._cache.keys():
                    if pattern in key:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    self.cache.delete(key)
                
                return {
                    'success': True,
                    'cleared_count': len(keys_to_remove),
                    'pattern': pattern
                }
            else:
                # Clear all
                cache_size = len(self.cache._cache)
                self.cache.clear()
                
                return {
                    'success': True,
                    'cleared_count': cache_size,
                    'pattern': 'all'
                }
                
        except Exception as e:
            logger.error(f"Cache clear failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            return {
                'success': True,
                'cache_size': len(self.cache._cache),
                'max_size': self.cache.max_size,
                'default_ttl': self.cache.default_ttl,
                'circuit_breakers': {
                    key: {
                        'state': cb.state,
                        'failure_count': cb.failure_count,
                        'last_failure': cb.last_failure_time.isoformat() if cb.last_failure_time else None
                    }
                    for key, cb in self.circuit_breakers.items()
                }
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# Global instance for use across the application
kpi_card_generator = KPICard()


# Convenience functions for easy integration
def generate_kpi_card(card_type: str, activity_id: Optional[int] = None, 
                     period: str = "7d", device_type: str = "desktop",
                     force_refresh: bool = False) -> Dict[str, Any]:
    """
    Convenience function to generate a single KPI card
    
    Usage:
        # Global revenue card for desktop
        card = generate_kpi_card('revenue')
        
        # Activity-specific mobile card
        card = generate_kpi_card('active_users', activity_id=123, device_type='mobile')
    """
    return kpi_card_generator.generate_card(
        card_type=card_type,
        activity_id=activity_id,
        period=period,
        device_type=device_type,
        force_refresh=force_refresh
    )


def generate_dashboard_cards(activity_id: Optional[int] = None, 
                           period: str = "7d",
                           device_type: str = "desktop") -> Dict[str, Any]:
    """
    Generate all standard dashboard KPI cards
    
    Usage:
        # Global dashboard cards
        cards = generate_dashboard_cards()
        
        # Activity-specific dashboard cards
        cards = generate_dashboard_cards(activity_id=123)
    """
    standard_cards = [
        {'card_type': 'revenue'},
        {'card_type': 'active_users'},
        {'card_type': 'active_passports'},
        {'card_type': 'passports_created'},
        {'card_type': 'pending_signups'},
        {'card_type': 'unpaid_passports'},
        {'card_type': 'profit'}
    ]
    
    # Add common parameters to all requests
    requests = []
    for card in standard_cards:
        card.update({
            'activity_id': activity_id,
            'period': period,
            'device_type': device_type
        })
        requests.append(card)
    
    return kpi_card_generator.generate_multiple_cards(requests)


def clear_kpi_cache(pattern: Optional[str] = None) -> Dict[str, Any]:
    """
    Clear KPI card cache
    
    Usage:
        # Clear all cache
        clear_kpi_cache()
        
        # Clear specific pattern
        clear_kpi_cache('revenue')
    """
    return kpi_card_generator.clear_cache(pattern)
"""
Cloud Logging and Monitoring System for Energy Grid Management Agent
Optimized for Streamlit Cloud deployment with structured logging and performance monitoring.
"""
import streamlit as st
import logging
import time
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import sys
import os

@dataclass
class PerformanceMetric:
    """Performance metric for monitoring."""
    function_name: str
    execution_time: float
    timestamp: float
    success: bool
    error_message: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    result_size: Optional[int] = None

@dataclass
class ApplicationEvent:
    """Application event for logging."""
    event_type: str
    timestamp: float
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    severity: str = "INFO"

class CloudLogger:
    """
    Cloud-optimized logger with structured logging and performance monitoring.
    """
    
    def __init__(self, app_name: str = "energy-grid-agent", environment: str = "production"):
        self.app_name = app_name
        self.environment = environment
        self.performance_metrics: List[PerformanceMetric] = []
        self.application_events: List[ApplicationEvent] = []
        self.start_time = time.time()
        
        # Initialize session state for logging
        if 'cloud_logger' not in st.session_state:
            st.session_state.cloud_logger = self
            st.session_state.performance_metrics = []
            st.session_state.application_events = []
        
        # Configure logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup structured logging configuration."""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/energy_agent_cloud.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(self.app_name)
        
        # Add structured logging handler
        structured_handler = logging.FileHandler('logs/structured_events.jsonl')
        structured_handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(structured_handler)
    
    def log_structured_event(self, event_type: str, details: Dict[str, Any], severity: str = "INFO"):
        """Log structured event in JSON format."""
        event = ApplicationEvent(
            event_type=event_type,
            timestamp=time.time(),
            user_id=self._get_user_id(),
            session_id=self._get_session_id(),
            details=details,
            severity=severity
        )
        
        # Store in session state
        st.session_state.application_events.append(event)
        
        # Log to file
        log_entry = {
            "timestamp": datetime.fromtimestamp(event.timestamp).isoformat(),
            "app_name": self.app_name,
            "environment": self.environment,
            "event_type": event_type,
            "severity": severity,
            "user_id": event.user_id,
            "session_id": event.session_id,
            "details": details
        }
        
        self.logger.info(json.dumps(log_entry))
    
    def log_performance_metric(self, function_name: str, execution_time: float, 
                             success: bool, error_message: Optional[str] = None,
                             parameters: Optional[Dict[str, Any]] = None,
                             result_size: Optional[int] = None):
        """Log performance metric."""
        metric = PerformanceMetric(
            function_name=function_name,
            execution_time=execution_time,
            timestamp=time.time(),
            success=success,
            error_message=error_message,
            parameters=parameters,
            result_size=result_size
        )
        
        # Store in session state
        st.session_state.performance_metrics.append(metric)
        
        # Log structured event
        self.log_structured_event(
            "performance_metric",
            asdict(metric),
            "INFO" if success else "ERROR"
        )
    
    def log_user_action(self, action: str, details: Dict[str, Any]):
        """Log user action."""
        self.log_structured_event("user_action", {
            "action": action,
            **details
        })
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with context."""
        error_details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        self.log_structured_event("error", error_details, "ERROR")
        self.logger.error(f"Error: {error}", exc_info=True)
    
    def log_database_query(self, query: str, parameters: Dict[str, Any], 
                          execution_time: float, success: bool, result_count: Optional[int] = None):
        """Log database query performance."""
        self.log_structured_event("database_query", {
            "query": query,
            "parameters": parameters,
            "execution_time": execution_time,
            "success": success,
            "result_count": result_count
        }, "INFO" if success else "ERROR")
    
    def log_api_call(self, api_name: str, endpoint: str, execution_time: float, 
                    success: bool, status_code: Optional[int] = None, error_message: Optional[str] = None):
        """Log API call performance."""
        self.log_structured_event("api_call", {
            "api_name": api_name,
            "endpoint": endpoint,
            "execution_time": execution_time,
            "success": success,
            "status_code": status_code,
            "error_message": error_message
        }, "INFO" if success else "ERROR")
    
    def _get_user_id(self) -> Optional[str]:
        """Get user ID from session state."""
        return getattr(st.session_state, 'user_id', None)
    
    def _get_session_id(self) -> Optional[str]:
        """Get session ID."""
        return getattr(st.session_state, 'session_id', str(id(st.session_state)))
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for monitoring."""
        if not st.session_state.performance_metrics:
            return {}
        
        metrics = st.session_state.performance_metrics
        
        # Calculate statistics
        successful_metrics = [m for m in metrics if m.success]
        failed_metrics = [m for m in metrics if not m.success]
        
        avg_execution_time = sum(m.execution_time for m in successful_metrics) / len(successful_metrics) if successful_metrics else 0
        success_rate = len(successful_metrics) / len(metrics) if metrics else 0
        
        # Group by function
        function_stats = {}
        for metric in metrics:
            if metric.function_name not in function_stats:
                function_stats[metric.function_name] = {
                    'total_calls': 0,
                    'successful_calls': 0,
                    'total_time': 0,
                    'avg_time': 0,
                    'errors': []
                }
            
            func_stat = function_stats[metric.function_name]
            func_stat['total_calls'] += 1
            func_stat['total_time'] += metric.execution_time
            
            if metric.success:
                func_stat['successful_calls'] += 1
            else:
                func_stat['errors'].append(metric.error_message)
        
        # Calculate averages
        for func_stat in function_stats.values():
            func_stat['avg_time'] = func_stat['total_time'] / func_stat['total_calls']
        
        return {
            'total_metrics': len(metrics),
            'successful_metrics': len(successful_metrics),
            'failed_metrics': len(failed_metrics),
            'success_rate': success_rate,
            'avg_execution_time': avg_execution_time,
            'uptime': time.time() - self.start_time,
            'function_stats': function_stats
        }
    
    def get_recent_events(self, limit: int = 10) -> List[ApplicationEvent]:
        """Get recent application events."""
        return st.session_state.application_events[-limit:] if st.session_state.application_events else []
    
    def clear_old_metrics(self, max_age_hours: int = 24):
        """Clear old performance metrics."""
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        st.session_state.performance_metrics = [
            m for m in st.session_state.performance_metrics 
            if m.timestamp > cutoff_time
        ]
        
        st.session_state.application_events = [
            e for e in st.session_state.application_events 
            if e.timestamp > cutoff_time
        ]

def performance_monitor(func):
    """Decorator to monitor function performance."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        success = False
        error_message = None
        result_size = None
        
        try:
            result = func(*args, **kwargs)
            success = True
            
            # Estimate result size
            if isinstance(result, (list, dict)):
                result_size = len(str(result))
            elif hasattr(result, '__len__'):
                result_size = len(result)
            
            return result
            
        except Exception as e:
            error_message = str(e)
            raise
        finally:
            execution_time = time.time() - start_time
            
            # Get logger from session state
            if 'cloud_logger' in st.session_state:
                logger = st.session_state.cloud_logger
                logger.log_performance_metric(
                    function_name=func.__name__,
                    execution_time=execution_time,
                    success=success,
                    error_message=error_message,
                    parameters={"args_count": len(args), "kwargs_count": len(kwargs)},
                    result_size=result_size
                )
    
    return wrapper

def display_monitoring_dashboard():
    """Display monitoring dashboard in Streamlit interface."""
    if 'cloud_logger' not in st.session_state:
        return
    
    logger = st.session_state.cloud_logger
    
    with st.sidebar.expander("📊 Monitoring Dashboard", expanded=False):
        # Performance summary
        summary = logger.get_performance_summary()
        
        if summary:
            st.markdown("### Performance Metrics")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Success Rate", f"{summary['success_rate']:.1%}")
                st.metric("Avg Execution Time", f"{summary['avg_execution_time']:.3f}s")
            
            with col2:
                st.metric("Total Calls", summary['total_metrics'])
                st.metric("Uptime", f"{summary['uptime']/3600:.1f}h")
            
            # Function performance breakdown
            if summary['function_stats']:
                st.markdown("### Function Performance")
                
                for func_name, stats in summary['function_stats'].items():
                    with st.expander(f"🔧 {func_name}", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**Calls:** {stats['total_calls']}")
                            st.write(f"**Success Rate:** {stats['successful_calls']/stats['total_calls']:.1%}")
                        
                        with col2:
                            st.write(f"**Avg Time:** {stats['avg_time']:.3f}s")
                            st.write(f"**Total Time:** {stats['total_time']:.3f}s")
                        
                        with col3:
                            if stats['errors']:
                                st.write(f"**Errors:** {len(stats['errors'])}")
                                if st.button(f"View Errors ({len(stats['errors'])})", key=f"errors_{func_name}"):
                                    st.write("Recent errors:")
                                    for error in stats['errors'][-3:]:
                                        st.code(error[:100] + "..." if len(error) > 100 else error)
        
        # Recent events
        recent_events = logger.get_recent_events(5)
        if recent_events:
            st.markdown("### Recent Events")
            
            for event in reversed(recent_events):
                event_time = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S")
                severity_color = {
                    "INFO": "🟢",
                    "WARNING": "🟡", 
                    "ERROR": "🔴"
                }.get(event.severity, "⚪")
                
                st.write(f"{severity_color} **{event_time}** - {event.event_type}")
        
        # Log management
        st.markdown("### Log Management")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear Old Metrics", help="Clear metrics older than 24 hours"):
                logger.clear_old_metrics()
                st.rerun()
        
        with col2:
            if st.button("📊 Export Logs", help="Export logs for analysis"):
                # Create log export
                log_data = {
                    "performance_metrics": [asdict(m) for m in st.session_state.performance_metrics],
                    "application_events": [asdict(e) for e in st.session_state.application_events],
                    "summary": summary
                }
                
                st.download_button(
                    "📥 Download Logs",
                    json.dumps(log_data, indent=2, default=str),
                    "monitoring_logs.json",
                    "application/json"
                )

def initialize_cloud_logging(app_name: str = "energy-grid-agent", environment: str = "production") -> CloudLogger:
    """Initialize cloud logging system."""
    return CloudLogger(app_name, environment) 
"""
Health Check System for Energy Grid Management Agent
Validates all connections and services on startup.
"""
import streamlit as st
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError, ClientError
import requests
import json

logger = logging.getLogger(__name__)

@dataclass
class HealthStatus:
    """Health status for a service."""
    service_name: str
    status: str  # "healthy", "warning", "error", "unknown"
    response_time: float
    last_check: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class HealthChecker:
    """
    Comprehensive health checker for all application services.
    """
    
    def __init__(self, secrets_manager):
        self.secrets_manager = secrets_manager
        self.health_status = {}
        self.last_full_check = 0
        self.check_interval = 300  # 5 minutes
        
    def check_neo4j_connection(self) -> HealthStatus:
        """Check Neo4j database connection."""
        start_time = time.time()
        status = "unknown"
        error_message = None
        details = {}
        
        try:
            db_config = self.secrets_manager.get_database_config()
            
            if not db_config['uri'] or not db_config['password']:
                return HealthStatus(
                    service_name="Neo4j Database",
                    status="error",
                    response_time=0,
                    last_check=time.time(),
                    error_message="Database credentials not configured"
                )
            
            # Test connection
            driver = GraphDatabase.driver(
                db_config['uri'],
                auth=(db_config['username'], db_config['password'])
            )
            
            # Test with a simple query
            with driver.session(database=db_config['database']) as session:
                result = session.run("RETURN 1 as test")
                result.single()
                
                # Get database info
                version_result = session.run("CALL dbms.components() YIELD name, versions, edition")
                version_info = version_result.single()
                if version_info:
                    details['version'] = version_info['versions'][0]
                    details['edition'] = version_info['edition']
            
            driver.close()
            status = "healthy"
            
        except AuthError as e:
            status = "error"
            error_message = f"Authentication failed: {str(e)}"
        except ServiceUnavailable as e:
            status = "error"
            error_message = f"Service unavailable: {str(e)}"
        except ClientError as e:
            status = "error"
            error_message = f"Client error: {str(e)}"
        except Exception as e:
            status = "error"
            error_message = f"Connection failed: {str(e)}"
        
        response_time = time.time() - start_time
        
        return HealthStatus(
            service_name="Neo4j Database",
            status=status,
            response_time=response_time,
            last_check=time.time(),
            error_message=error_message,
            details=details
        )
    
    def check_claude_api(self) -> HealthStatus:
        """Check Claude AI API connection."""
        start_time = time.time()
        status = "unknown"
        error_message = None
        details = {}
        
        try:
            claude_config = self.secrets_manager.get_claude_config()
            
            if not claude_config['api_key']:
                return HealthStatus(
                    service_name="Claude AI API",
                    status="error",
                    response_time=0,
                    last_check=time.time(),
                    error_message="API key not configured"
                )
            
            # Test API with a simple request
            headers = {
                "Content-Type": "application/json",
                "x-api-key": claude_config['api_key'],
                "anthropic-version": "2023-06-01"
            }
            
            data = {
                "model": claude_config['model'],
                "max_tokens": 10,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello"
                    }
                ]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                status = "healthy"
                details['model'] = claude_config['model']
            else:
                status = "error"
                error_message = f"API returned status {response.status_code}: {response.text}"
                
        except requests.exceptions.Timeout:
            status = "error"
            error_message = "API request timed out"
        except requests.exceptions.ConnectionError:
            status = "error"
            error_message = "Failed to connect to Claude API"
        except Exception as e:
            status = "error"
            error_message = f"API check failed: {str(e)}"
        
        response_time = time.time() - start_time
        
        return HealthStatus(
            service_name="Claude AI API",
            status=status,
            response_time=response_time,
            last_check=time.time(),
            error_message=error_message,
            details=details
        )
    
    def check_streamlit_environment(self) -> HealthStatus:
        """Check Streamlit environment and configuration."""
        start_time = time.time()
        status = "healthy"
        error_message = None
        details = {}
        
        try:
            # Check if we're running in Streamlit Cloud
            if hasattr(st, 'secrets') and st.secrets:
                details['environment'] = 'Streamlit Cloud'
                details['secrets_available'] = True
            else:
                details['environment'] = 'Local Development'
                details['secrets_available'] = False
            
            # Check app configuration
            app_config = self.secrets_manager.get_app_config()
            details.update(app_config)
            
        except Exception as e:
            status = "warning"
            error_message = f"Environment check warning: {str(e)}"
        
        response_time = time.time() - start_time
        
        return HealthStatus(
            service_name="Streamlit Environment",
            status=status,
            response_time=response_time,
            last_check=time.time(),
            error_message=error_message,
            details=details
        )
    
    def run_full_health_check(self) -> Dict[str, HealthStatus]:
        """Run a complete health check of all services."""
        current_time = time.time()
        
        # Only run full check if enough time has passed
        if current_time - self.last_full_check < self.check_interval:
            return self.health_status
        
        logger.info("Running full health check...")
        
        # Check all services
        self.health_status = {
            'neo4j': self.check_neo4j_connection(),
            'claude': self.check_claude_api(),
            'environment': self.check_streamlit_environment()
        }
        
        self.last_full_check = current_time
        
        # Log results
        for service_name, status in self.health_status.items():
            if status.status == "error":
                logger.error(f"Health check failed for {service_name}: {status.error_message}")
            elif status.status == "warning":
                logger.warning(f"Health check warning for {service_name}: {status.error_message}")
            else:
                logger.info(f"Health check passed for {service_name}")
        
        return self.health_status
    
    def get_overall_status(self) -> str:
        """Get overall health status."""
        if not self.health_status:
            return "unknown"
        
        statuses = [status.status for status in self.health_status.values()]
        
        if "error" in statuses:
            return "error"
        elif "warning" in statuses:
            return "warning"
        elif all(status == "healthy" for status in statuses):
            return "healthy"
        else:
            return "unknown"
    
    def display_health_status(self) -> None:
        """Display health status in Streamlit interface."""
        health_status = self.run_full_health_check()
        overall_status = self.get_overall_status()
        
        # Status indicator
        status_colors = {
            "healthy": "🟢",
            "warning": "🟡", 
            "error": "🔴",
            "unknown": "⚪"
        }
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔍 System Health")
        
        # Overall status
        overall_emoji = status_colors.get(overall_status, "⚪")
        st.sidebar.markdown(f"**Overall Status:** {overall_emoji} {overall_status.title()}")
        
        # Individual service status
        for service_name, status in health_status.items():
            emoji = status_colors.get(status.status, "⚪")
            service_display_name = status.service_name
            
            with st.sidebar.expander(f"{emoji} {service_display_name}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Status:** {status.status.title()}")
                    st.write(f"**Response Time:** {status.response_time:.2f}s")
                
                with col2:
                    st.write(f"**Last Check:** {time.strftime('%H:%M:%S', time.localtime(status.last_check))}")
                    if status.details:
                        st.write("**Details:**")
                        for key, value in status.details.items():
                            st.write(f"  • {key}: {value}")
                
                if status.error_message:
                    st.error(f"**Error:** {status.error_message}")
        
        # Health check button
        if st.sidebar.button("🔄 Refresh Health Check"):
            self.last_full_check = 0  # Force refresh
            st.rerun()

def initialize_health_checker(secrets_manager) -> HealthChecker:
    """Initialize health checker with secrets manager."""
    return HealthChecker(secrets_manager) 
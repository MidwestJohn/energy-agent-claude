"""
Enhanced Energy Grid Management Agent - Main Streamlit Application
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
import time
import traceback
from typing import List, Dict, Any, Optional, Tuple
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError, ClientError
import requests
from io import BytesIO
import base64

from config import Config
from claude_utils import ClaudeClient, validate_claude_api_key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Energy Grid Management Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2980b9 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-online { background-color: #28a745; }
    .status-offline { background-color: #dc3545; }
    .status-warning { background-color: #ffc107; }
    
    .footer {
        position: fixed;
        bottom: 0;
        width: 100%;
        background: linear-gradient(90deg, #2c3e50 0%, #34495e 100%);
        color: white;
        padding: 1rem;
        text-align: center;
        font-size: 0.9rem;
    }
    
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    
    .progress-container {
        background-color: #f0f0f0;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .export-button {
        background: linear-gradient(45deg, #4CAF50, #45a049);
        color: white;
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        margin: 0.5rem;
    }
    
    .export-button:hover {
        background: linear-gradient(45deg, #45a049, #4CAF50);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = "disconnected"
if 'energy_tools' not in st.session_state:
    st.session_state.energy_tools = None
if 'claude_client' not in st.session_state:
    st.session_state.claude_client = None
if 'performance_metrics' not in st.session_state:
    st.session_state.performance_metrics = {}
if 'health_status' not in st.session_state:
    st.session_state.health_status = {
        'neo4j': {'status': 'unknown', 'last_check': None, 'response_time': None},
        'claude': {'status': 'unknown', 'last_check': None, 'response_time': None}
    }

def performance_monitor(func):
    """Decorator to monitor function performance."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Store performance metrics
            if 'performance_metrics' not in st.session_state:
                st.session_state.performance_metrics = {}
            
            func_name = func.__name__
            if func_name not in st.session_state.performance_metrics:
                st.session_state.performance_metrics[func_name] = []
            
            st.session_state.performance_metrics[func_name].append({
                'execution_time': execution_time,
                'timestamp': datetime.now(),
                'success': True
            })
            
            # Keep only last 10 measurements
            if len(st.session_state.performance_metrics[func_name]) > 10:
                st.session_state.performance_metrics[func_name] = st.session_state.performance_metrics[func_name][-10:]
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Store error metrics
            func_name = func.__name__
            if func_name not in st.session_state.performance_metrics:
                st.session_state.performance_metrics[func_name] = []
            
            st.session_state.performance_metrics[func_name].append({
                'execution_time': execution_time,
                'timestamp': datetime.now(),
                'success': False,
                'error': str(e)
            })
            
            raise e
    
    return wrapper

@st.cache_data(ttl=300)  # Cache for 5 minutes
def cached_database_query(query_func, *args, **kwargs):
    """Cache database queries to improve performance."""
    return query_func(*args, **kwargs)

def check_neo4j_health(uri: str, username: str, password: str) -> Dict[str, Any]:
    """Check Neo4j database health."""
    try:
        start_time = time.time()
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        with driver.session() as session:
            result = session.run("RETURN 1 as health_check")
            result.single()
        
        response_time = time.time() - start_time
        driver.close()
        
        return {
            'status': 'online',
            'response_time': response_time,
            'last_check': datetime.now(),
            'message': f'Database responding in {response_time:.3f}s'
        }
    except Exception as e:
        return {
            'status': 'offline',
            'response_time': None,
            'last_check': datetime.now(),
            'message': f'Connection failed: {str(e)}'
        }

def check_claude_health(api_key: str) -> Dict[str, Any]:
    """Check Claude API health."""
    try:
        start_time = time.time()
        
        # Simple validation check
        is_valid = validate_claude_api_key(api_key)
        
        if not is_valid:
            return {
                'status': 'offline',
                'response_time': None,
                'last_check': datetime.now(),
                'message': 'Invalid API key format'
            }
        
        # Test API call (simple validation)
        client = ClaudeClient(api_key=api_key)
        test_response = client.analyze_grid_data("Test connection")
        
        response_time = time.time() - start_time
        
        return {
            'status': 'online',
            'response_time': response_time,
            'last_check': datetime.now(),
            'message': f'API responding in {response_time:.3f}s'
        }
    except Exception as e:
        return {
            'status': 'offline',
            'response_time': None,
            'last_check': datetime.now(),
            'message': f'API test failed: {str(e)}'
        }

def export_data_to_csv(data: List[Dict[str, Any]], filename: str) -> str:
    """Export data to CSV and return download link."""
    if not data:
        return None
    
    df = pd.DataFrame(data)
    csv = df.to_csv(index=False)
    
    # Create download link
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv" class="export-button">📥 Download CSV</a>'
    
    return href

def export_data_to_json(data: List[Dict[str, Any]], filename: str) -> str:
    """Export data to JSON and return download link."""
    if not data:
        return None
    
    json_str = json.dumps(data, indent=2, default=str)
    b64 = base64.b64encode(json_str.encode()).decode()
    href = f'<a href="data:file/json;base64,{b64}" download="{filename}.json" class="export-button">📥 Download JSON</a>'
    
    return href

def show_health_status():
    """Display health status of services."""
    st.subheader("🏥 System Health Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📡 Neo4j Database**")
        neo4j_status = st.session_state.health_status['neo4j']
        
        if neo4j_status['status'] == 'online':
            st.success(f"🟢 Online - {neo4j_status['message']}")
        elif neo4j_status['status'] == 'offline':
            st.error(f"🔴 Offline - {neo4j_status['message']}")
        else:
            st.warning("🟡 Unknown")
        
        if neo4j_status['last_check']:
            st.caption(f"Last checked: {neo4j_status['last_check'].strftime('%H:%M:%S')}")
    
    with col2:
        st.markdown("**🤖 Claude AI**")
        claude_status = st.session_state.health_status['claude']
        
        if claude_status['status'] == 'online':
            st.success(f"🟢 Online - {claude_status['message']}")
        elif claude_status['status'] == 'offline':
            st.error(f"🔴 Offline - {claude_status['message']}")
        else:
            st.warning("🟡 Unknown")
        
        if claude_status['last_check']:
            st.caption(f"Last checked: {claude_status['last_check'].strftime('%H:%M:%S')}")

def show_performance_metrics():
    """Display performance metrics."""
    if not st.session_state.performance_metrics:
        return
    
    st.subheader("⚡ Performance Metrics")
    
    metrics_data = []
    for func_name, measurements in st.session_state.performance_metrics.items():
        if measurements:
            avg_time = np.mean([m['execution_time'] for m in measurements if m['success']])
            success_rate = sum(1 for m in measurements if m['success']) / len(measurements)
            
            metrics_data.append({
                'Function': func_name,
                'Avg Time (s)': f"{avg_time:.3f}",
                'Success Rate': f"{success_rate:.1%}",
                'Total Calls': len(measurements)
            })
    
    if metrics_data:
        df = pd.DataFrame(metrics_data)
        st.dataframe(df, use_container_width=True)

def show_help_tooltip(text: str, help_text: str):
    """Display a help tooltip."""
    st.markdown(f"""
    <div class="tooltip">
        {text}
        <span class="tooltiptext">{help_text}</span>
    </div>
    """, unsafe_allow_html=True)

def error_boundary(func):
    """Decorator for error boundary handling."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            st.info("💡 Please check your connection settings and try again.")
            
            # Log the error
            logger.error(f"Error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            
            return None
    
    return wrapper

def show_footer():
    """Display application footer."""
    st.markdown("""
    <div class="footer">
        <strong>⚡ Energy Grid Management Agent v1.0.0</strong> | 
        Powered by Claude AI & Neo4j | 
        Built with Streamlit | 
        © 2024 Energy Grid Management Team
    </div>
    """, unsafe_allow_html=True)

@performance_monitor
@st.cache_data(ttl=600)  # Cache for 10 minutes
def create_maintenance_chart(maintenance_data: List[Dict[str, Any]]) -> Optional[go.Figure]:
    """
    Create a bar chart of maintenance by equipment type.
    
    Args:
        maintenance_data: List of maintenance records
        
    Returns:
        Plotly figure object or None if no data
    """
    if not maintenance_data:
        return None
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(maintenance_data)
        
        # Check if required columns exist
        if 'equipment_type' not in df.columns:
            return None
        
        # Count maintenance by equipment type
        type_counts = df['equipment_type'].value_counts()
        
        if type_counts.empty:
            return None
        
        # Create bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=type_counts.index,
            y=type_counts.values,
            marker=dict(
                color=type_counts.values,
                colorscale='viridis',
                showscale=True,
                colorbar=dict(title="Maintenance Count")
            ),
            hovertemplate=(
                "<b>Equipment Type:</b> %{x}<br>" +
                "<b>Maintenance Count:</b> %{y}<br>" +
                "<extra></extra>"
            ),
            name="Maintenance Count"
        ))
        
        # Update layout
        fig.update_layout(
            title=dict(
                text="Maintenance Frequency by Equipment Type",
                x=0.5,
                font=dict(size=18, color='#2c3e50')
            ),
            xaxis=dict(
                title="Equipment Type",
                titlefont=dict(size=14, color='#34495e'),
                tickfont=dict(size=12),
                tickangle=45
            ),
            yaxis=dict(
                title="Maintenance Count",
                titlefont=dict(size=14, color='#34495e'),
                tickfont=dict(size=12)
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=60, r=60, t=80, b=80),
            height=500,
            showlegend=False,
            hovermode='closest'
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating maintenance chart: {e}")
        return None

@performance_monitor
@st.cache_data(ttl=600)  # Cache for 10 minutes
def create_risk_chart(risk_data: List[Dict[str, Any]]) -> Optional[go.Figure]:
    """
    Create a scatter plot of risk scores vs equipment types.
    
    Args:
        risk_data: List of risk assessment records
        
    Returns:
        Plotly figure object or None if no data
    """
    if not risk_data:
        return None
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(risk_data)
        
        # Check if required columns exist
        if 'equipment_type' not in df.columns or 'risk_score' not in df.columns:
            return None
        
        # Remove rows with missing data
        df = df.dropna(subset=['equipment_type', 'risk_score'])
        
        if df.empty:
            return None
        
        # Create size mapping for criticality
        criticality_size_map = {
            'Critical': 20,
            'High': 15,
            'Medium': 10,
            'Low': 5
        }
        
        df['size'] = df.get('equipment_criticality', 'Medium').map(criticality_size_map).fillna(10)
        
        # Create scatter plot
        fig = go.Figure()
        
        # Group by equipment type for better visualization
        for eq_type in df['equipment_type'].unique():
            type_data = df[df['equipment_type'] == eq_type]
            
            fig.add_trace(go.Scatter(
                x=[eq_type] * len(type_data),
                y=type_data['risk_score'],
                mode='markers',
                marker=dict(
                    size=type_data['size'],
                    color=type_data['risk_score'],
                    colorscale='reds',
                    showscale=True,
                    colorbar=dict(title="Risk Score")
                ),
                text=type_data.get('equipment_name', ''),
                hovertemplate=(
                    "<b>Equipment:</b> %{text}<br>" +
                    "<b>Type:</b> " + eq_type + "<br>" +
                    "<b>Risk Score:</b> %{y:.3f}<br>" +
                    "<b>Criticality:</b> " + type_data.get('equipment_criticality', 'Unknown').iloc[0] + "<br>" +
                    "<extra></extra>"
                ),
                name=eq_type,
                showlegend=True
            ))
        
        # Update layout
        fig.update_layout(
            title=dict(
                text="Equipment Risk Assessment by Type",
                x=0.5,
                font=dict(size=18, color='#2c3e50')
            ),
            xaxis=dict(
                title="Equipment Type",
                titlefont=dict(size=14, color='#34495e'),
                tickfont=dict(size=12),
                tickangle=45
            ),
            yaxis=dict(
                title="Risk Score",
                titlefont=dict(size=14, color='#34495e'),
                tickfont=dict(size=12),
                range=[0, 1]
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=60, r=60, t=80, b=80),
            height=500,
            hovermode='closest',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating risk chart: {e}")
        return None

@performance_monitor
@st.cache_data(ttl=600)  # Cache for 10 minutes
def create_timeline_chart(maintenance_data: List[Dict[str, Any]]) -> Optional[go.Figure]:
    """
    Create a timeline chart of maintenance activities.
    
    Args:
        maintenance_data: List of maintenance records
        
    Returns:
        Plotly figure object or None if no data
    """
    if not maintenance_data:
        return None
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(maintenance_data)
        
        # Check if required columns exist
        if 'maintenance_date' not in df.columns:
            return None
        
        # Convert dates and sort
        df['maintenance_date'] = pd.to_datetime(df['maintenance_date'])
        df = df.sort_values('maintenance_date')
        
        if df.empty:
            return None
        
        # Create timeline chart
        fig = go.Figure()
        
        # Color mapping for maintenance types
        maintenance_colors = {
            'Preventive': '#2ecc71',
            'Corrective': '#e74c3c',
            'Predictive': '#3498db',
            'Emergency': '#f39c12'
        }
        
        for maint_type in df.get('maintenance_type', ['Unknown']).unique():
            type_data = df[df.get('maintenance_type', 'Unknown') == maint_type]
            
            fig.add_trace(go.Scatter(
                x=type_data['maintenance_date'],
                y=[maint_type] * len(type_data),
                mode='markers',
                marker=dict(
                    size=10,
                    color=maintenance_colors.get(maint_type, '#95a5a6'),
                    symbol='circle'
                ),
                text=type_data.get('equipment_name', ''),
                hovertemplate=(
                    "<b>Equipment:</b> %{text}<br>" +
                    "<b>Date:</b> %{x}<br>" +
                    "<b>Type:</b> " + maint_type + "<br>" +
                    "<extra></extra>"
                ),
                name=maint_type
            ))
        
        # Update layout
        fig.update_layout(
            title=dict(
                text="Maintenance Timeline",
                x=0.5,
                font=dict(size=18, color='#2c3e50')
            ),
            xaxis=dict(
                title="Date",
                titlefont=dict(size=14, color='#34495e'),
                tickfont=dict(size=12)
            ),
            yaxis=dict(
                title="Maintenance Type",
                titlefont=dict(size=14, color='#34495e'),
                tickfont=dict(size=12)
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=60, r=60, t=80, b=80),
            height=400,
            hovermode='closest'
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating timeline chart: {e}")
        return None

@performance_monitor
@st.cache_data(ttl=600)  # Cache for 10 minutes
def create_cost_analysis_chart(maintenance_data: List[Dict[str, Any]]) -> Optional[go.Figure]:
    """
    Create a cost analysis chart.
    
    Args:
        maintenance_data: List of maintenance records
        
    Returns:
        Plotly figure object or None if no data
    """
    if not maintenance_data:
        return None
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(maintenance_data)
        
        # Check if required columns exist
        if 'maintenance_cost' not in df.columns:
            return None
        
        # Group by equipment type and calculate costs
        cost_by_type = df.groupby('equipment_type')['maintenance_cost'].agg(['sum', 'mean', 'count']).reset_index()
        
        if cost_by_type.empty:
            return None
        
        # Create subplot
        fig = go.Figure()
        
        # Add bar chart for total costs
        fig.add_trace(go.Bar(
            x=cost_by_type['equipment_type'],
            y=cost_by_type['sum'],
            name='Total Cost',
            marker_color='#3498db',
            hovertemplate=(
                "<b>Equipment Type:</b> %{x}<br>" +
                "<b>Total Cost:</b> $%{y:,.2f}<br>" +
                "<extra></extra>"
            )
        ))
        
        # Update layout
        fig.update_layout(
            title=dict(
                text="Maintenance Cost Analysis by Equipment Type",
                x=0.5,
                font=dict(size=18, color='#2c3e50')
            ),
            xaxis=dict(
                title="Equipment Type",
                titlefont=dict(size=14, color='#34495e'),
                tickfont=dict(size=12),
                tickangle=45
            ),
            yaxis=dict(
                title="Total Cost ($)",
                titlefont=dict(size=14, color='#34495e'),
                tickfont=dict(size=12)
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=60, r=60, t=80, b=80),
            height=500,
            showlegend=False,
            hovermode='closest'
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating cost analysis chart: {e}")
        return None

class EnergyAgentTools:
    """Enhanced tools for energy grid management with performance monitoring."""
    
    def __init__(self, uri: str = None, username: str = None, password: str = None, database: str = None):
        """Initialize the EnergyAgentTools with connection parameters."""
        self.uri = uri or Config.NEO4J_URI
        self.username = username or Config.NEO4J_USERNAME
        self.password = password or Config.NEO4J_PASSWORD
        self.database = database or Config.NEO4J_DATABASE
        self.driver = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Neo4j database with error handling."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_connection_pool_size=50,
                connection_timeout=30
            )
            
            # Test connection
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1")
                
            logger.info("Successfully connected to Neo4j database")
            
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise ConnectionError(f"Failed to connect to Neo4j database: {e}")
    
    @performance_monitor
    def _execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query with error handling and performance monitoring."""
        if not self.driver:
            raise ConnectionError("Database connection not established")
        
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, parameters or {})
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            raise e
    
    @performance_monitor
    def search_equipment_maintenance_records(
        self, 
        equipment_type: Optional[str] = None,
        issue_type: Optional[str] = None,
        days_back: int = 365
    ) -> List[Dict[str, Any]]:
        """
        Search equipment maintenance records with enhanced filtering.
        
        Args:
            equipment_type: Filter by equipment type
            issue_type: Filter by issue type (e.g., vibration, overheating)
            days_back: Number of days to look back
            
        Returns:
            List of maintenance records
        """
        try:
            # Build query with parameters
            query_parts = [
                "MATCH (e:Equipment)-[:HAS_MAINTENANCE_RECORD]->(mr:MaintenanceRecord)"
            ]
            
            params = {}
            
            if equipment_type:
                query_parts.append("WHERE e.type = $equipment_type")
                params['equipment_type'] = equipment_type
            
            if issue_type:
                if equipment_type:
                    query_parts.append("AND")
                else:
                    query_parts.append("WHERE")
                query_parts.append("mr.description CONTAINS $issue_type")
                params['issue_type'] = issue_type
            
            # Add date filter
            if equipment_type or issue_type:
                query_parts.append("AND")
            else:
                query_parts.append("WHERE")
            query_parts.append("mr.date >= datetime() - duration({days: $days_back})")
            params['days_back'] = days_back
            
            query_parts.extend([
                "RETURN e.id as equipment_id, e.type as equipment_type,",
                "e.name as equipment_name, e.location as equipment_location,",
                "e.criticality as equipment_criticality, mr.date as maintenance_date,",
                "mr.description as maintenance_description, mr.type as maintenance_type,",
                "mr.cost as maintenance_cost",
                "ORDER BY mr.date DESC"
            ])
            
            query = " ".join(query_parts)
            
            return self._execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Error searching maintenance records: {e}")
            return []
    
    @performance_monitor
    def get_risky_equipment(self, risk_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Get equipment with risk scores above threshold.
        
        Args:
            risk_threshold: Minimum risk score threshold
            
        Returns:
            List of risky equipment
        """
        try:
            query = """
            MATCH (e:Equipment)-[:HAS_RISK_ASSESSMENT]->(ra:RiskAssessment)
            WHERE ra.risk_score >= $risk_threshold
            RETURN e.id as equipment_id, e.type as equipment_type,
                   e.name as equipment_name, e.location as equipment_location,
                   e.criticality as equipment_criticality, ra.risk_score as risk_score,
                   ra.risk_factors as risk_factors, ra.assessment_date as assessment_date
            ORDER BY ra.risk_score DESC
            """
            
            return self._execute_query(query, {'risk_threshold': risk_threshold})
            
        except Exception as e:
            logger.error(f"Error getting risky equipment: {e}")
            return []
    
    @performance_monitor
    def get_installation_equipments_dependency(self, installation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get equipment dependencies for installations.
        
        Args:
            installation_id: Specific installation ID (optional)
            
        Returns:
            List of installation dependencies
        """
        try:
            if installation_id:
                query = """
                MATCH (i:Installation {id: $installation_id})-[:CONTAINS]->(e:Equipment)
                OPTIONAL MATCH (e)-[:DEPENDS_ON]->(dep:Equipment)
                OPTIONAL MATCH (e)-[:HAS_MAINTENANCE_RECORD]->(mr:MaintenanceRecord)
                OPTIONAL MATCH (e)-[:HAS_RISK_ASSESSMENT]->(ra:RiskAssessment)
                RETURN i.id as installation_id, i.name as installation_name,
                       i.type as installation_type, e.id as equipment_id,
                       e.type as equipment_type, e.name as equipment_name,
                       e.criticality as equipment_criticality,
                       collect(DISTINCT dep.id) as dependent_equipment,
                       collect(DISTINCT {date: mr.date, type: mr.type, description: mr.description}) as maintenance_history,
                       ra.risk_score as current_risk_score
                ORDER BY e.criticality DESC
                """
                params = {'installation_id': installation_id}
            else:
                query = """
                MATCH (i:Installation)-[:CONTAINS]->(e:Equipment)
                OPTIONAL MATCH (e)-[:DEPENDS_ON]->(dep:Equipment)
                OPTIONAL MATCH (e)-[:HAS_MAINTENANCE_RECORD]->(mr:MaintenanceRecord)
                OPTIONAL MATCH (e)-[:HAS_RISK_ASSESSMENT]->(ra:RiskAssessment)
                RETURN i.id as installation_id, i.name as installation_name,
                       i.type as installation_type, e.id as equipment_id,
                       e.type as equipment_type, e.name as equipment_name,
                       e.criticality as equipment_criticality,
                       collect(DISTINCT dep.id) as dependent_equipment,
                       collect(DISTINCT {date: mr.date, type: mr.type, description: mr.description}) as maintenance_history,
                       ra.risk_score as current_risk_score
                ORDER BY i.name, e.criticality DESC
                """
                params = {}
            
            return self._execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Error getting installation dependencies: {e}")
            return []
    
    @performance_monitor
    def get_vibration_analysis(self, equipment_type: Optional[str] = None, days_back: int = 90) -> List[Dict[str, Any]]:
        """
        Get vibration analysis data for equipment.
        
        Args:
            equipment_type: Filter by equipment type
            days_back: Number of days to look back
            
        Returns:
            List of vibration analysis records
        """
        try:
            query_parts = [
                "MATCH (e:Equipment)-[:HAS_MAINTENANCE_RECORD]->(mr:MaintenanceRecord)"
            ]
            
            params = {'days_back': days_back}
            
            if equipment_type:
                query_parts.append("WHERE e.type = $equipment_type")
                params['equipment_type'] = equipment_type
            
            query_parts.extend([
                "AND mr.description CONTAINS 'vibration'",
                "AND mr.date >= datetime() - duration({days: $days_back})",
                "RETURN e.id as equipment_id, e.type as equipment_type,",
                "e.name as equipment_name, e.location as equipment_location,",
                "e.criticality as equipment_criticality, mr.date as maintenance_date,",
                "mr.description as maintenance_description, mr.type as maintenance_type,",
                "mr.cost as maintenance_cost",
                "ORDER BY mr.date DESC"
            ])
            
            query = " ".join(query_parts)
            
            return self._execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Error getting vibration analysis: {e}")
            return []
    
    @performance_monitor
    def generate_maintenance_schedule(self, equipment_ids: List[str] = None, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """
        Generate maintenance schedule for equipment.
        
        Args:
            equipment_ids: List of equipment IDs to schedule
            days_ahead: Number of days ahead to schedule
            
        Returns:
            List of maintenance schedule items
        """
        try:
            if equipment_ids:
                query = """
                MATCH (e:Equipment)-[:HAS_RISK_ASSESSMENT]->(ra:RiskAssessment)
                WHERE e.id IN $equipment_ids
                OPTIONAL MATCH (e)-[:HAS_MAINTENANCE_RECORD]->(mr:MaintenanceRecord)
                WITH e, ra, collect(mr) as maintenance_history
                RETURN e.id as equipment_id, e.type as equipment_type,
                       e.name as equipment_name, e.location as equipment_location,
                       e.criticality as equipment_criticality, ra.risk_score as risk_score,
                       ra.risk_factors as risk_factors, size(maintenance_history) as recent_maintenance_count,
                       datetime() + duration({days: $days_ahead}) as recommended_date,
                       CASE 
                           WHEN ra.risk_score >= 0.8 THEN 'High Priority'
                           WHEN ra.risk_score >= 0.6 THEN 'Medium Priority'
                           ELSE 'Low Priority'
                       END as priority
                ORDER BY ra.risk_score DESC
                """
                params = {'equipment_ids': equipment_ids, 'days_ahead': days_ahead}
            else:
                query = """
                MATCH (e:Equipment)-[:HAS_RISK_ASSESSMENT]->(ra:RiskAssessment)
                OPTIONAL MATCH (e)-[:HAS_MAINTENANCE_RECORD]->(mr:MaintenanceRecord)
                WHERE mr.date >= datetime() - duration({days: 365})
                WITH e, ra, collect(mr) as maintenance_history
                RETURN e.id as equipment_id, e.type as equipment_type,
                       e.name as equipment_name, e.location as equipment_location,
                       e.criticality as equipment_criticality, ra.risk_score as risk_score,
                       ra.risk_factors as risk_factors, size(maintenance_history) as recent_maintenance_count,
                       datetime() + duration({days: $days_ahead}) as recommended_date,
                       CASE 
                           WHEN ra.risk_score >= 0.8 THEN 'High Priority'
                           WHEN ra.risk_score >= 0.6 THEN 'Medium Priority'
                           ELSE 'Low Priority'
                       END as priority
                ORDER BY ra.risk_score DESC
                LIMIT 20
                """
                params = {'days_ahead': days_ahead}
            
            return self._execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Error generating maintenance schedule: {e}")
            return []
    
    @performance_monitor
    def analyze_maintenance_patterns(self, maintenance_records: List[Dict[str, Any]]) -> str:
        """
        Analyze maintenance patterns using Claude AI.
        
        Args:
            maintenance_records: List of maintenance records
            
        Returns:
            AI-generated analysis text
        """
        try:
            if not maintenance_records:
                return "No maintenance records available for analysis."
            
            # Prepare data for analysis
            df = pd.DataFrame(maintenance_records)
            
            # Create summary statistics
            summary = {
                'total_records': len(df),
                'equipment_types': df.get('equipment_type', []).nunique() if 'equipment_type' in df.columns else 0,
                'total_cost': df.get('maintenance_cost', []).sum() if 'maintenance_cost' in df.columns else 0,
                'avg_cost': df.get('maintenance_cost', []).mean() if 'maintenance_cost' in df.columns else 0,
                'maintenance_types': df.get('maintenance_type', []).value_counts().to_dict() if 'maintenance_type' in df.columns else {}
            }
            
            # Create analysis prompt
            prompt = f"""
            Analyze the following maintenance data for energy grid equipment:
            
            Summary Statistics:
            - Total Records: {summary['total_records']}
            - Equipment Types: {summary['equipment_types']}
            - Total Cost: ${summary['total_cost']:,.2f}
            - Average Cost: ${summary['avg_cost']:,.2f}
            - Maintenance Types: {summary['maintenance_types']}
            
            Sample Data:
            {df.head(10).to_string()}
            
            Please provide:
            1. Key insights about maintenance patterns
            2. Equipment types requiring most attention
            3. Cost analysis and recommendations
            4. Predictive maintenance suggestions
            5. Risk factors to monitor
            """
            
            # Use Claude AI for analysis
            if st.session_state.claude_client:
                return st.session_state.claude_client.analyze_grid_data(prompt)
            else:
                return "Claude AI client not available for analysis."
                
        except Exception as e:
            logger.error(f"Error analyzing maintenance patterns: {e}")
            return f"Analysis failed: {str(e)}"
    
    def close(self):
        """Close database connection."""
        if self.driver:
            self.driver.close()
            logger.info("Database connection closed")

@error_boundary
def initialize_connection(uri: str, username: str, password: str, database: str, claude_key: str):
    """Initialize database and Claude AI connections with health checks."""
    
    # Progress indicator
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Validate Claude API key
        status_text.text("Validating Claude API key...")
        progress_bar.progress(25)
        
        if not validate_claude_api_key(claude_key):
            st.error("❌ Invalid Claude API key format")
            return
        
        # Step 2: Test Neo4j connection
        status_text.text("Testing Neo4j database connection...")
        progress_bar.progress(50)
        
        neo4j_health = check_neo4j_health(uri, username, password)
        st.session_state.health_status['neo4j'] = neo4j_health
        
        if neo4j_health['status'] == 'offline':
            st.error(f"❌ Neo4j connection failed: {neo4j_health['message']}")
            return
        
        # Step 3: Test Claude API connection
        status_text.text("Testing Claude AI API connection...")
        progress_bar.progress(75)
        
        claude_health = check_claude_health(claude_key)
        st.session_state.health_status['claude'] = claude_health
        
        if claude_health['status'] == 'offline':
            st.error(f"❌ Claude API connection failed: {claude_health['message']}")
            return
        
        # Step 4: Initialize tools
        status_text.text("Initializing tools and clients...")
        progress_bar.progress(90)
        
        st.session_state.energy_tools = EnergyAgentTools(uri, username, password, database)
        st.session_state.claude_client = ClaudeClient(api_key=claude_key)
        st.session_state.connection_status = "connected"
        
        # Complete
        progress_bar.progress(100)
        status_text.text("✅ Connection established successfully!")
        
        # Show success message
        st.success("🎉 Successfully connected to Neo4j and Claude AI!")
        
        # Show health status
        show_health_status()
        
        # Clear progress indicators
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        st.error(f"❌ Connection failed: {str(e)}")
        st.session_state.connection_status = "failed"
        progress_bar.empty()
        status_text.empty()

def main():
    """Enhanced main application function with health monitoring and performance tracking."""
    
    # Header with enhanced styling
    st.markdown("""
    <div class="main-header">
        <h1>⚡ Energy Grid Management Agent</h1>
        <p>Intelligent analysis and management for energy grid optimization</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar Configuration with enhanced features
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Health Status Section
        st.subheader("🏥 System Health")
        show_health_status()
        
        # Performance Metrics Section
        if st.session_state.performance_metrics:
            with st.expander("⚡ Performance Metrics"):
                show_performance_metrics()
        
        st.divider()
        
        # Neo4j Connection Section
        st.subheader("📡 Neo4j Database")
        
        neo4j_uri = st.text_input(
            "Database URI",
            value="neo4j+s://your-instance.databases.neo4j.io",
            help="Neo4j database URI (neo4j://, neo4j+s://, bolt://, bolt+s://)"
        )
        
        neo4j_username = st.text_input(
            "Username",
            value="neo4j",
            help="Neo4j username"
        )
        
        neo4j_password = st.text_input(
            "Password",
            type="password",
            help="Neo4j password"
        )
        
        neo4j_database = st.text_input(
            "Database Name",
            value="neo4j",
            help="Neo4j database name"
        )
        
        # Claude API Configuration
        st.subheader("🤖 Claude AI")
        claude_api_key = st.text_input(
            "Claude API Key",
            type="password",
            help="Your Claude API key from Anthropic"
        )
        
        # Connection Controls
        st.divider()
        st.subheader("🔌 Connection Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔌 Connect", type="primary", use_container_width=True):
                if neo4j_uri and neo4j_username and neo4j_password and claude_api_key:
                    initialize_connection(neo4j_uri, neo4j_username, neo4j_password, neo4j_database, claude_api_key)
                else:
                    st.warning("Please fill in all required fields.")
        
        with col2:
            if st.button("🔄 Refresh Health", use_container_width=True):
                if neo4j_uri and neo4j_username and neo4j_password:
                    neo4j_health = check_neo4j_health(neo4j_uri, neo4j_username, neo4j_password)
                    st.session_state.health_status['neo4j'] = neo4j_health
                
                if claude_api_key:
                    claude_health = check_claude_health(claude_api_key)
                    st.session_state.health_status['claude'] = claude_health
                
                st.success("Health status refreshed!")
        
        # Disconnect Button
        if st.session_state.connection_status == "connected":
            if st.button("🔌 Disconnect", use_container_width=True):
                if st.session_state.energy_tools:
                    st.session_state.energy_tools.close()
                st.session_state.energy_tools = None
                st.session_state.claude_client = None
                st.session_state.connection_status = "disconnected"
                st.success("Disconnected successfully!")
                st.rerun()
        
        # Help Section
        st.divider()
        with st.expander("❓ Help & Tips"):
            st.markdown("""
            **Quick Start:**
            1. Enter your Neo4j database credentials
            2. Enter your Claude API key
            3. Click "Connect" to establish connections
            4. Navigate through the tabs to analyze your data
            
            **Tips:**
            - Use the health check to monitor connection status
            - Export data for external analysis
            - Adjust risk thresholds based on your requirements
            - Monitor performance metrics for optimization
            """)
    
    # Main Interface
    if st.session_state.connection_status != "connected":
        st.warning("⚠️ Please connect to the database and Claude AI in the sidebar to use the application.")
        
        # Show connection help
        with st.expander("🔗 Connection Help"):
            st.markdown("""
            **Neo4j Setup:**
            - Use Neo4j AuraDB for cloud hosting
            - Or install Neo4j Desktop locally
            - Ensure your database has the required schema
            
            **Claude API Setup:**
            - Sign up at console.anthropic.com
            - Generate an API key
            - Ensure you have sufficient credits
            
            **Troubleshooting:**
            - Check network connectivity
            - Verify credentials are correct
            - Ensure database is running
            """)
        return
    
    # Create tabs with enhanced styling
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏠 Dashboard", 
        "🔍 Equipment Analysis", 
        "⚠️ Risk Assessment", 
        "🔗 Dependencies", 
        "📅 Maintenance Scheduling", 
        "🌊 Vibration Analysis"
    ])
    
    with tab1:
        show_dashboard()
    
    with tab2:
        show_equipment_analysis()
    
    with tab3:
        show_risk_assessment()
    
    with tab4:
        show_dependencies()
    
    with tab5:
        show_maintenance_scheduling()
    
    with tab6:
        show_vibration_analysis()
    
    # Footer
    show_footer()

def show_dashboard():
    """Enhanced dashboard with overview metrics and quick actions."""
    st.header("🏠 Dashboard")
    st.markdown("Overview of your energy grid management system")
    
    # Quick metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>📊 Total Equipment</h3>
            <h2>Loading...</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>⚠️ High Risk</h3>
            <h2>Loading...</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>🔧 Maintenance Due</h3>
            <h2>Loading...</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>💰 Total Cost</h3>
            <h2>Loading...</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Search Equipment", use_container_width=True):
            st.switch_page("pages/equipment_analysis.py")
    
    with col2:
        if st.button("⚠️ Risk Assessment", use_container_width=True):
            st.switch_page("pages/risk_assessment.py")
    
    with col3:
        if st.button("📅 Schedule Maintenance", use_container_width=True):
            st.switch_page("pages/maintenance_scheduling.py")
    
    # Recent Activity
    st.subheader("📈 Recent Activity")
    
    # Placeholder for recent activity
    st.info("Recent activity will be displayed here once you perform operations.")
    
    # System Status
    st.subheader("🔧 System Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Database Status:**")
        if st.session_state.health_status['neo4j']['status'] == 'online':
            st.success("🟢 Online")
        else:
            st.error("🔴 Offline")
    
    with col2:
        st.markdown("**AI Service Status:**")
        if st.session_state.health_status['claude']['status'] == 'online':
            st.success("🟢 Online")
        else:
            st.error("🔴 Offline")

def show_equipment_analysis():
    """Enhanced equipment analysis with caching and performance monitoring."""
    st.header("🔍 Equipment Analysis")
    st.markdown("Analyze equipment maintenance patterns and performance")
    
    # Search filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        equipment_type = st.selectbox(
            "Equipment Type",
            ["All", "Transformer", "Generator", "Switchgear", "Cable", "Circuit Breaker"],
            help="Filter by equipment type"
        )
    
    with col2:
        issue_type = st.selectbox(
            "Issue Type",
            ["All", "Electrical", "Mechanical", "Thermal", "Environmental"],
            help="Filter by issue type"
        )
    
    with col3:
        days_back = st.slider(
            "Days Back",
            min_value=1,
            max_value=365,
            value=30,
            help="Number of days to look back"
        )
    
    # Search button with progress indicator
    if st.button("🔍 Search Records", type="primary"):
        with st.spinner("Searching equipment records..."):
            try:
                # Use cached search function
                records = search_equipment_maintenance_records_cached(
                    st.session_state.energy_tools,
                    equipment_type if equipment_type != "All" else None,
                    issue_type if issue_type != "All" else None,
                    days_back
                )
                
                if records:
                    st.success(f"Found {len(records)} maintenance records")
                    
                    # Display results
                    df = pd.DataFrame(records)
                    
                    # Export functionality
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.dataframe(df, use_container_width=True)
                    with col2:
                        export_data(df, "equipment_maintenance_records")
                    
                    # Charts
                    st.subheader("📊 Analysis Charts")
                    
                    tab1, tab2, tab3 = st.tabs(["Maintenance by Type", "Timeline", "Cost Analysis"])
                    
                    with tab1:
                        fig = create_maintenance_chart(df)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with tab2:
                        fig = create_timeline_chart(df)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with tab3:
                        fig = create_cost_analysis_chart(df)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # AI Analysis
                    if st.button("🤖 Get AI Insights"):
                        with st.spinner("Analyzing with Claude AI..."):
                            try:
                                analysis = st.session_state.energy_tools.analyze_maintenance_patterns(records)
                                st.subheader("🤖 AI Analysis")
                                st.markdown(analysis)
                            except Exception as e:
                                st.error(f"AI analysis failed: {str(e)}")
                
                else:
                    st.warning("No maintenance records found for the specified criteria.")
                    
            except Exception as e:
                st.error(f"Search failed: {str(e)}")

def show_risk_assessment():
    """Enhanced risk assessment with interactive thresholds and export."""
    st.header("⚠️ Risk Assessment")
    st.markdown("Identify and analyze high-risk equipment")
    
    # Risk threshold configuration
    col1, col2 = st.columns(2)
    
    with col1:
        risk_threshold = st.slider(
            "Risk Threshold",
            min_value=0.0,
            max_value=10.0,
            value=7.0,
            step=0.1,
            help="Minimum risk score to consider equipment as high-risk"
        )
    
    with col2:
        include_critical = st.checkbox(
            "Include Critical Equipment",
            value=True,
            help="Include equipment marked as critical regardless of risk score"
        )
    
    # Search button
    if st.button("🔍 Find Risky Equipment", type="primary"):
        with st.spinner("Analyzing risk data..."):
            try:
                risky_equipment = st.session_state.energy_tools.get_risky_equipment(risk_threshold)
                
                if risky_equipment:
                    st.success(f"Found {len(risky_equipment)} high-risk equipment items")
                    
                    # Display results
                    df = pd.DataFrame(risky_equipment)
                    
                    # Export functionality
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.dataframe(df, use_container_width=True)
                    with col2:
                        export_data(df, "risky_equipment")
                    
                    # Risk visualization
                    st.subheader("📊 Risk Analysis")
                    
                    # Risk score distribution
                    fig = create_risk_chart(df)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Risk summary
                    st.subheader("📈 Risk Summary")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        avg_risk = df['risk_score'].mean()
                        st.metric("Average Risk Score", f"{avg_risk:.2f}")
                    
                    with col2:
                        max_risk = df['risk_score'].max()
                        st.metric("Highest Risk Score", f"{max_risk:.2f}")
                    
                    with col3:
                        critical_count = len(df[df['criticality'] == 'Critical'])
                        st.metric("Critical Equipment", critical_count)
                    
                    with col4:
                        high_risk_count = len(df[df['risk_score'] >= 8.0])
                        st.metric("Very High Risk", high_risk_count)
                    
                    # Recommendations
                    st.subheader("💡 Recommendations")
                    
                    if avg_risk > 7.0:
                        st.warning("⚠️ Overall risk level is high. Consider immediate maintenance scheduling.")
                    
                    if critical_count > 0:
                        st.info("ℹ️ Critical equipment detected. Prioritize maintenance for these items.")
                    
                    if high_risk_count > 0:
                        st.error("🚨 Very high-risk equipment detected. Immediate attention required.")
                
                else:
                    st.info("No equipment found above the specified risk threshold.")
                    
            except Exception as e:
                st.error(f"Risk assessment failed: {str(e)}")

def show_dependencies():
    """Enhanced dependency mapping with interactive visualization."""
    st.header("🔗 Equipment Dependencies")
    st.markdown("Map and analyze equipment dependencies")
    
    # Dependency search
    col1, col2 = st.columns(2)
    
    with col1:
        installation_id = st.text_input(
            "Installation ID (Optional)",
            help="Specific installation ID to analyze, or leave empty for all"
        )
    
    with col2:
        dependency_depth = st.slider(
            "Dependency Depth",
            min_value=1,
            max_value=5,
            value=3,
            help="How many levels of dependencies to analyze"
        )
    
    # Search button
    if st.button("🔍 Map Dependencies", type="primary"):
        with st.spinner("Mapping equipment dependencies..."):
            try:
                dependencies = st.session_state.energy_tools.get_installation_equipments_dependency(
                    installation_id if installation_id else None
                )
                
                if dependencies:
                    st.success(f"Found {len(dependencies)} dependency relationships")
                    
                    # Display results
                    df = pd.DataFrame(dependencies)
                    
                    # Export functionality
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.dataframe(df, use_container_width=True)
                    with col2:
                        export_data(df, "equipment_dependencies")
                    
                    # Dependency visualization
                    st.subheader("📊 Dependency Network")
                    
                    # Create network visualization
                    if len(dependencies) > 0:
                        # Simple dependency chart
                        st.info("📈 Dependency network visualization would be displayed here")
                        
                        # Dependency statistics
                        st.subheader("📈 Dependency Statistics")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            unique_equipment = len(set([d['equipment_id'] for d in dependencies]))
                            st.metric("Unique Equipment", unique_equipment)
                        
                        with col2:
                            unique_installations = len(set([d['installation_id'] for d in dependencies]))
                            st.metric("Installations", unique_installations)
                        
                        with col3:
                            avg_dependencies = len(dependencies) / max(unique_equipment, 1)
                            st.metric("Avg Dependencies", f"{avg_dependencies:.1f}")
                
                else:
                    st.info("No dependency relationships found.")
                    
            except Exception as e:
                st.error(f"Dependency mapping failed: {str(e)}")

def show_maintenance_scheduling():
    """Enhanced maintenance scheduling with AI recommendations."""
    st.header("📅 Maintenance Scheduling")
    st.markdown("Generate and optimize maintenance schedules")
    
    # Schedule configuration
    col1, col2 = st.columns(2)
    
    with col1:
        equipment_ids = st.text_area(
            "Equipment IDs (Optional)",
            help="Comma-separated list of equipment IDs, or leave empty for all equipment"
        )
    
    with col2:
        schedule_type = st.selectbox(
            "Schedule Type",
            ["Preventive", "Corrective", "Predictive", "All"],
            help="Type of maintenance to schedule"
        )
    
    # Generate schedule button
    if st.button("📅 Generate Schedule", type="primary"):
        with st.spinner("Generating maintenance schedule..."):
            try:
                # Parse equipment IDs
                equipment_list = None
                if equipment_ids.strip():
                    equipment_list = [eid.strip() for eid in equipment_ids.split(',')]
                
                schedule = st.session_state.energy_tools.generate_maintenance_schedule(
                    equipment_ids=equipment_list
                )
                
                if schedule:
                    st.success(f"Generated schedule with {len(schedule)} maintenance tasks")
                    
                    # Display schedule
                    df = pd.DataFrame(schedule)
                    
                    # Export functionality
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.dataframe(df, use_container_width=True)
                    with col2:
                        export_data(df, "maintenance_schedule")
                    
                    # Schedule analysis
                    st.subheader("📊 Schedule Analysis")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_cost = df['estimated_cost'].sum() if 'estimated_cost' in df.columns else 0
                        st.metric("Total Estimated Cost", format_currency(total_cost))
                    
                    with col2:
                        avg_duration = df['estimated_duration'].mean() if 'estimated_duration' in df.columns else 0
                        st.metric("Avg Duration (hours)", f"{avg_duration:.1f}")
                    
                    with col3:
                        priority_tasks = len(df[df['priority'] == 'High']) if 'priority' in df.columns else 0
                        st.metric("High Priority Tasks", priority_tasks)
                    
                    with col4:
                        urgent_tasks = len(df[df['urgency'] == 'Immediate']) if 'urgency' in df.columns else 0
                        st.metric("Immediate Tasks", urgent_tasks)
                    
                    # Timeline visualization
                    if 'scheduled_date' in df.columns:
                        st.subheader("📈 Maintenance Timeline")
                        fig = create_timeline_chart(df)
                        st.plotly_chart(fig, use_container_width=True)
                
                else:
                    st.info("No maintenance schedule could be generated.")
                    
            except Exception as e:
                st.error(f"Schedule generation failed: {str(e)}")

def show_vibration_analysis():
    """Enhanced vibration analysis with trend detection."""
    st.header("🌊 Vibration Analysis")
    st.markdown("Analyze equipment vibration patterns and trends")
    
    # Vibration analysis filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        vibration_equipment_type = st.selectbox(
            "Equipment Type",
            ["All", "Motor", "Pump", "Compressor", "Turbine", "Fan"],
            help="Filter by equipment type for vibration analysis"
        )
    
    with col2:
        vibration_days_back = st.slider(
            "Analysis Period (Days)",
            min_value=1,
            max_value=90,
            value=30,
            help="Number of days to analyze"
        )
    
    with col3:
        vibration_threshold = st.slider(
            "Vibration Threshold",
            min_value=0.0,
            max_value=50.0,
            value=10.0,
            step=0.1,
            help="Vibration level threshold for alerts"
        )
    
    # Analyze button
    if st.button("🌊 Analyze Vibration", type="primary"):
        with st.spinner("Analyzing vibration data..."):
            try:
                vibration_data = st.session_state.energy_tools.get_vibration_analysis(
                    equipment_type=vibration_equipment_type if vibration_equipment_type != "All" else None,
                    days_back=vibration_days_back
                )
                
                if vibration_data:
                    st.success(f"Found {len(vibration_data)} vibration records")
                    
                    # Display results
                    df = pd.DataFrame(vibration_data)
                    
                    # Export functionality
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.dataframe(df, use_container_width=True)
                    with col2:
                        export_data(df, "vibration_analysis")
                    
                    # Vibration analysis
                    st.subheader("📊 Vibration Analysis")
                    
                    # Vibration trends
                    if 'vibration_level' in df.columns and 'timestamp' in df.columns:
                        # Create vibration trend chart
                        fig = px.line(
                            df,
                            x='timestamp',
                            y='vibration_level',
                            title='Vibration Level Trends',
                            labels={'vibration_level': 'Vibration Level (mm/s)', 'timestamp': 'Time'}
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Vibration statistics
                    st.subheader("📈 Vibration Statistics")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        avg_vibration = df['vibration_level'].mean() if 'vibration_level' in df.columns else 0
                        st.metric("Average Vibration", f"{avg_vibration:.2f} mm/s")
                    
                    with col2:
                        max_vibration = df['vibration_level'].max() if 'vibration_level' in df.columns else 0
                        st.metric("Peak Vibration", f"{max_vibration:.2f} mm/s")
                    
                    with col3:
                        above_threshold = len(df[df['vibration_level'] > vibration_threshold]) if 'vibration_level' in df.columns else 0
                        st.metric("Above Threshold", above_threshold)
                    
                    with col4:
                        equipment_count = len(df['equipment_id'].unique()) if 'equipment_id' in df.columns else 0
                        st.metric("Equipment Monitored", equipment_count)
                    
                    # Alerts and recommendations
                    st.subheader("⚠️ Alerts & Recommendations")
                    
                    if 'vibration_level' in df.columns:
                        high_vibration = df[df['vibration_level'] > vibration_threshold]
                        
                        if len(high_vibration) > 0:
                            st.warning(f"⚠️ {len(high_vibration)} records above vibration threshold")
                            
                            # Show high vibration equipment
                            st.markdown("**Equipment with High Vibration:**")
                            high_vib_df = high_vibration[['equipment_id', 'vibration_level', 'timestamp']].head(10)
                            st.dataframe(high_vib_df, use_container_width=True)
                        else:
                            st.success("✅ All vibration levels are within acceptable limits")
                
                else:
                    st.info("No vibration data found for the specified criteria.")
                    
            except Exception as e:
                st.error(f"Vibration analysis failed: {str(e)}")

# Continue with the rest of the application... 

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.error("Please check your configuration and try again.")
        
        # Log the error for debugging
        logging.error(f"Application crashed: {str(e)}", exc_info=True)
        
        # Show error details in development
        if st.secrets.get("DEBUG", False):
            st.exception(e) 
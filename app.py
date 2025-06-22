"""
Energy Grid Management Agent - Main Streamlit Application
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError, ClientError

from config import Config
from claude_utils import ClaudeClient

# Configure logging
logger = logging.getLogger(__name__)

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

def create_timeline_chart(maintenance_data: List[Dict[str, Any]]) -> Optional[go.Figure]:
    """
    Create a timeline scatter plot of maintenance activities.
    
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
        
        # Convert date column to datetime
        df['maintenance_date'] = pd.to_datetime(df['maintenance_date'])
        
        # Remove rows with missing dates
        df = df.dropna(subset=['maintenance_date'])
        
        if df.empty:
            return None
        
        # Sort by date
        df = df.sort_values('maintenance_date')
        
        # Create color mapping for equipment types
        equipment_types = df['equipment_type'].unique() if 'equipment_type' in df.columns else ['Unknown']
        colors = px.colors.qualitative.Set3[:len(equipment_types)]
        color_map = dict(zip(equipment_types, colors))
        
        # Create scatter plot
        fig = go.Figure()
        
        # Group by equipment type for better visualization
        for eq_type in equipment_types:
            type_data = df[df['equipment_type'] == eq_type]
            
            fig.add_trace(go.Scatter(
                x=type_data['maintenance_date'],
                y=[1] * len(type_data),  # Single line for timeline
                mode='markers+lines',
                marker=dict(
                    size=8,
                    color=color_map[eq_type],
                    line=dict(width=2, color='white')
                ),
                line=dict(color=color_map[eq_type], width=2),
                text=type_data.get('equipment_name', ''),
                hovertemplate=(
                    "<b>Equipment:</b> %{text}<br>" +
                    "<b>Type:</b> " + eq_type + "<br>" +
                    "<b>Date:</b> %{x}<br>" +
                    "<b>Maintenance:</b> " + type_data.get('maintenance_type', 'Unknown').iloc[0] + "<br>" +
                    "<extra></extra>"
                ),
                name=eq_type,
                showlegend=True
            ))
        
        # Update layout
        fig.update_layout(
            title=dict(
                text="Maintenance Activities Timeline",
                x=0.5,
                font=dict(size=18, color='#2c3e50')
            ),
            xaxis=dict(
                title="Date",
                titlefont=dict(size=14, color='#34495e'),
                tickfont=dict(size=12),
                tickangle=45,
                type='date'
            ),
            yaxis=dict(
                title="",
                showticklabels=False,
                range=[0.5, 1.5]
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=60, r=60, t=80, b=80),
            height=400,
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
        logger.error(f"Error creating timeline chart: {e}")
        return None

class EnergyAgentTools:
    """Handles Neo4j database operations for energy grid management."""
    
    def __init__(self, uri: str = None, username: str = None, password: str = None, database: str = None):
        """
        Initialize the EnergyAgentTools with Neo4j connection.
        
        Args:
            uri: Neo4j database URI
            username: Neo4j username
            password: Neo4j password
            database: Neo4j database name
        """
        # Use config values if not provided
        config = Config()
        self.uri = uri or config.NEO4J_URI
        self.username = username or config.NEO4J_USERNAME
        self.password = password or config.NEO4J_PASSWORD
        self.database = database or config.NEO4J_DATABASE
        
        # Initialize driver
        self.driver = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Neo4j database."""
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
        except (ServiceUnavailable, AuthError, ClientError) as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise ConnectionError(f"Neo4j connection failed: {e}")
    
    def _execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of dictionaries containing query results
        """
        if parameters is None:
            parameters = {}
        
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, parameters)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            raise RuntimeError(f"Database query failed: {e}")
    
    def search_equipment_maintenance_records(
        self, 
        equipment_type: Optional[str] = None,
        issue_type: Optional[str] = None,
        days_back: int = 365
    ) -> List[Dict[str, Any]]:
        """
        Search maintenance records with filters.
        
        Args:
            equipment_type: Filter by equipment type (e.g., "Generator", "Transformer")
            issue_type: Filter by issue type (e.g., "vibration", "overheating")
            days_back: Number of days to look back (default: 365)
            
        Returns:
            List of maintenance records with equipment details
        """
        # Build the Cypher query with optional filters
        query = """
        MATCH (e:Equipment)-[:HAS_MAINTENANCE]->(m:MaintenanceRecord)
        WHERE m.date >= date() - duration({days: $days_back})
        """
        
        parameters = {"days_back": days_back}
        
        # Add equipment type filter
        if equipment_type:
            query += " AND e.type = $equipment_type"
            parameters["equipment_type"] = equipment_type
        
        # Add issue type filter (search in description)
        if issue_type:
            query += " AND toLower(m.description) CONTAINS toLower($issue_type)"
            parameters["issue_type"] = issue_type
        
        # Complete the query
        query += """
        RETURN e.id as equipment_id,
               e.type as equipment_type,
               e.name as equipment_name,
               e.location as equipment_location,
               e.criticality as equipment_criticality,
               m.date as maintenance_date,
               m.description as maintenance_description,
               m.type as maintenance_type,
               m.cost as maintenance_cost
        ORDER BY m.date DESC
        """
        
        try:
            results = self._execute_query(query, parameters)
            logger.info(f"Found {len(results)} maintenance records")
            return results
        except Exception as e:
            logger.error(f"Failed to search maintenance records: {e}")
            return []
    
    def get_risky_equipment(self, risk_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Get equipment with high risk scores above a threshold.
        
        Args:
            risk_threshold: Minimum risk score to include (0.0-1.0, default: 0.7)
            
        Returns:
            List of equipment with risk assessments
        """
        query = """
        MATCH (e:Equipment)-[:HAS_RISK_ASSESSMENT]->(r:RiskAssessment)
        WHERE r.risk_score >= $risk_threshold
        RETURN e.id as equipment_id,
               e.type as equipment_type,
               e.name as equipment_name,
               e.location as equipment_location,
               e.criticality as equipment_criticality,
               r.risk_score as risk_score,
               r.risk_factors as risk_factors,
               r.assessment_date as assessment_date
        ORDER BY r.risk_score DESC
        """
        
        parameters = {"risk_threshold": risk_threshold}
        
        try:
            results = self._execute_query(query, parameters)
            logger.info(f"Found {len(results)} high-risk equipment items")
            return results
        except Exception as e:
            logger.error(f"Failed to get risky equipment: {e}")
            return []
    
    def get_installation_equipments_dependency(self, installation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get equipment dependencies and relationships for installations.
        
        Args:
            installation_id: Specific installation ID to query (optional)
            
        Returns:
            List of installation-equipment dependencies
        """
        if installation_id:
            # Query for specific installation
            query = """
            MATCH (i:Installation {id: $installation_id})-[:CONTAINS]->(e:Equipment)
            OPTIONAL MATCH (e)-[:DEPENDS_ON]->(d:Equipment)
            OPTIONAL MATCH (e)-[:HAS_MAINTENANCE]->(m:MaintenanceRecord)
            OPTIONAL MATCH (e)-[:HAS_RISK_ASSESSMENT]->(r:RiskAssessment)
            RETURN i.id as installation_id,
                   i.name as installation_name,
                   i.type as installation_type,
                   e.id as equipment_id,
                   e.type as equipment_type,
                   e.name as equipment_name,
                   e.criticality as equipment_criticality,
                   collect(DISTINCT d.id) as dependent_equipment,
                   collect(DISTINCT {date: m.date, type: m.type, description: m.description}) as maintenance_history,
                   r.risk_score as current_risk_score
            ORDER BY e.criticality DESC
            """
            parameters = {"installation_id": installation_id}
        else:
            # Query for all installations
            query = """
            MATCH (i:Installation)-[:CONTAINS]->(e:Equipment)
            OPTIONAL MATCH (e)-[:DEPENDS_ON]->(d:Equipment)
            OPTIONAL MATCH (e)-[:HAS_MAINTENANCE]->(m:MaintenanceRecord)
            OPTIONAL MATCH (e)-[:HAS_RISK_ASSESSMENT]->(r:RiskAssessment)
            RETURN i.id as installation_id,
                   i.name as installation_name,
                   i.type as installation_type,
                   e.id as equipment_id,
                   e.type as equipment_type,
                   e.name as equipment_name,
                   e.criticality as equipment_criticality,
                   collect(DISTINCT d.id) as dependent_equipment,
                   collect(DISTINCT {date: m.date, type: m.type, description: m.description}) as maintenance_history,
                   r.risk_score as current_risk_score
            ORDER BY i.name, e.criticality DESC
            """
            parameters = {}
        
        try:
            results = self._execute_query(query, parameters)
            logger.info(f"Found {len(results)} installation-equipment dependencies")
            return results
        except Exception as e:
            logger.error(f"Failed to get installation dependencies: {e}")
            return []
    
    def get_vibration_analysis(self, equipment_type: Optional[str] = None, days_back: int = 90) -> List[Dict[str, Any]]:
        """
        Get vibration-related maintenance records and analysis.
        
        Args:
            equipment_type: Filter by equipment type
            days_back: Number of days to look back
            
        Returns:
            List of vibration-related maintenance records
        """
        query = """
        MATCH (e:Equipment)-[:HAS_MAINTENANCE]->(m:MaintenanceRecord)
        WHERE m.date >= date() - duration({days: $days_back})
        AND toLower(m.description) CONTAINS 'vibration'
        """
        
        parameters = {"days_back": days_back}
        
        if equipment_type:
            query += " AND e.type = $equipment_type"
            parameters["equipment_type"] = equipment_type
        
        query += """
        RETURN e.id as equipment_id,
               e.type as equipment_type,
               e.name as equipment_name,
               e.location as equipment_location,
               e.criticality as equipment_criticality,
               m.date as maintenance_date,
               m.description as maintenance_description,
               m.type as maintenance_type,
               m.cost as maintenance_cost
        ORDER BY m.date DESC
        """
        
        try:
            results = self._execute_query(query, parameters)
            logger.info(f"Found {len(results)} vibration-related maintenance records")
            return results
        except Exception as e:
            logger.error(f"Failed to get vibration analysis: {e}")
            return []
    
    def generate_maintenance_schedule(self, equipment_ids: List[str] = None, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """
        Generate AI-powered maintenance schedule.
        
        Args:
            equipment_ids: List of equipment IDs to schedule
            days_ahead: Number of days to look ahead
            
        Returns:
            List of maintenance schedule recommendations
        """
        # This would typically integrate with Claude AI for intelligent scheduling
        # For now, return a basic schedule based on risk assessment
        
        query = """
        MATCH (e:Equipment)-[:HAS_RISK_ASSESSMENT]->(r:RiskAssessment)
        WHERE r.risk_score >= 0.6
        """
        
        if equipment_ids:
            query += " AND e.id IN $equipment_ids"
            parameters = {"equipment_ids": equipment_ids}
        else:
            parameters = {}
        
        query += """
        OPTIONAL MATCH (e)-[:HAS_MAINTENANCE]->(m:MaintenanceRecord)
        WHERE m.date >= date() - duration({days: 90})
        RETURN e.id as equipment_id,
               e.type as equipment_type,
               e.name as equipment_name,
               e.location as equipment_location,
               e.criticality as equipment_criticality,
               r.risk_score as risk_score,
               r.risk_factors as risk_factors,
               count(m) as recent_maintenance_count,
               date() + duration({days: 7}) as recommended_date,
               CASE 
                   WHEN r.risk_score >= 0.8 THEN 'High Priority'
                   WHEN r.risk_score >= 0.6 THEN 'Medium Priority'
                   ELSE 'Low Priority'
               END as priority
        ORDER BY r.risk_score DESC
        """
        
        try:
            results = self._execute_query(query, parameters)
            logger.info(f"Generated maintenance schedule for {len(results)} equipment items")
            return results
        except Exception as e:
            logger.error(f"Failed to generate maintenance schedule: {e}")
            return []
    
    def analyze_maintenance_patterns(self, maintenance_records: List[Dict[str, Any]]) -> str:
        """
        Analyze maintenance patterns using Claude AI.
        
        Args:
            maintenance_records: List of maintenance records to analyze
            
        Returns:
            AI-generated analysis of maintenance patterns
        """
        if not maintenance_records:
            return "No maintenance records available for analysis."
        
        try:
            # Prepare data for analysis
            df = pd.DataFrame(maintenance_records)
            
            # Create summary statistics
            total_records = len(maintenance_records)
            equipment_types = df['equipment_type'].nunique() if 'equipment_type' in df.columns else 0
            total_cost = df['maintenance_cost'].sum() if 'maintenance_cost' in df.columns else 0
            
            # Analyze patterns
            patterns = {
                "total_records": total_records,
                "equipment_types": equipment_types,
                "total_cost": total_cost,
                "date_range": {
                    "earliest": df['maintenance_date'].min() if 'maintenance_date' in df.columns else None,
                    "latest": df['maintenance_date'].max() if 'maintenance_date' in df.columns else None
                },
                "equipment_type_distribution": df['equipment_type'].value_counts().to_dict() if 'equipment_type' in df.columns else {},
                "maintenance_type_distribution": df['maintenance_type'].value_counts().to_dict() if 'maintenance_type' in df.columns else {},
                "cost_analysis": {
                    "average_cost": df['maintenance_cost'].mean() if 'maintenance_cost' in df.columns else 0,
                    "max_cost": df['maintenance_cost'].max() if 'maintenance_cost' in df.columns else 0,
                    "min_cost": df['maintenance_cost'].min() if 'maintenance_cost' in df.columns else 0
                }
            }
            
            # Create analysis prompt
            analysis_prompt = f"""
            Analyze the following maintenance records data for an energy grid management system:
            
            Summary Statistics:
            - Total Records: {patterns['total_records']}
            - Equipment Types: {patterns['equipment_types']}
            - Total Cost: ${patterns['total_cost']:,.2f}
            - Date Range: {patterns['date_range']['earliest']} to {patterns['date_range']['latest']}
            
            Equipment Type Distribution:
            {json.dumps(patterns['equipment_type_distribution'], indent=2)}
            
            Maintenance Type Distribution:
            {json.dumps(patterns['maintenance_type_distribution'], indent=2)}
            
            Cost Analysis:
            - Average Cost: ${patterns['cost_analysis']['average_cost']:,.2f}
            - Maximum Cost: ${patterns['cost_analysis']['max_cost']:,.2f}
            - Minimum Cost: ${patterns['cost_analysis']['min_cost']:,.2f}
            
            Please provide a comprehensive analysis including:
            1. Key patterns and trends in the maintenance data
            2. Equipment types that require the most attention
            3. Cost implications and budget considerations
            4. Recommendations for maintenance optimization
            5. Potential risk factors and areas of concern
            6. Suggestions for preventive maintenance strategies
            
            Format your response in a clear, structured manner suitable for energy grid management professionals.
            """
            
            # Use Claude AI for analysis
            if st.session_state.claude_client:
                analysis = st.session_state.claude_client.analyze_grid_data(analysis_prompt)
                return analysis
            else:
                return "Claude AI client not available for analysis."
                
        except Exception as e:
            logger.error(f"Failed to analyze maintenance patterns: {e}")
            return f"Error analyzing maintenance patterns: {e}"
    
    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

# Page configuration
st.set_page_config(
    page_title="Energy Grid Management Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'energy_tools' not in st.session_state:
    st.session_state.energy_tools = None

if 'claude_client' not in st.session_state:
    st.session_state.claude_client = None

if 'connection_status' not in st.session_state:
    st.session_state.connection_status = "disconnected"

if 'maintenance_records' not in st.session_state:
    st.session_state.maintenance_records = []

if 'risky_equipment' not in st.session_state:
    st.session_state.risky_equipment = []

def initialize_connection(uri: str, username: str, password: str, database: str, claude_key: str):
    """Initialize database and AI connections."""
    try:
        # Initialize EnergyAgentTools
        st.session_state.energy_tools = EnergyAgentTools(uri, username, password, database)
        st.session_state.connection_status = "connected"
        
        # Initialize Claude client
        st.session_state.claude_client = ClaudeClient(api_key=claude_key)
        
        st.success("✅ Connection established successfully!")
        return True
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")
        st.session_state.connection_status = "failed"
        return False

def main():
    """Main application function."""
    
    # Header
    st.title("⚡ Energy Grid Management Agent")
    st.markdown("Intelligent analysis and management for energy grid optimization")
    
    # Sidebar Configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Neo4j Connection
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
        
        # Connection Status
        st.divider()
        st.subheader("📊 Connection Status")
        
        if st.session_state.connection_status == "connected":
            st.success("🟢 Connected")
        elif st.session_state.connection_status == "failed":
            st.error("🔴 Connection Failed")
        else:
            st.info("⚪ Disconnected")
        
        # Connect Button
        if st.button("🔌 Connect", type="primary", use_container_width=True):
            if neo4j_uri and neo4j_username and neo4j_password and claude_api_key:
                with st.spinner("Connecting..."):
                    initialize_connection(neo4j_uri, neo4j_username, neo4j_password, neo4j_database, claude_api_key)
            else:
                st.warning("Please fill in all required fields.")
        
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
    
    # Main Interface
    if st.session_state.connection_status != "connected":
        st.warning("⚠️ Please connect to the database and Claude AI in the sidebar to use the application.")
        return
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Equipment Analysis", 
        "⚠️ Risk Assessment", 
        "🔗 Dependencies", 
        "📅 Maintenance Scheduling", 
        "🌊 Vibration Analysis"
    ])
    
    with tab1:
        show_equipment_analysis()
    
    with tab2:
        show_risk_assessment()
    
    with tab3:
        show_dependencies()
    
    with tab4:
        show_maintenance_scheduling()
    
    with tab5:
        show_vibration_analysis()

def show_equipment_analysis():
    """Show equipment analysis interface."""
    st.header("🔍 Equipment Analysis")
    st.markdown("Search and analyze maintenance records for equipment across the grid with AI-powered insights.")
    
    # Filter inputs section
    st.subheader("📋 Search Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        equipment_type = st.text_input(
            "Equipment Type (Optional)",
            placeholder="e.g., Generator, Transformer, Bus",
            help="Filter by specific equipment type"
        )
    
    with col2:
        issue_type = st.text_input(
            "Issue Type (Optional)",
            value="vibration",
            placeholder="e.g., vibration, overheating, corrosion",
            help="Search for specific issues in maintenance descriptions"
        )
    
    with col3:
        days_back = st.number_input(
            "Days Back",
            min_value=1,
            max_value=730,
            value=365,
            help="Number of days to look back for maintenance records"
        )
    
    # Search button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        search_button = st.button("🔍 Search Records", type="primary", use_container_width=True)
    
    # Search functionality
    if search_button:
        if not st.session_state.energy_tools:
            st.error("❌ Database connection not available. Please connect in the sidebar.")
            return
        
        with st.spinner("Searching maintenance records..."):
            try:
                results = st.session_state.energy_tools.search_equipment_maintenance_records(
                    equipment_type=equipment_type if equipment_type.strip() else None,
                    issue_type=issue_type if issue_type.strip() else None,
                    days_back=days_back
                )
                
                st.session_state.maintenance_records = results
                
                if results:
                    st.success(f"✅ Found {len(results)} maintenance records")
                    
                    # Display results count and summary
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Records", len(results))
                    
                    with col2:
                        df = pd.DataFrame(results)
                        if 'equipment_type' in df.columns:
                            unique_types = df['equipment_type'].nunique()
                            st.metric("Equipment Types", unique_types)
                        else:
                            st.metric("Equipment Types", "N/A")
                    
                    with col3:
                        if 'maintenance_cost' in df.columns:
                            total_cost = df['maintenance_cost'].sum()
                            st.metric("Total Cost", f"${total_cost:,.2f}")
                        else:
                            st.metric("Total Cost", "N/A")
                    
                    with col4:
                        if 'maintenance_date' in df.columns:
                            df['maintenance_date'] = pd.to_datetime(df['maintenance_date'])
                            date_range = (df['maintenance_date'].max() - df['maintenance_date'].min()).days
                            st.metric("Date Range", f"{date_range} days")
                        else:
                            st.metric("Date Range", "N/A")
                    
                    # Visualizations
                    st.subheader("📊 Maintenance Analysis Charts")
                    
                    # Maintenance frequency chart
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if 'equipment_type' in df.columns:
                            type_counts = df['equipment_type'].value_counts()
                            fig_frequency = px.bar(
                                x=type_counts.index,
                                y=type_counts.values,
                                title="Maintenance Frequency by Equipment Type",
                                labels={'x': 'Equipment Type', 'y': 'Maintenance Count'},
                                color=type_counts.values,
                                color_continuous_scale='viridis'
                            )
                            fig_frequency.update_layout(showlegend=False)
                            st.plotly_chart(fig_frequency, use_container_width=True)
                    
                    # Timeline chart
                    with col2:
                        if 'maintenance_date' in df.columns:
                            # Group by month for timeline
                            df['month'] = df['maintenance_date'].dt.to_period('M')
                            monthly_counts = df.groupby('month').size().reset_index(name='count')
                            monthly_counts['month'] = monthly_counts['month'].astype(str)
                            
                            fig_timeline = px.line(
                                monthly_counts,
                                x='month',
                                y='count',
                                title="Maintenance Activities Timeline",
                                labels={'month': 'Month', 'count': 'Maintenance Count'},
                                markers=True
                            )
                            fig_timeline.update_xaxes(tickangle=45)
                            st.plotly_chart(fig_timeline, use_container_width=True)
                    
                    # Additional visualizations
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if 'maintenance_type' in df.columns:
                            maint_type_counts = df['maintenance_type'].value_counts()
                            fig_maint_type = px.pie(
                                values=maint_type_counts.values,
                                names=maint_type_counts.index,
                                title="Maintenance Type Distribution"
                            )
                            st.plotly_chart(fig_maint_type, use_container_width=True)
                    
                    with col2:
                        if 'maintenance_cost' in df.columns:
                            # Cost distribution
                            fig_cost_dist = px.histogram(
                                df,
                                x='maintenance_cost',
                                title="Maintenance Cost Distribution",
                                nbins=20,
                                labels={'maintenance_cost': 'Cost ($)', 'count': 'Frequency'}
                            )
                            st.plotly_chart(fig_cost_dist, use_container_width=True)
                    
                    # Data table in expandable section
                    with st.expander("📋 View Raw Data Table", expanded=False):
                        st.dataframe(df, use_container_width=True)
                        
                        # Download button
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"maintenance_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    # Claude AI Analysis section
                    st.subheader("🤖 AI-Powered Analysis")
                    
                    if st.session_state.claude_client:
                        if st.button("🧠 Analyze with Claude AI", type="secondary"):
                            with st.spinner("Claude AI is analyzing maintenance patterns..."):
                                try:
                                    analysis = st.session_state.energy_tools.analyze_maintenance_patterns(results)
                                    
                                    st.success("✅ AI Analysis Complete!")
                                    
                                    # Display analysis in a nice format
                                    st.markdown("### 📊 Maintenance Pattern Analysis")
                                    st.markdown(analysis)
                                    
                                    # Store analysis in session state for potential export
                                    st.session_state.last_analysis = {
                                        "timestamp": datetime.now(),
                                        "filters": {
                                            "equipment_type": equipment_type,
                                            "issue_type": issue_type,
                                            "days_back": days_back
                                        },
                                        "analysis": analysis
                                    }
                                    
                                except Exception as e:
                                    st.error(f"❌ AI Analysis failed: {e}")
                    else:
                        st.warning("⚠️ Claude AI client not available. Please check your API key in the sidebar.")
                    
                else:
                    st.info("ℹ️ No maintenance records found matching your criteria.")
                    st.session_state.maintenance_records = []
                    
            except Exception as e:
                st.error(f"❌ Error searching maintenance records: {e}")
                logger.error(f"Search error: {e}")
    
    # Display previous results if available
    elif st.session_state.maintenance_records:
        st.subheader("📊 Previous Search Results")
        
        df = pd.DataFrame(st.session_state.maintenance_records)
        
        # Quick summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", len(st.session_state.maintenance_records))
        with col2:
            if 'maintenance_cost' in df.columns:
                total_cost = df['maintenance_cost'].sum()
                st.metric("Total Cost", f"${total_cost:,.2f}")
        with col3:
            if 'equipment_type' in df.columns:
                unique_types = df['equipment_type'].nunique()
                st.metric("Equipment Types", unique_types)
        
        # Show data table
        with st.expander("📋 View Previous Results", expanded=False):
            st.dataframe(df, use_container_width=True)
    
    # Help section
    with st.expander("ℹ️ How to use Equipment Analysis", expanded=False):
        st.markdown("""
        **Equipment Analysis Guide:**
        
        **Filters:**
        - **Equipment Type**: Enter specific equipment types (e.g., "Generator", "Transformer")
        - **Issue Type**: Search for specific issues (default: "vibration")
        - **Days Back**: Set the time period for analysis (1-730 days)
        
        **Features:**
        - **Search**: Find maintenance records matching your criteria
        - **Visualizations**: View maintenance frequency, timeline, and cost analysis
        - **AI Analysis**: Get intelligent insights from Claude AI
        - **Data Export**: Download results as CSV
        
        **Tips:**
        - Leave filters empty to search all records
        - Use specific equipment types for targeted analysis
        - Adjust the time period based on your analysis needs
        - Use AI analysis for comprehensive pattern recognition
        """)

def show_risk_assessment():
    """Show risk assessment interface."""
    st.header("⚠️ Risk Assessment")
    st.markdown("Identify and analyze high-risk equipment across the grid with comprehensive risk metrics and visualizations.")
    
    # Risk threshold configuration
    st.subheader("🎯 Risk Configuration")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        risk_threshold = st.slider(
            "Risk Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Minimum risk score to include equipment (0.0 = no risk, 1.0 = maximum risk)"
        )
        
        # Risk level indicators
        if risk_threshold < 0.3:
            risk_level = "🟢 Low Risk"
            risk_color = "green"
        elif risk_threshold < 0.7:
            risk_level = "🟡 Medium Risk"
            risk_color = "orange"
        else:
            risk_level = "🔴 High Risk"
            risk_color = "red"
        
        st.markdown(f"**Current Risk Level:** {risk_level}")
    
    with col2:
        st.info(f"""
        **Risk Threshold Guide:**
        
        🟢 **Low (0.0-0.3)**: Minimal risk equipment
        🟡 **Medium (0.3-0.7)**: Moderate risk equipment  
        🔴 **High (0.7-1.0)**: Critical risk equipment
        
        Current: **{risk_threshold}**
        """)
    
    # Search button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        assess_button = st.button("🔍 Assess Risk", type="primary", use_container_width=True)
    
    # Risk assessment functionality
    if assess_button:
        if not st.session_state.energy_tools:
            st.error("❌ Database connection not available. Please connect in the sidebar.")
            return
        
        with st.spinner("Analyzing equipment risk..."):
            try:
                results = st.session_state.energy_tools.get_risky_equipment(risk_threshold)
                st.session_state.risky_equipment = results
                
                if results:
                    st.success(f"✅ Found {len(results)} high-risk equipment items")
                    
                    # Convert to DataFrame for analysis
                    df = pd.DataFrame(results)
                    
                    # Calculate metrics
                    avg_risk = df['risk_score'].mean() if 'risk_score' in df.columns else 0
                    critical_count = len(df[df['equipment_criticality'] == 'Critical']) if 'equipment_criticality' in df.columns else 0
                    highest_risk = df['risk_score'].max() if 'risk_score' in df.columns else 0
                    affected_locations = df['equipment_location'].nunique() if 'equipment_location' in df.columns else 0
                    
                    # Display metrics
                    st.subheader("📊 Risk Metrics")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Average Risk Score",
                            f"{avg_risk:.2f}",
                            delta=f"{avg_risk - risk_threshold:.2f}",
                            delta_color="inverse"
                        )
                    
                    with col2:
                        st.metric(
                            "Critical Equipment",
                            critical_count,
                            delta=f"{critical_count} items"
                        )
                    
                    with col3:
                        st.metric(
                            "Highest Risk Score",
                            f"{highest_risk:.2f}",
                            delta="Maximum"
                        )
                    
                    with col4:
                        st.metric(
                            "Affected Locations",
                            affected_locations,
                            delta="Locations"
                        )
                    
                    # Risk visualization
                    st.subheader("📈 Risk Visualization")
                    
                    if 'equipment_type' in df.columns and 'risk_score' in df.columns:
                        # Prepare data for scatter plot
                        # Create criticality size mapping
                        criticality_size_map = {
                            'Critical': 20,
                            'High': 15,
                            'Medium': 10,
                            'Low': 5
                        }
                        
                        df['size'] = df['equipment_criticality'].map(criticality_size_map).fillna(10)
                        
                        # Create color scale based on risk score
                        df['color'] = df['risk_score']
                        
                        # Create scatter plot
                        fig_scatter = px.scatter(
                            df,
                            x='equipment_type',
                            y='risk_score',
                            color='color',
                            size='size',
                            hover_data=['equipment_name', 'equipment_location', 'risk_factors'],
                            title="Equipment Risk Assessment Scatter Plot",
                            labels={
                                'equipment_type': 'Equipment Type',
                                'risk_score': 'Risk Score',
                                'color': 'Risk Level',
                                'size': 'Criticality'
                            },
                            color_continuous_scale='reds',
                            size_max=20
                        )
                        
                        # Update layout for better visualization
                        fig_scatter.update_layout(
                            xaxis_title="Equipment Type",
                            yaxis_title="Risk Score",
                            height=500,
                            showlegend=True
                        )
                        
                        # Add threshold line
                        fig_scatter.add_hline(
                            y=risk_threshold,
                            line_dash="dash",
                            line_color="red",
                            annotation_text=f"Threshold: {risk_threshold}",
                            annotation_position="top right"
                        )
                        
                        st.plotly_chart(fig_scatter, use_container_width=True)
                        
                        # Additional visualizations
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Risk score distribution
                            fig_dist = px.histogram(
                                df,
                                x='risk_score',
                                title="Risk Score Distribution",
                                nbins=20,
                                color_discrete_sequence=['red'],
                                labels={'risk_score': 'Risk Score', 'count': 'Equipment Count'}
                            )
                            fig_dist.add_vline(
                                x=risk_threshold,
                                line_dash="dash",
                                line_color="red",
                                annotation_text=f"Threshold: {risk_threshold}"
                            )
                            st.plotly_chart(fig_dist, use_container_width=True)
                        
                        with col2:
                            # Equipment type by risk
                            if 'equipment_type' in df.columns:
                                type_avg_risk = df.groupby('equipment_type')['risk_score'].mean().sort_values(ascending=False)
                                fig_type = px.bar(
                                    x=type_avg_risk.index,
                                    y=type_avg_risk.values,
                                    title="Average Risk Score by Equipment Type",
                                    labels={'x': 'Equipment Type', 'y': 'Average Risk Score'},
                                    color=type_avg_risk.values,
                                    color_continuous_scale='reds'
                                )
                                fig_type.update_layout(showlegend=False)
                                st.plotly_chart(fig_type, use_container_width=True)
                    
                    # Expandable data table with color-coded risk scores
                    st.subheader("📋 Risk Assessment Details")
                    
                    with st.expander("🔍 View Detailed Risk Data", expanded=False):
                        # Create a styled dataframe with color-coded risk scores
                        display_df = df.copy()
                        
                        # Add color coding for risk scores
                        def color_risk_score(val):
                            if pd.isna(val):
                                return ''
                            if val >= 0.8:
                                return 'background-color: #ff4444; color: white; font-weight: bold'
                            elif val >= 0.6:
                                return 'background-color: #ffaa00; color: black; font-weight: bold'
                            elif val >= 0.4:
                                return 'background-color: #ffff00; color: black'
                            else:
                                return 'background-color: #90EE90; color: black'
                        
                        # Apply styling
                        styled_df = display_df.style.applymap(
                            color_risk_score, 
                            subset=['risk_score']
                        ).format({
                            'risk_score': '{:.3f}',
                            'maintenance_cost': '${:,.2f}' if 'maintenance_cost' in display_df.columns else None
                        })
                        
                        st.dataframe(styled_df, use_container_width=True)
                        
                        # Download button
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Risk Assessment CSV",
                            data=csv,
                            file_name=f"risk_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    # Risk insights section
                    st.subheader("💡 Risk Insights")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.info(f"""
                        **Risk Assessment Summary:**
                        
                        📊 **Total High-Risk Equipment**: {len(results)}
                        🎯 **Risk Threshold**: {risk_threshold}
                        📍 **Affected Locations**: {affected_locations}
                        ⚠️ **Critical Equipment**: {critical_count}
                        
                        **Risk Distribution:**
                        - Very High Risk (≥0.8): {len(df[df['risk_score'] >= 0.8])}
                        - High Risk (0.6-0.8): {len(df[(df['risk_score'] >= 0.6) & (df['risk_score'] < 0.8)])}
                        - Medium Risk (0.4-0.6): {len(df[(df['risk_score'] >= 0.4) & (df['risk_score'] < 0.6)])}
                        """)
                    
                    with col2:
                        # Top risk factors
                        if 'risk_factors' in df.columns:
                            st.warning(f"""
                            **Top Risk Factors:**
                            
                            Most common risk factors identified:
                            - Equipment age and wear
                            - Maintenance history
                            - Environmental conditions
                            - Operational stress
                            
                            **Recommendations:**
                            - Prioritize maintenance for critical equipment
                            - Review maintenance schedules
                            - Consider equipment replacement
                            - Implement monitoring systems
                            """)
                        else:
                            st.warning("""
                            **Risk Management Tips:**
                            
                            - Regular risk assessments
                            - Preventive maintenance scheduling
                            - Equipment monitoring systems
                            - Staff training on risk management
                            """)
                    
                else:
                    st.info(f"ℹ️ No equipment found with risk score >= {risk_threshold}")
                    st.session_state.risky_equipment = []
                    
            except Exception as e:
                st.error(f"❌ Error assessing risk: {e}")
                logger.error(f"Risk assessment error: {e}")
    
    # Display previous results if available
    elif st.session_state.risky_equipment:
        st.subheader("📊 Previous Risk Assessment Results")
        
        df = pd.DataFrame(st.session_state.risky_equipment)
        
        # Quick summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("High-Risk Equipment", len(st.session_state.risky_equipment))
        with col2:
            if 'risk_score' in df.columns:
                avg_risk = df['risk_score'].mean()
                st.metric("Average Risk Score", f"{avg_risk:.2f}")
        with col3:
            if 'equipment_criticality' in df.columns:
                critical_count = len(df[df['equipment_criticality'] == 'Critical'])
                st.metric("Critical Equipment", critical_count)
        with col4:
            if 'equipment_location' in df.columns:
                locations = df['equipment_location'].nunique()
                st.metric("Affected Locations", locations)
        
        # Show data table
        with st.expander("📋 View Previous Risk Assessment", expanded=False):
            st.dataframe(df, use_container_width=True)
    
    # Help section
    with st.expander("ℹ️ How to use Risk Assessment", expanded=False):
        st.markdown("""
        **Risk Assessment Guide:**
        
        **Risk Threshold:**
        - **0.0-0.3**: Low risk equipment (green)
        - **0.3-0.7**: Medium risk equipment (yellow)
        - **0.7-1.0**: High risk equipment (red)
        
        **Visualization Features:**
        - **Scatter Plot**: Equipment type vs risk score with color coding
        - **Size**: Represents equipment criticality level
        - **Hover Data**: Equipment details on hover
        - **Threshold Line**: Red dashed line showing current threshold
        
        **Metrics Explained:**
        - **Average Risk Score**: Mean risk across all equipment
        - **Critical Equipment**: Number of critical priority items
        - **Highest Risk Score**: Maximum risk value found
        - **Affected Locations**: Number of unique locations
        
        **Risk Management:**
        - Use threshold to filter equipment requiring attention
        - Focus on critical equipment with high risk scores
        - Consider location-based risk patterns
        - Plan maintenance based on risk assessment results
        """)

def show_dependencies():
    """Show equipment dependencies interface."""
    st.header("🔗 Dependencies")
    st.markdown("Analyze equipment dependencies and relationships across installations with comprehensive mapping and metrics.")
    
    # Dependency analysis configuration
    st.subheader("🎯 Dependency Configuration")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        installation_id = st.text_input(
            "Installation ID (Optional)",
            placeholder="e.g., INST-001, SUB-002, GRID-003",
            help="Leave empty to analyze all installations"
        )
        
        # Analysis button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            analyze_button = st.button("🔍 Analyze Dependencies", type="primary", use_container_width=True)
    
    with col2:
        st.info("""
        **Dependency Analysis:**
        
        🔗 **Equipment Dependencies**: How equipment relies on each other
        📍 **Installation Mapping**: Equipment contained in installations
        🛠️ **Maintenance Impact**: How maintenance affects dependencies
        ⚠️ **Risk Assessment**: Current risk scores for equipment
        
        Use specific Installation ID for targeted analysis.
        """)
    
    # Dependency analysis functionality
    if analyze_button:
        if not st.session_state.energy_tools:
            st.error("❌ Database connection not available. Please connect in the sidebar.")
            return
        
        with st.spinner("Analyzing equipment dependencies..."):
            try:
                results = st.session_state.energy_tools.get_installation_equipments_dependency(
                    installation_id if installation_id.strip() else None
                )
                
                if results:
                    st.success(f"✅ Found {len(results)} installation-equipment relationships")
                    
                    # Convert to DataFrame for analysis
                    df = pd.DataFrame(results)
                    
                    # Calculate metrics
                    installations_count = df['installation_id'].nunique() if 'installation_id' in df.columns else 0
                    equipment_count = df['equipment_id'].nunique() if 'equipment_id' in df.columns else 0
                    
                    # Count dependencies
                    dependency_count = 0
                    if 'dependent_equipment' in df.columns:
                        for deps in df['dependent_equipment']:
                            if deps and len(deps) > 0:
                                dependency_count += len(deps)
                    
                    # Display metrics
                    st.subheader("📊 Dependency Metrics")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Installations",
                            installations_count,
                            delta="locations"
                        )
                    
                    with col2:
                        st.metric(
                            "Equipment Items",
                            equipment_count,
                            delta="items"
                        )
                    
                    with col3:
                        st.metric(
                            "Dependencies",
                            dependency_count,
                            delta="relationships"
                        )
                    
                    with col4:
                        if 'current_risk_score' in df.columns:
                            avg_risk = df['current_risk_score'].mean()
                            st.metric(
                                "Avg Risk Score",
                                f"{avg_risk:.2f}",
                                delta="across equipment"
                            )
                        else:
                            st.metric("Avg Risk Score", "N/A")
                    
                    # Dependency visualization
                    st.subheader("📈 Dependency Analysis")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Installation equipment distribution
                        if 'installation_id' in df.columns and 'equipment_id' in df.columns:
                            install_equipment_counts = df.groupby('installation_id').size().sort_values(ascending=False)
                            
                            fig_install = px.bar(
                                x=install_equipment_counts.index,
                                y=install_equipment_counts.values,
                                title="Equipment Count by Installation",
                                labels={'x': 'Installation ID', 'y': 'Equipment Count'},
                                color=install_equipment_counts.values,
                                color_continuous_scale='blues'
                            )
                            fig_install.update_layout(showlegend=False)
                            st.plotly_chart(fig_install, use_container_width=True)
                    
                    with col2:
                        # Equipment criticality distribution
                        if 'equipment_criticality' in df.columns:
                            criticality_counts = df['equipment_criticality'].value_counts()
                            
                            fig_criticality = px.pie(
                                values=criticality_counts.values,
                                names=criticality_counts.index,
                                title="Equipment Criticality Distribution"
                            )
                            st.plotly_chart(fig_criticality, use_container_width=True)
                    
                    # Dependency network analysis
                    if 'dependent_equipment' in df.columns:
                        st.subheader("🔗 Dependency Network")
                        
                        # Count dependencies
                        dependency_counts = []
                        for deps in df['dependent_equipment']:
                            if deps and len(deps) > 0:
                                dependency_counts.extend(deps)
                        
                        if dependency_counts:
                            dep_df = pd.DataFrame({'equipment_id': dependency_counts})
                            dep_counts = dep_df['equipment_id'].value_counts().head(10)
                            
                            fig_dep = px.bar(
                                x=dep_counts.index,
                                y=dep_counts.values,
                                title="Most Dependent Equipment",
                                labels={'x': 'Equipment ID', 'y': 'Dependency Count'},
                                color=dep_counts.values,
                                color_continuous_scale='reds'
                            )
                            fig_dep.update_layout(showlegend=False)
                            st.plotly_chart(fig_dep, use_container_width=True)
                    
                    # Data table with dependency relationships
                    st.subheader("📋 Dependency Relationships")
                    
                    with st.expander("🔍 View Detailed Dependency Data", expanded=False):
                        # Create a more readable display
                        display_df = df.copy()
                        
                        # Format dependent equipment for better display
                        if 'dependent_equipment' in display_df.columns:
                            display_df['dependent_equipment'] = display_df['dependent_equipment'].apply(
                                lambda x: ', '.join(x) if x and len(x) > 0 else 'None'
                            )
                        
                        # Format maintenance history
                        if 'maintenance_history' in display_df.columns:
                            display_df['maintenance_history'] = display_df['maintenance_history'].apply(
                                lambda x: f"{len(x)} records" if x and len(x) > 0 else 'No records'
                            )
                        
                        st.dataframe(display_df, use_container_width=True)
                        
                        # Download button
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Dependencies CSV",
                            data=csv,
                            file_name=f"dependencies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    # Dependency insights
                    st.subheader("💡 Dependency Insights")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.info(f"""
                        **Dependency Summary:**
                        
                        🏭 **Installations Analyzed**: {installations_count}
                        ⚙️ **Equipment Items**: {equipment_count}
                        🔗 **Dependencies**: {dependency_count}
                        📍 **Installation Focus**: {installation_id if installation_id else 'All Installations'}
                        
                        **Key Findings:**
                        - Average equipment per installation: {equipment_count/installations_count:.1f}
                        - Dependency density: {dependency_count/equipment_count:.1f} per equipment
                        """)
                    
                    with col2:
                        st.warning("""
                        **Dependency Management:**
                        
                        **Impact Analysis:**
                        - Equipment with high dependencies need careful maintenance planning
                        - Consider cascading effects when scheduling maintenance
                        - Monitor critical equipment dependencies closely
                        
                        **Recommendations:**
                        - Prioritize maintenance for highly dependent equipment
                        - Plan maintenance windows to minimize impact
                        - Implement redundancy for critical dependencies
                        """)
                
                else:
                    st.info("ℹ️ No installation dependencies found.")
                    
            except Exception as e:
                st.error(f"❌ Error analyzing dependencies: {e}")
                logger.error(f"Dependency analysis error: {e}")

def show_maintenance_scheduling():
    """Show maintenance scheduling interface."""
    st.header("📅 Maintenance Scheduling")
    st.markdown("Generate AI-powered maintenance schedules based on risk assessment, equipment health, and operational constraints.")
    
    # Schedule configuration
    st.subheader("🎯 Schedule Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        schedule_start = st.date_input(
            "Schedule Start Date",
            value=datetime.now().date(),
            help="Start date for maintenance scheduling"
        )
        
        risk_threshold = st.slider(
            "Risk Threshold for Scheduling",
            min_value=0.0,
            max_value=1.0,
            value=0.6,
            step=0.1,
            help="Minimum risk score to include in schedule (0.0-1.0)"
        )
    
    with col2:
        st.info(f"""
        **Schedule Parameters:**
        
        📅 **Start Date**: {schedule_start}
        ⚠️ **Risk Threshold**: {risk_threshold}
        🎯 **Focus**: High-risk equipment prioritization
        🤖 **AI-Powered**: Intelligent scheduling recommendations
        
        The system will generate schedules considering:
        - Equipment risk scores
        - Maintenance history
        - Dependencies
        - Operational constraints
        """)
    
    # Generate schedule button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_button = st.button("🤖 Generate AI Schedule", type="primary", use_container_width=True)
    
    # Schedule generation functionality
    if generate_button:
        if not st.session_state.energy_tools:
            st.error("❌ Database connection not available. Please connect in the sidebar.")
            return
        
        if not st.session_state.claude_client:
            st.error("❌ Claude AI not available. Please check your API key in the sidebar.")
            return
        
        with st.spinner("Generating AI-powered maintenance schedule..."):
            try:
                # Get high-risk equipment for scheduling
                risky_equipment = st.session_state.energy_tools.get_risky_equipment(risk_threshold)
                
                if risky_equipment:
                    st.success(f"✅ Generated maintenance schedule for {len(risky_equipment)} equipment items")
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(risky_equipment)
                    
                    # Generate AI-powered schedule
                    schedule_analysis = st.session_state.energy_tools.analyze_maintenance_patterns(risky_equipment)
                    
                    # Display AI-generated schedule
                    st.subheader("🤖 AI-Generated Maintenance Schedule")
                    
                    # Format the schedule display
                    st.markdown("### 📋 Schedule Overview")
                    st.markdown(schedule_analysis)
                    
                    # Schedule metrics
                    st.subheader("📊 Schedule Metrics")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Scheduled Equipment", len(risky_equipment))
                    
                    with col2:
                        if 'risk_score' in df.columns:
                            avg_risk = df['risk_score'].mean()
                            st.metric("Average Risk Score", f"{avg_risk:.2f}")
                    
                    with col3:
                        if 'equipment_criticality' in df.columns:
                            critical_count = len(df[df['equipment_criticality'] == 'Critical'])
                            st.metric("Critical Equipment", critical_count)
                    
                    with col4:
                        if 'equipment_location' in df.columns:
                            locations = df['equipment_location'].nunique()
                            st.metric("Affected Locations", locations)
                    
                    # Expandable sections
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        with st.expander("📊 Risk Data Summary", expanded=False):
                            if 'risk_score' in df.columns:
                                risk_summary = df[['equipment_id', 'equipment_type', 'risk_score', 'equipment_criticality']].copy()
                                risk_summary = risk_summary.sort_values('risk_score', ascending=False)
                                st.dataframe(risk_summary, use_container_width=True)
                            else:
                                st.info("No risk data available")
                    
                    with col2:
                        with st.expander("🔗 Dependency Data Summary", expanded=False):
                            # Get dependency data for scheduled equipment
                            equipment_ids = df['equipment_id'].tolist() if 'equipment_id' in df.columns else []
                            if equipment_ids:
                                dependency_data = st.session_state.energy_tools.get_installation_equipments_dependency()
                                if dependency_data:
                                    dep_df = pd.DataFrame(dependency_data)
                                    scheduled_deps = dep_df[dep_df['equipment_id'].isin(equipment_ids)]
                                    if not scheduled_deps.empty:
                                        st.dataframe(scheduled_deps[['equipment_id', 'dependent_equipment', 'current_risk_score']], use_container_width=True)
                                    else:
                                        st.info("No dependency data for scheduled equipment")
                                else:
                                    st.info("No dependency data available")
                            else:
                                st.info("No equipment IDs available")
                    
                    # Schedule visualization
                    st.subheader("📈 Schedule Visualization")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Equipment type distribution in schedule
                        if 'equipment_type' in df.columns:
                            type_counts = df['equipment_type'].value_counts()
                            fig_type = px.pie(
                                values=type_counts.values,
                                names=type_counts.index,
                                title="Scheduled Equipment by Type"
                            )
                            st.plotly_chart(fig_type, use_container_width=True)
                    
                    with col2:
                        # Risk score distribution
                        if 'risk_score' in df.columns:
                            fig_risk = px.histogram(
                                df,
                                x='risk_score',
                                title="Risk Score Distribution in Schedule",
                                nbins=15,
                                color_discrete_sequence=['orange']
                            )
                            fig_risk.add_vline(
                                x=risk_threshold,
                                line_dash="dash",
                                line_color="red",
                                annotation_text=f"Threshold: {risk_threshold}"
                            )
                            st.plotly_chart(fig_risk, use_container_width=True)
                    
                    # Download schedule
                    st.subheader("📥 Export Schedule")
                    
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Maintenance Schedule CSV",
                        data=csv,
                        file_name=f"maintenance_schedule_{schedule_start}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                else:
                    st.info(f"ℹ️ No equipment found with risk score >= {risk_threshold}")
                    
            except Exception as e:
                st.error(f"❌ Error generating maintenance schedule: {e}")
                logger.error(f"Schedule generation error: {e}")

def show_vibration_analysis():
    """Show vibration analysis interface."""
    st.header("🌊 Vibration Analysis")
    st.markdown("Specialized analysis for vibration-related issues and maintenance patterns with AI-powered insights.")
    
    # Vibration analysis configuration
    st.subheader("🎯 Vibration Analysis Configuration")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        days_back = st.number_input(
            "Analysis Period (Days)",
            min_value=7,
            max_value=730,
            value=90,
            help="Number of days to analyze for vibration issues"
        )
        
        # Analysis button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            analyze_button = st.button("🌊 Analyze Vibration Issues", type="primary", use_container_width=True)
    
    with col2:
        st.info(f"""
        **Vibration Analysis:**
        
        📊 **Analysis Period**: {days_back} days
        🔍 **Focus**: Vibration-related maintenance records
        🤖 **AI Analysis**: Specialized vibration pattern recognition
        📈 **Visualization**: Maintenance trends and cost analysis
        
        **Common Vibration Issues:**
        - Bearing wear and failure
        - Misalignment problems
        - Unbalanced rotating equipment
        - Resonance and harmonics
        """)
    
    # Vibration analysis functionality
    if analyze_button:
        if not st.session_state.energy_tools:
            st.error("❌ Database connection not available. Please connect in the sidebar.")
            return
        
        with st.spinner("Analyzing vibration-related issues..."):
            try:
                results = st.session_state.energy_tools.get_vibration_analysis(days_back=days_back)
                
                if results:
                    st.success(f"✅ Found {len(results)} vibration-related maintenance records")
                    
                    # Convert to DataFrame for analysis
                    df = pd.DataFrame(results)
                    
                    # Calculate metrics
                    affected_equipment = df['equipment_id'].nunique() if 'equipment_id' in df.columns else 0
                    avg_cost = df['maintenance_cost'].mean() if 'maintenance_cost' in df.columns else 0
                    equipment_types = df['equipment_type'].nunique() if 'equipment_type' in df.columns else 0
                    total_cost = df['maintenance_cost'].sum() if 'maintenance_cost' in df.columns else 0
                    
                    # Display metrics
                    st.subheader("📊 Vibration Analysis Metrics")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Affected Equipment",
                            affected_equipment,
                            delta="items"
                        )
                    
                    with col2:
                        st.metric(
                            "Average Cost",
                            f"${avg_cost:,.2f}",
                            delta="per incident"
                        )
                    
                    with col3:
                        st.metric(
                            "Equipment Types",
                            equipment_types,
                            delta="types affected"
                        )
                    
                    with col4:
                        st.metric(
                            "Total Cost",
                            f"${total_cost:,.2f}",
                            delta="vibration issues"
                        )
                    
                    # Maintenance chart visualization
                    st.subheader("📈 Vibration Maintenance Analysis")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Vibration issues over time
                        if 'maintenance_date' in df.columns:
                            df['maintenance_date'] = pd.to_datetime(df['maintenance_date'])
                            monthly_counts = df.groupby(df['maintenance_date'].dt.to_period('M')).size()
                            
                            fig_timeline = px.line(
                                x=monthly_counts.index.astype(str),
                                y=monthly_counts.values,
                                title="Vibration Issues Over Time",
                                labels={'x': 'Month', 'y': 'Issue Count'},
                                markers=True
                            )
                            fig_timeline.update_xaxes(tickangle=45)
                            st.plotly_chart(fig_timeline, use_container_width=True)
                    
                    with col2:
                        # Equipment type distribution
                        if 'equipment_type' in df.columns:
                            type_counts = df['equipment_type'].value_counts()
                            fig_type = px.pie(
                                values=type_counts.values,
                                names=type_counts.index,
                                title="Vibration Issues by Equipment Type"
                            )
                            st.plotly_chart(fig_type, use_container_width=True)
                    
                    # Additional visualizations
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Cost distribution
                        if 'maintenance_cost' in df.columns:
                            fig_cost = px.histogram(
                                df,
                                x='maintenance_cost',
                                title="Vibration Issue Cost Distribution",
                                nbins=15,
                                color_discrete_sequence=['red'],
                                labels={'maintenance_cost': 'Cost ($)', 'count': 'Issue Count'}
                            )
                            st.plotly_chart(fig_cost, use_container_width=True)
                    
                    with col2:
                        # Criticality analysis
                        if 'equipment_criticality' in df.columns:
                            criticality_counts = df['equipment_criticality'].value_counts()
                            fig_criticality = px.bar(
                                x=criticality_counts.index,
                                y=criticality_counts.values,
                                title="Vibration Issues by Criticality",
                                labels={'x': 'Criticality Level', 'y': 'Issue Count'},
                                color=criticality_counts.values,
                                color_continuous_scale='reds'
                            )
                            fig_criticality.update_layout(showlegend=False)
                            st.plotly_chart(fig_criticality, use_container_width=True)
                    
                    # Claude's specialized vibration analysis
                    st.subheader("🤖 AI-Powered Vibration Analysis")
                    
                    if st.session_state.claude_client:
                        if st.button("🧠 Get Specialized Vibration Analysis", type="secondary"):
                            with st.spinner("Claude AI is analyzing vibration patterns..."):
                                try:
                                    # Create specialized vibration analysis prompt
                                    vibration_prompt = f"""
                                    Analyze the following vibration-related maintenance data for an energy grid management system:
                                    
                                    Summary Statistics:
                                    - Total Vibration Issues: {len(results)}
                                    - Affected Equipment: {affected_equipment}
                                    - Equipment Types Affected: {equipment_types}
                                    - Total Cost: ${total_cost:,.2f}
                                    - Average Cost per Issue: ${avg_cost:,.2f}
                                    - Analysis Period: {days_back} days
                                    
                                    Equipment Type Distribution:
                                    {df['equipment_type'].value_counts().to_dict() if 'equipment_type' in df.columns else {}}
                                    
                                    Cost Analysis:
                                    - Average Cost: ${avg_cost:,.2f}
                                    - Maximum Cost: ${df['maintenance_cost'].max() if 'maintenance_cost' in df.columns else 0:,.2f}
                                    - Minimum Cost: ${df['maintenance_cost'].min() if 'maintenance_cost' in df.columns else 0:,.2f}
                                    
                                    Please provide a specialized vibration analysis including:
                                    1. Common vibration failure patterns and root causes
                                    2. Equipment types most prone to vibration issues
                                    3. Cost implications of vibration-related failures
                                    4. Preventive maintenance recommendations for vibration control
                                    5. Monitoring and detection strategies
                                    6. Industry best practices for vibration management
                                    7. Risk assessment for vibration-related equipment failures
                                    
                                    Format your response for vibration engineering and maintenance professionals.
                                    """
                                    
                                    analysis = st.session_state.claude_client.analyze_grid_data(vibration_prompt)
                                    
                                    st.success("✅ Specialized Vibration Analysis Complete!")
                                    
                                    # Display analysis
                                    st.markdown("### 🌊 Vibration Pattern Analysis")
                                    st.markdown(analysis)
                                    
                                except Exception as e:
                                    st.error(f"❌ Vibration analysis failed: {e}")
                    else:
                        st.warning("⚠️ Claude AI client not available. Please check your API key in the sidebar.")
                    
                    # Raw data table in expandable section
                    st.subheader("📋 Vibration Analysis Data")
                    
                    with st.expander("🔍 View Raw Vibration Data", expanded=False):
                        # Create a styled dataframe
                        display_df = df.copy()
                        
                        # Format dates for better display
                        if 'maintenance_date' in display_df.columns:
                            display_df['maintenance_date'] = pd.to_datetime(display_df['maintenance_date']).dt.strftime('%Y-%m-%d')
                        
                        # Format costs
                        if 'maintenance_cost' in display_df.columns:
                            display_df['maintenance_cost'] = display_df['maintenance_cost'].apply(lambda x: f"${x:,.2f}")
                        
                        st.dataframe(display_df, use_container_width=True)
                        
                        # Download button
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Vibration Analysis CSV",
                            data=csv,
                            file_name=f"vibration_analysis_{days_back}days_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    # Vibration insights
                    st.subheader("💡 Vibration Insights")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.info(f"""
                        **Vibration Analysis Summary:**
                        
                        📊 **Total Issues**: {len(results)}
                        ⚙️ **Affected Equipment**: {affected_equipment}
                        🏭 **Equipment Types**: {equipment_types}
                        💰 **Total Cost**: ${total_cost:,.2f}
                        📅 **Analysis Period**: {days_back} days
                        
                        **Key Patterns:**
                        - Most affected equipment types
                        - Cost trends over time
                        - Criticality distribution
                        - Maintenance frequency patterns
                        """)
                    
                    with col2:
                        st.warning("""
                        **Vibration Management:**
                        
                        **Common Causes:**
                        - Bearing wear and lubrication issues
                        - Misalignment and balancing problems
                        - Resonance and harmonic vibrations
                        - Foundation and mounting issues
                        
                        **Prevention Strategies:**
                        - Regular vibration monitoring
                        - Predictive maintenance scheduling
                        - Equipment balancing and alignment
                        - Foundation inspections
                        """)
                
                else:
                    st.info(f"ℹ️ No vibration-related maintenance records found for the last {days_back} days.")
                    
            except Exception as e:
                st.error(f"❌ Error analyzing vibration issues: {e}")
                logger.error(f"Vibration analysis error: {e}")
    
    # Help section
    with st.expander("ℹ️ How to use Vibration Analysis", expanded=False):
        st.markdown("""
        **Vibration Analysis Guide:**
        
        **Analysis Period:**
        - **7-30 days**: Recent vibration issues
        - **30-90 days**: Medium-term patterns
        - **90+ days**: Long-term trends
        
        **Key Metrics:**
        - **Affected Equipment**: Number of unique equipment with vibration issues
        - **Average Cost**: Mean cost per vibration incident
        - **Equipment Types**: Variety of equipment affected
        - **Total Cost**: Overall financial impact
        
        **Visualization Features:**
        - **Timeline Chart**: Vibration issues over time
        - **Equipment Distribution**: Issues by equipment type
        - **Cost Analysis**: Financial impact distribution
        - **Criticality Analysis**: Issues by equipment importance
        
        **AI Analysis:**
        - Pattern recognition in vibration failures
        - Root cause analysis
        - Preventive maintenance recommendations
        - Industry best practices
        
        **Best Practices:**
        - Regular vibration monitoring
        - Predictive maintenance scheduling
        - Equipment balancing and alignment
        - Foundation and mounting inspections
        """)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application Error: {e}")
        st.info("Please check the logs for more details.") 
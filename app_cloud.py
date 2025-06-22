"""
Energy Grid Management Agent - Cloud Optimized Streamlit Application
Optimized for Streamlit Cloud deployment with enhanced performance and reliability.
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
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError, ClientError

# Import our cloud-optimized modules
from secrets_manager import initialize_secrets, display_secrets_status
from health_checker import initialize_health_checker
from cloud_cache import cloud_cache, streamlit_cache_data, display_cache_stats
from cloud_logging import initialize_cloud_logging, display_monitoring_dashboard, performance_monitor

# Configure logging for cloud environment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration for Streamlit Cloud
st.set_page_config(
    page_title="Energy Grid Management Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-username/energy-agent-claude',
        'Report a bug': 'https://github.com/your-username/energy-agent-claude/issues',
        'About': 'Energy Grid Management Agent - Cloud Optimized Version'
    }
)

# Custom CSS for cloud-optimized styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    .error-boundary {
        background: #fee;
        border: 1px solid #fcc;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .success-message {
        background: #efe;
        border: 1px solid #cfc;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables for cloud environment."""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
        st.session_state.secrets_manager = None
        st.session_state.health_checker = None
        st.session_state.energy_tools = None
        st.session_state.claude_client = None
        st.session_state.performance_metrics = {}
        st.session_state.error_count = 0
        st.session_state.start_time = time.time()
        st.session_state.cloud_logger = None

def error_boundary(func):
    """Decorator for graceful error handling in cloud environment."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.session_state.error_count += 1
            logger.error(f"Error in {func.__name__}: {str(e)}")
            
            st.error(f"""
            ⚠️ An error occurred while processing your request.
            
            **Error Details:** {str(e)}
            
            Please try refreshing the page or contact support if the issue persists.
            """)
            
            # Show error details in expander for debugging
            with st.expander("🔧 Technical Details (for debugging)"):
                st.code(f"""
                Function: {func.__name__}
                Error: {str(e)}
                Error Count: {st.session_state.error_count}
                Session Time: {time.time() - st.session_state.start_time:.1f}s
                """)
            
            return None
    return wrapper

@streamlit_cache_data(ttl=600)  # Cache for 10 minutes
def create_maintenance_chart(maintenance_data: List[Dict[str, Any]]) -> Optional[go.Figure]:
    """Create a bar chart of maintenance by equipment type with cloud caching."""
    if not maintenance_data:
        return None
    
    try:
        df = pd.DataFrame(maintenance_data)
        
        if 'equipment_type' not in df.columns:
            return None
        
        type_counts = df['equipment_type'].value_counts()
        
        if type_counts.empty:
            return None
        
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

@streamlit_cache_data(ttl=600)
def create_risk_chart(risk_data: List[Dict[str, Any]]) -> Optional[go.Figure]:
    """Create a scatter plot of risk scores vs equipment types with cloud caching."""
    if not risk_data:
        return None
    
    try:
        df = pd.DataFrame(risk_data)
        
        if 'equipment_type' not in df.columns or 'risk_score' not in df.columns:
            return None
        
        df = df.dropna(subset=['equipment_type', 'risk_score'])
        
        if df.empty:
            return None
        
        criticality_size_map = {
            'Critical': 20,
            'High': 15,
            'Medium': 10,
            'Low': 5
        }
        
        df['size'] = df.get('equipment_criticality', 'Medium').map(criticality_size_map).fillna(10)
        
        fig = go.Figure()
        
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

class CloudEnergyAgentTools:
    """Enhanced tools for energy grid management with cloud optimizations."""
    
    def __init__(self, uri: str = None, username: str = None, password: str = None, database: str = None):
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Neo4j with cloud-optimized error handling."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            # Test connection
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1 as test")
            logger.info("Successfully connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    @error_boundary
    def _execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute Cypher query with cloud-optimized error handling."""
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, parameters or {})
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    @streamlit_cache_data(ttl=300)  # Cache for 5 minutes
    def search_equipment_maintenance_records(
        self, 
        equipment_type: Optional[str] = None,
        issue_type: Optional[str] = None,
        days_back: int = 365
    ) -> List[Dict[str, Any]]:
        """Search equipment maintenance records with cloud caching."""
        try:
            query = """
            MATCH (eq:Generator|Bus|Link)-[:HAS_MAINTENANCE_RECORD]->(mr:MaintenanceRecord)
            WHERE mr.date > date() - duration({days: $days_back})
            """
            
            params = {'days_back': days_back}
            
            if equipment_type:
                query += " AND labels(eq) CONTAINS $equipment_type"
                params['equipment_type'] = equipment_type
            
            if issue_type:
                query += " AND mr.Type = $issue_type"
                params['issue_type'] = issue_type
            
            query += """
            RETURN eq.id as equipment_id,
                   labels(eq)[0] as equipment_type,
                   eq.name_eng as equipment_name,
                   mr.date as maintenance_date,
                   mr.Type as maintenance_type,
                   mr.description as description,
                   mr.downTime as downtime
            ORDER BY mr.date DESC
            LIMIT 100
            """
            
            return self._execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Error searching maintenance records: {e}")
            return []
    
    @streamlit_cache_data(ttl=600)  # Cache for 10 minutes
    def get_risky_equipment(self, risk_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Get equipment with high risk scores with cloud caching."""
        try:
            query = """
            MATCH (eq:Generator|Bus|Link)-[:HAS_MAINTENANCE_RECORD]->(mr:MaintenanceRecord)
            WHERE mr.Type = "Corretivo" AND mr.date > date() - duration({days: 365})
            WITH eq, collect(mr) as maintenance_records
            WITH eq, maintenance_records, size(maintenance_records) as maintenance_count
            WITH eq, maintenance_records, maintenance_count,
                 maintenance_count * 1.0 / 365 as risk_score
            WHERE risk_score >= $risk_threshold
            RETURN eq.id as equipment_id,
                   labels(eq)[0] as equipment_type,
                   eq.name_eng as equipment_name,
                   risk_score,
                   maintenance_count,
                   CASE 
                       WHEN risk_score > 0.8 THEN 'Critical'
                       WHEN risk_score > 0.6 THEN 'High'
                       WHEN risk_score > 0.4 THEN 'Medium'
                       ELSE 'Low'
                   END as equipment_criticality
            ORDER BY risk_score DESC
            LIMIT 50
            """
            
            return self._execute_query(query, {'risk_threshold': risk_threshold})
            
        except Exception as e:
            logger.error(f"Error getting risky equipment: {e}")
            return []
    
    def close(self):
        """Close database connection."""
        if self.driver:
            self.driver.close()
            logger.info("Database connection closed")

def display_startup_health_check():
    """Display startup health check and initialization status."""
    st.markdown("""
    <div class="main-header">
        <h1>⚡ Energy Grid Management Agent</h1>
        <p>Cloud-Optimized Analytics Platform for Energy Service Providers</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize components
    with st.spinner("🔧 Initializing application..."):
        initialize_session_state()
        
        if not st.session_state.initialized:
            # Initialize cloud logging
            try:
                st.session_state.cloud_logger = initialize_cloud_logging()
                st.session_state.cloud_logger.log_structured_event("app_startup", {"status": "initializing"})
                st.success("✅ Cloud logging initialized")
            except Exception as e:
                st.error(f"❌ Failed to initialize logging: {e}")
            
            # Initialize secrets manager
            try:
                st.session_state.secrets_manager = initialize_secrets()
                st.session_state.cloud_logger.log_structured_event("secrets_loaded", {"status": "success"})
                st.success("✅ Secrets loaded successfully")
            except Exception as e:
                st.session_state.cloud_logger.log_error(e, {"context": "secrets_initialization"})
                st.error(f"❌ Failed to load secrets: {e}")
                st.stop()
            
            # Initialize health checker
            try:
                st.session_state.health_checker = initialize_health_checker(st.session_state.secrets_manager)
                st.session_state.cloud_logger.log_structured_event("health_checker_initialized", {"status": "success"})
                st.success("✅ Health checker initialized")
            except Exception as e:
                st.session_state.cloud_logger.log_error(e, {"context": "health_checker_initialization"})
                st.error(f"❌ Failed to initialize health checker: {e}")
            
            st.session_state.initialized = True
            st.session_state.cloud_logger.log_structured_event("app_startup", {"status": "completed"})
    
    # Display health status
    if st.session_state.health_checker:
        st.session_state.health_checker.display_health_status()

def main():
    """Main application function optimized for Streamlit Cloud."""
    try:
        # Display startup health check
        display_startup_health_check()
        
        # Sidebar configuration
        st.sidebar.title("⚙️ Configuration")
        
        # Display secrets status
        if st.session_state.secrets_manager:
            display_secrets_status(st.session_state.secrets_manager)
        
        # Display cache statistics
        display_cache_stats()
        
        # Display monitoring dashboard
        display_monitoring_dashboard()
        
        # Main content area
        st.markdown("## 📊 Energy Grid Analytics Dashboard")
        
        # Check if we have valid connections
        if not st.session_state.secrets_manager:
            st.error("❌ Application not properly initialized. Please check your configuration.")
            return
        
        secrets = st.session_state.secrets_manager.get_secrets()
        
        if not secrets.NEO4J_URI or not secrets.CLAUDE_API_KEY:
            st.warning("⚠️ Please configure your database and API credentials in the sidebar.")
            st.info("💡 For Streamlit Cloud deployment, configure secrets in the Streamlit Cloud dashboard.")
            return
        
        # Initialize energy tools
        if 'energy_tools' not in st.session_state or st.session_state.energy_tools is None:
            try:
                db_config = st.session_state.secrets_manager.get_database_config()
                st.session_state.energy_tools = CloudEnergyAgentTools(
                    uri=db_config['uri'],
                    username=db_config['username'],
                    password=db_config['password'],
                    database=db_config['database']
                )
                st.session_state.cloud_logger.log_structured_event("database_connected", {"status": "success"})
                st.success("✅ Database connection established")
            except Exception as e:
                st.session_state.cloud_logger.log_error(e, {"context": "database_connection"})
                st.error(f"❌ Failed to connect to database: {e}")
                return
        
        # Create tabs for different functionalities
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🔧 Equipment Analysis", 
            "⚠️ Risk Assessment", 
            "🔗 Dependencies", 
            "📅 Maintenance Scheduling",
            "📈 Vibration Analysis"
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
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.8em;">
            <p>Energy Grid Management Agent v1.0.0 | Cloud Optimized | Built with Streamlit</p>
            <p>⚡ Powered by Neo4j & Claude AI</p>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        if 'cloud_logger' in st.session_state and st.session_state.cloud_logger:
            st.session_state.cloud_logger.log_error(e, {"context": "main_application"})
        
        st.error(f"""
        🚨 Application Error
        
        An unexpected error occurred: {str(e)}
        
        Please try refreshing the page or contact support if the issue persists.
        """)
        logger.error(f"Application error: {e}")

@error_boundary
@performance_monitor
def show_equipment_analysis():
    """Display equipment analysis with cloud optimizations."""
    st.header("🔧 Equipment Analysis")
    
    # Log user action
    if 'cloud_logger' in st.session_state:
        st.session_state.cloud_logger.log_user_action("view_equipment_analysis", {})
    
    # Search filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        equipment_type = st.selectbox(
            "Equipment Type",
            ["All", "Generator", "Bus", "Link"],
            help="Filter by equipment type"
        )
    
    with col2:
        issue_type = st.selectbox(
            "Issue Type",
            ["All", "Corretivo", "Preventivo", "Preditivo"],
            help="Filter by maintenance type"
        )
    
    with col3:
        days_back = st.slider(
            "Days Back",
            min_value=30,
            max_value=365,
            value=90,
            help="Number of days to look back"
        )
    
    # Search button
    if st.button("🔍 Search Maintenance Records", type="primary"):
        with st.spinner("Searching maintenance records..."):
            try:
                # Log search action
                if 'cloud_logger' in st.session_state:
                    st.session_state.cloud_logger.log_user_action("search_maintenance_records", {
                        "equipment_type": equipment_type,
                        "issue_type": issue_type,
                        "days_back": days_back
                    })
                
                # Get equipment type filter
                eq_type_filter = None if equipment_type == "All" else equipment_type
                issue_filter = None if issue_type == "All" else issue_type
                
                # Search records
                records = st.session_state.energy_tools.search_equipment_maintenance_records(
                    equipment_type=eq_type_filter,
                    issue_type=issue_filter,
                    days_back=days_back
                )
                
                if records:
                    st.success(f"✅ Found {len(records)} maintenance records")
                    
                    # Log successful search
                    if 'cloud_logger' in st.session_state:
                        st.session_state.cloud_logger.log_structured_event("search_completed", {
                            "record_count": len(records),
                            "filters": {"equipment_type": equipment_type, "issue_type": issue_type, "days_back": days_back}
                        })
                    
                    # Create chart
                    chart = create_maintenance_chart(records)
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                    
                    # Display data table
                    df = pd.DataFrame(records)
                    st.dataframe(df, use_container_width=True)
                    
                    # Export options
                    col1, col2 = st.columns(2)
                    with col1:
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "📥 Download CSV",
                            csv,
                            "maintenance_records.csv",
                            "text/csv",
                            key="download_csv"
                        )
                    
                    with col2:
                        json_str = df.to_json(orient="records", indent=2)
                        st.download_button(
                            "📥 Download JSON",
                            json_str,
                            "maintenance_records.json",
                            "application/json",
                            key="download_json"
                        )
                else:
                    st.info("ℹ️ No maintenance records found for the selected criteria.")
                    
            except Exception as e:
                if 'cloud_logger' in st.session_state:
                    st.session_state.cloud_logger.log_error(e, {"context": "equipment_analysis_search"})
                st.error(f"❌ Error searching records: {e}")

@error_boundary
@performance_monitor
def show_risk_assessment():
    """Display risk assessment with cloud optimizations."""
    st.header("⚠️ Risk Assessment")
    
    # Log user action
    if 'cloud_logger' in st.session_state:
        st.session_state.cloud_logger.log_user_action("view_risk_assessment", {})
    
    # Risk threshold slider
    risk_threshold = st.slider(
        "Risk Threshold",
        min_value=0.1,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Minimum risk score to include equipment"
    )
    
    if st.button("🔍 Analyze Risk", type="primary"):
        with st.spinner("Analyzing equipment risk..."):
            try:
                # Log risk analysis action
                if 'cloud_logger' in st.session_state:
                    st.session_state.cloud_logger.log_user_action("analyze_risk", {
                        "risk_threshold": risk_threshold
                    })
                
                risky_equipment = st.session_state.energy_tools.get_risky_equipment(risk_threshold)
                
                if risky_equipment:
                    st.success(f"✅ Found {len(risky_equipment)} high-risk equipment items")
                    
                    # Log successful analysis
                    if 'cloud_logger' in st.session_state:
                        st.session_state.cloud_logger.log_structured_event("risk_analysis_completed", {
                            "equipment_count": len(risky_equipment),
                            "risk_threshold": risk_threshold
                        })
                    
                    # Create risk chart
                    chart = create_risk_chart(risky_equipment)
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                    
                    # Display risk table
                    df = pd.DataFrame(risky_equipment)
                    
                    # Color code risk scores
                    def color_risk_score(val):
                        if val >= 0.8:
                            return 'background-color: #ffcccc'
                        elif val >= 0.6:
                            return 'background-color: #ffebcc'
                        elif val >= 0.4:
                            return 'background-color: #ffffcc'
                        else:
                            return 'background-color: #ccffcc'
                    
                    styled_df = df.style.applymap(color_risk_score, subset=['risk_score'])
                    st.dataframe(styled_df, use_container_width=True)
                    
                else:
                    st.info("ℹ️ No high-risk equipment found for the selected threshold.")
                    
            except Exception as e:
                if 'cloud_logger' in st.session_state:
                    st.session_state.cloud_logger.log_error(e, {"context": "risk_assessment"})
                st.error(f"❌ Error analyzing risk: {e}")

@error_boundary
def show_dependencies():
    """Display equipment dependencies."""
    st.header("🔗 Equipment Dependencies")
    st.info("💡 This feature shows how equipment is interconnected and dependencies between installations.")
    
    # Placeholder for dependencies analysis
    st.markdown("""
    ### 🔗 Dependency Analysis
    
    This section will show:
    - Equipment interconnection maps
    - Installation dependencies
    - Impact analysis for maintenance scheduling
    - Network topology visualization
    
    *Feature coming soon...*
    """)

@error_boundary
def show_maintenance_scheduling():
    """Display maintenance scheduling."""
    st.header("📅 Maintenance Scheduling")
    st.info("💡 This feature helps optimize maintenance schedules based on equipment health and dependencies.")
    
    # Placeholder for maintenance scheduling
    st.markdown("""
    ### 📅 Smart Maintenance Scheduling
    
    This section will provide:
    - Automated maintenance recommendations
    - Schedule optimization based on risk scores
    - Dependency-aware scheduling
    - Resource allocation planning
    
    *Feature coming soon...*
    """)

@error_boundary
def show_vibration_analysis():
    """Display vibration analysis."""
    st.header("📈 Vibration Analysis")
    st.info("💡 This feature analyzes vibration data to predict equipment failures.")
    
    # Placeholder for vibration analysis
    st.markdown("""
    ### 📈 Vibration Monitoring & Analysis
    
    This section will show:
    - Real-time vibration monitoring
    - Trend analysis and predictions
    - Failure prediction models
    - Alert thresholds and notifications
    
    *Feature coming soon...*
    """)

if __name__ == "__main__":
    main() 
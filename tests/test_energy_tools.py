"""
Unit tests for EnergyAgentTools - Neo4j database operations
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import EnergyAgentTools
from neo4j.exceptions import ServiceUnavailable, AuthError, ClientError


class TestEnergyAgentTools(unittest.TestCase):
    """Test cases for EnergyAgentTools class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_uri = "neo4j+s://test-instance.databases.neo4j.io"
        self.mock_username = "neo4j"
        self.mock_password = "test_password"
        self.mock_database = "neo4j"
        
        # Sample test data
        self.sample_maintenance_data = [
            {
                "equipment_id": "EQ-001",
                "equipment_type": "Generator",
                "equipment_name": "Generator Alpha",
                "equipment_location": "Plant A",
                "equipment_criticality": "Critical",
                "maintenance_date": "2024-01-15",
                "maintenance_description": "Vibration analysis and bearing replacement",
                "maintenance_type": "Preventive",
                "maintenance_cost": 15000.0
            },
            {
                "equipment_id": "EQ-002",
                "equipment_type": "Transformer",
                "equipment_name": "Transformer Beta",
                "equipment_location": "Plant B",
                "equipment_criticality": "High",
                "maintenance_date": "2024-01-20",
                "maintenance_description": "Oil analysis and filter replacement",
                "maintenance_type": "Corrective",
                "maintenance_cost": 8000.0
            }
        ]
        
        self.sample_risk_data = [
            {
                "equipment_id": "EQ-001",
                "equipment_type": "Generator",
                "equipment_name": "Generator Alpha",
                "equipment_location": "Plant A",
                "equipment_criticality": "Critical",
                "risk_score": 0.85,
                "risk_factors": "High vibration, bearing wear",
                "assessment_date": "2024-01-15"
            },
            {
                "equipment_id": "EQ-002",
                "equipment_type": "Transformer",
                "equipment_name": "Transformer Beta",
                "equipment_location": "Plant B",
                "equipment_criticality": "High",
                "risk_score": 0.65,
                "risk_factors": "Oil degradation",
                "assessment_date": "2024-01-20"
            }
        ]
        
        self.sample_dependency_data = [
            {
                "installation_id": "INST-001",
                "installation_name": "Installation Alpha",
                "installation_type": "Power Plant",
                "equipment_id": "EQ-001",
                "equipment_type": "Generator",
                "equipment_name": "Generator Alpha",
                "equipment_criticality": "Critical",
                "dependent_equipment": ["EQ-003", "EQ-004"],
                "maintenance_history": [
                    {"date": "2024-01-15", "type": "Preventive", "description": "Routine maintenance"}
                ],
                "current_risk_score": 0.85
            }
        ]
    
    @patch('app.GraphDatabase')
    def test_init_success(self, mock_graph_database):
        """Test successful initialization of EnergyAgentTools."""
        # Mock the driver and session
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_graph_database.driver.return_value = mock_driver
        
        # Test initialization
        tools = EnergyAgentTools(
            uri=self.mock_uri,
            username=self.mock_username,
            password=self.mock_password,
            database=self.mock_database
        )
        
        # Verify driver was created with correct parameters
        mock_graph_database.driver.assert_called_once_with(
            self.mock_uri,
            auth=(self.mock_username, self.mock_password),
            max_connection_pool_size=50,
            connection_timeout=30
        )
        
        # Verify connection test was performed
        mock_session.run.assert_called_once_with("RETURN 1")
    
    @patch('app.GraphDatabase')
    def test_init_connection_failure(self, mock_graph_database):
        """Test initialization with connection failure."""
        # Mock connection failure
        mock_graph_database.driver.side_effect = ServiceUnavailable("Connection failed")
        
        # Test that exception is raised
        with self.assertRaises(ConnectionError):
            EnergyAgentTools(
                uri=self.mock_uri,
                username=self.mock_username,
                password=self.mock_password,
                database=self.mock_database
            )
    
    @patch('app.GraphDatabase')
    def test_init_auth_failure(self, mock_graph_database):
        """Test initialization with authentication failure."""
        # Mock authentication failure
        mock_graph_database.driver.side_effect = AuthError("Invalid credentials")
        
        # Test that exception is raised
        with self.assertRaises(ConnectionError):
            EnergyAgentTools(
                uri=self.mock_uri,
                username=self.mock_username,
                password=self.mock_password,
                database=self.mock_database
            )
    
    @patch('app.GraphDatabase')
    def test_search_equipment_maintenance_records_success(self, mock_graph_database):
        """Test successful search_equipment_maintenance_records."""
        # Mock the driver and session
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock query result
        mock_result = Mock()
        mock_result.__iter__ = lambda x: iter(self.sample_maintenance_data)
        mock_session.run.return_value = mock_result
        
        mock_graph_database.driver.return_value = mock_driver
        
        # Create tools instance
        tools = EnergyAgentTools(
            uri=self.mock_uri,
            username=self.mock_username,
            password=self.mock_password,
            database=self.mock_database
        )
        
        # Test search with filters
        result = tools.search_equipment_maintenance_records(
            equipment_type="Generator",
            issue_type="vibration",
            days_back=365
        )
        
        # Verify result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["equipment_type"], "Generator")
        self.assertEqual(result[1]["equipment_type"], "Transformer")
        
        # Verify query was executed
        mock_session.run.assert_called()
    
    @patch('app.GraphDatabase')
    def test_search_equipment_maintenance_records_no_filters(self, mock_graph_database):
        """Test search_equipment_maintenance_records without filters."""
        # Mock the driver and session
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock query result
        mock_result = Mock()
        mock_result.__iter__ = lambda x: iter(self.sample_maintenance_data)
        mock_session.run.return_value = mock_result
        
        mock_graph_database.driver.return_value = mock_driver
        
        # Create tools instance
        tools = EnergyAgentTools(
            uri=self.mock_uri,
            username=self.mock_username,
            password=self.mock_password,
            database=self.mock_database
        )
        
        # Test search without filters
        result = tools.search_equipment_maintenance_records()
        
        # Verify result
        self.assertEqual(len(result), 2)
        
        # Verify query was executed
        mock_session.run.assert_called()
    
    @patch('app.GraphDatabase')
    def test_search_equipment_maintenance_records_exception(self, mock_graph_database):
        """Test search_equipment_maintenance_records with database exception."""
        # Mock the driver and session
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock database exception
        mock_session.run.side_effect = ClientError("Query failed")
        
        mock_graph_database.driver.return_value = mock_driver
        
        # Create tools instance
        tools = EnergyAgentTools(
            uri=self.mock_uri,
            username=self.mock_username,
            password=self.mock_password,
            database=self.mock_database
        )
        
        # Test that exception is handled and empty list is returned
        result = tools.search_equipment_maintenance_records()
        self.assertEqual(result, [])
    
    @patch('app.GraphDatabase')
    def test_get_risky_equipment_success(self, mock_graph_database):
        """Test successful get_risky_equipment."""
        # Mock the driver and session
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock query result
        mock_result = Mock()
        mock_result.__iter__ = lambda x: iter(self.sample_risk_data)
        mock_session.run.return_value = mock_result
        
        mock_graph_database.driver.return_value = mock_driver
        
        # Create tools instance
        tools = EnergyAgentTools(
            uri=self.mock_uri,
            username=self.mock_username,
            password=self.mock_password,
            database=self.mock_database
        )
        
        # Test get risky equipment
        result = tools.get_risky_equipment(risk_threshold=0.6)
        
        # Verify result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["risk_score"], 0.85)
        self.assertEqual(result[1]["risk_score"], 0.65)
        
        # Verify query was executed
        mock_session.run.assert_called()
    
    @patch('app.GraphDatabase')
    def test_get_risky_equipment_exception(self, mock_graph_database):
        """Test get_risky_equipment with database exception."""
        # Mock the driver and session
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock database exception
        mock_session.run.side_effect = ClientError("Query failed")
        
        mock_graph_database.driver.return_value = mock_driver
        
        # Create tools instance
        tools = EnergyAgentTools(
            uri=self.mock_uri,
            username=self.mock_username,
            password=self.mock_password,
            database=self.mock_database
        )
        
        # Test that exception is handled and empty list is returned
        result = tools.get_risky_equipment()
        self.assertEqual(result, [])
    
    @patch('app.GraphDatabase')
    def test_get_installation_equipments_dependency_success(self, mock_graph_database):
        """Test successful get_installation_equipments_dependency."""
        # Mock the driver and session
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock query result
        mock_result = Mock()
        mock_result.__iter__ = lambda x: iter(self.sample_dependency_data)
        mock_session.run.return_value = mock_result
        
        mock_graph_database.driver.return_value = mock_driver
        
        # Create tools instance
        tools = EnergyAgentTools(
            uri=self.mock_uri,
            username=self.mock_username,
            password=self.mock_password,
            database=self.mock_database
        )
        
        # Test get dependencies with specific installation
        result = tools.get_installation_equipments_dependency(installation_id="INST-001")
        
        # Verify result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["installation_id"], "INST-001")
        self.assertEqual(result[0]["equipment_id"], "EQ-001")
        
        # Verify query was executed
        mock_session.run.assert_called()
    
    @patch('app.GraphDatabase')
    def test_get_installation_equipments_dependency_all_installations(self, mock_graph_database):
        """Test get_installation_equipments_dependency for all installations."""
        # Mock the driver and session
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock query result
        mock_result = Mock()
        mock_result.__iter__ = lambda x: iter(self.sample_dependency_data)
        mock_session.run.return_value = mock_result
        
        mock_graph_database.driver.return_value = mock_driver
        
        # Create tools instance
        tools = EnergyAgentTools(
            uri=self.mock_uri,
            username=self.mock_username,
            password=self.mock_password,
            database=self.mock_database
        )
        
        # Test get dependencies for all installations
        result = tools.get_installation_equipments_dependency()
        
        # Verify result
        self.assertEqual(len(result), 1)
        
        # Verify query was executed
        mock_session.run.assert_called()
    
    @patch('app.GraphDatabase')
    def test_get_installation_equipments_dependency_exception(self, mock_graph_database):
        """Test get_installation_equipments_dependency with database exception."""
        # Mock the driver and session
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock database exception
        mock_session.run.side_effect = ClientError("Query failed")
        
        mock_graph_database.driver.return_value = mock_driver
        
        # Create tools instance
        tools = EnergyAgentTools(
            uri=self.mock_uri,
            username=self.mock_username,
            password=self.mock_password,
            database=self.mock_database
        )
        
        # Test that exception is handled and empty list is returned
        result = tools.get_installation_equipments_dependency()
        self.assertEqual(result, [])
    
    @patch('app.GraphDatabase')
    def test_get_vibration_analysis_success(self, mock_graph_database):
        """Test successful get_vibration_analysis."""
        # Mock the driver and session
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock query result with vibration data
        vibration_data = [
            {
                "equipment_id": "EQ-001",
                "equipment_type": "Generator",
                "equipment_name": "Generator Alpha",
                "equipment_location": "Plant A",
                "equipment_criticality": "Critical",
                "maintenance_date": "2024-01-15",
                "maintenance_description": "Vibration analysis and bearing replacement",
                "maintenance_type": "Corrective",
                "maintenance_cost": 15000.0
            }
        ]
        
        mock_result = Mock()
        mock_result.__iter__ = lambda x: iter(vibration_data)
        mock_session.run.return_value = mock_result
        
        mock_graph_database.driver.return_value = mock_driver
        
        # Create tools instance
        tools = EnergyAgentTools(
            uri=self.mock_uri,
            username=self.mock_username,
            password=self.mock_password,
            database=self.mock_database
        )
        
        # Test vibration analysis
        result = tools.get_vibration_analysis(equipment_type="Generator", days_back=90)
        
        # Verify result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["equipment_type"], "Generator")
        self.assertIn("vibration", result[0]["maintenance_description"].lower())
        
        # Verify query was executed
        mock_session.run.assert_called()
    
    @patch('app.GraphDatabase')
    def test_generate_maintenance_schedule_success(self, mock_graph_database):
        """Test successful generate_maintenance_schedule."""
        # Mock the driver and session
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock query result
        schedule_data = [
            {
                "equipment_id": "EQ-001",
                "equipment_type": "Generator",
                "equipment_name": "Generator Alpha",
                "equipment_location": "Plant A",
                "equipment_criticality": "Critical",
                "risk_score": 0.85,
                "risk_factors": "High vibration",
                "recent_maintenance_count": 3,
                "recommended_date": "2024-02-15",
                "priority": "High Priority"
            }
        ]
        
        mock_result = Mock()
        mock_result.__iter__ = lambda x: iter(schedule_data)
        mock_session.run.return_value = mock_result
        
        mock_graph_database.driver.return_value = mock_driver
        
        # Create tools instance
        tools = EnergyAgentTools(
            uri=self.mock_uri,
            username=self.mock_username,
            password=self.mock_password,
            database=self.mock_database
        )
        
        # Test maintenance schedule generation
        result = tools.generate_maintenance_schedule(
            equipment_ids=["EQ-001"],
            days_ahead=30
        )
        
        # Verify result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["equipment_id"], "EQ-001")
        self.assertEqual(result[0]["priority"], "High Priority")
        
        # Verify query was executed
        mock_session.run.assert_called()
    
    @patch('app.GraphDatabase')
    def test_close_connection(self, mock_graph_database):
        """Test closing database connection."""
        # Mock the driver
        mock_driver = Mock()
        mock_graph_database.driver.return_value = mock_driver
        
        # Create tools instance
        tools = EnergyAgentTools(
            uri=self.mock_uri,
            username=self.mock_username,
            password=self.mock_password,
            database=self.mock_database
        )
        
        # Test close method
        tools.close()
        
        # Verify driver close was called
        mock_driver.close.assert_called_once()
    
    @patch('app.GraphDatabase')
    def test_analyze_maintenance_patterns_success(self, mock_graph_database):
        """Test successful analyze_maintenance_patterns."""
        # Mock the driver and session
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock query result
        mock_result = Mock()
        mock_result.__iter__ = lambda x: iter(self.sample_maintenance_data)
        mock_session.run.return_value = mock_result
        
        mock_graph_database.driver.return_value = mock_driver
        
        # Create tools instance
        tools = EnergyAgentTools(
            uri=self.mock_uri,
            username=self.mock_username,
            password=self.mock_password,
            database=self.mock_database
        )
        
        # Test maintenance pattern analysis
        result = tools.analyze_maintenance_patterns(self.sample_maintenance_data)
        
        # Verify result is a string (AI analysis)
        self.assertIsInstance(result, str)
        self.assertIn("maintenance", result.lower())
    
    @patch('app.GraphDatabase')
    def test_analyze_maintenance_patterns_empty_data(self, mock_graph_database):
        """Test analyze_maintenance_patterns with empty data."""
        # Mock the driver and session
        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock query result
        mock_result = Mock()
        mock_result.__iter__ = lambda x: iter(self.sample_maintenance_data)
        mock_session.run.return_value = mock_result
        
        mock_graph_database.driver.return_value = mock_driver
        
        # Create tools instance
        tools = EnergyAgentTools(
            uri=self.mock_uri,
            username=self.mock_username,
            password=self.mock_password,
            database=self.mock_database
        )
        
        # Test with empty data
        result = tools.analyze_maintenance_patterns([])
        
        # Verify result
        self.assertIn("No maintenance records available", result)


if __name__ == '__main__':
    unittest.main() 
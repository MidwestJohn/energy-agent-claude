"""
Unit tests for Claude API integration
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude_utils import (
    ClaudeClient, 
    AdvancedClaudeAnalyzer, 
    AnalysisResult, 
    ClaudeAnalysisError,
    validate_claude_api_key
)
from anthropic import APIError, RateLimitError, AuthenticationError


class TestClaudeIntegration(unittest.TestCase):
    """Test cases for Claude API integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_api_key = "sk-ant-api03-test123456789012345678901234567890123456789012345678901234567890"
        self.invalid_api_key = "invalid-key"
        
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
        
        # Sample Claude API responses
        self.sample_analysis_response = """
        # Equipment Maintenance Analysis
        
        ## Key Insights
        - Generator equipment shows higher maintenance frequency
        - Vibration-related issues are common in critical equipment
        - Average maintenance cost is $11,500 per incident
        
        ## Recommendations
        1. Implement predictive maintenance for generators
        2. Increase vibration monitoring frequency
        3. Consider equipment replacement for high-cost items
        """
        
        self.sample_risk_report = """
        # Risk Assessment Report
        
        ## High-Risk Equipment
        - Generator Alpha (Risk Score: 0.85)
        - Transformer Beta (Risk Score: 0.65)
        
        ## Risk Factors
        - Vibration issues in rotating equipment
        - Oil degradation in transformers
        - Bearing wear in generators
        
        ## Recommendations
        1. Immediate inspection of Generator Alpha
        2. Oil analysis for Transformer Beta
        3. Schedule preventive maintenance
        """
    
    def test_validate_claude_api_key_valid(self):
        """Test validation of valid Claude API key."""
        result = validate_claude_api_key(self.valid_api_key)
        self.assertTrue(result)
    
    def test_validate_claude_api_key_invalid_format(self):
        """Test validation of invalid API key format."""
        result = validate_claude_api_key(self.invalid_api_key)
        self.assertFalse(result)
    
    def test_validate_claude_api_key_empty(self):
        """Test validation of empty API key."""
        result = validate_claude_api_key("")
        self.assertFalse(result)
    
    def test_validate_claude_api_key_none(self):
        """Test validation of None API key."""
        result = validate_claude_api_key(None)
        self.assertFalse(result)
    
    def test_validate_claude_api_key_too_short(self):
        """Test validation of API key that's too short."""
        short_key = "sk-ant-api03-short"
        result = validate_claude_api_key(short_key)
        self.assertFalse(result)
    
    def test_validate_claude_api_key_invalid_characters(self):
        """Test validation of API key with invalid characters."""
        invalid_key = "sk-ant-api03-test@#$%^&*()"
        result = validate_claude_api_key(invalid_key)
        self.assertFalse(result)
    
    @patch('claude_utils.anthropic.Anthropic')
    def test_claude_client_init_success(self, mock_anthropic):
        """Test successful initialization of ClaudeClient."""
        # Mock the Anthropic client
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        # Test initialization
        client = ClaudeClient(api_key=self.valid_api_key)
        
        # Verify Anthropic client was created
        mock_anthropic.assert_called_once_with(api_key=self.valid_api_key)
        self.assertEqual(client.api_key, self.valid_api_key)
    
    @patch('claude_utils.anthropic.Anthropic')
    def test_claude_client_init_invalid_key(self, mock_anthropic):
        """Test initialization with invalid API key."""
        # Test that exception is raised
        with self.assertRaises(ClaudeAnalysisError):
            ClaudeClient(api_key=self.invalid_api_key)
    
    @patch('claude_utils.anthropic.Anthropic')
    def test_analyze_grid_data_success(self, mock_anthropic):
        """Test successful analyze_grid_data."""
        # Mock the Anthropic client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = self.sample_analysis_response
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        # Create client and test analysis
        client = ClaudeClient(api_key=self.valid_api_key)
        result = client.analyze_grid_data("Analyze this maintenance data")
        
        # Verify result
        self.assertEqual(result, self.sample_analysis_response)
        
        # Verify API call was made
        mock_client.messages.create.assert_called_once()
    
    @patch('claude_utils.anthropic.Anthropic')
    def test_analyze_grid_data_api_error(self, mock_anthropic):
        """Test analyze_grid_data with API error."""
        # Mock the Anthropic client with API error
        mock_client = Mock()
        mock_client.messages.create.side_effect = APIError("API Error", response=Mock())
        mock_anthropic.return_value = mock_client
        
        # Create client and test analysis
        client = ClaudeClient(api_key=self.valid_api_key)
        result = client.analyze_grid_data("Analyze this data")
        
        # Verify error handling
        self.assertIn("Analysis failed", result)
    
    @patch('claude_utils.anthropic.Anthropic')
    def test_analyze_grid_data_rate_limit_error(self, mock_anthropic):
        """Test analyze_grid_data with rate limit error."""
        # Mock the Anthropic client with rate limit error
        mock_client = Mock()
        mock_client.messages.create.side_effect = RateLimitError("Rate limit exceeded", response=Mock())
        mock_anthropic.return_value = mock_client
        
        # Create client and test analysis
        client = ClaudeClient(api_key=self.valid_api_key)
        result = client.analyze_grid_data("Analyze this data")
        
        # Verify error handling
        self.assertIn("Analysis failed", result)
    
    @patch('claude_utils.anthropic.Anthropic')
    def test_advanced_claude_analyzer_init_success(self, mock_anthropic):
        """Test successful initialization of AdvancedClaudeAnalyzer."""
        # Mock the Anthropic client
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        # Test initialization
        analyzer = AdvancedClaudeAnalyzer(api_key=self.valid_api_key)
        
        # Verify initialization
        self.assertEqual(analyzer.api_key, self.valid_api_key)
        self.assertEqual(analyzer.model, "claude-3-5-sonnet-20241022")
    
    @patch('claude_utils.anthropic.Anthropic')
    def test_advanced_claude_analyzer_init_invalid_key(self, mock_anthropic):
        """Test initialization with invalid API key."""
        # Test that exception is raised
        with self.assertRaises(ClaudeAnalysisError):
            AdvancedClaudeAnalyzer(api_key=self.invalid_api_key)
    
    @patch('claude_utils.anthropic.Anthropic')
    def test_analyze_equipment_trends_success(self, mock_anthropic):
        """Test successful analyze_equipment_trends."""
        # Mock the Anthropic client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = self.sample_analysis_response
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        # Create analyzer and test analysis
        analyzer = AdvancedClaudeAnalyzer(api_key=self.valid_api_key)
        result = analyzer.analyze_equipment_trends(
            maintenance_data=self.sample_maintenance_data,
            analysis_period="12 months"
        )
        
        # Verify result
        self.assertIsInstance(result, AnalysisResult)
        self.assertTrue(result.success)
        self.assertIn("analysis", result.data)
        self.assertEqual(result.data["analysis"], self.sample_analysis_response)
        self.assertEqual(result.data["analysis_period"], "12 months")
        
        # Verify API call was made
        mock_client.messages.create.assert_called_once()
    
    @patch('claude_utils.anthropic.Anthropic')
    def test_analyze_equipment_trends_api_error(self, mock_anthropic):
        """Test analyze_equipment_trends with API error."""
        # Mock the Anthropic client with API error
        mock_client = Mock()
        mock_client.messages.create.side_effect = APIError("API Error", response=Mock())
        mock_anthropic.return_value = mock_client
        
        # Create analyzer and test analysis
        analyzer = AdvancedClaudeAnalyzer(api_key=self.valid_api_key)
        result = analyzer.analyze_equipment_trends(
            maintenance_data=self.sample_maintenance_data
        )
        
        # Verify error handling
        self.assertIsInstance(result, AnalysisResult)
        self.assertFalse(result.success)
        self.assertIn("Equipment trends analysis failed", result.error_message)
    
    @patch('claude_utils.anthropic.Anthropic')
    def test_generate_risk_report_success(self, mock_anthropic):
        """Test successful generate_risk_report."""
        # Mock the Anthropic client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = self.sample_risk_report
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        # Create analyzer and test risk report generation
        analyzer = AdvancedClaudeAnalyzer(api_key=self.valid_api_key)
        result = analyzer.generate_risk_report(
            risk_data=self.sample_risk_data,
            risk_threshold=0.6
        )
        
        # Verify result
        self.assertIsInstance(result, AnalysisResult)
        self.assertTrue(result.success)
        self.assertIn("risk_report", result.data)
        self.assertEqual(result.data["risk_report"], self.sample_risk_report)
        self.assertEqual(result.data["risk_threshold"], 0.6)
        
        # Verify API call was made
        mock_client.messages.create.assert_called_once()
    
    @patch('claude_utils.anthropic.Anthropic')
    def test_generate_risk_report_api_error(self, mock_anthropic):
        """Test generate_risk_report with API error."""
        # Mock the Anthropic client with API error
        mock_client = Mock()
        mock_client.messages.create.side_effect = APIError("API Error", response=Mock())
        mock_anthropic.return_value = mock_client
        
        # Create analyzer and test risk report generation
        analyzer = AdvancedClaudeAnalyzer(api_key=self.valid_api_key)
        result = analyzer.generate_risk_report(
            risk_data=self.sample_risk_data
        )
        
        # Verify error handling
        self.assertIsInstance(result, AnalysisResult)
        self.assertFalse(result.success)
        self.assertIn("Risk report generation failed", result.error_message)
    
    @patch('claude_utils.anthropic.Anthropic')
    def test_optimize_maintenance_workflow_success(self, mock_anthropic):
        """Test successful optimize_maintenance_workflow."""
        # Mock the Anthropic client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Optimization plan: Schedule maintenance based on risk scores"
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        # Create analyzer and test workflow optimization
        analyzer = AdvancedClaudeAnalyzer(api_key=self.valid_api_key)
        constraints = {"budget": 100000, "manpower": 10}
        result = analyzer.optimize_maintenance_workflow(
            maintenance_data=self.sample_maintenance_data,
            risk_data=self.sample_risk_data,
            constraints=constraints
        )
        
        # Verify result
        self.assertIsInstance(result, AnalysisResult)
        self.assertTrue(result.success)
        self.assertIn("optimization_plan", result.data)
        self.assertEqual(result.data["constraints"], constraints)
        
        # Verify API call was made
        mock_client.messages.create.assert_called_once()
    
    @patch('claude_utils.anthropic.Anthropic')
    def test_optimize_maintenance_workflow_no_risk_data(self, mock_anthropic):
        """Test optimize_maintenance_workflow without risk data."""
        # Mock the Anthropic client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Optimization plan without risk data"
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        # Create analyzer and test workflow optimization
        analyzer = AdvancedClaudeAnalyzer(api_key=self.valid_api_key)
        result = analyzer.optimize_maintenance_workflow(
            maintenance_data=self.sample_maintenance_data
        )
        
        # Verify result
        self.assertIsInstance(result, AnalysisResult)
        self.assertTrue(result.success)
        self.assertIn("optimization_plan", result.data)
        
        # Verify API call was made
        mock_client.messages.create.assert_called_once()
    
    @patch('claude_utils.anthropic.Anthropic')
    def test_predict_failure_scenarios_success(self, mock_anthropic):
        """Test successful predict_failure_scenarios."""
        # Mock the Anthropic client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Failure prediction: Generator Alpha at high risk"
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        # Create analyzer and test failure prediction
        analyzer = AdvancedClaudeAnalyzer(api_key=self.valid_api_key)
        result = analyzer.predict_failure_scenarios(
            maintenance_data=self.sample_maintenance_data,
            risk_data=self.sample_risk_data,
            prediction_horizon="6 months"
        )
        
        # Verify result
        self.assertIsInstance(result, AnalysisResult)
        self.assertTrue(result.success)
        self.assertIn("failure_predictions", result.data)
        self.assertEqual(result.data["prediction_horizon"], "6 months")
        
        # Verify API call was made
        mock_client.messages.create.assert_called_once()
    
    @patch('claude_utils.anthropic.Anthropic')
    def test_predict_failure_scenarios_api_error(self, mock_anthropic):
        """Test predict_failure_scenarios with API error."""
        # Mock the Anthropic client with API error
        mock_client = Mock()
        mock_client.messages.create.side_effect = APIError("API Error", response=Mock())
        mock_anthropic.return_value = mock_client
        
        # Create analyzer and test failure prediction
        analyzer = AdvancedClaudeAnalyzer(api_key=self.valid_api_key)
        result = analyzer.predict_failure_scenarios(
            maintenance_data=self.sample_maintenance_data,
            risk_data=self.sample_risk_data
        )
        
        # Verify error handling
        self.assertIsInstance(result, AnalysisResult)
        self.assertFalse(result.success)
        self.assertIn("Failure scenario prediction failed", result.error_message)
    
    def test_analysis_result_dataclass(self):
        """Test AnalysisResult dataclass functionality."""
        # Test successful result
        success_result = AnalysisResult(
            success=True,
            data={"test": "data"},
            error_message=None
        )
        
        self.assertTrue(success_result.success)
        self.assertEqual(success_result.data, {"test": "data"})
        self.assertIsNone(success_result.error_message)
        self.assertIsInstance(success_result.timestamp, datetime)
        
        # Test failed result
        failed_result = AnalysisResult(
            success=False,
            data=None,
            error_message="Test error"
        )
        
        self.assertFalse(failed_result.success)
        self.assertIsNone(failed_result.data)
        self.assertEqual(failed_result.error_message, "Test error")
        self.assertIsInstance(failed_result.timestamp, datetime)
    
    @patch('claude_utils.anthropic.Anthropic')
    def test_claude_client_get_advanced_analyzer(self, mock_anthropic):
        """Test getting advanced analyzer from ClaudeClient."""
        # Mock the Anthropic client
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        # Create client and get advanced analyzer
        client = ClaudeClient(api_key=self.valid_api_key)
        advanced_analyzer = client.get_advanced_analyzer()
        
        # Verify advanced analyzer
        self.assertIsInstance(advanced_analyzer, AdvancedClaudeAnalyzer)
        self.assertEqual(advanced_analyzer.api_key, self.valid_api_key)
    
    @patch('claude_utils.anthropic.Anthropic')
    def test_create_analysis_prompt(self, mock_anthropic):
        """Test _create_analysis_prompt method."""
        # Mock the Anthropic client
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        # Create analyzer
        analyzer = AdvancedClaudeAnalyzer(api_key=self.valid_api_key)
        
        # Test prompt creation
        data_summary = {"test": "data"}
        prompt = analyzer._create_analysis_prompt(
            analysis_type="Test Analysis",
            data_summary=data_summary,
            additional_context="Test context"
        )
        
        # Verify prompt structure
        self.assertIn("Test Analysis", prompt)
        self.assertIn("Test context", prompt)
        self.assertIn("energy grid management analyst", prompt)
        self.assertIn("professional analysis", prompt)


if __name__ == '__main__':
    unittest.main() 
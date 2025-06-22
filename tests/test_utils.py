"""
Unit tests for utility functions
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude_utils import (
    format_currency,
    format_risk_score,
    validate_claude_api_key,
    _summarize_dataframe,
    _summarize_risk_data,
    _create_detailed_vibration_summary,
    DataFormattingError
)


class TestUtilityFunctions(unittest.TestCase):
    """Test cases for utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample test data
        self.sample_dataframe = pd.DataFrame({
            'equipment_id': ['EQ-001', 'EQ-002', 'EQ-003'],
            'equipment_type': ['Generator', 'Transformer', 'Generator'],
            'equipment_name': ['Gen Alpha', 'Trans Beta', 'Gen Gamma'],
            'equipment_location': ['Plant A', 'Plant B', 'Plant A'],
            'equipment_criticality': ['Critical', 'High', 'Medium'],
            'maintenance_date': ['2024-01-15', '2024-01-20', '2024-01-25'],
            'maintenance_cost': [15000.0, 8000.0, 12000.0],
            'risk_score': [0.85, 0.65, 0.45]
        })
        
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
            },
            {
                "equipment_id": "EQ-003",
                "equipment_type": "Generator",
                "equipment_name": "Generator Gamma",
                "equipment_location": "Plant A",
                "equipment_criticality": "Medium",
                "risk_score": 0.45,
                "risk_factors": "Minor wear",
                "assessment_date": "2024-01-25"
            }
        ]
        
        self.sample_vibration_data = [
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
            },
            {
                "equipment_id": "EQ-002",
                "equipment_type": "Motor",
                "equipment_name": "Motor Beta",
                "equipment_location": "Plant B",
                "equipment_criticality": "High",
                "maintenance_date": "2024-01-20",
                "maintenance_description": "Vibration monitoring and alignment",
                "maintenance_type": "Preventive",
                "maintenance_cost": 8000.0
            },
            {
                "equipment_id": "EQ-003",
                "equipment_type": "Pump",
                "equipment_name": "Pump Gamma",
                "equipment_location": "Plant A",
                "equipment_criticality": "Medium",
                "maintenance_date": "2024-01-25",
                "maintenance_description": "Vibration testing and balancing",
                "maintenance_type": "Corrective",
                "maintenance_cost": 12000.0
            }
        ]

    # ============================================================================
    # FORMAT_CURRENCY TESTS
    # ============================================================================
    
    def test_format_currency_usd_small_value(self):
        """Test format_currency with small USD value."""
        result = format_currency(1234.56, "USD")
        self.assertEqual(result, "$1,234.56")
    
    def test_format_currency_usd_medium_value(self):
        """Test format_currency with medium USD value."""
        result = format_currency(150000, "USD")
        self.assertEqual(result, "$150.0K")
    
    def test_format_currency_usd_large_value(self):
        """Test format_currency with large USD value."""
        result = format_currency(2500000, "USD")
        self.assertEqual(result, "$2.5M")
    
    def test_format_currency_eur_small_value(self):
        """Test format_currency with small EUR value."""
        result = format_currency(1234.56, "EUR")
        self.assertEqual(result, "€1,234.56")
    
    def test_format_currency_eur_medium_value(self):
        """Test format_currency with medium EUR value."""
        result = format_currency(150000, "EUR")
        self.assertEqual(result, "€150.0K")
    
    def test_format_currency_eur_large_value(self):
        """Test format_currency with large EUR value."""
        result = format_currency(2500000, "EUR")
        self.assertEqual(result, "€2.5M")
    
    def test_format_currency_generic_currency(self):
        """Test format_currency with generic currency."""
        result = format_currency(150000, "GBP")
        self.assertEqual(result, "GBP 150.0K")
    
    def test_format_currency_string_input(self):
        """Test format_currency with string input."""
        result = format_currency("150000", "USD")
        self.assertEqual(result, "$150.0K")
    
    def test_format_currency_string_with_symbols(self):
        """Test format_currency with string containing currency symbols."""
        result = format_currency("$150,000", "USD")
        self.assertEqual(result, "$150.0K")
    
    def test_format_currency_integer_input(self):
        """Test format_currency with integer input."""
        result = format_currency(150000, "USD")
        self.assertEqual(result, "$150.0K")
    
    def test_format_currency_invalid_type(self):
        """Test format_currency with invalid type."""
        with self.assertRaises(DataFormattingError):
            format_currency(None, "USD")
    
    def test_format_currency_invalid_string(self):
        """Test format_currency with invalid string."""
        with self.assertRaises(DataFormattingError):
            format_currency("invalid", "USD")

    # ============================================================================
    # FORMAT_RISK_SCORE TESTS
    # ============================================================================
    
    def test_format_risk_score_critical_with_emoji(self):
        """Test format_risk_score for critical risk with emoji."""
        result = format_risk_score(0.85, include_emoji=True)
        self.assertEqual(result, "🔴 0.850 (Critical)")
    
    def test_format_risk_score_high_with_emoji(self):
        """Test format_risk_score for high risk with emoji."""
        result = format_risk_score(0.75, include_emoji=True)
        self.assertEqual(result, "🟠 0.750 (High)")
    
    def test_format_risk_score_medium_with_emoji(self):
        """Test format_risk_score for medium risk with emoji."""
        result = format_risk_score(0.55, include_emoji=True)
        self.assertEqual(result, "🟡 0.550 (Medium)")
    
    def test_format_risk_score_low_with_emoji(self):
        """Test format_risk_score for low risk with emoji."""
        result = format_risk_score(0.35, include_emoji=True)
        self.assertEqual(result, "🟢 0.350 (Low)")
    
    def test_format_risk_score_minimal_with_emoji(self):
        """Test format_risk_score for minimal risk with emoji."""
        result = format_risk_score(0.15, include_emoji=True)
        self.assertEqual(result, "🟢 0.150 (Minimal)")
    
    def test_format_risk_score_critical_without_emoji(self):
        """Test format_risk_score for critical risk without emoji."""
        result = format_risk_score(0.85, include_emoji=False)
        self.assertEqual(result, "0.850 (Critical)")
    
    def test_format_risk_score_high_without_emoji(self):
        """Test format_risk_score for high risk without emoji."""
        result = format_risk_score(0.75, include_emoji=False)
        self.assertEqual(result, "0.750 (High)")
    
    def test_format_risk_score_string_input(self):
        """Test format_risk_score with string input."""
        result = format_risk_score("0.75", include_emoji=True)
        self.assertEqual(result, "🟠 0.750 (High)")
    
    def test_format_risk_score_integer_input(self):
        """Test format_risk_score with integer input."""
        result = format_risk_score(1, include_emoji=True)
        self.assertEqual(result, "🔴 1.000 (Critical)")
    
    def test_format_risk_score_boundary_values(self):
        """Test format_risk_score with boundary values."""
        # Test exact boundary values
        self.assertEqual(format_risk_score(0.8, include_emoji=True), "🔴 0.800 (Critical)")
        self.assertEqual(format_risk_score(0.6, include_emoji=True), "🟠 0.600 (High)")
        self.assertEqual(format_risk_score(0.4, include_emoji=True), "🟡 0.400 (Medium)")
        self.assertEqual(format_risk_score(0.2, include_emoji=True), "🟢 0.200 (Low)")
        self.assertEqual(format_risk_score(0.0, include_emoji=True), "🟢 0.000 (Minimal)")
    
    def test_format_risk_score_out_of_range(self):
        """Test format_risk_score with out-of-range values."""
        with self.assertRaises(DataFormattingError):
            format_risk_score(1.5, include_emoji=True)
        
        with self.assertRaises(DataFormattingError):
            format_risk_score(-0.1, include_emoji=True)
    
    def test_format_risk_score_invalid_type(self):
        """Test format_risk_score with invalid type."""
        with self.assertRaises(DataFormattingError):
            format_risk_score(None, include_emoji=True)
    
    def test_format_risk_score_invalid_string(self):
        """Test format_risk_score with invalid string."""
        with self.assertRaises(DataFormattingError):
            format_risk_score("invalid", include_emoji=True)

    # ============================================================================
    # VALIDATE_CLAUDE_API_KEY TESTS
    # ============================================================================
    
    def test_validate_claude_api_key_valid(self):
        """Test validation of valid Claude API key."""
        valid_key = "sk-ant-api03-test123456789012345678901234567890123456789012345678901234567890"
        result = validate_claude_api_key(valid_key)
        self.assertTrue(result)
    
    def test_validate_claude_api_key_invalid_prefix(self):
        """Test validation of API key with invalid prefix."""
        invalid_key = "sk-invalid-test123456789012345678901234567890123456789012345678901234567890"
        result = validate_claude_api_key(invalid_key)
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
    
    def test_validate_claude_api_key_empty(self):
        """Test validation of empty API key."""
        result = validate_claude_api_key("")
        self.assertFalse(result)
    
    def test_validate_claude_api_key_none(self):
        """Test validation of None API key."""
        result = validate_claude_api_key(None)
        self.assertFalse(result)
    
    def test_validate_claude_api_key_non_string(self):
        """Test validation of non-string API key."""
        result = validate_claude_api_key(12345)
        self.assertFalse(result)

    # ============================================================================
    # _SUMMARIZE_DATAFRAME TESTS
    # ============================================================================
    
    def test_summarize_dataframe_success(self):
        """Test successful _summarize_dataframe."""
        result = _summarize_dataframe(self.sample_dataframe)
        
        # Verify basic structure
        self.assertIn("shape", result)
        self.assertIn("columns", result)
        self.assertIn("dtypes", result)
        self.assertIn("memory_usage", result)
        self.assertIn("missing_values", result)
        self.assertIn("numeric_columns", result)
        self.assertIn("categorical_columns", result)
        self.assertIn("sample_data", result)
        
        # Verify specific values
        self.assertEqual(result["shape"], (3, 8))
        self.assertEqual(len(result["columns"]), 8)
        self.assertIn("equipment_id", result["categorical_columns"])
        self.assertIn("maintenance_cost", result["numeric_columns"])
        self.assertEqual(len(result["sample_data"]), 3)
    
    def test_summarize_dataframe_empty(self):
        """Test _summarize_dataframe with empty DataFrame."""
        empty_df = pd.DataFrame()
        result = _summarize_dataframe(empty_df)
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "DataFrame is empty")
    
    def test_summarize_dataframe_with_numeric_stats(self):
        """Test _summarize_dataframe with numeric statistics."""
        result = _summarize_dataframe(self.sample_dataframe)
        
        self.assertIn("numeric_stats", result)
        numeric_stats = result["numeric_stats"]
        self.assertIn("maintenance_cost", numeric_stats)
        self.assertIn("risk_score", numeric_stats)
    
    def test_summarize_dataframe_with_categorical_stats(self):
        """Test _summarize_dataframe with categorical statistics."""
        result = _summarize_dataframe(self.sample_dataframe)
        
        self.assertIn("categorical_stats", result)
        categorical_stats = result["categorical_stats"]
        self.assertIn("equipment_type", categorical_stats)
        self.assertIn("equipment_criticality", categorical_stats)
    
    def test_summarize_dataframe_exception_handling(self):
        """Test _summarize_dataframe exception handling."""
        # Create a problematic DataFrame
        problematic_df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        
        # Mock pandas methods to raise exceptions
        with patch.object(problematic_df, 'memory_usage', side_effect=Exception("Memory error")):
            result = _summarize_dataframe(problematic_df)
            self.assertIn("error", result)
            self.assertIn("Failed to summarize DataFrame", result["error"])

    # ============================================================================
    # _SUMMARIZE_RISK_DATA TESTS
    # ============================================================================
    
    def test_summarize_risk_data_success(self):
        """Test successful _summarize_risk_data."""
        result = _summarize_risk_data(self.sample_risk_data)
        
        # Verify basic structure
        self.assertIn("total_records", result)
        self.assertIn("equipment_types", result)
        self.assertIn("locations", result)
        self.assertIn("risk_analysis", result)
        self.assertIn("equipment_type_distribution", result)
        self.assertIn("avg_risk_by_type", result)
        self.assertIn("criticality_distribution", result)
        self.assertIn("top_locations", result)
        
        # Verify specific values
        self.assertEqual(result["total_records"], 3)
        self.assertEqual(result["equipment_types"], 2)  # Generator, Transformer
        self.assertEqual(result["locations"], 2)  # Plant A, Plant B
        
        # Verify risk analysis
        risk_analysis = result["risk_analysis"]
        self.assertAlmostEqual(risk_analysis["mean_risk"], 0.65, places=2)
        self.assertAlmostEqual(risk_analysis["median_risk"], 0.65, places=2)
        self.assertEqual(risk_analysis["critical_count"], 1)
        self.assertEqual(risk_analysis["high_count"], 1)
        self.assertEqual(risk_analysis["medium_count"], 1)
        self.assertEqual(risk_analysis["low_count"], 0)
    
    def test_summarize_risk_data_empty(self):
        """Test _summarize_risk_data with empty data."""
        result = _summarize_risk_data([])
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "No risk data provided")
    
    def test_summarize_risk_data_missing_columns(self):
        """Test _summarize_risk_data with missing columns."""
        incomplete_data = [
            {"equipment_id": "EQ-001", "risk_score": 0.85}
        ]
        
        result = _summarize_risk_data(incomplete_data)
        
        # Should still work with missing columns
        self.assertEqual(result["total_records"], 1)
        self.assertEqual(result["equipment_types"], 0)  # No equipment_type column
        self.assertEqual(result["locations"], 0)  # No equipment_location column
        
        # Should still have risk analysis
        self.assertIn("risk_analysis", result)
        self.assertEqual(result["risk_analysis"]["mean_risk"], 0.85)
    
    def test_summarize_risk_data_exception_handling(self):
        """Test _summarize_risk_data exception handling."""
        # Create problematic data
        problematic_data = [{"invalid": "data"}]
        
        # Mock pandas to raise exception
        with patch('pandas.DataFrame') as mock_df:
            mock_df.side_effect = Exception("DataFrame error")
            result = _summarize_risk_data(problematic_data)
            self.assertIn("error", result)
            self.assertIn("Failed to summarize risk data", result["error"])

    # ============================================================================
    # _CREATE_DETAILED_VIBRATION_SUMMARY TESTS
    # ============================================================================
    
    def test_create_detailed_vibration_summary_success(self):
        """Test successful _create_detailed_vibration_summary."""
        result = _create_detailed_vibration_summary(self.sample_vibration_data)
        
        # Verify basic structure
        self.assertIn("total_incidents", result)
        self.assertIn("affected_equipment", result)
        self.assertIn("equipment_types", result)
        self.assertIn("analysis_period_days", result)
        self.assertIn("date_range", result)
        self.assertIn("cost_analysis", result)
        self.assertIn("equipment_type_analysis", result)
        self.assertIn("monthly_trends", result)
        self.assertIn("criticality_analysis", result)
        
        # Verify specific values
        self.assertEqual(result["total_incidents"], 3)
        self.assertEqual(result["affected_equipment"], 3)
        self.assertEqual(result["equipment_types"], 3)  # Generator, Motor, Pump
        
        # Verify cost analysis
        cost_analysis = result["cost_analysis"]
        self.assertEqual(cost_analysis["total_cost"], 35000.0)
        self.assertAlmostEqual(cost_analysis["average_cost"], 11666.67, places=2)
        self.assertEqual(cost_analysis["max_cost"], 15000.0)
        self.assertEqual(cost_analysis["min_cost"], 8000.0)
        
        # Verify date range
        date_range = result["date_range"]
        self.assertEqual(date_range["start"], "2024-01-15")
        self.assertEqual(date_range["end"], "2024-01-25")
        self.assertEqual(result["analysis_period_days"], 10)
    
    def test_create_detailed_vibration_summary_empty(self):
        """Test _create_detailed_vibration_summary with empty data."""
        result = _create_detailed_vibration_summary([])
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "No vibration data provided")
    
    def test_create_detailed_vibration_summary_missing_columns(self):
        """Test _create_detailed_vibration_summary with missing columns."""
        incomplete_data = [
            {"equipment_id": "EQ-001", "maintenance_cost": 15000.0}
        ]
        
        result = _create_detailed_vibration_summary(incomplete_data)
        
        # Should still work with missing columns
        self.assertEqual(result["total_incidents"], 1)
        self.assertEqual(result["affected_equipment"], 1)
        self.assertEqual(result["equipment_types"], 0)  # No equipment_type column
        self.assertIsNone(result["analysis_period_days"])  # No maintenance_date column
        
        # Should still have cost analysis
        self.assertIn("cost_analysis", result)
        self.assertEqual(result["cost_analysis"]["total_cost"], 15000.0)
    
    def test_create_detailed_vibration_summary_exception_handling(self):
        """Test _create_detailed_vibration_summary exception handling."""
        # Create problematic data
        problematic_data = [{"invalid": "data"}]
        
        # Mock pandas to raise exception
        with patch('pandas.DataFrame') as mock_df:
            mock_df.side_effect = Exception("DataFrame error")
            result = _create_detailed_vibration_summary(problematic_data)
            self.assertIn("error", result)
            self.assertIn("Failed to create vibration summary", result["error"])

    # ============================================================================
    # INTEGRATION TESTS
    # ============================================================================
    
    def test_format_currency_and_risk_score_integration(self):
        """Test integration between format_currency and format_risk_score."""
        # Test that both functions work together in a workflow
        cost = 150000
        risk_score = 0.85
        
        formatted_cost = format_currency(cost, "USD")
        formatted_risk = format_risk_score(risk_score, include_emoji=True)
        
        self.assertEqual(formatted_cost, "$150.0K")
        self.assertEqual(formatted_risk, "🔴 0.850 (Critical)")
    
    def test_data_summarization_integration(self):
        """Test integration between different summarization functions."""
        # Test that all summarization functions work together
        df_summary = _summarize_dataframe(self.sample_dataframe)
        risk_summary = _summarize_risk_data(self.sample_risk_data)
        vibration_summary = _create_detailed_vibration_summary(self.sample_vibration_data)
        
        # All should be successful
        self.assertNotIn("error", df_summary)
        self.assertNotIn("error", risk_summary)
        self.assertNotIn("error", vibration_summary)
        
        # Should have consistent data
        self.assertEqual(df_summary["shape"][0], 3)  # 3 rows in DataFrame
        self.assertEqual(risk_summary["total_records"], 3)  # 3 risk records
        self.assertEqual(vibration_summary["total_incidents"], 3)  # 3 vibration incidents)


if __name__ == '__main__':
    unittest.main() 
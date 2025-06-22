"""
Claude AI Utilities for Energy Grid Management Agent
"""
import anthropic
import pandas as pd
import numpy as np
import logging
import re
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from config import Config

# Configure logging
logger = logging.getLogger(__name__)

class ClaudeAnalysisError(Exception):
    """Custom exception for Claude analysis errors."""
    pass

class DataFormattingError(Exception):
    """Custom exception for data formatting errors."""
    pass

@dataclass
class AnalysisResult:
    """Data class for analysis results."""
    success: bool
    data: Any
    error_message: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

# ============================================================================
# DATA FORMATTING HELPERS
# ============================================================================

def format_currency(value: Union[float, int, str], currency: str = "USD") -> str:
    """
    Format monetary values with proper currency formatting.
    
    Args:
        value: Numeric value to format
        currency: Currency code (default: USD)
        
    Returns:
        Formatted currency string
        
    Raises:
        DataFormattingError: If value cannot be formatted
    """
    try:
        # Convert to float if string
        if isinstance(value, str):
            # Remove any currency symbols and commas
            value = re.sub(r'[^\d.-]', '', value)
            value = float(value)
        elif isinstance(value, (int, float)):
            value = float(value)
        else:
            raise ValueError(f"Unsupported value type: {type(value)}")
        
        # Format based on currency
        if currency.upper() == "USD":
            if value >= 1_000_000:
                return f"${value/1_000_000:.1f}M"
            elif value >= 1_000:
                return f"${value/1_000:.1f}K"
            else:
                return f"${value:,.2f}"
        elif currency.upper() == "EUR":
            if value >= 1_000_000:
                return f"€{value/1_000_000:.1f}M"
            elif value >= 1_000:
                return f"€{value/1_000:.1f}K"
            else:
                return f"€{value:,.2f}"
        else:
            # Generic formatting
            if value >= 1_000_000:
                return f"{currency} {value/1_000_000:.1f}M"
            elif value >= 1_000:
                return f"{currency} {value/1_000:.1f}K"
            else:
                return f"{currency} {value:,.2f}"
                
    except (ValueError, TypeError) as e:
        logger.error(f"Error formatting currency value {value}: {e}")
        raise DataFormattingError(f"Cannot format currency value: {value}") from e

def format_risk_score(risk_score: Union[float, int, str], include_emoji: bool = True) -> str:
    """
    Color-code risk scores with emojis and formatting.
    
    Args:
        risk_score: Risk score value (0.0-1.0)
        include_emoji: Whether to include emoji indicators
        
    Returns:
        Formatted risk score string
        
    Raises:
        DataFormattingError: If risk score is invalid
    """
    try:
        # Convert to float
        if isinstance(risk_score, str):
            risk_score = float(risk_score)
        elif isinstance(risk_score, (int, float)):
            risk_score = float(risk_score)
        else:
            raise ValueError(f"Unsupported risk score type: {type(risk_score)}")
        
        # Validate range
        if not 0.0 <= risk_score <= 1.0:
            raise ValueError(f"Risk score must be between 0.0 and 1.0, got: {risk_score}")
        
        # Format with emoji and color coding
        if include_emoji:
            if risk_score >= 0.8:
                return f"🔴 {risk_score:.3f} (Critical)"
            elif risk_score >= 0.6:
                return f"🟠 {risk_score:.3f} (High)"
            elif risk_score >= 0.4:
                return f"🟡 {risk_score:.3f} (Medium)"
            elif risk_score >= 0.2:
                return f"🟢 {risk_score:.3f} (Low)"
            else:
                return f"🟢 {risk_score:.3f} (Minimal)"
        else:
            if risk_score >= 0.8:
                return f"{risk_score:.3f} (Critical)"
            elif risk_score >= 0.6:
                return f"{risk_score:.3f} (High)"
            elif risk_score >= 0.4:
                return f"{risk_score:.3f} (Medium)"
            elif risk_score >= 0.2:
                return f"{risk_score:.3f} (Low)"
            else:
                return f"{risk_score:.3f} (Minimal)"
                
    except (ValueError, TypeError) as e:
        logger.error(f"Error formatting risk score {risk_score}: {e}")
        raise DataFormattingError(f"Cannot format risk score: {risk_score}") from e

def validate_claude_api_key(api_key: str) -> bool:
    """
    Validate Claude API key format.
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if valid format, False otherwise
    """
    try:
        if not api_key or not isinstance(api_key, str):
            return False
        
        # Claude API keys typically start with 'sk-ant-api03-' and are 64+ characters
        if not api_key.startswith('sk-ant-api03-'):
            return False
        
        if len(api_key) < 64:
            return False
        
        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not re.match(r'^sk-ant-api03-[a-zA-Z0-9_-]+$', api_key):
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating API key: {e}")
        return False

# ============================================================================
# DATA SUMMARIZATION HELPERS
# ============================================================================

def _summarize_dataframe(df: pd.DataFrame, max_rows: int = 1000) -> Dict[str, Any]:
    """
    Create a comprehensive summary of a DataFrame.
    
    Args:
        df: DataFrame to summarize
        max_rows: Maximum rows to include in summary
        
    Returns:
        Dictionary containing DataFrame summary
    """
    try:
        if df.empty:
            return {"error": "DataFrame is empty"}
        
        summary = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": df.dtypes.to_dict(),
            "memory_usage": df.memory_usage(deep=True).sum(),
            "missing_values": df.isnull().sum().to_dict(),
            "numeric_columns": df.select_dtypes(include=[np.number]).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object', 'category']).columns.tolist(),
            "datetime_columns": df.select_dtypes(include=['datetime']).columns.tolist()
        }
        
        # Add descriptive statistics for numeric columns
        if summary["numeric_columns"]:
            summary["numeric_stats"] = df[summary["numeric_columns"]].describe().to_dict()
        
        # Add value counts for categorical columns (top 10)
        if summary["categorical_columns"]:
            summary["categorical_stats"] = {}
            for col in summary["categorical_columns"]:
                value_counts = df[col].value_counts().head(10)
                summary["categorical_stats"][col] = value_counts.to_dict()
        
        # Add sample data (first few rows)
        summary["sample_data"] = df.head(min(5, len(df))).to_dict('records')
        
        return summary
        
    except Exception as e:
        logger.error(f"Error summarizing DataFrame: {e}")
        return {"error": f"Failed to summarize DataFrame: {e}"}

def _summarize_risk_data(risk_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a specialized summary for risk assessment data.
    
    Args:
        risk_data: List of risk assessment records
        
    Returns:
        Dictionary containing risk data summary
    """
    try:
        if not risk_data:
            return {"error": "No risk data provided"}
        
        df = pd.DataFrame(risk_data)
        
        summary = {
            "total_records": len(risk_data),
            "equipment_types": df['equipment_type'].nunique() if 'equipment_type' in df.columns else 0,
            "locations": df['equipment_location'].nunique() if 'equipment_location' in df.columns else 0
        }
        
        # Risk score analysis
        if 'risk_score' in df.columns:
            risk_scores = df['risk_score'].dropna()
            if not risk_scores.empty:
                summary["risk_analysis"] = {
                    "mean_risk": float(risk_scores.mean()),
                    "median_risk": float(risk_scores.median()),
                    "std_risk": float(risk_scores.std()),
                    "min_risk": float(risk_scores.min()),
                    "max_risk": float(risk_scores.max()),
                    "critical_count": len(risk_scores[risk_scores >= 0.8]),
                    "high_count": len(risk_scores[(risk_scores >= 0.6) & (risk_scores < 0.8)]),
                    "medium_count": len(risk_scores[(risk_scores >= 0.4) & (risk_scores < 0.6)]),
                    "low_count": len(risk_scores[risk_scores < 0.4])
                }
        
        # Equipment type analysis
        if 'equipment_type' in df.columns:
            type_counts = df['equipment_type'].value_counts()
            summary["equipment_type_distribution"] = type_counts.to_dict()
            
            # Average risk by equipment type
            if 'risk_score' in df.columns:
                avg_risk_by_type = df.groupby('equipment_type')['risk_score'].mean().sort_values(ascending=False)
                summary["avg_risk_by_type"] = avg_risk_by_type.to_dict()
        
        # Criticality analysis
        if 'equipment_criticality' in df.columns:
            criticality_counts = df['equipment_criticality'].value_counts()
            summary["criticality_distribution"] = criticality_counts.to_dict()
        
        # Location analysis
        if 'equipment_location' in df.columns:
            location_counts = df['equipment_location'].value_counts().head(10)
            summary["top_locations"] = location_counts.to_dict()
        
        return summary
        
    except Exception as e:
        logger.error(f"Error summarizing risk data: {e}")
        return {"error": f"Failed to summarize risk data: {e}"}

def _create_detailed_vibration_summary(vibration_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a detailed summary for vibration analysis data.
    
    Args:
        vibration_data: List of vibration-related maintenance records
        
    Returns:
        Dictionary containing detailed vibration summary
    """
    try:
        if not vibration_data:
            return {"error": "No vibration data provided"}
        
        df = pd.DataFrame(vibration_data)
        
        summary = {
            "total_incidents": len(vibration_data),
            "affected_equipment": df['equipment_id'].nunique() if 'equipment_id' in df.columns else 0,
            "equipment_types": df['equipment_type'].nunique() if 'equipment_type' in df.columns else 0,
            "analysis_period_days": None
        }
        
        # Date range analysis
        if 'maintenance_date' in df.columns:
            df['maintenance_date'] = pd.to_datetime(df['maintenance_date'])
            date_range = df['maintenance_date'].max() - df['maintenance_date'].min()
            summary["analysis_period_days"] = date_range.days
            summary["date_range"] = {
                "start": df['maintenance_date'].min().strftime('%Y-%m-%d'),
                "end": df['maintenance_date'].max().strftime('%Y-%m-%d')
            }
        
        # Cost analysis
        if 'maintenance_cost' in df.columns:
            costs = df['maintenance_cost'].dropna()
            if not costs.empty:
                summary["cost_analysis"] = {
                    "total_cost": float(costs.sum()),
                    "average_cost": float(costs.mean()),
                    "median_cost": float(costs.median()),
                    "max_cost": float(costs.max()),
                    "min_cost": float(costs.min()),
                    "cost_std": float(costs.std())
                }
        
        # Equipment type analysis
        if 'equipment_type' in df.columns:
            type_analysis = df.groupby('equipment_type').agg({
                'equipment_id': 'count',
                'maintenance_cost': ['sum', 'mean'] if 'maintenance_cost' in df.columns else 'count'
            }).round(2)
            
            summary["equipment_type_analysis"] = type_analysis.to_dict()
        
        # Temporal analysis
        if 'maintenance_date' in df.columns:
            # Monthly trends
            df['month'] = df['maintenance_date'].dt.to_period('M')
            monthly_counts = df.groupby('month').size()
            summary["monthly_trends"] = {
                "peak_month": monthly_counts.idxmax().strftime('%Y-%m'),
                "peak_count": int(monthly_counts.max()),
                "average_monthly": float(monthly_counts.mean())
            }
        
        # Criticality analysis
        if 'equipment_criticality' in df.columns:
            criticality_analysis = df.groupby('equipment_criticality').agg({
                'equipment_id': 'count',
                'maintenance_cost': 'sum' if 'maintenance_cost' in df.columns else 'count'
            })
            summary["criticality_analysis"] = criticality_analysis.to_dict()
        
        return summary
        
    except Exception as e:
        logger.error(f"Error creating vibration summary: {e}")
        return {"error": f"Failed to create vibration summary: {e}"}

# ============================================================================
# ADVANCED CLAUDE ANALYSIS CLASS
# ============================================================================

class AdvancedClaudeAnalyzer:
    """Advanced Claude AI analysis for energy grid management."""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize the advanced Claude analyzer.
        
        Args:
            api_key: Claude API key
            model: Claude model to use
        """
        if not validate_claude_api_key(api_key):
            raise ClaudeAnalysisError("Invalid Claude API key format")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.config = Config()
        
        logger.info(f"Initialized AdvancedClaudeAnalyzer with model: {model}")
    
    def _create_analysis_prompt(self, analysis_type: str, data_summary: Dict[str, Any], 
                               additional_context: str = "") -> str:
        """
        Create a structured prompt for Claude analysis.
        
        Args:
            analysis_type: Type of analysis to perform
            data_summary: Summary of data to analyze
            additional_context: Additional context for analysis
            
        Returns:
            Formatted prompt string
        """
        base_prompt = f"""
        You are an expert energy grid management analyst with deep knowledge of:
        - Power generation and distribution systems
        - Equipment maintenance and reliability engineering
        - Risk assessment and failure prediction
        - Vibration analysis and mechanical systems
        - Predictive maintenance strategies
        
        Analysis Type: {analysis_type}
        
        Data Summary:
        {json.dumps(data_summary, indent=2)}
        
        Additional Context:
        {additional_context}
        
        Please provide a comprehensive, professional analysis that includes:
        1. Key insights and patterns identified
        2. Risk factors and their implications
        3. Specific recommendations for action
        4. Industry best practices and standards
        5. Quantifiable metrics and benchmarks
        
        Format your response in clear, structured sections with appropriate headers.
        Use professional terminology suitable for energy grid management professionals.
        """
        
        return base_prompt
    
    def analyze_equipment_trends(self, maintenance_data: List[Dict[str, Any]], 
                                analysis_period: str = "12 months") -> AnalysisResult:
        """
        Analyze equipment maintenance trends and patterns.
        
        Args:
            maintenance_data: List of maintenance records
            analysis_period: Period for trend analysis
            
        Returns:
            AnalysisResult with trend analysis
        """
        try:
            logger.info(f"Starting equipment trends analysis for {len(maintenance_data)} records")
            
            # Create data summary
            df = pd.DataFrame(maintenance_data)
            data_summary = _summarize_dataframe(df)
            
            # Add trend-specific analysis
            if 'maintenance_date' in df.columns:
                df['maintenance_date'] = pd.to_datetime(df['maintenance_date'])
                df['month'] = df['maintenance_date'].dt.to_period('M')
                
                monthly_trends = df.groupby('month').agg({
                    'equipment_id': 'count',
                    'maintenance_cost': 'sum' if 'maintenance_cost' in df.columns else 'count'
                })
                
                data_summary["trend_analysis"] = {
                    "monthly_maintenance_count": monthly_trends['equipment_id'].to_dict(),
                    "monthly_cost_trend": monthly_trends['maintenance_cost'].to_dict() if 'maintenance_cost' in df.columns else None,
                    "total_months": len(monthly_trends),
                    "average_monthly_maintenance": float(monthly_trends['equipment_id'].mean())
                }
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(
                "Equipment Maintenance Trends Analysis",
                data_summary,
                f"Analysis Period: {analysis_period}"
            )
            
            # Get Claude response
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            analysis_result = AnalysisResult(
                success=True,
                data={
                    "analysis": response.content[0].text,
                    "data_summary": data_summary,
                    "analysis_period": analysis_period
                }
            )
            
            logger.info("Equipment trends analysis completed successfully")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in equipment trends analysis: {e}")
            return AnalysisResult(
                success=False,
                data=None,
                error_message=f"Equipment trends analysis failed: {e}"
            )
    
    def generate_risk_report(self, risk_data: List[Dict[str, Any]], 
                           risk_threshold: float = 0.6) -> AnalysisResult:
        """
        Generate comprehensive risk assessment report.
        
        Args:
            risk_data: List of risk assessment records
            risk_threshold: Risk threshold for analysis
            
        Returns:
            AnalysisResult with risk report
        """
        try:
            logger.info(f"Generating risk report for {len(risk_data)} records with threshold {risk_threshold}")
            
            # Create risk data summary
            risk_summary = _summarize_risk_data(risk_data)
            
            # Add threshold-specific analysis
            df = pd.DataFrame(risk_data)
            if 'risk_score' in df.columns:
                high_risk_equipment = df[df['risk_score'] >= risk_threshold]
                risk_summary["threshold_analysis"] = {
                    "threshold": risk_threshold,
                    "high_risk_count": len(high_risk_equipment),
                    "high_risk_percentage": len(high_risk_equipment) / len(df) * 100,
                    "critical_equipment": len(high_risk_equipment[high_risk_equipment['equipment_criticality'] == 'Critical']) if 'equipment_criticality' in df.columns else 0
                }
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(
                "Comprehensive Risk Assessment Report",
                risk_summary,
                f"Risk Threshold: {risk_threshold}"
            )
            
            # Get Claude response
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            
            analysis_result = AnalysisResult(
                success=True,
                data={
                    "risk_report": response.content[0].text,
                    "risk_summary": risk_summary,
                    "risk_threshold": risk_threshold
                }
            )
            
            logger.info("Risk report generated successfully")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error generating risk report: {e}")
            return AnalysisResult(
                success=False,
                data=None,
                error_message=f"Risk report generation failed: {e}"
            )
    
    def optimize_maintenance_workflow(self, maintenance_data: List[Dict[str, Any]], 
                                    risk_data: List[Dict[str, Any]] = None,
                                    constraints: Dict[str, Any] = None) -> AnalysisResult:
        """
        Optimize maintenance workflow using AI analysis.
        
        Args:
            maintenance_data: List of maintenance records
            risk_data: Optional risk assessment data
            constraints: Operational constraints (budget, manpower, etc.)
            
        Returns:
            AnalysisResult with optimization recommendations
        """
        try:
            logger.info("Starting maintenance workflow optimization analysis")
            
            # Create comprehensive data summary
            maintenance_summary = _summarize_dataframe(pd.DataFrame(maintenance_data))
            
            analysis_data = {
                "maintenance_data": maintenance_summary,
                "constraints": constraints or {}
            }
            
            if risk_data:
                risk_summary = _summarize_risk_data(risk_data)
                analysis_data["risk_data"] = risk_summary
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(
                "Maintenance Workflow Optimization",
                analysis_data,
                "Focus on optimizing maintenance schedules, resource allocation, and cost efficiency"
            )
            
            # Get Claude response
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}]
            )
            
            analysis_result = AnalysisResult(
                success=True,
                data={
                    "optimization_plan": response.content[0].text,
                    "analysis_data": analysis_data,
                    "constraints": constraints
                }
            )
            
            logger.info("Maintenance workflow optimization completed successfully")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in maintenance workflow optimization: {e}")
            return AnalysisResult(
                success=False,
                data=None,
                error_message=f"Maintenance workflow optimization failed: {e}"
            )
    
    def predict_failure_scenarios(self, maintenance_data: List[Dict[str, Any]], 
                                risk_data: List[Dict[str, Any]],
                                prediction_horizon: str = "6 months") -> AnalysisResult:
        """
        Predict potential failure scenarios using AI analysis.
        
        Args:
            maintenance_data: Historical maintenance records
            risk_data: Current risk assessment data
            prediction_horizon: Time horizon for predictions
            
        Returns:
            AnalysisResult with failure predictions
        """
        try:
            logger.info(f"Starting failure scenario prediction for {prediction_horizon} horizon")
            
            # Create comprehensive analysis data
            maintenance_summary = _summarize_dataframe(pd.DataFrame(maintenance_data))
            risk_summary = _summarize_risk_data(risk_data)
            
            analysis_data = {
                "historical_maintenance": maintenance_summary,
                "current_risk_assessment": risk_summary,
                "prediction_horizon": prediction_horizon
            }
            
            # Add failure pattern analysis
            df_maintenance = pd.DataFrame(maintenance_data)
            if 'maintenance_date' in df_maintenance.columns and 'equipment_id' in df_maintenance.columns:
                df_maintenance['maintenance_date'] = pd.to_datetime(df_maintenance['maintenance_date'])
                
                # Calculate time between maintenance for each equipment
                equipment_maintenance_gaps = {}
                for equipment_id in df_maintenance['equipment_id'].unique():
                    equipment_data = df_maintenance[df_maintenance['equipment_id'] == equipment_id].sort_values('maintenance_date')
                    if len(equipment_data) > 1:
                        gaps = equipment_data['maintenance_date'].diff().dt.days.dropna()
                        equipment_maintenance_gaps[equipment_id] = {
                            "avg_gap_days": float(gaps.mean()),
                            "last_maintenance": equipment_data['maintenance_date'].max().strftime('%Y-%m-%d'),
                            "maintenance_count": len(equipment_data)
                        }
                
                analysis_data["maintenance_patterns"] = equipment_maintenance_gaps
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(
                "Failure Scenario Prediction",
                analysis_data,
                f"Prediction Horizon: {prediction_horizon}. Focus on identifying high-risk equipment and potential failure modes."
            )
            
            # Get Claude response
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            analysis_result = AnalysisResult(
                success=True,
                data={
                    "failure_predictions": response.content[0].text,
                    "analysis_data": analysis_data,
                    "prediction_horizon": prediction_horizon
                }
            )
            
            logger.info("Failure scenario prediction completed successfully")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in failure scenario prediction: {e}")
            return AnalysisResult(
                success=False,
                data=None,
                error_message=f"Failure scenario prediction failed: {e}"
            )

# ============================================================================
# LEGACY CLAUDE CLIENT (for backward compatibility)
# ============================================================================

class ClaudeClient:
    """Legacy Claude client for backward compatibility."""
    
    def __init__(self, api_key: str = None, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize Claude client.
        
        Args:
            api_key: Claude API key (optional, will use config if not provided)
            model: Claude model to use
        """
        config = Config()
        self.api_key = api_key or config.CLAUDE_API_KEY
        self.model = model or config.CLAUDE_MODEL
        
        if not validate_claude_api_key(self.api_key):
            raise ClaudeAnalysisError("Invalid Claude API key")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.advanced_analyzer = AdvancedClaudeAnalyzer(self.api_key, self.model)
        
        logger.info(f"Initialized ClaudeClient with model: {self.model}")
    
    def analyze_grid_data(self, prompt: str) -> str:
        """
        Analyze grid data using Claude AI.
        
        Args:
            prompt: Analysis prompt
            
        Returns:
            Claude's analysis response
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error in grid data analysis: {e}")
            return f"Analysis failed: {e}"
    
    def get_advanced_analyzer(self) -> AdvancedClaudeAnalyzer:
        """
        Get the advanced analyzer instance.
        
        Returns:
            AdvancedClaudeAnalyzer instance
        """
        return self.advanced_analyzer 
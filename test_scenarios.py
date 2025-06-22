"""
Test Scenarios for Energy Grid Management Agent
Demonstrates application capabilities with sample queries and data
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from test_data_generator import MockDataGenerator, mock_generator
import logging

logger = logging.getLogger(__name__)

class TestScenarios:
    """Test scenarios demonstrating Energy Grid Management Agent capabilities."""
    
    def __init__(self):
        self.mock_data = None
        self.generator = MockDataGenerator()
        
    def load_mock_data(self, filename: str = "mock_data.json"):
        """Load mock data for testing."""
        try:
            self.mock_data = self.generator.load_from_json(filename)
            logger.info("Mock data loaded successfully")
        except FileNotFoundError:
            logger.info("Mock data file not found, generating new data...")
            self.mock_data = self.generator.generate_all_data()
            self.generator.save_to_json(self.mock_data, filename)
    
    def scenario_1_vibration_issues_search(self) -> Dict[str, Any]:
        """
        Test Scenario 1: Search equipment that presented vibration issues
        Original query: "Search equipment that presented vibration issues and list and summarize the description..."
        """
        logger.info("Running Scenario 1: Vibration Issues Search")
        
        # Filter maintenance records for vibration issues
        vibration_records = []
        for record in self.mock_data["maintenance_records"]:
            if "vibration" in record["description"].lower():
                vibration_records.append(record)
        
        # Get equipment details for vibration issues
        equipment_with_vibration = []
        for record in vibration_records:
            equipment_id = record["equipment_id"]
            equipment = next((eq for eq in self.mock_data["equipment"] if eq["id"] == equipment_id), None)
            if equipment:
                equipment_with_vibration.append({
                    "equipment": equipment,
                    "maintenance_record": record,
                    "issue_type": "vibration",
                    "severity": "high" if record["downtime_hours"] > 24 else "medium"
                })
        
        # Generate summary
        summary = {
            "total_vibration_issues": len(vibration_records),
            "equipment_affected": len(set(record["equipment_id"] for record in vibration_records)),
            "total_downtime_hours": sum(record["downtime_hours"] for record in vibration_records),
            "total_cost": sum(record["cost"] for record in vibration_records),
            "common_issues": self._get_common_issues(vibration_records),
            "equipment_details": equipment_with_vibration
        }
        
        return {
            "scenario": "Vibration Issues Search",
            "query": "Search equipment that presented vibration issues and list and summarize the description",
            "results": summary,
            "sample_data": vibration_records[:5]  # First 5 records for display
        }
    
    def scenario_2_maintenance_schedule_2_weeks(self) -> Dict[str, Any]:
        """
        Test Scenario 2: Develop maintenance schedule over the next two weeks
        Original query: "Can you develop a maintenance schedule over the next two weeks..."
        """
        logger.info("Running Scenario 2: Maintenance Schedule for Next 2 Weeks")
        
        # Get current date and calculate 2 weeks ahead
        current_date = datetime.now()
        end_date = current_date + timedelta(weeks=2)
        
        # Filter equipment that needs maintenance in the next 2 weeks
        maintenance_schedule = []
        
        for equipment in self.mock_data["equipment"]:
            # Calculate days since last maintenance
            if equipment["last_maintenance"]:
                last_maintenance = datetime.strptime(equipment["last_maintenance"], "%Y-%m-%d")
                days_since_maintenance = (current_date - last_maintenance).days
                
                # Determine maintenance priority based on risk score and time since last maintenance
                maintenance_priority = self._calculate_maintenance_priority(
                    equipment["risk_score"], 
                    days_since_maintenance,
                    equipment["type"]
                )
                
                if maintenance_priority["needs_maintenance"]:
                    # Schedule maintenance within the 2-week period
                    scheduled_date = self._calculate_scheduled_date(
                        current_date, 
                        end_date, 
                        maintenance_priority["priority"]
                    )
                    
                    maintenance_schedule.append({
                        "equipment": equipment,
                        "scheduled_date": scheduled_date.strftime("%Y-%m-%d"),
                        "priority": maintenance_priority["priority"],
                        "maintenance_type": maintenance_priority["maintenance_type"],
                        "estimated_duration": maintenance_priority["estimated_duration"],
                        "estimated_cost": maintenance_priority["estimated_cost"],
                        "reason": maintenance_priority["reason"]
                    })
        
        # Sort by priority and date
        maintenance_schedule.sort(key=lambda x: (x["priority"], x["scheduled_date"]))
        
        # Group by week
        week_1_schedule = [item for item in maintenance_schedule 
                          if datetime.strptime(item["scheduled_date"], "%Y-%m-%d") <= current_date + timedelta(weeks=1)]
        week_2_schedule = [item for item in maintenance_schedule 
                          if datetime.strptime(item["scheduled_date"], "%Y-%m-%d") > current_date + timedelta(weeks=1)]
        
        summary = {
            "total_maintenance_tasks": len(maintenance_schedule),
            "week_1_tasks": len(week_1_schedule),
            "week_2_tasks": len(week_2_schedule),
            "total_estimated_cost": sum(item["estimated_cost"] for item in maintenance_schedule),
            "total_estimated_duration": sum(item["estimated_duration"] for item in maintenance_schedule),
            "high_priority_tasks": len([item for item in maintenance_schedule if item["priority"] == "high"]),
            "schedule": {
                "week_1": week_1_schedule,
                "week_2": week_2_schedule
            }
        }
        
        return {
            "scenario": "Maintenance Schedule for Next 2 Weeks",
            "query": "Can you develop a maintenance schedule over the next two weeks",
            "results": summary,
            "detailed_schedule": maintenance_schedule
        }
    
    def scenario_3_risk_assessment_analysis(self) -> Dict[str, Any]:
        """
        Test Scenario 3: Risk Assessment Analysis
        Analyze equipment risk scores and identify high-risk equipment
        """
        logger.info("Running Scenario 3: Risk Assessment Analysis")
        
        # Analyze equipment by risk score
        high_risk_equipment = [eq for eq in self.mock_data["equipment"] if eq["risk_score"] >= 7.0]
        medium_risk_equipment = [eq for eq in self.mock_data["equipment"] if 4.0 <= eq["risk_score"] < 7.0]
        low_risk_equipment = [eq for eq in self.mock_data["equipment"] if eq["risk_score"] < 4.0]
        
        # Get maintenance history for high-risk equipment
        high_risk_maintenance = []
        for equipment in high_risk_equipment:
            equipment_maintenance = [mr for mr in self.mock_data["maintenance_records"] 
                                   if mr["equipment_id"] == equipment["id"]]
            high_risk_maintenance.append({
                "equipment": equipment,
                "maintenance_count": len(equipment_maintenance),
                "total_downtime": sum(mr["downtime_hours"] for mr in equipment_maintenance),
                "total_cost": sum(mr["cost"] for mr in equipment_maintenance),
                "last_maintenance": max([mr["date"] for mr in equipment_maintenance]) if equipment_maintenance else None
            })
        
        # Risk analysis by equipment type
        risk_by_type = {}
        for equipment_type in set(eq["type"] for eq in self.mock_data["equipment"]):
            type_equipment = [eq for eq in self.mock_data["equipment"] if eq["type"] == equipment_type]
            avg_risk = sum(eq["risk_score"] for eq in type_equipment) / len(type_equipment)
            risk_by_type[equipment_type] = {
                "count": len(type_equipment),
                "average_risk_score": round(avg_risk, 2),
                "high_risk_count": len([eq for eq in type_equipment if eq["risk_score"] >= 7.0])
            }
        
        return {
            "scenario": "Risk Assessment Analysis",
            "query": "Analyze equipment risk scores and identify high-risk equipment",
            "results": {
                "risk_distribution": {
                    "high_risk": len(high_risk_equipment),
                    "medium_risk": len(medium_risk_equipment),
                    "low_risk": len(low_risk_equipment)
                },
                "high_risk_equipment": high_risk_maintenance,
                "risk_by_equipment_type": risk_by_type,
                "recommendations": self._generate_risk_recommendations(high_risk_equipment)
            }
        }
    
    def scenario_4_dependency_analysis(self) -> Dict[str, Any]:
        """
        Test Scenario 4: Dependency Analysis
        Analyze equipment dependencies and impact assessment
        """
        logger.info("Running Scenario 4: Dependency Analysis")
        
        # Create dependency relationships (simulating the graph structure)
        dependencies = []
        for equipment in self.mock_data["equipment"]:
            # Simulate dependencies based on equipment type and location
            dependent_equipment = []
            for other_equipment in self.mock_data["equipment"]:
                if (equipment["id"] != other_equipment["id"] and 
                    equipment["location"] == other_equipment["location"]):
                    dependency_strength = self._calculate_dependency_strength(equipment, other_equipment)
                    if dependency_strength > 0.3:  # Threshold for dependency
                        dependent_equipment.append({
                            "equipment": other_equipment,
                            "dependency_strength": dependency_strength,
                            "dependency_type": self._get_dependency_type(equipment, other_equipment)
                        })
            
            if dependent_equipment:
                dependencies.append({
                    "equipment": equipment,
                    "dependencies": dependent_equipment,
                    "total_dependencies": len(dependent_equipment)
                })
        
        # Impact analysis for maintenance scheduling
        impact_analysis = []
        for dep in dependencies:
            if dep["equipment"]["risk_score"] >= 6.0:  # High-risk equipment
                impact_analysis.append({
                    "equipment": dep["equipment"],
                    "affected_equipment": dep["dependencies"],
                    "potential_impact": self._calculate_potential_impact(dep["equipment"], dep["dependencies"]),
                    "recommended_action": "Schedule maintenance during low-demand periods"
                })
        
        return {
            "scenario": "Dependency Analysis",
            "query": "Analyze equipment dependencies and impact assessment",
            "results": {
                "total_dependencies": len(dependencies),
                "equipment_with_dependencies": len([d for d in dependencies if d["total_dependencies"] > 0]),
                "dependency_analysis": dependencies,
                "impact_analysis": impact_analysis,
                "critical_paths": self._identify_critical_paths(dependencies)
            }
        }
    
    def scenario_5_sensor_analysis(self) -> Dict[str, Any]:
        """
        Test Scenario 5: Sensor Data Analysis
        Analyze sensor readings and identify anomalies
        """
        logger.info("Running Scenario 5: Sensor Data Analysis")
        
        # Analyze sensor data for anomalies
        anomalies = []
        for sensor in self.mock_data["sensors"]:
            ratio = sensor["measurement_value"] / sensor["expected_value"]
            if ratio > 1.5 or ratio < 0.7:  # Anomaly threshold
                equipment = next((eq for eq in self.mock_data["equipment"] if eq["id"] == sensor["equipment_id"]), None)
                anomalies.append({
                    "sensor": sensor,
                    "equipment": equipment,
                    "anomaly_ratio": round(ratio, 2),
                    "severity": "high" if ratio > 2.0 or ratio < 0.5 else "medium",
                    "recommendation": self._get_sensor_recommendation(sensor["type"], ratio)
                })
        
        # Sensor performance by type
        sensor_performance = {}
        for sensor_type in set(s["type"] for s in self.mock_data["sensors"]):
            type_sensors = [s for s in self.mock_data["sensors"] if s["type"] == sensor_type]
            avg_ratio = sum(s["measurement_value"] / s["expected_value"] for s in type_sensors) / len(type_sensors)
            anomaly_count = len([s for s in type_sensors 
                               if s["measurement_value"] / s["expected_value"] > 1.5 or 
                               s["measurement_value"] / s["expected_value"] < 0.7])
            
            sensor_performance[sensor_type] = {
                "count": len(type_sensors),
                "average_ratio": round(avg_ratio, 2),
                "anomaly_count": anomaly_count,
                "anomaly_percentage": round((anomaly_count / len(type_sensors)) * 100, 2)
            }
        
        return {
            "scenario": "Sensor Data Analysis",
            "query": "Analyze sensor readings and identify anomalies",
            "results": {
                "total_sensors": len(self.mock_data["sensors"]),
                "anomalies_detected": len(anomalies),
                "anomalies": anomalies,
                "sensor_performance": sensor_performance,
                "recommendations": self._generate_sensor_recommendations(anomalies)
            }
        }
    
    def scenario_6_cost_analysis(self) -> Dict[str, Any]:
        """
        Test Scenario 6: Cost Analysis
        Analyze maintenance costs and budget planning
        """
        logger.info("Running Scenario 6: Cost Analysis")
        
        # Cost analysis by equipment type
        cost_by_type = {}
        for equipment_type in set(eq["type"] for eq in self.mock_data["equipment"]):
            type_equipment_ids = [eq["id"] for eq in self.mock_data["equipment"] if eq["type"] == equipment_type]
            type_maintenance = [mr for mr in self.mock_data["maintenance_records"] 
                              if mr["equipment_id"] in type_equipment_ids]
            
            if type_maintenance:
                cost_by_type[equipment_type] = {
                    "total_cost": sum(mr["cost"] for mr in type_maintenance),
                    "average_cost": sum(mr["cost"] for mr in type_maintenance) / len(type_maintenance),
                    "maintenance_count": len(type_maintenance),
                    "total_downtime": sum(mr["downtime_hours"] for mr in type_maintenance),
                    "cost_per_hour": sum(mr["cost"] for mr in type_maintenance) / sum(mr["downtime_hours"] for mr in type_maintenance) if sum(mr["downtime_hours"] for mr in type_maintenance) > 0 else 0
                }
        
        # Monthly cost trend (simulated)
        monthly_costs = []
        for i in range(12):
            month_date = datetime.now() - timedelta(days=30*i)
            month_maintenance = [mr for mr in self.mock_data["maintenance_records"] 
                               if datetime.strptime(mr["date"], "%Y-%m-%d").month == month_date.month]
            monthly_costs.append({
                "month": month_date.strftime("%Y-%m"),
                "total_cost": sum(mr["cost"] for mr in month_maintenance),
                "maintenance_count": len(month_maintenance)
            })
        
        # Budget recommendations
        total_annual_cost = sum(mc["total_cost"] for mc in monthly_costs)
        budget_recommendations = {
            "annual_budget": total_annual_cost * 1.2,  # 20% buffer
            "monthly_budget": (total_annual_cost * 1.2) / 12,
            "high_cost_equipment": [eq for eq in self.mock_data["equipment"] 
                                  if sum(mr["cost"] for mr in self.mock_data["maintenance_records"] 
                                        if mr["equipment_id"] == eq["id"]) > 10000],
            "cost_optimization_opportunities": self._identify_cost_optimization()
        }
        
        return {
            "scenario": "Cost Analysis",
            "query": "Analyze maintenance costs and budget planning",
            "results": {
                "cost_by_equipment_type": cost_by_type,
                "monthly_cost_trend": monthly_costs,
                "total_annual_cost": total_annual_cost,
                "budget_recommendations": budget_recommendations
            }
        }
    
    def run_all_scenarios(self) -> Dict[str, Any]:
        """Run all test scenarios and return comprehensive results."""
        logger.info("Running all test scenarios...")
        
        if not self.mock_data:
            self.load_mock_data()
        
        scenarios = {
            "scenario_1": self.scenario_1_vibration_issues_search(),
            "scenario_2": self.scenario_2_maintenance_schedule_2_weeks(),
            "scenario_3": self.scenario_3_risk_assessment_analysis(),
            "scenario_4": self.scenario_4_dependency_analysis(),
            "scenario_5": self.scenario_5_sensor_analysis(),
            "scenario_6": self.scenario_6_cost_analysis()
        }
        
        # Generate overall summary
        summary = {
            "total_equipment": len(self.mock_data["equipment"]),
            "total_maintenance_records": len(self.mock_data["maintenance_records"]),
            "total_sensors": len(self.mock_data["sensors"]),
            "total_alerts": len(self.mock_data["alerts"]),
            "scenarios_executed": len(scenarios),
            "execution_timestamp": datetime.now().isoformat()
        }
        
        return {
            "summary": summary,
            "scenarios": scenarios
        }
    
    def _calculate_maintenance_priority(self, risk_score: float, days_since_maintenance: int, equipment_type: str) -> Dict[str, Any]:
        """Calculate maintenance priority for equipment."""
        priority_score = (risk_score * 0.4) + (min(days_since_maintenance / 365, 1.0) * 0.6)
        
        if priority_score > 0.8:
            priority = "high"
            maintenance_type = "Corrective"
            estimated_duration = 8
            estimated_cost = 5000
            reason = "High risk equipment requiring immediate attention"
        elif priority_score > 0.6:
            priority = "medium"
            maintenance_type = "Preventive"
            estimated_duration = 4
            estimated_cost = 2000
            reason = "Scheduled preventive maintenance"
        else:
            priority = "low"
            maintenance_type = "Preventive"
            estimated_duration = 2
            estimated_cost = 1000
            reason = "Routine inspection"
        
        return {
            "needs_maintenance": priority_score > 0.4,
            "priority": priority,
            "maintenance_type": maintenance_type,
            "estimated_duration": estimated_duration,
            "estimated_cost": estimated_cost,
            "reason": reason
        }
    
    def _calculate_scheduled_date(self, current_date: datetime, end_date: datetime, priority: str) -> datetime:
        """Calculate scheduled maintenance date based on priority."""
        if priority == "high":
            # Schedule within first 3 days
            days_offset = random.randint(1, 3)
        elif priority == "medium":
            # Schedule within first week
            days_offset = random.randint(4, 7)
        else:
            # Schedule within second week
            days_offset = random.randint(8, 14)
        
        return current_date + timedelta(days=days_offset)
    
    def _get_common_issues(self, records: List[Dict[str, Any]]) -> List[str]:
        """Get common issues from maintenance records."""
        descriptions = [record["description"] for record in records]
        # Simple frequency analysis
        issue_counts = {}
        for desc in descriptions:
            issue_counts[desc] = issue_counts.get(desc, 0) + 1
        
        return sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def _calculate_dependency_strength(self, equipment1: Dict[str, Any], equipment2: Dict[str, Any]) -> float:
        """Calculate dependency strength between equipment."""
        # Simple dependency calculation based on location and type
        strength = 0.0
        
        if equipment1["location"] == equipment2["location"]:
            strength += 0.5
        
        if equipment1["type"] == equipment2["type"]:
            strength += 0.3
        
        # Add some randomness for realistic simulation
        strength += random.uniform(0, 0.2)
        
        return min(strength, 1.0)
    
    def _get_dependency_type(self, equipment1: Dict[str, Any], equipment2: Dict[str, Any]) -> str:
        """Get dependency type between equipment."""
        if equipment1["type"] == equipment2["type"]:
            return "peer"
        elif equipment1["type"] in ["Generator", "Transformer"] and equipment2["type"] in ["Bus", "Link"]:
            return "power_flow"
        else:
            return "operational"
    
    def _calculate_potential_impact(self, equipment: Dict[str, Any], dependencies: List[Dict[str, Any]]) -> str:
        """Calculate potential impact of equipment failure."""
        if len(dependencies) > 5:
            return "high"
        elif len(dependencies) > 2:
            return "medium"
        else:
            return "low"
    
    def _identify_critical_paths(self, dependencies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify critical paths in the dependency graph."""
        critical_paths = []
        for dep in dependencies:
            if dep["total_dependencies"] > 3 and dep["equipment"]["risk_score"] > 6.0:
                critical_paths.append({
                    "equipment": dep["equipment"],
                    "dependency_count": dep["total_dependencies"],
                    "risk_level": "critical"
                })
        return critical_paths
    
    def _get_sensor_recommendation(self, sensor_type: str, ratio: float) -> str:
        """Get recommendation based on sensor anomaly."""
        if sensor_type == "Vibration" and ratio > 1.5:
            return "Schedule immediate maintenance - vibration levels critical"
        elif sensor_type == "Temperature" and ratio > 1.3:
            return "Monitor closely - temperature above normal range"
        elif ratio < 0.7:
            return "Check sensor calibration - readings below expected"
        else:
            return "Continue monitoring - readings within acceptable range"
    
    def _generate_risk_recommendations(self, high_risk_equipment: List[Dict[str, Any]]) -> List[str]:
        """Generate risk mitigation recommendations."""
        recommendations = []
        
        if len(high_risk_equipment) > 10:
            recommendations.append("Consider equipment replacement program for high-risk assets")
        
        if any(eq["risk_score"] > 8.0 for eq in high_risk_equipment):
            recommendations.append("Immediate action required for critical equipment")
        
        recommendations.append("Increase monitoring frequency for high-risk equipment")
        recommendations.append("Develop preventive maintenance schedule for risk mitigation")
        
        return recommendations
    
    def _generate_sensor_recommendations(self, anomalies: List[Dict[str, Any]]) -> List[str]:
        """Generate sensor-related recommendations."""
        recommendations = []
        
        high_severity = [a for a in anomalies if a["severity"] == "high"]
        if high_severity:
            recommendations.append(f"Immediate attention required for {len(high_severity)} critical sensor anomalies")
        
        vibration_anomalies = [a for a in anomalies if a["sensor"]["type"] == "Vibration"]
        if vibration_anomalies:
            recommendations.append("Schedule vibration analysis for affected equipment")
        
        recommendations.append("Review sensor calibration schedules")
        recommendations.append("Consider upgrading sensors with frequent anomalies")
        
        return recommendations
    
    def _identify_cost_optimization(self) -> List[Dict[str, Any]]:
        """Identify cost optimization opportunities."""
        opportunities = []
        
        # Equipment with high maintenance costs
        equipment_costs = {}
        for equipment in self.mock_data["equipment"]:
            equipment_maintenance = [mr for mr in self.mock_data["maintenance_records"] 
                                   if mr["equipment_id"] == equipment["id"]]
            total_cost = sum(mr["cost"] for mr in equipment_maintenance)
            if total_cost > 5000:
                equipment_costs[equipment["id"]] = total_cost
        
        high_cost_equipment = sorted(equipment_costs.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for equipment_id, cost in high_cost_equipment:
            equipment = next(eq for eq in self.mock_data["equipment"] if eq["id"] == equipment_id)
            opportunities.append({
                "equipment": equipment,
                "annual_cost": cost,
                "recommendation": "Consider replacement if cost exceeds 50% of new equipment value"
            })
        
        return opportunities

# Global instance for easy access
test_scenarios = TestScenarios() 
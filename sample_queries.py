"""
Sample Queries for Energy Grid Management Agent
Demonstrates various query capabilities and use cases
"""
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SampleQueries:
    """Sample queries demonstrating Energy Grid Management Agent capabilities."""
    
    def __init__(self):
        self.queries = self._initialize_queries()
    
    def _initialize_queries(self) -> Dict[str, Dict[str, Any]]:
        """Initialize sample queries with descriptions and expected results."""
        return {
            "vibration_issues_search": {
                "title": "Search Equipment with Vibration Issues",
                "description": "Find equipment that presented vibration issues and summarize the descriptions",
                "original_query": "Search equipment that presented vibration issues and list and summarize the description...",
                "cypher_query": """
                MATCH (eq:Generator|Link|Bus)-[:HAS_MAINTENANCE_RECORD]->(mr:MaintenanceRecord)
                WHERE toLower(mr.description) CONTAINS 'vibration'
                WITH eq, mr ORDER BY mr.date DESC
                WITH eq, collect({
                    maint_id: mr.id, 
                    description: mr.description, 
                    date: mr.date, 
                    downtime: mr.downTime,
                    cost: mr.cost
                }) AS vibrationIssues
                RETURN eq{
                    assetType: labels(eq), 
                    vibrationIssues: vibrationIssues, 
                    totalIssues: size(vibrationIssues),
                    totalDowntime: reduce(total = 0, issue in vibrationIssues | total + issue.downtime),
                    totalCost: reduce(total = 0, issue in vibrationIssues | total + issue.cost)
                }
                ORDER BY size(vibrationIssues) DESC
                """,
                "expected_result_type": "equipment_with_vibration_issues",
                "use_case": "Maintenance Analysis",
                "difficulty": "Intermediate"
            },
            
            "maintenance_schedule_2_weeks": {
                "title": "Maintenance Schedule for Next 2 Weeks",
                "description": "Develop a comprehensive maintenance schedule over the next two weeks",
                "original_query": "Can you develop a maintenance schedule over the next two weeks...",
                "cypher_query": """
                MATCH (eq:Generator|Link|Bus|Transformer)
                WHERE eq.lastMaintenance IS NOT NULL
                WITH eq, 
                     duration.between(date(eq.lastMaintenance), date()).days AS daysSinceMaintenance,
                     eq.riskScore AS riskScore
                WHERE daysSinceMaintenance > 180 OR riskScore > 6.0
                WITH eq, daysSinceMaintenance, riskScore,
                     CASE 
                         WHEN riskScore > 7.0 OR daysSinceMaintenance > 365 THEN 'high'
                         WHEN riskScore > 5.0 OR daysSinceMaintenance > 270 THEN 'medium'
                         ELSE 'low'
                     END AS priority
                RETURN eq{
                    assetType: labels(eq),
                    priority: priority,
                    daysSinceMaintenance: daysSinceMaintenance,
                    riskScore: riskScore,
                    recommendedMaintenanceType: CASE 
                        WHEN priority = 'high' THEN 'Corrective'
                        ELSE 'Preventive'
                    END,
                    estimatedDuration: CASE 
                        WHEN priority = 'high' THEN 8
                        WHEN priority = 'medium' THEN 4
                        ELSE 2
                    END,
                    estimatedCost: CASE 
                        WHEN priority = 'high' THEN 5000
                        WHEN priority = 'medium' THEN 2000
                        ELSE 1000
                    END
                }
                ORDER BY priority DESC, daysSinceMaintenance DESC
                """,
                "expected_result_type": "maintenance_schedule",
                "use_case": "Maintenance Planning",
                "difficulty": "Advanced"
            },
            
            "high_risk_equipment": {
                "title": "High Risk Equipment Analysis",
                "description": "Identify and analyze equipment with high risk scores",
                "cypher_query": """
                MATCH (eq:Generator|Link|Bus|Transformer)
                WHERE eq.riskScore >= 7.0
                OPTIONAL MATCH (eq)-[:HAS_MAINTENANCE_RECORD]->(mr:MaintenanceRecord)
                OPTIONAL MATCH (eq)-[:HAS_ALERT]->(alert:Alert)
                WITH eq, 
                     collect(DISTINCT mr) AS maintenanceHistory,
                     collect(DISTINCT alert) AS activeAlerts
                RETURN eq{
                    assetType: labels(eq),
                    riskScore: eq.riskScore,
                    maintenanceCount: size(maintenanceHistory),
                    activeAlerts: size(activeAlerts),
                    lastMaintenance: [mr in maintenanceHistory | mr.date][0],
                    totalDowntime: reduce(total = 0, mr in maintenanceHistory | total + mr.downTime),
                    totalCost: reduce(total = 0, mr in maintenanceHistory | total + mr.cost)
                }
                ORDER BY eq.riskScore DESC
                """,
                "expected_result_type": "high_risk_equipment",
                "use_case": "Risk Assessment",
                "difficulty": "Intermediate"
            },
            
            "equipment_dependencies": {
                "title": "Equipment Dependency Analysis",
                "description": "Analyze equipment dependencies and impact assessment",
                "cypher_query": """
                MATCH (eq:Generator|Link|Bus|Transformer)
                OPTIONAL MATCH (eq)-[:CONNECTED]-(connected:Generator|Link|Bus|Transformer)
                OPTIONAL MATCH (eq)-[:MONITORED_BY]-(sensor:Sensor)
                WITH eq, 
                     collect(DISTINCT connected) AS dependencies,
                     collect(DISTINCT sensor) AS sensors
                WHERE size(dependencies) > 0
                RETURN eq{
                    assetType: labels(eq),
                    dependencyCount: size(dependencies),
                    sensorCount: size(sensors),
                    dependencies: [dep in dependencies | {
                        id: dep.id,
                        type: labels(dep)[0],
                        riskScore: dep.riskScore
                    }],
                    impactLevel: CASE 
                        WHEN size(dependencies) > 5 THEN 'high'
                        WHEN size(dependencies) > 2 THEN 'medium'
                        ELSE 'low'
                    END
                }
                ORDER BY size(dependencies) DESC
                """,
                "expected_result_type": "equipment_dependencies",
                "use_case": "Impact Analysis",
                "difficulty": "Advanced"
            },
            
            "sensor_anomalies": {
                "title": "Sensor Anomaly Detection",
                "description": "Identify sensor readings that are outside normal ranges",
                "cypher_query": """
                MATCH (sensor:Sensor)-[:MONITORED_BY]-(eq:Generator|Link|Bus|Transformer)
                WHERE sensor.measurementValue > sensor.expectedValue * 1.5 
                   OR sensor.measurementValue < sensor.expectedValue * 0.7
                WITH sensor, eq,
                     sensor.measurementValue / sensor.expectedValue AS ratio
                RETURN {
                    sensorId: sensor.id,
                    sensorType: sensor.type,
                    equipmentId: eq.id,
                    equipmentType: labels(eq)[0],
                    measurementValue: sensor.measurementValue,
                    expectedValue: sensor.expectedValue,
                    ratio: ratio,
                    severity: CASE 
                        WHEN ratio > 2.0 OR ratio < 0.5 THEN 'critical'
                        WHEN ratio > 1.5 OR ratio < 0.7 THEN 'high'
                        ELSE 'medium'
                    END,
                    recommendation: CASE 
                        WHEN sensor.type = 'Vibration' AND ratio > 1.5 THEN 'Schedule immediate maintenance'
                        WHEN sensor.type = 'Temperature' AND ratio > 1.3 THEN 'Monitor closely'
                        ELSE 'Check sensor calibration'
                    END
                }
                ORDER BY abs(ratio - 1.0) DESC
                """,
                "expected_result_type": "sensor_anomalies",
                "use_case": "Predictive Maintenance",
                "difficulty": "Intermediate"
            },
            
            "maintenance_cost_analysis": {
                "title": "Maintenance Cost Analysis",
                "description": "Analyze maintenance costs by equipment type and time period",
                "cypher_query": """
                MATCH (eq:Generator|Link|Bus|Transformer)-[:HAS_MAINTENANCE_RECORD]->(mr:MaintenanceRecord)
                WHERE mr.date >= date() - duration({days: 365})
                WITH eq, mr, labels(eq)[0] AS equipmentType
                WITH equipmentType,
                     collect(mr) AS maintenanceRecords,
                     sum(mr.cost) AS totalCost,
                     sum(mr.downTime) AS totalDowntime,
                     avg(mr.cost) AS avgCost
                RETURN {
                    equipmentType: equipmentType,
                    maintenanceCount: size(maintenanceRecords),
                    totalCost: totalCost,
                    averageCost: avgCost,
                    totalDowntime: totalDowntime,
                    costPerHour: totalCost / totalDowntime,
                    costEfficiency: totalCost / size(maintenanceRecords)
                }
                ORDER BY totalCost DESC
                """,
                "expected_result_type": "cost_analysis",
                "use_case": "Budget Planning",
                "difficulty": "Intermediate"
            },
            
            "customer_impact_analysis": {
                "title": "Customer Impact Analysis",
                "description": "Analyze the impact of equipment maintenance on customers",
                "cypher_query": """
                MATCH (customer:Customer)-[:HAS_INSTALLATION]->(install:Installation)
                -[:LINK_HAS_INSTALLATION]-(link:Link)-[:CONNECTED]-(eq:Generator|Link|Bus|Transformer)
                -[:HAS_MAINTENANCE_RECORD]->(mr:MaintenanceRecord)
                WHERE mr.date >= date() - duration({days: 90})
                WITH customer, install, eq, mr
                WITH customer, install,
                     collect({
                         equipmentId: eq.id,
                         equipmentType: labels(eq)[0],
                         maintenanceDate: mr.date,
                         downtime: mr.downTime,
                         cost: mr.cost
                     }) AS maintenanceEvents
                RETURN {
                    customerId: customer.id,
                    customerType: customer.type,
                    installationId: install.installationNumber,
                    affectedMaintenanceEvents: size(maintenanceEvents),
                    totalDowntime: reduce(total = 0, event in maintenanceEvents | total + event.downtime),
                    totalCost: reduce(total = 0, event in maintenanceEvents | total + event.cost),
                    maintenanceEvents: maintenanceEvents
                }
                ORDER BY size(maintenanceEvents) DESC
                """,
                "expected_result_type": "customer_impact",
                "use_case": "Customer Service",
                "difficulty": "Advanced"
            },
            
            "predictive_maintenance_recommendations": {
                "title": "Predictive Maintenance Recommendations",
                "description": "Generate predictive maintenance recommendations based on historical data",
                "cypher_query": """
                MATCH (eq:Generator|Link|Bus|Transformer)
                OPTIONAL MATCH (eq)-[:HAS_MAINTENANCE_RECORD]->(mr:MaintenanceRecord)
                OPTIONAL MATCH (eq)-[:HAS_ALERT]->(alert:Alert)
                OPTIONAL MATCH (eq)-[:MONITORED_BY]-(sensor:Sensor)
                WITH eq, 
                     collect(mr) AS maintenanceHistory,
                     collect(alert) AS alerts,
                     collect(sensor) AS sensors
                WITH eq, maintenanceHistory, alerts, sensors,
                     size(maintenanceHistory) AS maintenanceCount,
                     size(alerts) AS alertCount,
                     size(sensors) AS sensorCount,
                     eq.riskScore AS riskScore
                WHERE maintenanceCount > 0
                WITH eq, maintenanceHistory, alerts, sensors, maintenanceCount, alertCount, sensorCount, riskScore,
                     CASE 
                         WHEN riskScore > 7.0 AND alertCount > 2 THEN 'Immediate'
                         WHEN riskScore > 5.0 OR maintenanceCount > 3 THEN 'High Priority'
                         WHEN alertCount > 0 OR sensorCount > 2 THEN 'Medium Priority'
                         ELSE 'Low Priority'
                     END AS recommendationPriority
                RETURN {
                    equipmentId: eq.id,
                    equipmentType: labels(eq)[0],
                    riskScore: riskScore,
                    maintenanceCount: maintenanceCount,
                    alertCount: alertCount,
                    sensorCount: sensorCount,
                    recommendationPriority: recommendationPriority,
                    recommendedAction: CASE 
                        WHEN recommendationPriority = 'Immediate' THEN 'Schedule emergency maintenance'
                        WHEN recommendationPriority = 'High Priority' THEN 'Schedule preventive maintenance within 1 week'
                        WHEN recommendationPriority = 'Medium Priority' THEN 'Schedule inspection within 2 weeks'
                        ELSE 'Continue monitoring'
                    END,
                    estimatedCost: CASE 
                        WHEN recommendationPriority = 'Immediate' THEN 10000
                        WHEN recommendationPriority = 'High Priority' THEN 5000
                        WHEN recommendationPriority = 'Medium Priority' THEN 2000
                        ELSE 500
                    END
                }
                ORDER BY recommendationPriority DESC, riskScore DESC
                """,
                "expected_result_type": "predictive_recommendations",
                "use_case": "Predictive Maintenance",
                "difficulty": "Advanced"
            }
        }
    
    def get_query(self, query_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific query by name."""
        return self.queries.get(query_name)
    
    def get_all_queries(self) -> Dict[str, Dict[str, Any]]:
        """Get all available queries."""
        return self.queries
    
    def get_queries_by_use_case(self, use_case: str) -> List[Dict[str, Any]]:
        """Get queries filtered by use case."""
        return [
            {"name": name, **query}
            for name, query in self.queries.items()
            if query["use_case"] == use_case
        ]
    
    def get_queries_by_difficulty(self, difficulty: str) -> List[Dict[str, Any]]:
        """Get queries filtered by difficulty level."""
        return [
            {"name": name, **query}
            for name, query in self.queries.items()
            if query["difficulty"] == difficulty
        ]
    
    def execute_query_simulation(self, query_name: str, mock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate query execution with mock data."""
        query = self.get_query(query_name)
        if not query:
            return {"error": f"Query '{query_name}' not found"}
        
        # Simulate query execution based on query type
        if query_name == "vibration_issues_search":
            return self._simulate_vibration_search(mock_data)
        elif query_name == "maintenance_schedule_2_weeks":
            return self._simulate_maintenance_schedule(mock_data)
        elif query_name == "high_risk_equipment":
            return self._simulate_high_risk_analysis(mock_data)
        elif query_name == "equipment_dependencies":
            return self._simulate_dependency_analysis(mock_data)
        elif query_name == "sensor_anomalies":
            return self._simulate_sensor_analysis(mock_data)
        elif query_name == "maintenance_cost_analysis":
            return self._simulate_cost_analysis(mock_data)
        elif query_name == "customer_impact_analysis":
            return self._simulate_customer_impact(mock_data)
        elif query_name == "predictive_maintenance_recommendations":
            return self._simulate_predictive_recommendations(mock_data)
        else:
            return {"error": f"Simulation not implemented for query '{query_name}'"}
    
    def _simulate_vibration_search(self, mock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate vibration issues search query."""
        vibration_records = [
            record for record in mock_data["maintenance_records"]
            if "vibration" in record["description"].lower()
        ]
        
        equipment_with_vibration = []
        for record in vibration_records:
            equipment = next(
                (eq for eq in mock_data["equipment"] if eq["id"] == record["equipment_id"]), 
                None
            )
            if equipment:
                equipment_with_vibration.append({
                    "equipment": equipment,
                    "vibration_issues": [record],
                    "total_issues": 1,
                    "total_downtime": record["downtime_hours"],
                    "total_cost": record["cost"]
                })
        
        return {
            "query_type": "vibration_issues_search",
            "results": equipment_with_vibration,
            "summary": {
                "total_equipment_affected": len(equipment_with_vibration),
                "total_vibration_issues": len(vibration_records),
                "total_downtime": sum(record["downtime_hours"] for record in vibration_records),
                "total_cost": sum(record["cost"] for record in vibration_records)
            }
        }
    
    def _simulate_maintenance_schedule(self, mock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate maintenance schedule query."""
        from datetime import datetime, timedelta
        
        current_date = datetime.now()
        schedule = []
        
        for equipment in mock_data["equipment"]:
            if equipment["last_maintenance"]:
                last_maintenance = datetime.strptime(equipment["last_maintenance"], "%Y-%m-%d")
                days_since = (current_date - last_maintenance).days
                
                if days_since > 180 or equipment["risk_score"] > 6.0:
                    priority = "high" if equipment["risk_score"] > 7.0 or days_since > 365 else "medium"
                    schedule.append({
                        "equipment": equipment,
                        "priority": priority,
                        "days_since_maintenance": days_since,
                        "recommended_maintenance_type": "Corrective" if priority == "high" else "Preventive",
                        "estimated_duration": 8 if priority == "high" else 4,
                        "estimated_cost": 5000 if priority == "high" else 2000
                    })
        
        return {
            "query_type": "maintenance_schedule_2_weeks",
            "results": schedule,
            "summary": {
                "total_tasks": len(schedule),
                "high_priority": len([s for s in schedule if s["priority"] == "high"]),
                "medium_priority": len([s for s in schedule if s["priority"] == "medium"]),
                "total_estimated_cost": sum(s["estimated_cost"] for s in schedule)
            }
        }
    
    def _simulate_high_risk_analysis(self, mock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate high risk equipment analysis."""
        high_risk_equipment = [
            eq for eq in mock_data["equipment"] if eq["risk_score"] >= 7.0
        ]
        
        results = []
        for equipment in high_risk_equipment:
            maintenance_records = [
                mr for mr in mock_data["maintenance_records"] 
                if mr["equipment_id"] == equipment["id"]
            ]
            alerts = [
                alert for alert in mock_data["alerts"] 
                if alert["equipment_id"] == equipment["id"]
            ]
            
            results.append({
                "equipment": equipment,
                "maintenance_count": len(maintenance_records),
                "active_alerts": len(alerts),
                "total_downtime": sum(mr["downtime_hours"] for mr in maintenance_records),
                "total_cost": sum(mr["cost"] for mr in maintenance_records)
            })
        
        return {
            "query_type": "high_risk_equipment",
            "results": results,
            "summary": {
                "total_high_risk_equipment": len(results),
                "average_risk_score": sum(eq["equipment"]["risk_score"] for eq in results) / len(results) if results else 0
            }
        }
    
    def _simulate_dependency_analysis(self, mock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate equipment dependency analysis."""
        dependencies = []
        
        for equipment in mock_data["equipment"]:
            # Simulate dependencies based on location
            dependent_equipment = [
                eq for eq in mock_data["equipment"] 
                if eq["id"] != equipment["id"] and eq["location"] == equipment["location"]
            ]
            
            if dependent_equipment:
                dependencies.append({
                    "equipment": equipment,
                    "dependency_count": len(dependent_equipment),
                    "dependencies": dependent_equipment,
                    "impact_level": "high" if len(dependent_equipment) > 5 else "medium" if len(dependent_equipment) > 2 else "low"
                })
        
        return {
            "query_type": "equipment_dependencies",
            "results": dependencies,
            "summary": {
                "total_equipment_with_dependencies": len(dependencies),
                "average_dependencies": sum(d["dependency_count"] for d in dependencies) / len(dependencies) if dependencies else 0
            }
        }
    
    def _simulate_sensor_analysis(self, mock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate sensor anomaly detection."""
        anomalies = []
        
        for sensor in mock_data["sensors"]:
            ratio = sensor["measurement_value"] / sensor["expected_value"]
            if ratio > 1.5 or ratio < 0.7:
                equipment = next(
                    (eq for eq in mock_data["equipment"] if eq["id"] == sensor["equipment_id"]), 
                    None
                )
                if equipment:
                    anomalies.append({
                        "sensor": sensor,
                        "equipment": equipment,
                        "ratio": ratio,
                        "severity": "critical" if ratio > 2.0 or ratio < 0.5 else "high" if ratio > 1.5 or ratio < 0.7 else "medium"
                    })
        
        return {
            "query_type": "sensor_anomalies",
            "results": anomalies,
            "summary": {
                "total_anomalies": len(anomalies),
                "critical_anomalies": len([a for a in anomalies if a["severity"] == "critical"]),
                "high_anomalies": len([a for a in anomalies if a["severity"] == "high"])
            }
        }
    
    def _simulate_cost_analysis(self, mock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate maintenance cost analysis."""
        cost_by_type = {}
        
        for equipment_type in set(eq["type"] for eq in mock_data["equipment"]):
            type_equipment_ids = [eq["id"] for eq in mock_data["equipment"] if eq["type"] == equipment_type]
            type_maintenance = [
                mr for mr in mock_data["maintenance_records"] 
                if mr["equipment_id"] in type_equipment_ids
            ]
            
            if type_maintenance:
                cost_by_type[equipment_type] = {
                    "maintenance_count": len(type_maintenance),
                    "total_cost": sum(mr["cost"] for mr in type_maintenance),
                    "average_cost": sum(mr["cost"] for mr in type_maintenance) / len(type_maintenance),
                    "total_downtime": sum(mr["downtime_hours"] for mr in type_maintenance)
                }
        
        return {
            "query_type": "maintenance_cost_analysis",
            "results": cost_by_type,
            "summary": {
                "total_cost": sum(data["total_cost"] for data in cost_by_type.values()),
                "equipment_types_analyzed": len(cost_by_type)
            }
        }
    
    def _simulate_customer_impact(self, mock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate customer impact analysis."""
        # This is a simplified simulation - in real implementation would need more complex relationship mapping
        customer_impact = []
        
        for customer in mock_data["customers"]:
            # Simulate impact based on customer type and region
            impact_score = 0
            if customer["type"] == "Industrial":
                impact_score = 3
            elif customer["type"] == "Commercial":
                impact_score = 2
            else:
                impact_score = 1
            
            customer_impact.append({
                "customer": customer,
                "impact_score": impact_score,
                "affected_maintenance_events": impact_score,
                "estimated_downtime": impact_score * 4,  # hours
                "estimated_cost": impact_score * 1000
            })
        
        return {
            "query_type": "customer_impact_analysis",
            "results": customer_impact,
            "summary": {
                "total_customers_affected": len(customer_impact),
                "total_estimated_downtime": sum(c["estimated_downtime"] for c in customer_impact),
                "total_estimated_cost": sum(c["estimated_cost"] for c in customer_impact)
            }
        }
    
    def _simulate_predictive_recommendations(self, mock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate predictive maintenance recommendations."""
        recommendations = []
        
        for equipment in mock_data["equipment"]:
            maintenance_records = [
                mr for mr in mock_data["maintenance_records"] 
                if mr["equipment_id"] == equipment["id"]
            ]
            alerts = [
                alert for alert in mock_data["alerts"] 
                if alert["equipment_id"] == equipment["id"]
            ]
            
            if maintenance_records:
                priority = "Immediate" if equipment["risk_score"] > 7.0 and len(alerts) > 2 else \
                          "High Priority" if equipment["risk_score"] > 5.0 or len(maintenance_records) > 3 else \
                          "Medium Priority" if len(alerts) > 0 else "Low Priority"
                
                recommendations.append({
                    "equipment": equipment,
                    "priority": priority,
                    "maintenance_count": len(maintenance_records),
                    "alert_count": len(alerts),
                    "recommended_action": f"Schedule {priority.lower()} maintenance",
                    "estimated_cost": 10000 if priority == "Immediate" else 5000 if priority == "High Priority" else 2000
                })
        
        return {
            "query_type": "predictive_maintenance_recommendations",
            "results": recommendations,
            "summary": {
                "total_recommendations": len(recommendations),
                "immediate_priority": len([r for r in recommendations if r["priority"] == "Immediate"]),
                "high_priority": len([r for r in recommendations if r["priority"] == "High Priority"]),
                "total_estimated_cost": sum(r["estimated_cost"] for r in recommendations)
            }
        }

# Global instance for easy access
sample_queries = SampleQueries() 
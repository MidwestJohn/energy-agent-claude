"""
Mock Data Generator for Energy Grid Management Agent Testing
"""
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class Equipment:
    """Equipment data structure."""
    id: str
    name: str
    type: str
    location: str
    installation_date: str
    capacity: Optional[float] = None
    voltage: Optional[int] = None
    status: str = "operational"
    risk_score: float = 0.0
    last_maintenance: Optional[str] = None

@dataclass
class MaintenanceRecord:
    """Maintenance record data structure."""
    id: str
    equipment_id: str
    date: str
    type: str  # "Preventive", "Corrective", "Emergency"
    description: str
    description_en: str
    root_cause: Optional[str] = None
    downtime_hours: float = 0.0
    cost: float = 0.0
    technician: str = ""
    status: str = "completed"
    embedding: Optional[List[float]] = None
    embedding_pt: Optional[List[float]] = None

@dataclass
class Sensor:
    """Sensor data structure."""
    id: str
    equipment_id: str
    type: str
    measurement_value: float
    expected_value: float
    measurement_date: str
    status: str = "active"

@dataclass
class Alert:
    """Alert data structure."""
    id: str
    equipment_id: str
    type: str
    severity: str
    date: str
    description: str
    status: str = "active"

@dataclass
class Customer:
    """Customer data structure."""
    id: str
    name: str
    type: str  # "Residential", "Commercial", "Industrial"
    region: str
    installation_id: str

@dataclass
class Installation:
    """Installation data structure."""
    id: str
    installation_number: str
    customer_id: str
    installation_date: str
    type: str
    region: str
    consumption_value: float = 0.0

class MockDataGenerator:
    """Generator for mock energy grid data."""
    
    def __init__(self):
        self.equipment_types = ["Generator", "Transformer", "Bus", "Link", "Switch"]
        self.maintenance_types = ["Preventive", "Corrective", "Emergency"]
        self.sensor_types = ["Temperature", "Vibration", "Pressure", "Current", "Voltage"]
        self.alert_types = ["High Temperature", "Vibration Alert", "Pressure Warning", "Overload"]
        self.regions = ["North", "South", "East", "West", "Central"]
        self.customer_types = ["Residential", "Commercial", "Industrial"]
        
        # Vibration-related issues for specific test scenarios
        self.vibration_issues = [
            "Excessive vibration detected in bearing assembly",
            "Unbalanced rotor causing vibration issues",
            "Misalignment leading to increased vibration levels",
            "Worn bearings resulting in vibration anomalies",
            "Resonance frequency causing equipment vibration"
        ]
        
        # Maintenance schedule scenarios
        self.maintenance_scenarios = [
            "Routine inspection and lubrication",
            "Bearing replacement due to wear",
            "Electrical component testing",
            "Cooling system maintenance",
            "Safety system verification"
        ]
    
    def generate_equipment(self, count: int = 50) -> List[Equipment]:
        """Generate mock equipment data."""
        equipment_list = []
        
        for i in range(count):
            equipment_type = random.choice(self.equipment_types)
            equipment_id = f"{equipment_type.lower()}_{i+1:03d}"
            
            # Generate realistic equipment data
            if equipment_type == "Generator":
                capacity = random.uniform(50, 500)
                voltage = random.choice([110, 220, 380, 660])
            elif equipment_type == "Transformer":
                capacity = random.uniform(100, 1000)
                voltage = random.choice([110, 220, 380, 660, 1100])
            else:
                capacity = None
                voltage = random.choice([110, 220, 380, 660])
            
            # Generate risk score based on equipment age and type
            installation_date = datetime.now() - timedelta(days=random.randint(100, 2000))
            age_factor = (datetime.now() - installation_date).days / 365
            risk_score = min(10.0, age_factor * random.uniform(0.5, 2.0))
            
            equipment = Equipment(
                id=equipment_id,
                name=f"{equipment_type} {i+1}",
                type=equipment_type,
                location=random.choice(self.regions),
                installation_date=installation_date.strftime("%Y-%m-%d"),
                capacity=capacity,
                voltage=voltage,
                status=random.choices(["operational", "maintenance", "faulty"], weights=[0.8, 0.15, 0.05])[0],
                risk_score=round(risk_score, 2),
                last_maintenance=(installation_date + timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d")
            )
            equipment_list.append(equipment)
        
        return equipment_list
    
    def generate_maintenance_records(self, equipment_list: List[Equipment], count: int = 200) -> List[MaintenanceRecord]:
        """Generate mock maintenance records."""
        maintenance_records = []
        
        for i in range(count):
            equipment = random.choice(equipment_list)
            maintenance_date = datetime.now() - timedelta(days=random.randint(1, 365))
            maintenance_type = random.choice(self.maintenance_types)
            
            # Generate realistic maintenance descriptions
            if maintenance_type == "Corrective":
                description = random.choice(self.vibration_issues)
                downtime_hours = random.uniform(2, 48)
                cost = random.uniform(1000, 50000)
            elif maintenance_type == "Preventive":
                description = random.choice(self.maintenance_scenarios)
                downtime_hours = random.uniform(0.5, 8)
                cost = random.uniform(500, 5000)
            else:  # Emergency
                description = "Emergency repair due to critical failure"
                downtime_hours = random.uniform(4, 72)
                cost = random.uniform(5000, 100000)
            
            # Generate English description
            description_en = self._translate_to_english(description)
            
            # Generate root cause for corrective maintenance
            root_cause = None
            if maintenance_type == "Corrective":
                root_causes = [
                    "Wear and tear", "Manufacturing defect", "Environmental factors",
                    "Operator error", "Design flaw", "Material fatigue"
                ]
                root_cause = random.choice(root_causes)
            
            maintenance_record = MaintenanceRecord(
                id=f"maint_{i+1:04d}",
                equipment_id=equipment.id,
                date=maintenance_date.strftime("%Y-%m-%d"),
                type=maintenance_type,
                description=description,
                description_en=description_en,
                root_cause=root_cause,
                downtime_hours=round(downtime_hours, 2),
                cost=round(cost, 2),
                technician=f"Tech_{random.randint(1, 20):02d}",
                status="completed"
            )
            maintenance_records.append(maintenance_record)
        
        return maintenance_records
    
    def generate_sensors(self, equipment_list: List[Equipment], count: int = 150) -> List[Sensor]:
        """Generate mock sensor data."""
        sensors = []
        
        for i in range(count):
            equipment = random.choice(equipment_list)
            sensor_type = random.choice(self.sensor_types)
            measurement_date = datetime.now() - timedelta(hours=random.randint(1, 168))
            
            # Generate realistic sensor values
            if sensor_type == "Vibration":
                expected_value = random.uniform(0.1, 2.0)
                measurement_value = expected_value * random.uniform(0.8, 3.0)  # Allow for anomalies
            elif sensor_type == "Temperature":
                expected_value = random.uniform(40, 80)
                measurement_value = expected_value * random.uniform(0.9, 1.3)
            elif sensor_type == "Pressure":
                expected_value = random.uniform(100, 500)
                measurement_value = expected_value * random.uniform(0.85, 1.2)
            else:
                expected_value = random.uniform(100, 1000)
                measurement_value = expected_value * random.uniform(0.9, 1.1)
            
            sensor = Sensor(
                id=f"sensor_{i+1:04d}",
                equipment_id=equipment.id,
                type=sensor_type,
                measurement_value=round(measurement_value, 2),
                expected_value=round(expected_value, 2),
                measurement_date=measurement_date.strftime("%Y-%m-%d %H:%M:%S"),
                status=random.choices(["active", "inactive", "faulty"], weights=[0.9, 0.08, 0.02])[0]
            )
            sensors.append(sensor)
        
        return sensors
    
    def generate_alerts(self, equipment_list: List[Equipment], count: int = 50) -> List[Alert]:
        """Generate mock alert data."""
        alerts = []
        
        for i in range(count):
            equipment = random.choice(equipment_list)
            alert_date = datetime.now() - timedelta(hours=random.randint(1, 168))
            alert_type = random.choice(self.alert_types)
            severity = random.choices(["Low", "Medium", "High", "Critical"], weights=[0.4, 0.3, 0.2, 0.1])[0]
            
            # Generate alert descriptions
            if alert_type == "Vibration Alert":
                description = "Vibration levels exceeded normal operating range"
            elif alert_type == "High Temperature":
                description = "Equipment temperature above recommended threshold"
            elif alert_type == "Pressure Warning":
                description = "System pressure outside normal operating parameters"
            else:
                description = "Equipment overload detected"
            
            alert = Alert(
                id=f"alert_{i+1:04d}",
                equipment_id=equipment.id,
                type=alert_type,
                severity=severity,
                date=alert_date.strftime("%Y-%m-%d %H:%M:%S"),
                description=description,
                status=random.choices(["active", "acknowledged", "resolved"], weights=[0.3, 0.4, 0.3])[0]
            )
            alerts.append(alert)
        
        return alerts
    
    def generate_customers(self, count: int = 30) -> List[Customer]:
        """Generate mock customer data."""
        customers = []
        
        for i in range(count):
            customer_type = random.choice(self.customer_types)
            customer_id = f"customer_{i+1:03d}"
            
            customer = Customer(
                id=customer_id,
                name=f"{customer_type} Customer {i+1}",
                type=customer_type,
                region=random.choice(self.regions),
                installation_id=f"install_{i+1:03d}"
            )
            customers.append(customer)
        
        return customers
    
    def generate_installations(self, customers: List[Customer]) -> List[Installation]:
        """Generate mock installation data."""
        installations = []
        
        for customer in customers:
            installation_date = datetime.now() - timedelta(days=random.randint(100, 1000))
            
            installation = Installation(
                id=customer.installation_id,
                installation_number=customer.installation_id,
                customer_id=customer.id,
                installation_date=installation_date.strftime("%Y-%m-%d"),
                type=customer.type,
                region=customer.region,
                consumption_value=random.uniform(100, 10000)
            )
            installations.append(installation)
        
        return installations
    
    def generate_all_data(self) -> Dict[str, List[Any]]:
        """Generate complete mock dataset."""
        logger.info("Generating mock data for Energy Grid Management Agent...")
        
        # Generate base data
        equipment_list = self.generate_equipment(50)
        customers = self.generate_customers(30)
        installations = self.generate_installations(customers)
        
        # Generate dependent data
        maintenance_records = self.generate_maintenance_records(equipment_list, 200)
        sensors = self.generate_sensors(equipment_list, 150)
        alerts = self.generate_alerts(equipment_list, 50)
        
        # Create relationships
        relationships = self._generate_relationships(equipment_list, customers, installations)
        
        return {
            "equipment": [asdict(eq) for eq in equipment_list],
            "maintenance_records": [asdict(mr) for mr in maintenance_records],
            "sensors": [asdict(sensor) for sensor in sensors],
            "alerts": [asdict(alert) for alert in alerts],
            "customers": [asdict(customer) for customer in customers],
            "installations": [asdict(install) for install in installations],
            "relationships": relationships
        }
    
    def _generate_relationships(self, equipment: List[Equipment], 
                              customers: List[Customer], 
                              installations: List[Installation]) -> List[Dict[str, Any]]:
        """Generate relationship data between entities."""
        relationships = []
        
        # Equipment to maintenance records
        for equipment_item in equipment:
            relationships.append({
                "source": {"id": equipment_item.id, "type": equipment_item.type},
                "target": {"id": f"maint_{equipment_item.id}", "type": "MaintenanceRecord"},
                "relationship": "HAS_MAINTENANCE_RECORD"
            })
        
        # Equipment to sensors
        for equipment_item in equipment:
            relationships.append({
                "source": {"id": equipment_item.id, "type": equipment_item.type},
                "target": {"id": f"sensor_{equipment_item.id}", "type": "Sensor"},
                "relationship": "MONITORED_BY"
            })
        
        # Equipment to alerts
        for equipment_item in equipment:
            relationships.append({
                "source": {"id": equipment_item.id, "type": equipment_item.type},
                "target": {"id": f"alert_{equipment_item.id}", "type": "Alert"},
                "relationship": "HAS_ALERT"
            })
        
        # Customer to installation
        for customer in customers:
            relationships.append({
                "source": {"id": customer.id, "type": "Customer"},
                "target": {"id": customer.installation_id, "type": "Installation"},
                "relationship": "HAS_INSTALLATION"
            })
        
        return relationships
    
    def _translate_to_english(self, description: str) -> str:
        """Simple translation to English for mock data."""
        translations = {
            "Excessive vibration detected in bearing assembly": "Excessive vibration detected in bearing assembly",
            "Unbalanced rotor causing vibration issues": "Unbalanced rotor causing vibration issues",
            "Misalignment leading to increased vibration levels": "Misalignment leading to increased vibration levels",
            "Worn bearings resulting in vibration anomalies": "Worn bearings resulting in vibration anomalies",
            "Resonance frequency causing equipment vibration": "Resonance frequency causing equipment vibration",
            "Routine inspection and lubrication": "Routine inspection and lubrication",
            "Bearing replacement due to wear": "Bearing replacement due to wear",
            "Electrical component testing": "Electrical component testing",
            "Cooling system maintenance": "Cooling system maintenance",
            "Safety system verification": "Safety system verification"
        }
        return translations.get(description, description)
    
    def save_to_json(self, data: Dict[str, List[Any]], filename: str = "mock_data.json"):
        """Save mock data to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Mock data saved to {filename}")
    
    def load_from_json(self, filename: str = "mock_data.json") -> Dict[str, List[Any]]:
        """Load mock data from JSON file."""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Mock data loaded from {filename}")
        return data

# Global instance for easy access
mock_generator = MockDataGenerator() 
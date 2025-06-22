# Testing Documentation

## Energy Grid Management Agent - Testing Guide

This document provides comprehensive guidance for testing the Energy Grid Management Agent application, including test scenarios, sample queries, and mock data generation.

## Table of Contents

1. [Overview](#overview)
2. [Test Data Generation](#test-data-generation)
3. [Test Scenarios](#test-scenarios)
4. [Sample Queries](#sample-queries)
5. [Demo Execution](#demo-execution)
6. [Running Tests](#running-tests)
7. [Expected Results](#expected-results)
8. [Troubleshooting](#troubleshooting)

## Overview

The Energy Grid Management Agent includes a comprehensive testing framework that allows you to:

- **Generate realistic mock data** without requiring a live Neo4j database
- **Test all application capabilities** through predefined scenarios
- **Execute sample queries** that demonstrate real-world use cases
- **Run the exact Neo4j demo queries** from the original demonstration
- **Validate application functionality** before production deployment

## Test Data Generation

### Mock Data Structure

The mock data generator creates realistic energy grid data including:

```python
# Equipment Data
{
    "id": "generator_001",
    "name": "Generator 1",
    "type": "Generator",
    "location": "North",
    "installation_date": "2020-01-15",
    "capacity": 250.5,
    "voltage": 380,
    "status": "operational",
    "risk_score": 6.8,
    "last_maintenance": "2024-01-15"
}

# Maintenance Records
{
    "id": "maint_0001",
    "equipment_id": "generator_001",
    "date": "2024-01-15",
    "type": "Corrective",
    "description": "Excessive vibration detected in bearing assembly",
    "description_en": "Excessive vibration detected in bearing assembly",
    "root_cause": "Wear and tear",
    "downtime_hours": 12.5,
    "cost": 8500.0,
    "technician": "Tech_05",
    "status": "completed"
}

# Sensor Data
{
    "id": "sensor_0001",
    "equipment_id": "generator_001",
    "type": "Vibration",
    "measurement_value": 2.8,
    "expected_value": 1.2,
    "measurement_date": "2024-12-19 14:30:00",
    "status": "active"
}
```

### Generating Mock Data

```python
from test_data_generator import MockDataGenerator

# Create generator instance
generator = MockDataGenerator()

# Generate complete dataset
mock_data = generator.generate_all_data()

# Save to file
generator.save_to_json(mock_data, "mock_data.json")

# Load from file
loaded_data = generator.load_from_json("mock_data.json")
```

### Data Volume

The default mock data includes:
- **50 Equipment** (Generators, Transformers, Buses, Links, Switches)
- **200 Maintenance Records** (Preventive, Corrective, Emergency)
- **150 Sensors** (Temperature, Vibration, Pressure, Current, Voltage)
- **50 Alerts** (Various severity levels)
- **30 Customers** (Residential, Commercial, Industrial)
- **30 Installations** (Linked to customers)

## Test Scenarios

### Scenario 1: Vibration Issues Search

**Original Query**: "Search equipment that presented vibration issues and list and summarize the description..."

**Purpose**: Demonstrates equipment analysis and maintenance record filtering

**Expected Results**:
- Equipment with vibration-related maintenance records
- Summary statistics (total issues, downtime, costs)
- Common vibration issues identified

```python
from test_scenarios import TestScenarios

scenarios = TestScenarios()
scenarios.load_mock_data()

# Run vibration issues scenario
result = scenarios.scenario_1_vibration_issues_search()
print(f"Equipment with vibration issues: {len(result['results']['equipment_details'])}")
```

### Scenario 2: Maintenance Schedule for Next 2 Weeks

**Original Query**: "Can you develop a maintenance schedule over the next two weeks..."

**Purpose**: Demonstrates predictive maintenance planning

**Expected Results**:
- Prioritized maintenance tasks
- Week-by-week scheduling
- Cost and duration estimates

```python
# Run maintenance schedule scenario
result = scenarios.scenario_2_maintenance_schedule_2_weeks()
print(f"Total maintenance tasks: {result['results']['total_maintenance_tasks']}")
```

### Scenario 3: Risk Assessment Analysis

**Purpose**: Demonstrates equipment risk evaluation

**Expected Results**:
- Risk distribution (high, medium, low)
- High-risk equipment details
- Risk mitigation recommendations

### Scenario 4: Dependency Analysis

**Purpose**: Demonstrates equipment relationship mapping

**Expected Results**:
- Equipment dependencies
- Impact assessment
- Critical path identification

### Scenario 5: Sensor Analysis

**Purpose**: Demonstrates sensor monitoring and anomaly detection

**Expected Results**:
- Sensor anomalies identified
- Performance metrics by sensor type
- Maintenance recommendations

### Scenario 6: Cost Analysis

**Purpose**: Demonstrates financial analysis and budgeting

**Expected Results**:
- Cost breakdown by equipment type
- Monthly cost trends
- Budget recommendations

## Sample Queries

### Available Queries

The application includes 8 sample queries covering different use cases:

1. **Vibration Issues Search** (Maintenance Analysis)
2. **Maintenance Schedule for Next 2 Weeks** (Maintenance Planning)
3. **High Risk Equipment Analysis** (Risk Assessment)
4. **Equipment Dependency Analysis** (Impact Analysis)
5. **Sensor Anomaly Detection** (Predictive Maintenance)
6. **Maintenance Cost Analysis** (Budget Planning)
7. **Customer Impact Analysis** (Customer Service)
8. **Predictive Maintenance Recommendations** (Predictive Maintenance)

### Query Execution

```python
from sample_queries import SampleQueries

queries = SampleQueries()

# Get all available queries
all_queries = queries.get_all_queries()

# Execute specific query
result = queries.execute_query_simulation("vibration_issues_search", mock_data)

# Get queries by use case
maintenance_queries = queries.get_queries_by_use_case("Maintenance Analysis")

# Get queries by difficulty
intermediate_queries = queries.get_queries_by_difficulty("Intermediate")
```

### Cypher Queries

Each sample query includes the corresponding Neo4j Cypher query:

```cypher
-- Vibration Issues Search
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
```

## Demo Execution

### Running the Complete Demo

```bash
# Execute the full demo
python test_demo.py
```

This will:
1. Generate or load mock data
2. Run all test scenarios
3. Execute Neo4j demo queries
4. Run all sample queries
5. Generate comprehensive reports

### Generated Files

The demo creates several output files:

- `mock_data.json` - Complete mock dataset
- `demo_results.json` - Test scenario results
- `neo4j_demo_results.json` - Neo4j demo query results
- `all_query_results.json` - All sample query results
- `demo_report.md` - Comprehensive demo report

### Demo Report

The demo generates a detailed markdown report including:

- Executive summary
- Data overview
- Query results
- Key features demonstrated
- Technical capabilities
- Recommendations

## Running Tests

### Individual Test Execution

```python
# Test specific scenario
from test_scenarios import TestScenarios

scenarios = TestScenarios()
scenarios.load_mock_data()

# Run individual scenario
vibration_result = scenarios.scenario_1_vibration_issues_search()
print(vibration_result['results']['total_vibration_issues'])

# Run all scenarios
all_results = scenarios.run_all_scenarios()
```

### Query Testing

```python
# Test specific query
from sample_queries import SampleQueries

queries = SampleQueries()
mock_data = MockDataGenerator().generate_all_data()

# Test vibration search
result = queries.execute_query_simulation("vibration_issues_search", mock_data)
print(f"Equipment affected: {result['summary']['total_equipment_affected']}")
```

### Data Validation

```python
# Validate mock data structure
from test_data_generator import MockDataGenerator

generator = MockDataGenerator()
data = generator.generate_all_data()

# Check data integrity
assert len(data['equipment']) > 0, "Equipment data is empty"
assert len(data['maintenance_records']) > 0, "Maintenance records are empty"
assert all('id' in eq for eq in data['equipment']), "Equipment missing IDs"
```

## Expected Results

### Vibration Issues Search

**Expected Output**:
```json
{
  "query_type": "vibration_issues_search",
  "results": [
    {
      "equipment": {
        "id": "generator_001",
        "name": "Generator 1",
        "type": "Generator",
        "risk_score": 6.8
      },
      "vibration_issues": [...],
      "total_issues": 3,
      "total_downtime": 24.5,
      "total_cost": 15000.0
    }
  ],
  "summary": {
    "total_equipment_affected": 15,
    "total_vibration_issues": 25,
    "total_downtime": 120.5,
    "total_cost": 75000.0
  }
}
```

### Maintenance Schedule

**Expected Output**:
```json
{
  "query_type": "maintenance_schedule_2_weeks",
  "results": [
    {
      "equipment": {...},
      "priority": "high",
      "days_since_maintenance": 400,
      "recommended_maintenance_type": "Corrective",
      "estimated_duration": 8,
      "estimated_cost": 5000
    }
  ],
  "summary": {
    "total_tasks": 25,
    "high_priority": 8,
    "medium_priority": 12,
    "total_estimated_cost": 85000
  }
}
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```python
# Ensure all dependencies are installed
pip install pandas numpy

# Check import paths
import sys
sys.path.append('.')
```

#### 2. Data Generation Issues

```python
# Regenerate mock data if corrupted
import os
if os.path.exists("mock_data.json"):
    os.remove("mock_data.json")

generator = MockDataGenerator()
data = generator.generate_all_data()
generator.save_to_json(data, "mock_data.json")
```

#### 3. Query Execution Errors

```python
# Validate mock data before query execution
def validate_mock_data(data):
    required_keys = ['equipment', 'maintenance_records', 'sensors', 'alerts']
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")
        if not isinstance(data[key], list):
            raise ValueError(f"Key {key} must be a list")
```

#### 4. Performance Issues

```python
# For large datasets, use sampling
def sample_data(data, sample_size=100):
    return {
        key: value[:sample_size] if isinstance(value, list) else value
        for key, value in data.items()
    }

# Use sampled data for testing
sampled_data = sample_data(mock_data, 50)
```

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run demo with debug output
demo = EnergyAgentDemo()
demo.setup_demo()
```

### Data Validation

```python
# Validate data structure
def validate_equipment_data(equipment_list):
    for equipment in equipment_list:
        required_fields = ['id', 'name', 'type', 'risk_score']
        for field in required_fields:
            if field not in equipment:
                print(f"Missing field {field} in equipment {equipment.get('id', 'unknown')}")

# Run validation
validate_equipment_data(mock_data['equipment'])
```

## Best Practices

### 1. Data Management

- Always validate mock data before use
- Use consistent data formats across tests
- Clean up test files after execution

### 2. Query Testing

- Test queries with different data scenarios
- Validate query results for expected structure
- Test edge cases and error conditions

### 3. Performance Testing

- Monitor execution time for large datasets
- Use sampling for quick testing
- Profile memory usage for optimization

### 4. Documentation

- Document any custom test scenarios
- Update expected results when data changes
- Maintain test data versioning

## Conclusion

The testing framework provides comprehensive validation of the Energy Grid Management Agent's capabilities. By following this guide, you can:

- **Validate application functionality** before deployment
- **Demonstrate capabilities** to stakeholders
- **Test edge cases** and error conditions
- **Ensure data quality** and consistency
- **Generate comprehensive reports** for analysis

The mock data generation and test scenarios enable thorough testing without requiring live database connections, making it ideal for development, demonstration, and validation purposes. 
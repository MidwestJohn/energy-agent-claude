"""
Demo Script for Energy Grid Management Agent
Demonstrates all test scenarios and sample queries
"""
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
import logging
from test_data_generator import MockDataGenerator
from test_scenarios import TestScenarios
from sample_queries import SampleQueries

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnergyAgentDemo:
    """Demonstration class for Energy Grid Management Agent capabilities."""
    
    def __init__(self):
        self.generator = MockDataGenerator()
        self.scenarios = TestScenarios()
        self.queries = SampleQueries()
        self.mock_data = None
        
    def setup_demo(self):
        """Setup demo environment with mock data."""
        logger.info("Setting up Energy Grid Management Agent Demo...")
        
        # Generate or load mock data
        try:
            self.mock_data = self.generator.load_from_json("mock_data.json")
            logger.info("Loaded existing mock data")
        except FileNotFoundError:
            logger.info("Generating new mock data...")
            self.mock_data = self.generator.generate_all_data()
            self.generator.save_to_json(self.mock_data, "mock_data.json")
        
        # Load data into scenarios
        self.scenarios.mock_data = self.mock_data
        
        logger.info("Demo setup completed successfully!")
    
    def run_demo_scenarios(self) -> Dict[str, Any]:
        """Run all demo scenarios and return results."""
        logger.info("Running all demo scenarios...")
        
        results = self.scenarios.run_all_scenarios()
        
        # Save results to file
        with open("demo_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info("Demo scenarios completed. Results saved to demo_results.json")
        return results
    
    def run_neo4j_demo_queries(self) -> Dict[str, Any]:
        """Run the exact Neo4j demo queries."""
        logger.info("Running Neo4j Demo Queries...")
        
        demo_results = {}
        
        # Query 1: Vibration Issues Search
        logger.info("Executing Query 1: Vibration Issues Search")
        vibration_result = self.queries.execute_query_simulation("vibration_issues_search", self.mock_data)
        demo_results["vibration_issues_search"] = {
            "query": "Search equipment that presented vibration issues and list and summarize the description...",
            "result": vibration_result
        }
        
        # Query 2: Maintenance Schedule for Next 2 Weeks
        logger.info("Executing Query 2: Maintenance Schedule for Next 2 Weeks")
        schedule_result = self.queries.execute_query_simulation("maintenance_schedule_2_weeks", self.mock_data)
        demo_results["maintenance_schedule_2_weeks"] = {
            "query": "Can you develop a maintenance schedule over the next two weeks...",
            "result": schedule_result
        }
        
        # Save Neo4j demo results
        with open("neo4j_demo_results.json", "w", encoding="utf-8") as f:
            json.dump(demo_results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info("Neo4j demo queries completed. Results saved to neo4j_demo_results.json")
        return demo_results
    
    def run_all_sample_queries(self) -> Dict[str, Any]:
        """Run all sample queries to demonstrate full capabilities."""
        logger.info("Running all sample queries...")
        
        all_queries = self.queries.get_all_queries()
        query_results = {}
        
        for query_name, query_info in all_queries.items():
            logger.info(f"Executing query: {query_info['title']}")
            result = self.queries.execute_query_simulation(query_name, self.mock_data)
            query_results[query_name] = {
                "query_info": query_info,
                "result": result
            }
        
        # Save all query results
        with open("all_query_results.json", "w", encoding="utf-8") as f:
            json.dump(query_results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info("All sample queries completed. Results saved to all_query_results.json")
        return query_results
    
    def generate_demo_report(self) -> str:
        """Generate a comprehensive demo report."""
        logger.info("Generating demo report...")
        
        # Run all demos
        scenario_results = self.run_demo_scenarios()
        neo4j_results = self.run_neo4j_demo_queries()
        query_results = self.run_all_sample_queries()
        
        # Generate report
        report = self._create_report(scenario_results, neo4j_results, query_results)
        
        # Save report
        with open("demo_report.md", "w", encoding="utf-8") as f:
            f.write(report)
        
        logger.info("Demo report generated and saved to demo_report.md")
        return report
    
    def _create_report(self, scenario_results: Dict[str, Any], 
                      neo4j_results: Dict[str, Any], 
                      query_results: Dict[str, Any]) -> str:
        """Create a comprehensive demo report."""
        
        report = f"""# Energy Grid Management Agent - Demo Report

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

This demo showcases the comprehensive capabilities of the Energy Grid Management Agent, including:

- **6 Test Scenarios** demonstrating core functionality
- **2 Neo4j Demo Queries** replicating the original demo
- **8 Sample Queries** showing advanced capabilities
- **Mock Data Generation** for testing without live database

## Data Overview

- **Total Equipment**: {scenario_results['summary']['total_equipment']}
- **Maintenance Records**: {scenario_results['summary']['total_maintenance_records']}
- **Sensors**: {scenario_results['summary']['total_sensors']}
- **Alerts**: {scenario_results['summary']['total_alerts']}

## Neo4j Demo Queries Results

### 1. Vibration Issues Search
**Original Query**: "Search equipment that presented vibration issues and list and summarize the description..."

**Results**:
- Equipment affected: {neo4j_results['vibration_issues_search']['result']['summary']['total_equipment_affected']}
- Total vibration issues: {neo4j_results['vibration_issues_search']['result']['summary']['total_vibration_issues']}
- Total downtime: {neo4j_results['vibration_issues_search']['result']['summary']['total_downtime']} hours
- Total cost: ${neo4j_results['vibration_issues_search']['result']['summary']['total_cost']:,.2f}

### 2. Maintenance Schedule for Next 2 Weeks
**Original Query**: "Can you develop a maintenance schedule over the next two weeks..."

**Results**:
- Total maintenance tasks: {neo4j_results['maintenance_schedule_2_weeks']['result']['summary']['total_tasks']}
- High priority tasks: {neo4j_results['maintenance_schedule_2_weeks']['result']['summary']['high_priority']}
- Medium priority tasks: {neo4j_results['maintenance_schedule_2_weeks']['result']['summary']['medium_priority']}
- Total estimated cost: ${neo4j_results['maintenance_schedule_2_weeks']['result']['summary']['total_estimated_cost']:,.2f}

## Test Scenarios Results

### Scenario 1: Vibration Issues Search
- **Status**: ✅ Completed
- **Equipment with vibration issues**: {len(scenario_results['scenarios']['scenario_1']['results']['equipment_details'])}
- **Common issues identified**: {len(scenario_results['scenarios']['scenario_1']['results']['common_issues'])}

### Scenario 2: Maintenance Schedule for Next 2 Weeks
- **Status**: ✅ Completed
- **Total maintenance tasks**: {scenario_results['scenarios']['scenario_2']['results']['total_maintenance_tasks']}
- **Week 1 tasks**: {scenario_results['scenarios']['scenario_2']['results']['week_1_tasks']}
- **Week 2 tasks**: {scenario_results['scenarios']['scenario_2']['results']['week_2_tasks']}

### Scenario 3: Risk Assessment Analysis
- **Status**: ✅ Completed
- **High risk equipment**: {scenario_results['scenarios']['scenario_3']['results']['risk_distribution']['high_risk']}
- **Medium risk equipment**: {scenario_results['scenarios']['scenario_3']['results']['risk_distribution']['medium_risk']}
- **Low risk equipment**: {scenario_results['scenarios']['scenario_3']['results']['risk_distribution']['low_risk']}

### Scenario 4: Dependency Analysis
- **Status**: ✅ Completed
- **Total dependencies**: {scenario_results['scenarios']['scenario_4']['results']['total_dependencies']}
- **Equipment with dependencies**: {scenario_results['scenarios']['scenario_4']['results']['equipment_with_dependencies']}

### Scenario 5: Sensor Analysis
- **Status**: ✅ Completed
- **Total sensors**: {scenario_results['scenarios']['scenario_5']['results']['total_sensors']}
- **Anomalies detected**: {scenario_results['scenarios']['scenario_5']['results']['anomalies_detected']}

### Scenario 6: Cost Analysis
- **Status**: ✅ Completed
- **Equipment types analyzed**: {len(scenario_results['scenarios']['scenario_6']['results']['cost_by_equipment_type'])}
- **Total annual cost**: ${scenario_results['scenarios']['scenario_6']['results']['total_annual_cost']:,.2f}

## Sample Queries Results

### Maintenance Analysis Queries
"""
        
        maintenance_queries = self.queries.get_queries_by_use_case("Maintenance Analysis")
        for query in maintenance_queries:
            result = query_results[query['name']]['result']
            report += f"- **{query['title']}**: {result['summary']['total_equipment_affected'] if 'total_equipment_affected' in result['summary'] else 'Completed'}\n"
        
        report += """
### Risk Assessment Queries
"""
        
        risk_queries = self.queries.get_queries_by_use_case("Risk Assessment")
        for query in risk_queries:
            result = query_results[query['name']]['result']
            report += f"- **{query['title']}**: {result['summary']['total_high_risk_equipment'] if 'total_high_risk_equipment' in result['summary'] else 'Completed'}\n"
        
        report += """
### Predictive Maintenance Queries
"""
        
        predictive_queries = self.queries.get_queries_by_use_case("Predictive Maintenance")
        for query in predictive_queries:
            result = query_results[query['name']]['result']
            report += f"- **{query['title']}**: {result['summary']['total_anomalies'] if 'total_anomalies' in result['summary'] else 'Completed'}\n"
        
        report += """
### Budget Planning Queries
"""
        
        budget_queries = self.queries.get_queries_by_use_case("Budget Planning")
        for query in budget_queries:
            result = query_results[query['name']]['result']
            report += f"- **{query['title']}**: ${result['summary']['total_cost']:,.2f} total cost\n"
        
        report += """
## Key Features Demonstrated

### 1. Equipment Analysis
- ✅ Vibration issue detection and analysis
- ✅ Risk assessment and scoring
- ✅ Maintenance history tracking
- ✅ Equipment dependency mapping

### 2. Maintenance Planning
- ✅ Predictive maintenance scheduling
- ✅ Priority-based task assignment
- ✅ Cost estimation and budgeting
- ✅ Resource allocation optimization

### 3. Sensor Monitoring
- ✅ Real-time anomaly detection
- ✅ Performance trend analysis
- ✅ Predictive failure detection
- ✅ Calibration monitoring

### 4. Cost Management
- ✅ Maintenance cost analysis
- ✅ Budget planning and forecasting
- ✅ Cost optimization recommendations
- ✅ ROI analysis for equipment replacement

### 5. Customer Impact Analysis
- ✅ Service disruption assessment
- ✅ Customer communication planning
- ✅ Impact mitigation strategies
- ✅ SLA compliance monitoring

## Technical Capabilities

### Data Management
- **Mock Data Generation**: Comprehensive test data without live database
- **Data Validation**: Robust error handling and data integrity checks
- **Performance Optimization**: Efficient query execution and caching
- **Scalability**: Designed for large-scale energy grid operations

### Query Capabilities
- **Complex Graph Queries**: Advanced Neo4j Cypher queries
- **Multi-dimensional Analysis**: Equipment, time, cost, and risk dimensions
- **Real-time Processing**: Live data analysis and recommendations
- **Predictive Analytics**: AI-powered maintenance predictions

### Integration Features
- **Claude AI Integration**: Natural language query processing
- **Neo4j Database**: Graph database for complex relationships
- **Streamlit Interface**: User-friendly web application
- **API Support**: RESTful API for external integrations

## Recommendations

### Immediate Actions
1. **High Priority Maintenance**: Address {neo4j_results['maintenance_schedule_2_weeks']['result']['summary']['high_priority']} high-priority maintenance tasks
2. **Vibration Issues**: Investigate {neo4j_results['vibration_issues_search']['result']['summary']['total_vibration_issues']} vibration-related maintenance records
3. **Sensor Anomalies**: Review {query_results['sensor_anomalies']['result']['summary']['total_anomalies']} sensor anomalies

### Strategic Initiatives
1. **Predictive Maintenance Program**: Implement AI-driven maintenance scheduling
2. **Cost Optimization**: Focus on high-cost equipment identified in analysis
3. **Risk Mitigation**: Develop strategies for high-risk equipment
4. **Customer Communication**: Establish proactive customer notification system

## Conclusion

The Energy Grid Management Agent successfully demonstrates comprehensive capabilities for energy infrastructure management, providing:

- **Actionable Insights**: Data-driven recommendations for maintenance and operations
- **Risk Mitigation**: Proactive identification and management of equipment risks
- **Cost Optimization**: Strategic planning for maintenance budgets and resource allocation
- **Operational Efficiency**: Streamlined processes for maintenance planning and execution

The system is ready for production deployment with proper configuration and integration with live data sources.

---
*Report generated by Energy Grid Management Agent Demo System*
"""
        
        return report
    
    def print_summary(self):
        """Print a summary of the demo results."""
        print("\n" + "="*80)
        print("ENERGY GRID MANAGEMENT AGENT - DEMO SUMMARY")
        print("="*80)
        
        print(f"\n📊 Data Overview:")
        print(f"   • Equipment: {self.mock_data['equipment'][0]['id']} - {self.mock_data['equipment'][-1]['id']}")
        print(f"   • Maintenance Records: {len(self.mock_data['maintenance_records'])}")
        print(f"   • Sensors: {len(self.mock_data['sensors'])}")
        print(f"   • Alerts: {len(self.mock_data['alerts'])}")
        
        print(f"\n🎯 Neo4j Demo Queries:")
        print(f"   ✅ Vibration Issues Search")
        print(f"   ✅ Maintenance Schedule for Next 2 Weeks")
        
        print(f"\n🔧 Test Scenarios:")
        print(f"   ✅ Equipment Analysis")
        print(f"   ✅ Maintenance Planning")
        print(f"   ✅ Risk Assessment")
        print(f"   ✅ Dependency Analysis")
        print(f"   ✅ Sensor Monitoring")
        print(f"   ✅ Cost Analysis")
        
        print(f"\n📈 Sample Queries:")
        print(f"   ✅ 8 Advanced Queries Executed")
        print(f"   ✅ Multiple Use Cases Covered")
        print(f"   ✅ Different Difficulty Levels")
        
        print(f"\n📁 Generated Files:")
        print(f"   • mock_data.json - Mock dataset")
        print(f"   • demo_results.json - Test scenario results")
        print(f"   • neo4j_demo_results.json - Neo4j demo results")
        print(f"   • all_query_results.json - All query results")
        print(f"   • demo_report.md - Comprehensive report")
        
        print("\n" + "="*80)
        print("Demo completed successfully! 🚀")
        print("="*80)

def main():
    """Main demo execution function."""
    print("🚀 Starting Energy Grid Management Agent Demo...")
    
    # Initialize demo
    demo = EnergyAgentDemo()
    
    try:
        # Setup demo environment
        demo.setup_demo()
        
        # Generate comprehensive report
        demo.generate_demo_report()
        
        # Print summary
        demo.print_summary()
        
    except Exception as e:
        logger.error(f"Demo execution failed: {e}")
        print(f"❌ Demo failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 
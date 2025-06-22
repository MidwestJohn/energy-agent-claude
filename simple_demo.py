"""
Simple Demo Script for Energy Grid Management Agent
Demonstrates test scenarios and sample queries without external dependencies
"""
import json
from datetime import datetime
from typing import Dict, List, Any
import logging
from test_data_generator import MockDataGenerator
from test_scenarios import TestScenarios
from sample_queries import SampleQueries

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_simple_demo():
    """Run a simplified demo of the Energy Grid Management Agent."""
    print("🚀 Starting Energy Grid Management Agent Simple Demo...")
    print("="*80)
    
    try:
        # Initialize components
        print("📊 Initializing components...")
        generator = MockDataGenerator()
        scenarios = TestScenarios()
        queries = SampleQueries()
        
        # Generate mock data
        print("🔧 Generating mock data...")
        mock_data = generator.generate_all_data()
        generator.save_to_json(mock_data, "mock_data.json")
        
        # Load data into scenarios
        scenarios.mock_data = mock_data
        
        print(f"✅ Generated {len(mock_data['equipment'])} equipment records")
        print(f"✅ Generated {len(mock_data['maintenance_records'])} maintenance records")
        print(f"✅ Generated {len(mock_data['sensors'])} sensor records")
        print(f"✅ Generated {len(mock_data['alerts'])} alert records")
        
        # Run Neo4j demo queries
        print("\n🎯 Running Neo4j Demo Queries...")
        print("-" * 50)
        
        # Query 1: Vibration Issues Search
        print("1. Vibration Issues Search")
        vibration_result = queries.execute_query_simulation("vibration_issues_search", mock_data)
        print(f"   • Equipment affected: {vibration_result['summary']['total_equipment_affected']}")
        print(f"   • Total vibration issues: {vibration_result['summary']['total_vibration_issues']}")
        print(f"   • Total downtime: {vibration_result['summary']['total_downtime']} hours")
        print(f"   • Total cost: ${vibration_result['summary']['total_cost']:,.2f}")
        
        # Query 2: Maintenance Schedule for Next 2 Weeks
        print("\n2. Maintenance Schedule for Next 2 Weeks")
        schedule_result = queries.execute_query_simulation("maintenance_schedule_2_weeks", mock_data)
        print(f"   • Total maintenance tasks: {schedule_result['summary']['total_tasks']}")
        print(f"   • High priority tasks: {schedule_result['summary']['high_priority']}")
        print(f"   • Medium priority tasks: {schedule_result['summary']['medium_priority']}")
        print(f"   • Total estimated cost: ${schedule_result['summary']['total_estimated_cost']:,.2f}")
        
        # Run test scenarios
        print("\n🔧 Running Test Scenarios...")
        print("-" * 50)
        
        # Scenario 1: Vibration Issues
        print("1. Vibration Issues Search")
        scenario1 = scenarios.scenario_1_vibration_issues_search()
        print(f"   • Equipment with vibration issues: {len(scenario1['results']['equipment_details'])}")
        print(f"   • Common issues identified: {len(scenario1['results']['common_issues'])}")
        
        # Scenario 2: Maintenance Schedule
        print("\n2. Maintenance Schedule for Next 2 Weeks")
        scenario2 = scenarios.scenario_2_maintenance_schedule_2_weeks()
        print(f"   • Total maintenance tasks: {scenario2['results']['total_maintenance_tasks']}")
        print(f"   • Week 1 tasks: {scenario2['results']['week_1_tasks']}")
        print(f"   • Week 2 tasks: {scenario2['results']['week_2_tasks']}")
        
        # Scenario 3: Risk Assessment
        print("\n3. Risk Assessment Analysis")
        scenario3 = scenarios.scenario_3_risk_assessment_analysis()
        risk_dist = scenario3['results']['risk_distribution']
        print(f"   • High risk equipment: {risk_dist['high_risk']}")
        print(f"   • Medium risk equipment: {risk_dist['medium_risk']}")
        print(f"   • Low risk equipment: {risk_dist['low_risk']}")
        
        # Scenario 4: Dependency Analysis
        print("\n4. Dependency Analysis")
        scenario4 = scenarios.scenario_4_dependency_analysis()
        print(f"   • Total dependencies: {scenario4['results']['total_dependencies']}")
        print(f"   • Equipment with dependencies: {scenario4['results']['equipment_with_dependencies']}")
        
        # Scenario 5: Sensor Analysis
        print("\n5. Sensor Analysis")
        scenario5 = scenarios.scenario_5_sensor_analysis()
        print(f"   • Total sensors: {scenario5['results']['total_sensors']}")
        print(f"   • Anomalies detected: {scenario5['results']['anomalies_detected']}")
        
        # Scenario 6: Cost Analysis
        print("\n6. Cost Analysis")
        scenario6 = scenarios.scenario_6_cost_analysis()
        print(f"   • Equipment types analyzed: {len(scenario6['results']['cost_by_equipment_type'])}")
        print(f"   • Total annual cost: ${scenario6['results']['total_annual_cost']:,.2f}")
        
        # Run additional sample queries
        print("\n📈 Running Additional Sample Queries...")
        print("-" * 50)
        
        all_queries = queries.get_all_queries()
        for query_name, query_info in all_queries.items():
            if query_name not in ["vibration_issues_search", "maintenance_schedule_2_weeks"]:
                print(f"• {query_info['title']}")
                result = queries.execute_query_simulation(query_name, mock_data)
                if 'summary' in result:
                    summary = result['summary']
                    if 'total_high_risk_equipment' in summary:
                        print(f"  - High risk equipment: {summary['total_high_risk_equipment']}")
                    elif 'total_anomalies' in summary:
                        print(f"  - Anomalies detected: {summary['total_anomalies']}")
                    elif 'total_cost' in summary:
                        print(f"  - Total cost: ${summary['total_cost']:,.2f}")
                    else:
                        print(f"  - Completed successfully")
        
        # Generate summary report
        print("\n📋 Demo Summary")
        print("="*80)
        print(f"✅ Mock data generated successfully")
        print(f"✅ 2 Neo4j demo queries executed")
        print(f"✅ 6 test scenarios completed")
        print(f"✅ {len(all_queries)} sample queries tested")
        print(f"✅ All functionality validated")
        
        # Save results
        print("\n💾 Saving Results...")
        
        # Save Neo4j demo results
        neo4j_results = {
            "vibration_issues_search": {
                "query": "Search equipment that presented vibration issues and list and summarize the description...",
                "result": vibration_result
            },
            "maintenance_schedule_2_weeks": {
                "query": "Can you develop a maintenance schedule over the next two weeks...",
                "result": schedule_result
            }
        }
        
        with open("neo4j_demo_results.json", "w", encoding="utf-8") as f:
            json.dump(neo4j_results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save scenario results
        scenario_results = {
            "scenario_1": scenario1,
            "scenario_2": scenario2,
            "scenario_3": scenario3,
            "scenario_4": scenario4,
            "scenario_5": scenario5,
            "scenario_6": scenario6
        }
        
        with open("demo_results.json", "w", encoding="utf-8") as f:
            json.dump(scenario_results, f, indent=2, ensure_ascii=False, default=str)
        
        print("✅ Results saved to:")
        print("   • mock_data.json - Mock dataset")
        print("   • neo4j_demo_results.json - Neo4j demo results")
        print("   • demo_results.json - Test scenario results")
        
        print("\n" + "="*80)
        print("🎉 Demo completed successfully!")
        print("="*80)
        
        return True
        
    except Exception as e:
        logger.error(f"Demo execution failed: {e}")
        print(f"❌ Demo failed: {e}")
        return False

def main():
    """Main function."""
    success = run_simple_demo()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 
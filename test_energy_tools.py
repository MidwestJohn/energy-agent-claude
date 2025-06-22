#!/usr/bin/env python3
"""
Test script for EnergyAgentTools class.
"""
import sys
import os
from datetime import datetime

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import EnergyAgentTools
from config import Config

def test_energy_tools():
    """Test the EnergyAgentTools functionality."""
    print("🧪 Testing EnergyAgentTools...")
    
    try:
        # Initialize the tools
        print("📡 Connecting to Neo4j database...")
        tools = EnergyAgentTools()
        print("✅ Database connection successful!")
        
        # Test 1: Search maintenance records
        print("\n🔍 Testing maintenance records search...")
        maintenance_records = tools.search_equipment_maintenance_records(
            equipment_type="Generator",
            days_back=30
        )
        print(f"Found {len(maintenance_records)} maintenance records")
        
        # Test 2: Get risky equipment
        print("\n⚠️ Testing risky equipment search...")
        risky_equipment = tools.get_risky_equipment(risk_threshold=0.5)
        print(f"Found {len(risky_equipment)} high-risk equipment items")
        
        # Test 3: Get installation dependencies
        print("\n🔗 Testing installation dependencies...")
        dependencies = tools.get_installation_equipments_dependency()
        print(f"Found {len(dependencies)} installation-equipment relationships")
        
        # Test 4: Get equipment health summary
        print("\n📊 Testing equipment health summary...")
        health_summary = tools.get_equipment_health_summary()
        print(f"Health summary: {health_summary}")
        
        # Test 5: Get maintenance trends
        print("\n📈 Testing maintenance trends...")
        trends = tools.get_maintenance_trends(days=30)
        print(f"Found {len(trends)} maintenance trend records")
        
        # Test 6: Get equipment by location
        print("\n📍 Testing equipment by location...")
        location_equipment = tools.get_equipment_by_location("Station")
        print(f"Found {len(location_equipment)} equipment items at location")
        
        # Close connection
        tools.close()
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration loading."""
    print("⚙️ Testing configuration...")
    
    try:
        config = Config()
        config.validate_config()
        print("✅ Configuration validation successful!")
        
        # Test Neo4j config
        neo4j_config = config.get_neo4j_config()
        print(f"📡 Neo4j URI: {neo4j_config['uri']}")
        print(f"📡 Neo4j Database: {neo4j_config['database']}")
        
        # Test Claude config
        claude_config = config.get_claude_config()
        print(f"🤖 Claude Model: {claude_config['model']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Energy Grid Management Agent - Tools Test")
    print("=" * 50)
    
    # Test configuration first
    if not test_configuration():
        print("❌ Configuration test failed. Exiting.")
        sys.exit(1)
    
    # Test energy tools
    if test_energy_tools():
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1) 
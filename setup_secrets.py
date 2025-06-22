#!/usr/bin/env python3
"""
Secrets Configuration Helper for Energy Agent Streamlit Cloud Deployment
Guides users through setting up all required secrets and configurations
"""

import os
import re
import getpass
from datetime import datetime

class SecretsManager:
    def __init__(self):
        self.secrets = {}
        self.env_file = '.env'
        self.secrets_template = '.streamlit/secrets.toml.example'
        
    def validate_neo4j_uri(self, uri):
        """Validate Neo4j URI format"""
        if not uri:
            return False, "URI cannot be empty"
        
        # Check for valid Neo4j URI patterns
        patterns = [
            r'^neo4j://[^:]+:\d+$',  # neo4j://host:port
            r'^neo4j\+s://[^:]+:\d+$',  # neo4j+s://host:port (secure)
            r'^bolt://[^:]+:\d+$',  # bolt://host:port
            r'^bolt\+s://[^:]+:\d+$',  # bolt+s://host:port (secure)
        ]
        
        for pattern in patterns:
            if re.match(pattern, uri):
                return True, "Valid Neo4j URI"
        
        return False, "Invalid Neo4j URI format. Expected: neo4j://host:port or neo4j+s://host:port"
    
    def validate_api_key(self, key):
        """Validate API key format"""
        if not key:
            return False, "API key cannot be empty"
        
        if key.startswith('sk-') and len(key) > 20:
            return True, "Valid API key format"
        
        return False, "Invalid API key format. Should start with 'sk-' and be at least 20 characters"
    
    def get_neo4j_uri(self):
        """Get and validate Neo4j URI"""
        print("\n🔗 Neo4j Database Configuration")
        print("="*40)
        
        while True:
            uri = input("Enter your Neo4j URI (e.g., neo4j+s://your-host:7687): ").strip()
            is_valid, message = self.validate_neo4j_uri(uri)
            
            if is_valid:
                print(f"✅ {message}")
                return uri
            else:
                print(f"❌ {message}")
                retry = input("Try again? (y/n): ").lower()
                if retry != 'y':
                    return None
    
    def get_neo4j_credentials(self):
        """Get Neo4j username and password"""
        print("\n👤 Neo4j Authentication")
        print("="*30)
        
        username = input("Enter Neo4j username (default: neo4j): ").strip()
        if not username:
            username = "neo4j"
        
        password = getpass.getpass("Enter Neo4j password: ")
        if not password:
            print("❌ Password cannot be empty")
            return None, None
        
        return username, password
    
    def get_neo4j_database(self):
        """Get Neo4j database name"""
        print("\n🗄️ Neo4j Database Selection")
        print("="*30)
        
        database = input("Enter database name (default: neo4j): ").strip()
        if not database:
            database = "neo4j"
        
        return database
    
    def get_claude_api_key(self):
        """Get Claude API key"""
        print("\n🤖 Claude AI API Configuration")
        print("="*35)
        print("Get your API key from: https://console.anthropic.com/")
        
        while True:
            api_key = getpass.getpass("Enter your Claude API key: ")
            is_valid, message = self.validate_api_key(api_key)
            
            if is_valid:
                print(f"✅ {message}")
                return api_key
            else:
                print(f"❌ {message}")
                retry = input("Try again? (y/n): ").lower()
                if retry != 'y':
                    return None
    
    def collect_secrets(self):
        """Collect all required secrets interactively"""
        print("🔐 Energy Agent Secrets Configuration")
        print("="*50)
        print("This script will help you configure all required secrets for Streamlit Cloud deployment.")
        print("Your secrets will be saved locally and you'll get copy-paste ready configurations.")
        print()
        
        # Neo4j URI
        neo4j_uri = self.get_neo4j_uri()
        if not neo4j_uri:
            print("❌ Neo4j URI configuration cancelled")
            return False
        self.secrets['NEO4J_URI'] = neo4j_uri
        
        # Neo4j credentials
        username, password = self.get_neo4j_credentials()
        if not username or not password:
            print("❌ Neo4j credentials configuration cancelled")
            return False
        self.secrets['NEO4J_USERNAME'] = username
        self.secrets['NEO4J_PASSWORD'] = password
        
        # Neo4j database
        database = self.get_neo4j_database()
        self.secrets['NEO4J_DATABASE'] = database
        
        # Claude API key
        api_key = self.get_claude_api_key()
        if not api_key:
            print("❌ Claude API key configuration cancelled")
            return False
        self.secrets['ANTHROPIC_API_KEY'] = api_key
        
        return True
    
    def create_env_file(self):
        """Create .env file for local development"""
        print(f"\n📝 Creating {self.env_file} for local development...")
        
        env_content = f"""# Energy Agent Environment Variables
# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# For local development only - DO NOT commit to version control

"""
        
        for key, value in self.secrets.items():
            env_content += f"{key}={value}\n"
        
        try:
            with open(self.env_file, 'w') as f:
                f.write(env_content)
            print(f"✅ {self.env_file} created successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to create {self.env_file}: {e}")
            return False
    
    def create_secrets_template(self):
        """Create secrets template for Streamlit Cloud"""
        print(f"\n📋 Creating {self.secrets_template}...")
        
        # Ensure .streamlit directory exists
        os.makedirs('.streamlit', exist_ok=True)
        
        template_content = f"""# Streamlit Cloud Secrets Template
# Copy this configuration to Streamlit Cloud Secrets Manager
# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        for key, value in self.secrets.items():
            # Mask sensitive values in template
            if 'PASSWORD' in key or 'API_KEY' in key:
                template_content += f'{key} = "your-{key.lower()}-here"\n'
            else:
                template_content += f'{key} = "{value}"\n'
        
        try:
            with open(self.secrets_template, 'w') as f:
                f.write(template_content)
            print(f"✅ {self.secrets_template} created successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to create {self.secrets_template}: {e}")
            return False
    
    def generate_streamlit_cloud_config(self):
        """Generate copy-paste ready configuration for Streamlit Cloud"""
        print("\n🌐 Streamlit Cloud Configuration")
        print("="*40)
        print("Copy the following configuration to Streamlit Cloud Secrets Manager:")
        print()
        print("```toml")
        
        for key, value in self.secrets.items():
            print(f'{key} = "{value}"')
        
        print("```")
        print()
        print("Instructions:")
        print("1. Go to your app on Streamlit Cloud")
        print("2. Click Settings (gear icon)")
        print("3. Select 'Secrets' from the sidebar")
        print("4. Paste the configuration above")
        print("5. Click 'Save'")
        print("6. Click 'Redeploy' to apply the secrets")
    
    def generate_summary(self):
        """Generate configuration summary"""
        print("\n📊 Configuration Summary")
        print("="*30)
        print(f"✅ Neo4j URI: {self.secrets.get('NEO4J_URI', 'Not set')}")
        print(f"✅ Neo4j Username: {self.secrets.get('NEO4J_USERNAME', 'Not set')}")
        print(f"✅ Neo4j Database: {self.secrets.get('NEO4J_DATABASE', 'Not set')}")
        print(f"✅ Claude API Key: {'Set' if self.secrets.get('ANTHROPIC_API_KEY') else 'Not set'}")
        print()
        print("📁 Generated files:")
        print(f"   - {self.env_file} (local development)")
        print(f"   - {self.secrets_template} (template)")
        print()
        print("🔒 Security notes:")
        print("   - .env file is for local development only")
        print("   - Never commit .env file to version control")
        print("   - Use Streamlit Cloud Secrets Manager for production")
    
    def run_setup(self):
        """Run the complete secrets setup process"""
        print("🚀 Energy Agent Secrets Setup")
        print("="*50)
        
        if not self.collect_secrets():
            print("❌ Secrets collection cancelled")
            return False
        
        # Create files
        if not self.create_env_file():
            return False
        
        if not self.create_secrets_template():
            return False
        
        # Generate configurations
        self.generate_streamlit_cloud_config()
        self.generate_summary()
        
        print("\n🎉 Secrets configuration completed successfully!")
        print("Next steps:")
        print("1. Test your local configuration")
        print("2. Deploy to Streamlit Cloud")
        print("3. Configure secrets in Streamlit Cloud")
        
        return True

def main():
    """Main function"""
    secrets_manager = SecretsManager()
    success = secrets_manager.run_setup()
    
    if not success:
        print("\n❌ Secrets setup failed")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 
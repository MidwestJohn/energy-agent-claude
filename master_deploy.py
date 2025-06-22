#!/usr/bin/env python3
"""
Master Deployment Script for Energy Agent Streamlit Cloud Deployment
Handles complete deployment process from local development to production
"""

import os
import sys
import subprocess
import logging
import json
import time
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('deployment.log')
    ]
)

class DeploymentManager:
    def __init__(self):
        self.deployment_id = f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.deployment_report = f"deployment_report_{self.deployment_id}.md"
        self.app_url = None
        self.success = False
        
    def run_command(self, command, description, check=True):
        """Run a shell command with error handling"""
        logging.info(f"🔄 {description}")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check)
            if result.stdout:
                logging.info(f"✅ {description} completed successfully")
            return result
        except subprocess.CalledProcessError as e:
            logging.error(f"❌ {description} failed: {e}")
            logging.error(f"Error output: {e.stderr}")
            return None

    def pre_deployment_checks(self):
        """Run all pre-deployment validation checks"""
        logging.info("🚀 Starting pre-deployment checks...")
        
        checks = [
            ("Code quality validation", "python deploy_prep.py"),
            ("Running tests", "python -m pytest tests/ -v"),
            ("Linting check", "flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics"),
            ("Security scan", "bandit -r . -f json -o bandit-report.json"),
            ("Dependency check", "pip check"),
        ]
        
        failed_checks = []
        for description, command in checks:
            result = self.run_command(command, description, check=False)
            if result and result.returncode != 0:
                failed_checks.append(description)
        
        if failed_checks:
            logging.error(f"❌ Pre-deployment checks failed: {failed_checks}")
            return False
        
        logging.info("✅ All pre-deployment checks passed")
        return True

    def git_operations(self):
        """Handle Git repository operations"""
        logging.info("📝 Starting Git operations...")
        
        # Check if we're in a git repository
        if not os.path.exists('.git'):
            logging.error("❌ Not in a Git repository. Please initialize Git first.")
            return False
        
        # Get current branch
        result = self.run_command("git branch --show-current", "Getting current branch")
        if not result:
            return False
        
        current_branch = result.stdout.strip()
        logging.info(f"📋 Current branch: {current_branch}")
        
        # Stage all changes
        self.run_command("git add .", "Staging all changes")
        
        # Check if there are changes to commit
        result = self.run_command("git status --porcelain", "Checking for changes")
        if not result or not result.stdout.strip():
            logging.info("📋 No changes to commit")
        else:
            # Commit changes
            commit_message = f"feat: deployment {self.deployment_id} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            self.run_command(f'git commit -m "{commit_message}"', "Committing changes")
        
        # Push to GitHub
        self.run_command(f"git push origin {current_branch}", "Pushing to GitHub")
        
        # Create deployment tag
        tag_name = f"v{datetime.now().strftime('%Y.%m.%d')}-{self.deployment_id}"
        self.run_command(f'git tag -a {tag_name} -m "Deployment {self.deployment_id}"', "Creating deployment tag")
        self.run_command(f"git push origin {tag_name}", "Pushing deployment tag")
        
        logging.info("✅ Git operations completed")
        return True

    def generate_deployment_instructions(self):
        """Generate step-by-step deployment instructions"""
        logging.info("📋 Generating deployment instructions...")
        
        instructions = f"""
# Streamlit Cloud Deployment Instructions

## Deployment ID: {self.deployment_id}
## Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Step 1: Access Streamlit Cloud
1. Go to [https://share.streamlit.io/](https://share.streamlit.io/)
2. Sign in with your GitHub account
3. Click "New app" in the top right

## Step 2: Configure App
1. **Repository:** Select your GitHub repository
2. **Branch:** Select `main` (or your deployment branch)
3. **Main file path:** Enter `app.py` (or `app_cloud.py`)
4. Click "Deploy"

## Step 3: Configure Secrets
1. Once deployed, click the gear icon (Settings) in the top right
2. Select "Secrets" from the sidebar
3. Paste the following configuration:

```toml
NEO4J_URI = "neo4j+s://your-neo4j-host:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "your-neo4j-password"
NEO4J_DATABASE = "neo4j"
ANTHROPIC_API_KEY = "your-anthropic-api-key"
```

4. Click "Save"
5. Click "Redeploy" to apply the secrets

## Step 4: Verify Deployment
1. Check that the app loads without errors
2. Test all main features:
   - Equipment Analysis
   - Risk Assessment
   - Maintenance Scheduling
   - Dependencies
   - Vibration Analysis
3. Verify database connections
4. Test Claude AI integration

## Step 5: Share Your App
Your app will be available at:
`https://your-app-name-your-username.streamlit.app`

Share this URL with your team and stakeholders.
"""
        
        with open("streamlit_cloud_deployment_instructions.md", "w") as f:
            f.write(instructions)
        
        logging.info("✅ Deployment instructions generated: streamlit_cloud_deployment_instructions.md")
        return True

    def create_deployment_documentation(self):
        """Create comprehensive deployment documentation"""
        logging.info("📚 Creating deployment documentation...")
        
        # Get Git information
        git_hash = subprocess.run("git rev-parse HEAD", shell=True, capture_output=True, text=True).stdout.strip()[:8]
        git_branch = subprocess.run("git branch --show-current", shell=True, capture_output=True, text=True).stdout.strip()
        
        # Get app configuration
        config_info = {}
        if os.path.exists('.streamlit/config.toml'):
            try:
                import toml
                with open('.streamlit/config.toml', 'r') as f:
                    config_info = toml.load(f)
            except:
                config_info = {"error": "Could not parse config.toml"}
        
        # Get requirements info
        requirements_info = []
        if os.path.exists('requirements.txt'):
            with open('requirements.txt', 'r') as f:
                requirements_info = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        documentation = f"""
# Deployment Report

## Deployment Information
- **Deployment ID:** {self.deployment_id}
- **Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Git Hash:** {git_hash}
- **Git Branch:** {git_branch}
- **Status:** {'✅ SUCCESS' if self.success else '❌ FAILED'}

## Configuration Used
### Streamlit Configuration
```toml
{json.dumps(config_info, indent=2)}
```

### Dependencies
```
{chr(10).join(requirements_info)}
```

## Post-Deployment Verification
- [ ] App loads successfully
- [ ] All tabs functional
- [ ] Database connection established
- [ ] Claude AI integration working
- [ ] Performance acceptable (< 3s load time)
- [ ] No errors in logs

## Access Information
- **App URL:** {self.app_url or 'To be configured after deployment'}
- **Admin Access:** Streamlit Cloud dashboard
- **Logs:** Available in Streamlit Cloud settings

## Monitoring Setup
- **Health Check:** /health endpoint
- **Metrics:** Available in Streamlit Cloud dashboard
- **Error Tracking:** Built-in logging

## Maintenance Procedures
1. **Updates:** Push to GitHub main branch
2. **Secrets:** Update in Streamlit Cloud settings
3. **Monitoring:** Check Streamlit Cloud metrics
4. **Backup:** Neo4j database backup (if applicable)

## Troubleshooting
- **App won't start:** Check secrets configuration
- **Database errors:** Verify Neo4j connection
- **API errors:** Check Claude API key
- **Performance issues:** Monitor resource usage

## Rollback Procedure
1. Go to Streamlit Cloud dashboard
2. Select previous deployment
3. Click "Redeploy"
4. Verify functionality
"""
        
        with open(self.deployment_report, "w") as f:
            f.write(documentation)
        
        logging.info(f"✅ Deployment documentation created: {self.deployment_report}")
        return True

    def setup_monitoring(self):
        """Set up monitoring and maintenance procedures"""
        logging.info("📊 Setting up monitoring...")
        
        monitoring_script = f"""
# Monitoring Script for Energy Agent App
# Run this script periodically to check app health

import requests
import time
from datetime import datetime

APP_URL = "{self.app_url or 'YOUR_APP_URL_HERE'}"

def check_app_health():
    try:
        response = requests.get(APP_URL, timeout=10)
        if response.status_code == 200:
            print(f"[{datetime.now()}] ✅ App is healthy")
            return True
        else:
            print(f"[{datetime.now()}] ❌ App returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"[{datetime.now()}] ❌ App health check failed: {e}")
        return False

if __name__ == "__main__":
    check_app_health()
"""
        
        with open("monitor_app.py", "w") as f:
            f.write(monitoring_script)
        
        # Create monitoring instructions
        monitoring_instructions = """
# Monitoring and Maintenance Guide

## Automated Monitoring
Run the monitoring script periodically:
```bash
python monitor_app.py
```

## Manual Monitoring
1. **Streamlit Cloud Dashboard:**
   - Check app status
   - Monitor resource usage
   - Review logs for errors

2. **Performance Metrics:**
   - App load time should be < 3 seconds
   - Memory usage should be stable
   - No frequent restarts

3. **User Experience:**
   - All features should be functional
   - No timeout errors
   - Responsive UI

## Maintenance Schedule
- **Daily:** Check app status and logs
- **Weekly:** Review performance metrics
- **Monthly:** Update dependencies and security patches
- **Quarterly:** Full system review and optimization

## Backup Strategy
- **Database:** Regular Neo4j backups (if applicable)
- **Configuration:** Version control all config changes
- **Code:** Git repository with deployment tags
"""
        
        with open("monitoring_guide.md", "w") as f:
            f.write(monitoring_instructions)
        
        logging.info("✅ Monitoring setup completed")
        return True

    def get_app_url_instructions(self):
        """Provide instructions for getting the app URL"""
        logging.info("🌐 App URL Instructions:")
        
        url_instructions = """
## Your App URL

After deploying to Streamlit Cloud, your app will be available at:
`https://your-app-name-your-username.streamlit.app`

### To find your exact URL:
1. Go to [Streamlit Cloud Dashboard](https://share.streamlit.io/)
2. Find your deployed app
3. Click on the app name
4. Copy the URL from your browser

### Sharing Your App:
- **Public Access:** Anyone with the URL can access your app
- **Team Sharing:** Share the URL with your team via email, Slack, or documentation
- **Documentation:** Include the URL in your project documentation
- **Bookmarks:** Add to browser bookmarks for easy access

### Security Considerations:
- Your app is public by default (required for free tier)
- Sensitive data should be protected via authentication (if needed)
- Monitor usage and set up alerts for unusual activity
"""
        
        print(url_instructions)
        return True

    def run_deployment(self):
        """Execute the complete deployment process"""
        logging.info("🚀 Starting complete Streamlit Cloud deployment process...")
        
        try:
            # Step 1: Pre-deployment checks
            if not self.pre_deployment_checks():
                logging.error("❌ Pre-deployment checks failed. Aborting deployment.")
                return False
            
            # Step 2: Git operations
            if not self.git_operations():
                logging.error("❌ Git operations failed. Aborting deployment.")
                return False
            
            # Step 3: Generate deployment instructions
            if not self.generate_deployment_instructions():
                logging.error("❌ Failed to generate deployment instructions.")
                return False
            
            # Step 4: Create deployment documentation
            if not self.create_deployment_documentation():
                logging.error("❌ Failed to create deployment documentation.")
                return False
            
            # Step 5: Setup monitoring
            if not self.setup_monitoring():
                logging.error("❌ Failed to setup monitoring.")
                return False
            
            # Step 6: Provide app URL instructions
            self.get_app_url_instructions()
            
            self.success = True
            logging.info("🎉 Deployment process completed successfully!")
            
            # Final summary
            print("\n" + "="*60)
            print("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
            print("="*60)
            print(f"📋 Deployment ID: {self.deployment_id}")
            print(f"📚 Documentation: {self.deployment_report}")
            print(f"📖 Instructions: streamlit_cloud_deployment_instructions.md")
            print(f"📊 Monitoring: monitor_app.py")
            print("="*60)
            print("Next steps:")
            print("1. Follow the deployment instructions in streamlit_cloud_deployment_instructions.md")
            print("2. Configure your secrets in Streamlit Cloud")
            print("3. Test your deployed app")
            print("4. Share the app URL with your team")
            print("="*60)
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Deployment failed with error: {e}")
            self.success = False
            return False

def main():
    """Main deployment function"""
    print("🚀 Energy Agent Streamlit Cloud Deployment")
    print("="*50)
    
    # Check if we're in the right directory
    if not os.path.exists('app.py') and not os.path.exists('app_cloud.py'):
        print("❌ Error: app.py or app_cloud.py not found in current directory")
        print("Please run this script from your project root directory")
        sys.exit(1)
    
    # Create deployment manager
    deployer = DeploymentManager()
    
    # Run deployment
    success = deployer.run_deployment()
    
    if success:
        print("\n✅ Deployment process completed successfully!")
        print("📋 Check the generated files for next steps:")
        print("   - streamlit_cloud_deployment_instructions.md")
        print(f"   - {deployer.deployment_report}")
        print("   - monitor_app.py")
    else:
        print("\n❌ Deployment process failed!")
        print("📋 Check deployment.log for detailed error information")
        sys.exit(1)

if __name__ == "__main__":
    main() 
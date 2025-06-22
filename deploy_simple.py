#!/usr/bin/env python3
"""
Simplified Deployment Script for Energy Agent Streamlit Cloud Deployment
Handles essential deployment steps without requiring external tools
"""

import os
import sys
import subprocess
import json
from datetime import datetime

class SimpleDeploymentManager:
    def __init__(self):
        self.deployment_id = f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.deployment_report = f"deployment_report_{self.deployment_id}.md"
        self.success = False
        
    def check_essential_files(self):
        """Check for essential deployment files"""
        print("🔍 Checking essential files...")
        
        essential_files = [
            'app.py',
            'requirements.txt',
            'README.md',
        ]
        
        missing_files = []
        for file in essential_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ Missing essential files: {missing_files}")
            return False
        
        print("✅ All essential files present")
        return True
    
    def check_git_status(self):
        """Check Git repository status"""
        print("📝 Checking Git status...")
        
        if not os.path.exists('.git'):
            print("❌ Not in a Git repository")
            print("Please run: git init && git remote add origin <your-repo-url>")
            return False
        
        try:
            # Check if we have a remote
            result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
            if not result.stdout.strip():
                print("❌ No Git remote configured")
                print("Please run: git remote add origin <your-repo-url>")
                return False
            
            print("✅ Git repository configured")
            return True
            
        except Exception as e:
            print(f"❌ Git check failed: {e}")
            return False
    
    def git_operations(self):
        """Handle Git operations"""
        print("📝 Performing Git operations...")
        
        try:
            # Stage all changes
            subprocess.run("git add .", shell=True, check=True)
            print("✅ Changes staged")
            
            # Check if there are changes to commit
            result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
            if not result.stdout.strip():
                print("📋 No changes to commit")
            else:
                # Commit changes
                commit_message = f"feat: deployment {self.deployment_id} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                subprocess.run(f'git commit -m "{commit_message}"', shell=True, check=True)
                print("✅ Changes committed")
            
            # Push to GitHub
            subprocess.run("git push origin main", shell=True, check=True)
            print("✅ Changes pushed to GitHub")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git operation failed: {e}")
            return False
    
    def generate_deployment_instructions(self):
        """Generate step-by-step deployment instructions"""
        print("📋 Generating deployment instructions...")
        
        instructions = f"""
# 🚀 Streamlit Cloud Deployment Instructions

## Deployment ID: {self.deployment_id}
## Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Step 1: Access Streamlit Cloud
1. Go to [https://share.streamlit.io/](https://share.streamlit.io/)
2. Sign in with your GitHub account
3. Click "New app" in the top right

## Step 2: Configure App
1. **Repository:** Select your GitHub repository (`energy-agent-claude`)
2. **Branch:** Select `main`
3. **Main file path:** Enter `app.py`
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

## Troubleshooting
- **App won't start:** Check secrets configuration
- **Database errors:** Verify Neo4j connection
- **API errors:** Check Claude API key
- **Performance issues:** Monitor resource usage

## Next Steps
1. Run: `python3 setup_secrets.py` to configure your secrets
2. Follow the deployment instructions above
3. Test your deployed app
4. Share the app URL with your team
"""
        
        with open("streamlit_cloud_deployment_instructions.md", "w") as f:
            f.write(instructions)
        
        print("✅ Deployment instructions generated: streamlit_cloud_deployment_instructions.md")
        return True
    
    def create_deployment_documentation(self):
        """Create deployment documentation"""
        print("📚 Creating deployment documentation...")
        
        try:
            # Get Git information
            git_hash = subprocess.run("git rev-parse HEAD", shell=True, capture_output=True, text=True).stdout.strip()[:8]
            git_branch = subprocess.run("git branch --show-current", shell=True, capture_output=True, text=True).stdout.strip()
        except:
            git_hash = "unknown"
            git_branch = "unknown"
        
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

## Dependencies
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
- **App URL:** To be configured after deployment
- **Admin Access:** Streamlit Cloud dashboard
- **Logs:** Available in Streamlit Cloud settings

## Monitoring Setup
- **Health Check:** Use monitor_app.py script
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
        
        print(f"✅ Deployment documentation created: {self.deployment_report}")
        return True
    
    def get_app_url_instructions(self):
        """Provide instructions for getting the app URL"""
        print("\n🌐 App URL Instructions:")
        
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
        """Execute the simplified deployment process"""
        print("🚀 Starting simplified Streamlit Cloud deployment process...")
        
        try:
            # Step 1: Check essential files
            if not self.check_essential_files():
                return False
            
            # Step 2: Check Git status
            if not self.check_git_status():
                return False
            
            # Step 3: Git operations
            if not self.git_operations():
                return False
            
            # Step 4: Generate deployment instructions
            if not self.generate_deployment_instructions():
                return False
            
            # Step 5: Create deployment documentation
            if not self.create_deployment_documentation():
                return False
            
            # Step 6: Provide app URL instructions
            self.get_app_url_instructions()
            
            self.success = True
            print("🎉 Deployment process completed successfully!")
            
            # Final summary
            print("\n" + "="*60)
            print("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
            print("="*60)
            print(f"📋 Deployment ID: {self.deployment_id}")
            print(f"📚 Documentation: {self.deployment_report}")
            print(f"📖 Instructions: streamlit_cloud_deployment_instructions.md")
            print("="*60)
            print("Next steps:")
            print("1. Run: python3 setup_secrets.py")
            print("2. Follow the deployment instructions in streamlit_cloud_deployment_instructions.md")
            print("3. Configure your secrets in Streamlit Cloud")
            print("4. Test your deployed app")
            print("5. Share the app URL with your team")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"❌ Deployment failed with error: {e}")
            self.success = False
            return False

def main():
    """Main deployment function"""
    print("🚀 Energy Agent Streamlit Cloud Deployment (Simplified)")
    print("="*60)
    
    # Check if we're in the right directory
    if not os.path.exists('app.py') and not os.path.exists('app_cloud.py'):
        print("❌ Error: app.py or app_cloud.py not found in current directory")
        print("Please run this script from your project root directory")
        sys.exit(1)
    
    # Create deployment manager
    deployer = SimpleDeploymentManager()
    
    # Run deployment
    success = deployer.run_deployment()
    
    if success:
        print("\n✅ Deployment process completed successfully!")
        print("📋 Check the generated files for next steps:")
        print("   - streamlit_cloud_deployment_instructions.md")
        print(f"   - {deployer.deployment_report}")
    else:
        print("\n❌ Deployment process failed!")
        print("📋 Check the output above for error details")
        sys.exit(1)

if __name__ == "__main__":
    main() 
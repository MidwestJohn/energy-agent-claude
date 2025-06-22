# Streamlit Cloud Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Energy Grid Management Agent to Streamlit Cloud, including all optimizations and best practices for cloud deployment.

## Prerequisites

Before deploying to Streamlit Cloud, ensure you have:

1. **GitHub Account**: Your code must be in a public GitHub repository
2. **Streamlit Cloud Account**: Sign up at [share.streamlit.io](https://share.streamlit.io)
3. **Neo4j Database**: AuraDB or self-hosted Neo4j instance
4. **Claude AI API Key**: Valid API key from Anthropic
5. **Required Secrets**: All necessary API keys and database credentials

## Step 1: Prepare Your Repository

### 1.1 Repository Structure

Ensure your repository has the following structure:

```
energy-agent-claude/
├── app_cloud.py              # Main cloud-optimized app
├── secrets_manager.py        # Secrets management system
├── health_checker.py         # Health check system
├── cloud_cache.py           # Cloud caching system
├── cloud_logging.py         # Logging and monitoring
├── requirements.txt         # Python dependencies
├── .streamlit/
│   ├── config.toml         # Streamlit configuration
│   └── secrets.toml.example # Example secrets file
├── README.md               # Project documentation
├── .gitignore             # Git ignore file
└── logs/                  # Log directory (created automatically)
```

### 1.2 Update Configuration Files

#### `.streamlit/config.toml`

```toml
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false
address = "0.0.0.0"
maxUploadSize = 200
maxMessageSize = 200

[theme]
base = "light"
primaryColor = "#0057B8"
backgroundColor = "#F7F9FB"
secondaryBackgroundColor = "#E3E8EF"
textColor = "#22272B"
font = "sans serif"

[browser]
gatherUsageStats = false
serverAddress = "auto"

[client]
showErrorDetails = true

[performance]
maxCachedMessageAge = 3600
maxCachedPages = 20
```

#### `requirements.txt`

Ensure your `requirements.txt` includes all necessary dependencies:

```txt
streamlit==1.35.0
pandas==2.2.2
plotly==5.22.0
neo4j==5.19.0
python-dotenv==1.0.1
requests==2.32.3
PyYAML==6.0.1
anthropic==0.18.1
numpy==1.26.4
matplotlib==3.8.3
seaborn==0.13.2
networkx==3.2.1
pydantic==2.6.1
httpx==0.27.0
python-dateutil==2.8.2
pytz==2024.1
orjson==3.9.15
```

## Step 2: Configure Streamlit Cloud Secrets

### 2.1 Access Streamlit Cloud Dashboard

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click "New app" to create a new deployment

### 2.2 Set Up Secrets

In the Streamlit Cloud dashboard, navigate to your app's settings and configure the following secrets:

#### Required Secrets

```toml
# Neo4j Database Configuration
NEO4J_URI = "neo4j+s://your-instance.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "your-secure-password"
NEO4J_DATABASE = "neo4j"

# Claude AI Configuration
CLAUDE_API_KEY = "sk-ant-api03-your-api-key-here"
```

#### Optional Secrets

```toml
# Security Configuration
ENCRYPTION_KEY = "your-32-character-encryption-key"
HASH_SALT = "your-16-character-salt"

# Application Configuration
SESSION_TIMEOUT = 3600
LOG_LEVEL = "INFO"
CACHE_TTL = 300
MAX_WORKERS = 4
HEALTH_CHECK_INTERVAL = 300
SERVICE_NAME = "energy-grid-agent"
APP_VERSION = "1.0.0"
```

### 2.3 Secrets Management Best Practices

1. **Never commit secrets to Git**: Ensure `.streamlit/secrets.toml` is in your `.gitignore`
2. **Use strong passwords**: Generate secure passwords for database access
3. **Rotate keys regularly**: Update API keys and passwords periodically
4. **Limit permissions**: Use least-privilege access for database users

## Step 3: Deploy to Streamlit Cloud

### 3.1 Create New App

1. In Streamlit Cloud dashboard, click "New app"
2. Select your GitHub repository: `your-username/energy-agent-claude`
3. Set the main file path: `app_cloud.py`
4. Choose Python version: `3.9` or higher

### 3.2 Configure App Settings

#### Basic Settings
- **App name**: `energy-grid-management-agent`
- **Main file path**: `app_cloud.py`
- **Python version**: `3.9`

#### Advanced Settings
- **Command line arguments**: Leave empty
- **Environment variables**: Configure if needed
- **Memory limit**: Set to 1GB or higher for optimal performance

### 3.3 Deploy

1. Click "Deploy!" to start the deployment process
2. Monitor the deployment logs for any errors
3. Wait for the app to become available (usually 2-5 minutes)

## Step 4: Post-Deployment Verification

### 4.1 Health Check

Once deployed, verify that:

1. **App loads successfully**: No error messages on startup
2. **Secrets are loaded**: Check the secrets status in the sidebar
3. **Database connection**: Health checker shows "Healthy" status
4. **API connection**: Claude AI API shows "Healthy" status

### 4.2 Performance Monitoring

Monitor the following metrics:

1. **Response times**: Check performance metrics in the monitoring dashboard
2. **Cache hit rates**: Verify caching is working efficiently
3. **Error rates**: Monitor for any recurring errors
4. **Memory usage**: Ensure app stays within memory limits

### 4.3 Testing Functionality

Test all major features:

1. **Equipment Analysis**: Search and display maintenance records
2. **Risk Assessment**: Analyze equipment risk scores
3. **Data Export**: Download CSV and JSON files
4. **Health Monitoring**: Check system health status

## Step 5: Production Optimization

### 5.1 Performance Optimization

#### Caching Strategy
- Database queries: 5-10 minutes TTL
- Chart generation: 10 minutes TTL
- Analysis results: 30 minutes TTL
- Database connections: 1 hour TTL

#### Memory Management
- Monitor cache size and eviction rates
- Clear old metrics periodically
- Optimize data structures for memory efficiency

### 5.2 Monitoring and Alerting

#### Log Analysis
- Monitor structured logs in `logs/structured_events.jsonl`
- Track performance metrics and error rates
- Export logs for analysis when needed

#### Health Monitoring
- Regular health checks every 5 minutes
- Automatic error reporting
- Performance degradation alerts

### 5.3 Security Best Practices

#### Access Control
- Use strong database passwords
- Rotate API keys regularly
- Monitor access logs for suspicious activity

#### Data Protection
- Encrypt sensitive data in transit and at rest
- Implement proper session management
- Regular security audits

## Step 6: Troubleshooting

### 6.1 Common Issues

#### App Won't Start
- Check secrets configuration
- Verify all required dependencies are in `requirements.txt`
- Review deployment logs for error messages

#### Database Connection Issues
- Verify Neo4j URI and credentials
- Check network connectivity
- Ensure database is accessible from Streamlit Cloud

#### API Connection Issues
- Verify Claude API key is valid
- Check API rate limits
- Monitor API response times

#### Performance Issues
- Review cache configuration
- Monitor memory usage
- Optimize database queries

### 6.2 Debugging Tools

#### Built-in Monitoring
- Use the monitoring dashboard in the sidebar
- Check performance metrics and error logs
- Export logs for detailed analysis

#### Streamlit Cloud Logs
- Access deployment logs in Streamlit Cloud dashboard
- Monitor resource usage and performance
- Check for any platform-specific issues

### 6.3 Support Resources

- **Streamlit Documentation**: [docs.streamlit.io](https://docs.streamlit.io)
- **Streamlit Community**: [discuss.streamlit.io](https://discuss.streamlit.io)
- **GitHub Issues**: Report bugs in your repository
- **Neo4j Documentation**: [neo4j.com/docs](https://neo4j.com/docs)

## Step 7: Maintenance and Updates

### 7.1 Regular Maintenance

#### Weekly Tasks
- Review performance metrics
- Check error logs
- Monitor resource usage
- Update dependencies if needed

#### Monthly Tasks
- Security audit
- Performance optimization review
- Backup verification
- Documentation updates

### 7.2 Updates and Upgrades

#### Code Updates
1. Push changes to GitHub
2. Streamlit Cloud automatically redeploys
3. Monitor deployment for any issues
4. Verify functionality after update

#### Dependency Updates
1. Update `requirements.txt`
2. Test locally before deploying
3. Monitor for compatibility issues
4. Rollback if necessary

### 7.3 Backup and Recovery

#### Data Backup
- Regular database backups
- Configuration backup
- Log file archiving
- Disaster recovery plan

#### Recovery Procedures
- Document recovery steps
- Test recovery procedures
- Maintain backup verification
- Update recovery documentation

## Conclusion

Your Energy Grid Management Agent is now optimized for Streamlit Cloud deployment with:

- ✅ **Cloud-optimized secrets management**
- ✅ **Comprehensive health checking**
- ✅ **Advanced caching strategies**
- ✅ **Structured logging and monitoring**
- ✅ **Performance optimization**
- ✅ **Error handling and recovery**
- ✅ **Security best practices**

The application is ready for production use and will provide reliable, scalable analytics for energy service providers.

## Additional Resources

- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)
- [Neo4j AuraDB Documentation](https://neo4j.com/docs/aura/)
- [Claude AI API Documentation](https://docs.anthropic.com/)
- [Project Repository](https://github.com/your-username/energy-agent-claude)

---

**Need Help?** If you encounter any issues during deployment, please check the troubleshooting section or create an issue in the project repository. 
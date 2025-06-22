# Streamlit Cloud Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the Energy Grid Management Agent to [Streamlit Cloud](https://share.streamlit.io/). It covers prerequisites, repository setup, environment variables, secrets management, deployment steps, troubleshooting, and production best practices.

---

## Prerequisites
- **GitHub account** with access to the repository
- **Streamlit Cloud account** ([sign up here](https://share.streamlit.io/signup))
- **Neo4j database** (AuraDB or self-hosted)
- **Claude API key** (from Anthropic)
- **Python 3.9+** specified in `requirements.txt`

---

## Repository Setup
1. **Push your code to GitHub**
   - Ensure your main app file is named `app_cloud.py` (or update Streamlit Cloud settings accordingly).
   - Include a `.streamlit/config.toml` file for custom configuration.
   - Ensure `requirements.txt` lists all dependencies.

2. **Recommended Directory Structure**
   ```
   energy-agent-claude/
   ├── app_cloud.py
   ├── requirements.txt
   ├── .streamlit/
   │   └── config.toml
   ├── docs/
   │   └── streamlit-cloud-deployment.md
   └── ...
   ```

---

## Environment Variables & Secrets
Streamlit Cloud uses the **Secrets Manager** for sensitive data. Add the following secrets in the Streamlit Cloud dashboard:

- `NEO4J_URI` (e.g., `neo4j+s://...`)
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`
- `CLAUDE_API_KEY`

**How to add secrets:**
1. Go to your app on [Streamlit Cloud](https://share.streamlit.io/).
2. Click **Settings** > **Secrets**.
3. Paste your secrets in the following format:
   ```
   NEO4J_URI=neo4j+s://...
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password
   CLAUDE_API_KEY=sk-...
   ```
4. Save changes.

---

## Deployment Steps
1. **Connect your GitHub repository** to Streamlit Cloud.
2. **Select the main file** (e.g., `app_cloud.py`).
3. **Set Python version** in `.streamlit/config.toml` (if needed):
   ```toml
   [runtime]
   python_version = "3.9"
   ```
4. **Configure secrets** as above.
5. **Click Deploy**. Streamlit Cloud will install dependencies and launch your app.

---

## Troubleshooting
- **App fails to start:**
  - Check logs for missing dependencies or import errors.
  - Ensure all secrets are set and correct.
  - Validate `requirements.txt` and `.streamlit/config.toml` syntax.
- **Database connection errors:**
  - Verify Neo4j URI, username, and password.
  - Ensure Neo4j is accessible from the cloud.
- **API key errors:**
  - Double-check the Claude API key and its permissions.
- **Memory/timeout issues:**
  - Optimize data queries and avoid loading large datasets at once.

---

## Best Practices for Production
- **Never commit secrets** to the repository.
- **Pin dependency versions** in `requirements.txt`.
- **Monitor app logs** for errors and performance issues.
- **Regularly update dependencies** and security patches.
- **Test locally** before deploying to Streamlit Cloud.
- **Use the provided GitHub Actions workflows** for CI/CD and code quality.

---

## References
- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)
- [Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Troubleshooting Guide](https://docs.streamlit.io/streamlit-community-cloud/troubleshooting) 
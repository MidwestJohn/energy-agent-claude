# Troubleshooting Guide

This guide helps resolve common issues when deploying or running the Energy Grid Management Agent on Streamlit Cloud.

---

## 1. App Fails to Start
- **Symptoms:** App does not load, shows error page, or crashes on startup.
- **Possible Causes:**
  - Missing or incorrect environment variables/secrets
  - Dependency installation failure
  - Syntax or import errors
- **Solutions:**
  - Check Streamlit Cloud logs for error details
  - Ensure all required secrets are set and correct
  - Validate `requirements.txt` and `.streamlit/config.toml` syntax
  - Test app locally before deploying

---

## 2. Database Connection Errors
- **Symptoms:** Errors like `Cannot connect to Neo4j`, `Authentication failed`, or timeouts
- **Possible Causes:**
  - Incorrect `NEO4J_URI`, `NEO4J_USERNAME`, or `NEO4J_PASSWORD`
  - Neo4j instance not running or not accessible from the cloud
- **Solutions:**
  - Double-check all Neo4j connection secrets
  - Ensure Neo4j is running and allows external connections
  - For AuraDB, verify cloud firewall settings

---

## 3. Claude API Key Errors
- **Symptoms:** Errors like `Invalid API key`, `Unauthorized`, or `API quota exceeded`
- **Possible Causes:**
  - Incorrect or expired `CLAUDE_API_KEY`
  - API key not enabled for required endpoints
- **Solutions:**
  - Verify the API key in Streamlit Cloud secrets
  - Check API key permissions and quota
  - Contact Anthropic support if needed

---

## 4. Memory or Timeout Issues
- **Symptoms:** App restarts, crashes, or times out on large queries
- **Possible Causes:**
  - Loading large datasets into memory
  - Inefficient queries or data processing
- **Solutions:**
  - Optimize queries and data handling
  - Use pagination or limit data volume
  - Monitor app logs for memory warnings

---

## 5. Dependency Issues
- **Symptoms:** Import errors, missing packages, or version conflicts
- **Possible Causes:**
  - Missing or incorrect package versions in `requirements.txt`
- **Solutions:**
  - Pin all dependencies with exact versions
  - Run `pip freeze > requirements.txt` after local testing

---

## 6. UI/Rendering Issues
- **Symptoms:** App UI is broken, charts not rendering, or widgets missing
- **Possible Causes:**
  - Incompatible Streamlit or Plotly versions
- **Solutions:**
  - Ensure `requirements.txt` specifies compatible versions
  - Test UI locally and on Streamlit Cloud

---

## 7. Security Warnings
- **Symptoms:** Warnings about exposed secrets or vulnerabilities
- **Possible Causes:**
  - Secrets committed to the repository
  - Outdated dependencies with known vulnerabilities
- **Solutions:**
  - Remove secrets from code and use environment variables
  - Update dependencies regularly
  - Use security scanning tools (Bandit, Safety)

---

## References
- [Streamlit Cloud Troubleshooting](https://docs.streamlit.io/streamlit-community-cloud/troubleshooting)
- [Neo4j AuraDB Support](https://neo4j.com/docs/aura/)
- [Anthropic Claude API Docs](https://docs.anthropic.com/claude/reference/getting-started-with-the-api) 
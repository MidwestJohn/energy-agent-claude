# Environment Variables Setup

This document lists all environment variables required for the Energy Grid Management Agent, their descriptions, example values, and security notes.

---

## Required Environment Variables

| Variable           | Description                                 | Example Value                        | Security Note                |
|--------------------|---------------------------------------------|--------------------------------------|------------------------------|
| NEO4J_URI          | Neo4j connection URI                        | neo4j+s://xxxx.databases.neo4j.io    | **Secret**                   |
| NEO4J_USERNAME     | Neo4j database username                     | neo4j                                | **Secret**                   |
| NEO4J_PASSWORD     | Neo4j database password                     | strongpassword123                    | **Secret**                   |
| CLAUDE_API_KEY     | Claude AI API key (Anthropic)               | sk-...                               | **Secret**                   |

---

## Optional Environment Variables

| Variable           | Description                                 | Example Value                        | Security Note                |
|--------------------|---------------------------------------------|--------------------------------------|------------------------------|
| STREAMLIT_SERVER_PORT | Custom port for Streamlit server         | 8501                                 | Not secret                   |
| STREAMLIT_SERVER_HEADLESS | Run Streamlit in headless mode       | true                                 | Not secret                   |
| LOG_LEVEL          | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO                                 | Not secret                   |

---

## How to Set Environment Variables

### Locally (using .env file)
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and fill in your values.

### On Streamlit Cloud
- Use the **Secrets Manager** in the app settings. Paste variables as:
  ```
  NEO4J_URI=neo4j+s://...
  NEO4J_USERNAME=neo4j
  NEO4J_PASSWORD=your_password
  CLAUDE_API_KEY=sk-...
  ```

---

## Security Notes
- **Never commit secrets** (passwords, API keys) to the repository.
- Use environment variables or Streamlit Cloud secrets for all sensitive data.
- Rotate secrets regularly and after any suspected exposure.

---

## References
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Neo4j AuraDB Docs](https://neo4j.com/docs/aura/)
- [Anthropic Claude API Docs](https://docs.anthropic.com/claude/reference/getting-started-with-the-api) 
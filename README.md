# Energy Grid Management Agent

A comprehensive energy grid management system that leverages Claude AI for intelligent analysis, risk assessment, and maintenance optimization of energy infrastructure equipment.

## 🎯 Project Overview

The Energy Grid Management Agent is an advanced analytics platform designed for energy service providers to monitor, analyze, and optimize their grid infrastructure. The system combines Neo4j graph database technology with Claude AI to provide intelligent insights into equipment maintenance, risk assessment, and operational efficiency.

### Key Features

- **🔍 Intelligent Equipment Analysis**: AI-powered analysis of maintenance patterns and equipment trends
- **⚠️ Risk Assessment**: Advanced risk scoring and predictive failure analysis
- **📊 Data Visualization**: Interactive dashboards with Plotly visualizations
- **🔄 Maintenance Optimization**: AI-driven maintenance scheduling and workflow optimization
- **📈 Trend Analysis**: Historical data analysis and predictive insights
- **🔗 Dependency Mapping**: Equipment dependency and impact analysis

### Technology Stack

- **Backend**: Python 3.8+
- **Database**: Neo4j Graph Database
- **AI Integration**: Claude AI (Anthropic)
- **Web Framework**: Streamlit
- **Data Visualization**: Plotly
- **Testing**: unittest with comprehensive mocking

## 📋 Prerequisites

Before installing the Energy Grid Management Agent, ensure you have:

- **Python 3.8 or higher**
- **Neo4j Database** (AuraDB or self-hosted)
- **Claude AI API Key** from Anthropic
- **Git** for version control
- **pip** package manager

### System Requirements

- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: 2GB free space
- **Network**: Internet connection for API calls
- **OS**: Windows 10+, macOS 10.14+, or Linux

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/energy-agent-claude.git
cd energy-agent-claude
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python -c "import streamlit, plotly, neo4j, anthropic; print('All dependencies installed successfully!')"
```

## ⚙️ Environment Setup

### 1. Create Environment File

Create a `.env` file in the project root:

```bash
touch .env
```

### 2. Configure Environment Variables

Add the following variables to your `.env` file:

```env
# Neo4j Database Configuration
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j

# Claude AI Configuration
CLAUDE_API_KEY=sk-ant-api03-your-api-key-here

# Application Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

## 🔑 API Key Setup

### Claude AI API Key

1. **Sign up** for an Anthropic account at [console.anthropic.com](https://console.anthropic.com)
2. **Navigate** to the API Keys section
3. **Create** a new API key
4. **Copy** the key (starts with `sk-ant-api03-`)
5. **Add** it to your `.env` file as `CLAUDE_API_KEY`

### API Key Validation

The system includes built-in API key validation:

```python
from claude_utils import validate_claude_api_key

# Validate your API key
is_valid = validate_claude_api_key("sk-ant-api03-your-key")
print(f"API Key is valid: {is_valid}")
```

## 🗄️ Neo4j Database Setup

### Option 1: Neo4j AuraDB (Recommended)

1. **Sign up** for Neo4j AuraDB at [neo4j.com/cloud/platform/aura-graph-database](https://neo4j.com/cloud/platform/aura-graph-database)
2. **Create** a new database instance
3. **Note** the connection details:
   - URI (neo4j+s://...)
   - Username (usually 'neo4j')
   - Password
4. **Add** these details to your `.env` file

### Option 2: Self-Hosted Neo4j

1. **Download** Neo4j Desktop or Community Edition
2. **Install** and start the database
3. **Create** a new database
4. **Set** username and password
5. **Configure** connection details in `.env`

### Database Schema

The system expects the following node types and relationships:

**Node Types:**
- `Generator`, `Transformer`, `Bus`, `Link`
- `MaintenanceRecord`, `Alert`, `Sensor`
- `Customer`, `Installation`, `Region`

**Key Relationships:**
- `HAS_MAINTENANCE_RECORD`
- `MONITORED_BY`
- `CONNECTED`
- `HAS_ALERT`

## 📖 Usage Guide

### Starting the Application

1. **Activate** your virtual environment
2. **Navigate** to the project directory
3. **Run** the Streamlit application:

```bash
streamlit run app.py
```

4. **Open** your browser to `http://localhost:8501`

### Application Interface

The application features a tabbed interface with the following sections:

#### 🏠 Dashboard Tab
- **Overview Metrics**: Equipment count, maintenance records, risk scores
- **Quick Actions**: Search equipment, view alerts, generate reports
- **Recent Activity**: Latest maintenance records and alerts

#### 🔍 Risk Assessment Tab
- **Risk Threshold Control**: Adjustable risk scoring threshold
- **Risk Visualization**: Interactive scatter plots and histograms
- **Risk Metrics**: High-risk equipment count, average risk scores
- **Export Functionality**: Download risk assessment data as CSV

#### 🔗 Dependencies Tab
- **Equipment Dependencies**: Visual mapping of equipment relationships
- **Impact Analysis**: Customer impact assessment for maintenance
- **Dependency Metrics**: Connection counts and critical paths

#### 📅 Maintenance Scheduling Tab
- **Schedule Generation**: AI-powered maintenance scheduling
- **Priority Assignment**: Risk-based priority scoring
- **Resource Allocation**: Manpower and budget optimization
- **Timeline View**: Calendar-based schedule visualization

#### 📊 Vibration Analysis Tab
- **Vibration Data**: Equipment vibration monitoring results
- **Trend Analysis**: Historical vibration patterns
- **Cost Impact**: Maintenance cost analysis by equipment type
- **Predictive Insights**: AI-generated recommendations

### Key Features Usage

#### Equipment Search
1. **Navigate** to the Dashboard tab
2. **Enter** search criteria (equipment type, location, etc.)
3. **Click** "Search Equipment"
4. **View** results with detailed information

#### Risk Assessment
1. **Go** to the Risk Assessment tab
2. **Adjust** the risk threshold slider
3. **Analyze** the scatter plot visualization
4. **Review** risk metrics and insights
5. **Export** data if needed

#### Maintenance Scheduling
1. **Select** the Maintenance Scheduling tab
2. **Choose** equipment for scheduling
3. **Set** time constraints and resources
4. **Generate** optimized schedule
5. **Review** and approve recommendations

## 🧪 Testing

### Running Tests

The project includes comprehensive unit tests:

```bash
# Run all tests
python -m unittest discover tests/

# Run specific test files
python -m unittest tests/test_energy_tools.py
python -m unittest tests/test_claude_integration.py
python -m unittest tests/test_utils.py

# Run with verbose output
python -m unittest discover tests/ -v
```

### Test Coverage

The test suite covers:
- **Database Operations**: Neo4j connection and query testing
- **AI Integration**: Claude API interaction testing
- **Utility Functions**: Data formatting and validation
- **Error Handling**: Exception scenarios and edge cases

## 🔧 Troubleshooting

### Common Issues

#### 1. Connection Errors

**Problem**: Cannot connect to Neo4j database
```
ConnectionError: Failed to connect to Neo4j database
```

**Solution**:
- Verify Neo4j URI, username, and password in `.env`
- Check network connectivity
- Ensure Neo4j service is running
- Verify database exists and is accessible

#### 2. API Key Issues

**Problem**: Claude API key validation fails
```
ClaudeAnalysisError: Invalid API key format
```

**Solution**:
- Verify API key starts with `sk-ant-api03-`
- Check for extra spaces or characters
- Ensure API key is active in Anthropic console
- Test key with simple API call

#### 3. Import Errors

**Problem**: Module import errors
```
ModuleNotFoundError: No module named 'streamlit'
```

**Solution**:
- Activate virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version compatibility
- Verify project structure

#### 4. Database Query Errors

**Problem**: Cypher query execution fails
```
ClientError: Query failed
```

**Solution**:
- Verify database schema matches expected structure
- Check node labels and relationship types
- Ensure sufficient database permissions
- Review query syntax and parameters

#### 5. Memory Issues

**Problem**: Application runs slowly or crashes
```
MemoryError: Insufficient memory
```

**Solution**:
- Close other applications to free memory
- Reduce data set size for testing
- Optimize database queries
- Increase system RAM if possible

### Performance Optimization

#### Database Optimization
- **Index Creation**: Create indexes on frequently queried properties
- **Query Optimization**: Use parameterized queries
- **Connection Pooling**: Configure appropriate pool sizes
- **Caching**: Implement result caching for repeated queries

#### Application Optimization
- **Data Pagination**: Load data in chunks
- **Lazy Loading**: Load data only when needed
- **Background Processing**: Use async operations for heavy tasks
- **Memory Management**: Clear unused variables and objects

## 🤝 Contributing

We welcome contributions to improve the Energy Grid Management Agent!

### Development Setup

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create** a feature branch: `git checkout -b feature/amazing-feature`
4. **Install** development dependencies: `pip install -r requirements-dev.txt`
5. **Make** your changes
6. **Add** tests for new functionality
7. **Run** tests: `python -m unittest discover tests/`
8. **Commit** your changes: `git commit -m 'Add amazing feature'`
9. **Push** to your branch: `git push origin feature/amazing-feature`
10. **Create** a Pull Request

### Code Style

- Follow **PEP 8** Python style guidelines
- Use **type hints** for function parameters and return values
- Write **comprehensive docstrings** for all functions and classes
- Include **error handling** for all external operations
- Add **unit tests** for new functionality

### Testing Guidelines

- **Test Coverage**: Aim for 90%+ test coverage
- **Mock External Dependencies**: Use unittest.mock for API and database calls
- **Test Edge Cases**: Include tests for error conditions and boundary values
- **Integration Tests**: Test component interactions
- **Performance Tests**: Test with realistic data volumes

### Documentation

- **Update README.md** for new features
- **Add inline comments** for complex logic
- **Document API changes** in code comments
- **Include usage examples** for new functions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### License Terms

```
MIT License

Copyright (c) 2024 Energy Grid Management Agent

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 📞 Support

### Getting Help

- **Documentation**: Check this README and inline code documentation
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Join community discussions on GitHub Discussions
- **Email**: Contact the development team for enterprise support

### Community

- **GitHub**: [Project Repository](https://github.com/your-username/energy-agent-claude)
- **Discussions**: [Community Forum](https://github.com/your-username/energy-agent-claude/discussions)
- **Issues**: [Bug Reports](https://github.com/your-username/energy-agent-claude/issues)

## 🔄 Version History

### v1.0.0 (Current)
- Initial release with core functionality
- Neo4j database integration
- Claude AI analysis capabilities
- Streamlit web interface
- Comprehensive test suite

### Planned Features
- Real-time monitoring dashboard
- Advanced predictive analytics
- Mobile application support
- Multi-tenant architecture
- Enhanced security features

---

**Note**: This is a development version. For production use, ensure proper security measures, backup strategies, and performance optimization are implemented. 
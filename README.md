# AI Property Research System

A sophisticated property research system built with CrewAI that uses multiple AI agents to search, analyze, and evaluate real estate listings. The system features a Streamlit dashboard with interactive maps and real-time analytics.

## Features

- 🤖 Multi-agent system with specialized roles:
  - Scout Agent: Web scraping and data collection
  - Analyzer Agent: Property evaluation and analysis
  - Planner Agent: Task coordination and optimization

- 🏠 Property Search Features:
  - Multi-source property listing scraping
  - Customizable search criteria
  - Price and location-based filtering
  - Investment potential analysis

- 📊 Interactive Dashboard:
  - Interactive map visualization
  - Property listing details
  - Market analytics and insights
  - Match score distribution

## Project Structure

```
ai-property-researcher/
├── config/
│   ├── agents.yaml     # Agent definitions and configurations
│   └── tasks.yaml      # Task definitions and workflows
├── tools/
│   ├── scraping_tools.py   # Web scraping implementations
│   └── analysis_tools.py   # Property analysis tools
├── data/
│   └── properties.json     # Local property database
├── app.py              # Streamlit UI implementation
├── crew.py            # CrewAI orchestration logic
├── main.py            # Main execution flow
├── requirements.txt    # Project dependencies
└── .env               # Environment configuration
```

## Prerequisites

- Python 3.8+
- pip package manager
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-property-researcher.git
cd ai-property-researcher
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configurations
```

## Configuration

1. Environment Variables (.env):
- `OPENAI_API_KEY`: Your OpenAI API key
- `MAX_LISTINGS`: Maximum number of listings to fetch (default: 100)
- `SEARCH_RADIUS`: Search radius in miles (default: 20)

2. Agent Configuration (config/agents.yaml):
- Customize agent roles, goals, and tools
- Adjust LLM parameters (model, temperature)

3. Task Configuration (config/tasks.yaml):
- Modify task dependencies and parameters
- Configure website sources and search criteria

## Usage

1. Start the Streamlit dashboard:
```bash
streamlit run app.py
```

2. Access the dashboard at http://localhost:8501

3. Use the sidebar to set search criteria:
- Price range
- Location
- Property type

4. Click "Start Property Search" to begin the agent-based search

## Agent Workflows

1. **Scout Agent**
- Scrapes property listings from configured websites
- Validates and cleans raw data
- Stores structured information in the database

2. **Analyzer Agent**
- Evaluates properties against user criteria
- Calculates match scores and investment potential
- Generates property insights and recommendations

3. **Planner Agent**
- Coordinates agent activities
- Optimizes search strategies
- Manages task priorities and dependencies

## Data Storage

Properties are stored in `data/properties.json` with the following structure:
```json
{
  "title": "Property Title",
  "price": "500000",
  "location": "Address",
  "details": {
    "bedrooms": 3,
    "bathrooms": 2,
    "sqft": 1500
  },
  "features": ["Garage", "Pool"],
  "match_score": 0.85,
  "location_analysis": {
    "coordinates": {
      "latitude": 37.7749,
      "longitude": -122.4194
    }
  }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- CrewAI for the multi-agent framework
- Streamlit for the interactive dashboard
- Folium for map visualizations 
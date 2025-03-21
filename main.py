import os
import json
from crew import PropertyResearchCrew
import streamlit as st
from dotenv import load_dotenv

def setup_environment():
    """Setup environment variables and create necessary directories"""
    load_dotenv()
    
    # Create required directories if they don't exist
    directories = ['config', 'data', 'tools']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def initialize_data():
    """Initialize the properties database if it doesn't exist"""
    if not os.path.exists('data/properties.json'):
        with open('data/properties.json', 'w') as f:
            json.dump([], f)

def main():
    """Main execution flow"""
    # Setup environment
    setup_environment()
    initialize_data()
    
    # Create and run the property research crew
    crew = PropertyResearchCrew()
    
    # Default search criteria (can be modified via the Streamlit UI)
    default_criteria = {
        "price_range": (300000, 800000),
        "location": "San Francisco, CA",
        "property_type": "Single Family"
    }
    
    # Execute the crew with default criteria
    # Note: In practice, criteria will come from the Streamlit UI
    results = crew.run(default_criteria)
    
    print(f"Found {len(results)} properties matching criteria")
    return results

if __name__ == "__main__":
    main() 
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from crew import PropertyResearchCrew
import streamlit as st
from dotenv import load_dotenv

def setup_logging():
    """Configure logging for the application"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"property_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def setup_environment():
    """Setup environment variables and create necessary directories"""
    load_dotenv()
    
    # Create required directories
    directories = ['config', 'data', 'tools', 'logs', 'cache']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    # Validate environment variables
    required_vars = [
        'OPENAI_API_KEY',
        'MAX_LISTINGS',
        'SEARCH_RADIUS',
        'USER_AGENT'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

def initialize_data():
    """Initialize the properties database and cache"""
    # Initialize properties database
    if not os.path.exists('data/properties.json'):
        with open('data/properties.json', 'w') as f:
            json.dump([], f)
    
    # Initialize cache directory
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    
    # Create cache cleanup script
    cleanup_script = cache_dir / "cleanup.sh"
    if not cleanup_script.exists():
        with open(cleanup_script, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('find . -type f -mtime +7 -delete\n')
        os.chmod(cleanup_script, 0o755)

def validate_configuration():
    """Validate configuration files and settings"""
    config_files = {
        'config/agents.yaml': 'Agent configuration',
        'config/tasks.yaml': 'Task configuration'
    }
    
    for file_path, description in config_files.items():
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Missing {description} file: {file_path}")

def main():
    """Main execution flow"""
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Property Research System")
    
    try:
        # Setup environment
        setup_environment()
        logger.info("Environment setup completed")
        
        # Initialize data structures
        initialize_data()
        logger.info("Data structures initialized")
        
        # Validate configuration
        validate_configuration()
        logger.info("Configuration validated")
        
        # Create and run the property research crew
        crew = PropertyResearchCrew()
        logger.info("CrewAI system initialized")
        
        # Default search criteria (can be modified via the Streamlit UI)
        default_criteria = {
            "price_range": (
                float(os.getenv("MIN_PRICE", 300000)),
                float(os.getenv("MAX_PRICE", 800000))
            ),
            "location": os.getenv("DEFAULT_LOCATION", "San Francisco, CA"),
            "property_type": "Single Family",
            "preferences": {
                "target_sqft": 2000,
                "required_amenities": ["parking", "central_air"]
            }
        }
        
        # Execute the crew with default criteria
        logger.info("Starting property search with default criteria")
        results = crew.run(default_criteria)
        
        logger.info(f"Search completed. Found {len(results)} properties matching criteria")
        return results
        
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 
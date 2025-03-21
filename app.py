import streamlit as st
import folium
from streamlit_folium import folium_static
import json
import pandas as pd
from crew import PropertyResearchCrew
from typing import Dict, List

def load_properties() -> List[Dict]:
    """Load properties from JSON database"""
    try:
        with open('data/properties.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def create_map(properties: List[Dict]):
    """Create a folium map with property markers"""
    # Initialize map centered on the first property or default location
    if properties and 'location_analysis' in properties[0]:
        center = [
            properties[0]['location_analysis']['coordinates']['latitude'],
            properties[0]['location_analysis']['coordinates']['longitude']
        ]
    else:
        center = [37.7749, -122.4194]  # Default to San Francisco

    m = folium.Map(location=center, zoom_start=12)

    # Add markers for each property
    for prop in properties:
        if 'location_analysis' in prop and 'coordinates' in prop['location_analysis']:
            coords = prop['location_analysis']['coordinates']
            folium.Marker(
                [coords['latitude'], coords['longitude']],
                popup=f"{prop.get('title', 'Property')}<br>Price: {prop.get('price', 'N/A')}",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)

    return m

def main():
    st.title("AI Property Research Dashboard")
    st.sidebar.header("Search Criteria")

    # Search criteria inputs
    price_range = st.sidebar.slider(
        "Price Range ($)",
        min_value=100000,
        max_value=2000000,
        value=(300000, 800000),
        step=50000
    )

    location = st.sidebar.text_input(
        "Target Location",
        "San Francisco, CA"
    )

    property_type = st.sidebar.selectbox(
        "Property Type",
        ["Single Family", "Condo", "Townhouse", "Multi-Family"]
    )

    if st.sidebar.button("Start Property Search"):
        with st.spinner("AI agents are searching for properties..."):
            crew = PropertyResearchCrew()
            search_criteria = {
                "price_range": price_range,
                "location": location,
                "property_type": property_type
            }
            crew.run(search_criteria)
            st.success("Search completed!")

    # Load and display properties
    properties = load_properties()
    
    if properties:
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Map View", "List View", "Analytics"])
        
        with tab1:
            st.subheader("Property Locations")
            m = create_map(properties)
            folium_static(m)
        
        with tab2:
            st.subheader("Property List")
            for prop in properties:
                with st.expander(f"{prop.get('title', 'Property')} - {prop.get('price', 'N/A')}"):
                    st.write(f"**Location:** {prop.get('location', 'N/A')}")
                    st.write(f"**Match Score:** {prop.get('match_score', 'N/A')}")
                    if 'features' in prop:
                        st.write("**Features:**")
                        for feature in prop['features']:
                            st.write(f"- {feature}")
        
        with tab3:
            st.subheader("Market Analytics")
            if properties:
                df = pd.DataFrame(properties)
                
                # Price distribution
                if 'price' in df.columns:
                    st.write("**Price Distribution**")
                    st.bar_chart(df['price'])
                
                # Match score distribution
                if 'match_score' in df.columns:
                    st.write("**Match Score Distribution**")
                    st.bar_chart(df['match_score'])
                
                # Location heat map
                if 'location_analysis' in df.columns:
                    st.write("**Location Analysis**")
                    location_data = pd.DataFrame([
                        p['location_analysis']['coordinates']
                        for p in properties
                        if 'location_analysis' in p and 'coordinates' in p['location_analysis']
                    ])
                    st.map(location_data)
    else:
        st.info("No properties found. Start a search to see results.")

if __name__ == "__main__":
    main() 
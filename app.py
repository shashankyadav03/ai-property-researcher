import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import pandas as pd
from crew import PropertyResearchCrew
from typing import Dict, List
import plotly.express as px

def load_properties() -> Dict:
    """Load properties from JSON database"""
    try:
        with open('data/properties.json', 'r') as f:
            cache_data = json.load(f)
            # Return the entire cache data structure
            return cache_data if isinstance(cache_data, dict) else {"result": [], "search_criteria": {}, "timestamp": ""}
    except FileNotFoundError:
        return {"result": [], "search_criteria": {}, "timestamp": ""}

def create_map(properties_data):
    if not properties_data or 'result' not in properties_data:
        return folium.Map(location=[39.8283, -98.5795], zoom_start=4)

    # Find the property listings data (usually the second task output)
    properties_list = None
    for task_output in properties_data['result']:
        if 'Scrape property listings' in task_output['description']:
            # Parse the raw JSON string into a dictionary
            try:
                raw_json = task_output['raw'].strip('```json\n').strip('```')
                listings_data = json.loads(raw_json)
                properties_list = listings_data.get('properties', [])
                break
            except json.JSONDecodeError:
                st.error("Failed to parse property listings data")
                continue

    if not properties_list:
        return folium.Map(location=[39.8283, -98.5795], zoom_start=4)

    # Create map centered on the US
    m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)
    
    # Add markers for each property
    for prop in properties_list:
        location = prop.get('location', {})
        price = prop.get('price', {}).get('amount', 'N/A')
        title = prop.get('title', 'Property')
        description = f"{title}<br>Price: ${price:,}<br>{location.get('city', '')}, {location.get('state', '')}"
        
        # You'll need to implement geocoding here to get lat/lng from address
        # For now, using dummy coordinates
        folium.Marker(
            location=[39.8283, -98.5795],  # Replace with actual geocoded coordinates
            popup=description,
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
            st_folium(m, width=700, height=500)
        
        with tab2:
            st.subheader("Property List")
            # Find the analysis data
            analysis_data = None
            for task_output in properties['result']:
                if 'Analyze properties' in task_output['description']:
                    try:
                        raw_json = task_output['raw'].strip('```json\n').strip('```')
                        analysis_data = json.loads(raw_json)
                        break
                    except json.JSONDecodeError:
                        st.error("Failed to parse property analysis data")
                        continue

            if analysis_data and 'analysis' in analysis_data:
                for prop in analysis_data['analysis']['properties']:
                    with st.expander(f"{prop['address']} - ${prop['price']:,}"):
                        st.write(f"**Address:** {prop['address']}")
                        st.write(f"**Price:** ${prop['price']:,}")
                        st.write(f"**Square Footage:** {prop['square_footage']}")
                        st.write(f"**Bedrooms:** {prop['bedrooms']}")
                        st.write(f"**Bathrooms:** {prop['bathrooms']}")
                        
                        # Investment return
                        if 'investment_return' in prop:
                            st.write("**Investment Return:**")
                            inv = prop['investment_return']
                            st.write(f"- Annual Growth Rate: {inv['annual_growth_rate']}%")
                            st.write(f"- Expected Value in 5 Years: ${inv['expected_value_in_5_years']:,}")
                        
                        # Risks
                        if 'risks' in prop:
                            st.write("**Risks:**")
                            for risk in prop['risks']:
                                st.write(f"- {risk['type']}: {risk['description']}")
            else:
                st.info("No property analysis data available")
        
        with tab3:
            st.subheader("Market Analytics")
            if analysis_data and 'analysis' in analysis_data:
                # Market trends
                if 'market_trends' in analysis_data['analysis']:
                    trends = analysis_data['analysis']['market_trends']
                    st.write("**Market Trends:**")
                    st.write(f"- Current Demand: {trends['current_demand']}")
                    st.write(f"- Forecasted Growth: {trends['forecasted_growth']}")
                    
                    if 'potential_opportunities' in trends:
                        st.write("**Potential Opportunities:**")
                        for opportunity in trends['potential_opportunities']:
                            st.write(f"- {opportunity['type']}: {opportunity['description']}")

                # Create DataFrame for visualization
                props_df = pd.DataFrame(analysis_data['analysis']['properties'])
                if not props_df.empty:
                    st.write("**Price Distribution**")
                    fig = px.histogram(props_df, x='price', title='Property Price Distribution')
                    st.plotly_chart(fig)

            else:
                st.info("No market analytics data available")
    else:
        st.info("No properties found. Start a search to see results.")

if __name__ == "__main__":
    main() 
from typing import Dict, List
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

class PropertyAnalysisTool(BaseTool):
    name = "PropertyAnalysisTool"
    description = "Tool for analyzing property data against user criteria"

    def _analyze_property(self, property_data: Dict, criteria: Dict) -> Dict:
        analysis = {
            "match_score": 0,
            "price_analysis": {},
            "location_analysis": {},
            "investment_potential": {},
            "recommendations": []
        }

        # Price Analysis
        if "price_range" in criteria and "price" in property_data:
            min_price, max_price = criteria["price_range"]
            price = self._extract_price(property_data["price"])
            analysis["price_analysis"] = {
                "within_range": min_price <= price <= max_price,
                "difference_from_min": price - min_price,
                "difference_from_max": max_price - price
            }

        # Location Analysis
        if "location" in criteria and "location" in property_data:
            analysis["location_analysis"] = self._analyze_location(
                property_data["location"],
                criteria["location"]
            )

        # Calculate match score
        analysis["match_score"] = self._calculate_match_score(analysis, criteria)

        return analysis

    def _extract_price(self, price_str: str) -> float:
        # Remove currency symbols and convert to float
        return float(''.join(filter(str.isdigit, price_str)))

    def _analyze_location(self, property_location: str, target_location: str) -> Dict:
        geolocator = Nominatim(user_agent="property_analyzer")
        
        try:
            prop_location = geolocator.geocode(property_location)
            target_loc = geolocator.geocode(target_location)
            
            if prop_location and target_loc:
                distance = geodesic(
                    (prop_location.latitude, prop_location.longitude),
                    (target_loc.latitude, target_loc.longitude)
                ).miles
                
                return {
                    "distance_miles": round(distance, 2),
                    "coordinates": {
                        "latitude": prop_location.latitude,
                        "longitude": prop_location.longitude
                    }
                }
        except Exception as e:
            return {"error": str(e)}
        
        return {}

    def _calculate_match_score(self, analysis: Dict, criteria: Dict) -> float:
        score = 0.0
        weights = {
            "price": 0.4,
            "location": 0.4,
            "features": 0.2
        }
        
        # Price score
        if "price_analysis" in analysis and analysis["price_analysis"].get("within_range"):
            score += weights["price"]
            
        # Location score
        if "location_analysis" in analysis and "distance_miles" in analysis["location_analysis"]:
            distance = analysis["location_analysis"]["distance_miles"]
            if distance <= 5:
                score += weights["location"]
            elif distance <= 10:
                score += weights["location"] * 0.7
            elif distance <= 20:
                score += weights["location"] * 0.4
                
        return round(score, 2)

    def _run(self, property_data: Dict, criteria: Dict) -> Dict:
        """Execute the property analysis tool"""
        return self._analyze_property(property_data, criteria)

class DataValidationTool(BaseTool):
    name = "DataValidationTool"
    description = "Tool for validating property data format and completeness"

    def _validate_property_data(self, data: Dict) -> Dict:
        required_fields = ["title", "price", "location", "details"]
        validation_results = {
            "is_valid": True,
            "missing_fields": [],
            "warnings": [],
            "cleaned_data": {}
        }

        # Check required fields
        for field in required_fields:
            if field not in data:
                validation_results["is_valid"] = False
                validation_results["missing_fields"].append(field)

        # Clean and validate data
        cleaned_data = self._clean_data(data)
        validation_results["cleaned_data"] = cleaned_data

        return validation_results

    def _clean_data(self, data: Dict) -> Dict:
        cleaned = data.copy()
        
        # Clean price
        if "price" in cleaned:
            cleaned["price"] = self._clean_price(cleaned["price"])
            
        # Clean location
        if "location" in cleaned:
            cleaned["location"] = cleaned["location"].strip()
            
        return cleaned

    def _clean_price(self, price: str) -> str:
        # Remove non-numeric characters except decimal point
        return ''.join(char for char in price if char.isdigit() or char == '.')

    def _run(self, data: Dict) -> Dict:
        """Execute the data validation tool"""
        return self._validate_property_data(data) 
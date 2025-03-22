from typing import Dict, List
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import os
from dotenv import load_dotenv
import numpy as np
from datetime import datetime

load_dotenv()

class PropertyAnalysisTool(BaseTool):
    name: str = "PropertyAnalysisTool"
    description: str = "Tool for analyzing property data and generating insights"

    def _analyze_property(self, property_data: Dict, criteria: Dict) -> Dict:
        analysis = {
            "match_score": 0,
            "price_analysis": {},
            "location_analysis": {},
            "investment_potential": {},
            "recommendations": [],
            "timestamp": datetime.now().isoformat()
        }

        # Price Analysis
        if "price_range" in criteria and "price" in property_data:
            analysis["price_analysis"] = self._analyze_price(
                self._extract_price(property_data["price"]),
                criteria["price_range"]
            )

        # Location Analysis
        if "location" in criteria and "location" in property_data:
            analysis["location_analysis"] = self._analyze_location(
                property_data["location"],
                criteria["location"]
            )

        # Property Details Analysis
        if "details" in property_data:
            analysis["details_analysis"] = self._analyze_details(
                property_data["details"],
                criteria.get("preferences", {})
            )

        # Investment Potential Analysis
        analysis["investment_potential"] = self._analyze_investment_potential(
            property_data,
            analysis["location_analysis"],
            analysis["price_analysis"]
        )

        # Generate Recommendations
        analysis["recommendations"] = self._generate_recommendations(
            property_data,
            analysis
        )

        # Calculate final match score
        analysis["match_score"] = self._calculate_match_score(analysis, criteria)

        return analysis

    def _analyze_price(self, price: float, price_range: tuple) -> Dict:
        min_price, max_price = price_range
        price_analysis = {
            "within_range": min_price <= price <= max_price,
            "difference_from_min": price - min_price,
            "difference_from_max": max_price - price,
            "percentage_from_min": ((price - min_price) / min_price) * 100 if min_price > 0 else 0,
            "percentage_from_max": ((max_price - price) / max_price) * 100 if max_price > 0 else 0,
            "price_per_sqft": None
        }

        return price_analysis

    def _analyze_details(self, details: Dict, preferences: Dict) -> Dict:
        analysis = {
            "size_score": 0,
            "amenities_score": 0,
            "condition_score": 0,
            "missing_features": []
        }

        # Analyze size and layout
        if "sqft" in details:
            target_size = preferences.get("target_sqft", 2000)
            size_diff = abs(details["sqft"] - target_size)
            analysis["size_score"] = max(0, 1 - (size_diff / target_size))

        # Check for required amenities
        required_amenities = preferences.get("required_amenities", [])
        available_features = details.get("features", [])
        
        for amenity in required_amenities:
            if amenity not in available_features:
                analysis["missing_features"].append(amenity)

        analysis["amenities_score"] = 1 - (len(analysis["missing_features"]) / len(required_amenities)) if required_amenities else 1

        return analysis

    def _analyze_investment_potential(self, property_data: Dict, location_analysis: Dict, price_analysis: Dict) -> Dict:
        potential = {
            "score": 0,
            "factors": [],
            "risks": [],
            "opportunities": []
        }

        # Location-based factors
        if location_analysis.get("neighborhood_score", 0) > 0.7:
            potential["factors"].append("Prime location")
            potential["score"] += 0.3

        # Price-based factors
        if price_analysis.get("price_per_sqft"):
            avg_price_per_sqft = float(os.getenv("AVG_PRICE_PER_SQFT", "200"))
            if price_analysis["price_per_sqft"] < avg_price_per_sqft:
                potential["factors"].append("Below market price per sqft")
                potential["score"] += 0.2
                potential["opportunities"].append("Potential for value appreciation")

        # Property condition and features
        if "details" in property_data:
            details = property_data["details"]
            if details.get("year_built"):
                age = datetime.now().year - details["year_built"]
                if age < 10:
                    potential["factors"].append("New construction")
                    potential["score"] += 0.2
                elif age > 30:
                    potential["risks"].append("May require significant maintenance")
                    potential["score"] -= 0.1

        # Normalize score
        potential["score"] = max(0, min(1, potential["score"]))

        return potential

    def _generate_recommendations(self, property_data: Dict, analysis: Dict) -> List[str]:
        recommendations = []

        # Price-based recommendations
        if analysis["price_analysis"].get("within_range"):
            if analysis["price_analysis"].get("percentage_from_min", 0) < 10:
                recommendations.append("Consider negotiating price due to proximity to minimum budget")
        else:
            recommendations.append("Property price is outside specified range")

        # Location-based recommendations
        if "distance_miles" in analysis.get("location_analysis", {}):
            distance = analysis["location_analysis"]["distance_miles"]
            if distance > 20:
                recommendations.append("Consider impact of long commute")
            elif distance < 5:
                recommendations.append("Excellent location within target area")

        # Investment-based recommendations
        investment = analysis["investment_potential"]
        if investment["score"] > 0.7:
            recommendations.append("Strong investment potential")
            recommendations.extend([f"Opportunity: {o}" for o in investment["opportunities"]])
        elif investment["score"] < 0.3:
            recommendations.append("Exercise caution with this investment")
            recommendations.extend([f"Risk: {r}" for r in investment["risks"]])

        return recommendations

    def _extract_price(self, price_str: str) -> float:
        """Extract numeric price value"""
        try:
            return float(''.join(filter(str.isdigit, price_str)))
        except ValueError:
            return 0.0

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
                    },
                    "neighborhood_score": self._calculate_neighborhood_score(
                        prop_location.latitude,
                        prop_location.longitude
                    )
                }
        except Exception as e:
            return {"error": str(e)}
        
        return {}

    def _calculate_neighborhood_score(self, lat: float, lon: float) -> float:
        """Calculate a neighborhood score based on location"""
        # This is a placeholder for more sophisticated neighborhood analysis
        # In a real implementation, you would integrate with external APIs
        # to get crime rates, school ratings, amenities, etc.
        return np.random.uniform(0.5, 1.0)

    def _calculate_match_score(self, analysis: Dict, criteria: Dict) -> float:
        weights = {
            "price": 0.3,
            "location": 0.3,
            "details": 0.2,
            "investment": 0.2
        }
        
        score = 0.0
        
        # Price score
        if analysis["price_analysis"].get("within_range"):
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

        # Details score
        if "details_analysis" in analysis:
            details_score = (
                analysis["details_analysis"]["size_score"] * 0.5 +
                analysis["details_analysis"]["amenities_score"] * 0.5
            )
            score += weights["details"] * details_score

        # Investment potential score
        if "investment_potential" in analysis:
            score += weights["investment"] * analysis["investment_potential"]["score"]
                
        return round(score, 2)

    def _run(self, property_data: Dict, criteria: Dict) -> Dict:
        """Execute the property analysis tool"""
        return self._analyze_property(property_data, criteria)

class DataValidationTool(BaseTool):
    name: str = "DataValidationTool"
    description: str = "Tool for validating property data format and completeness"

    def _validate_property_data(self, data: Dict) -> Dict:
        validation_results = {
            "is_valid": True,
            "missing_fields": [],
            "warnings": [],
            "cleaned_data": {},
            "validation_timestamp": datetime.now().isoformat()
        }

        # Required fields with their validation rules
        required_fields = {
            "title": self._validate_text,
            "price": self._validate_price,
            "location": self._validate_location,
            "details": self._validate_details
        }

        # Validate each required field
        for field, validator in required_fields.items():
            if field not in data:
                validation_results["is_valid"] = False
                validation_results["missing_fields"].append(field)
            else:
                field_validation = validator(data[field])
                if not field_validation["is_valid"]:
                    validation_results["warnings"].extend(field_validation["warnings"])

        # Clean and validate data
        validation_results["cleaned_data"] = self._clean_data(data)

        return validation_results

    def _validate_text(self, value: str) -> Dict:
        """Validate text fields"""
        result = {"is_valid": True, "warnings": []}
        if not value or not isinstance(value, str):
            result["is_valid"] = False
            result["warnings"].append("Invalid or empty text value")
        elif len(value.strip()) == 0:
            result["warnings"].append("Text value is empty after trimming")
        return result

    def _validate_price(self, price: str) -> Dict:
        """Validate price field"""
        result = {"is_valid": True, "warnings": []}
        if not price:
            result["is_valid"] = False
            result["warnings"].append("Missing price")
            return result

        try:
            price_value = float(''.join(filter(str.isdigit, price)))
            if price_value <= 0:
                result["warnings"].append("Price value is zero or negative")
            elif price_value < 10000:
                result["warnings"].append("Price seems unusually low")
            elif price_value > 100000000:
                result["warnings"].append("Price seems unusually high")
        except ValueError:
            result["is_valid"] = False
            result["warnings"].append("Invalid price format")

        return result

    def _validate_location(self, location: str) -> Dict:
        """Validate location field"""
        result = {"is_valid": True, "warnings": []}
        if not location or not isinstance(location, str):
            result["is_valid"] = False
            result["warnings"].append("Invalid location format")
        elif len(location.strip()) < 5:
            result["warnings"].append("Location seems too short")
        return result

    def _validate_details(self, details: Dict) -> Dict:
        """Validate property details"""
        result = {"is_valid": True, "warnings": []}
        if not isinstance(details, dict):
            result["is_valid"] = False
            result["warnings"].append("Details must be a dictionary")
            return result

        # Validate specific details
        if "bedrooms" in details and not isinstance(details["bedrooms"], (int, float)):
            result["warnings"].append("Invalid bedrooms value")
        if "bathrooms" in details and not isinstance(details["bathrooms"], (int, float)):
            result["warnings"].append("Invalid bathrooms value")
        if "sqft" in details and not isinstance(details["sqft"], (int, float)):
            result["warnings"].append("Invalid square footage value")

        return result

    def _clean_data(self, data: Dict) -> Dict:
        """Clean and standardize property data"""
        cleaned = data.copy()
        
        # Clean price
        if "price" in cleaned:
            cleaned["price"] = self._clean_price(cleaned["price"])
            
        # Clean location
        if "location" in cleaned:
            cleaned["location"] = cleaned["location"].strip()
            
        # Clean details
        if "details" in cleaned and isinstance(cleaned["details"], dict):
            cleaned["details"] = {
                k: self._clean_numeric(v) if k in ["bedrooms", "bathrooms", "sqft"] else v
                for k, v in cleaned["details"].items()
            }
            
        # Clean features
        if "features" in cleaned and isinstance(cleaned["features"], list):
            cleaned["features"] = [f.strip() for f in cleaned["features"] if f.strip()]
            
        return cleaned

    def _clean_price(self, price: str) -> str:
        """Clean price string"""
        if not price:
            return ""
        # Remove all non-numeric characters except decimal point
        return ''.join(char for char in price if char.isdigit() or char == '.')

    def _clean_numeric(self, value: any) -> float:
        """Convert value to float if possible"""
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            try:
                return float(''.join(filter(str.isdigit, value)))
            except ValueError:
                return 0.0
        return 0.0

    def _run(self, data: Dict) -> Dict:
        """Execute the data validation tool"""
        return self._validate_property_data(data) 
from typing import Dict, List
import requests
from bs4 import BeautifulSoup
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
import time
import re
from urllib.parse import urlparse

load_dotenv()

class BeautifulSoupTool(BaseTool):
    name: str = "BeautifulSoupTool"
    description: str = "Tool for scraping property listings using BeautifulSoup"

    def _scrape_website(self, url: str) -> Dict:
        headers = {
            'User-Agent': os.getenv('USER_AGENT'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        try:
            # Add rate limiting
            time.sleep(float(os.getenv('RATE_LIMIT_DELAY', '2')))
            
            response = requests.get(
                url, 
                headers=headers, 
                timeout=int(os.getenv('REQUEST_TIMEOUT', '30'))
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Determine which parser to use based on the domain
            domain = urlparse(url).netloc
            if 'zillow.com' in domain:
                return self._parse_zillow(soup)
            elif 'realtor.com' in domain:
                return self._parse_realtor(soup)
            elif 'redfin.com' in domain:
                return self._parse_redfin(soup)
            else:
                return self._parse_generic(soup)
                
        except Exception as e:
            return {"error": str(e)}

    def _parse_zillow(self, soup: BeautifulSoup) -> Dict:
        property_data = self._initialize_property_data()
        
        # Zillow-specific parsing
        try:
            # Title/Address
            address_elem = soup.find('h1', {'class': 'ds-address-container'})
            if address_elem:
                property_data["title"] = address_elem.text.strip()
                property_data["location"] = address_elem.text.strip()

            # Price
            price_elem = soup.find('span', {'class': 'ds-price'})
            if price_elem:
                property_data["price"] = self._clean_price(price_elem.text)

            # Details
            details = soup.find('div', {'class': 'ds-home-facts-and-features'})
            if details:
                beds = details.find('span', text=re.compile(r'bed'))
                baths = details.find('span', text=re.compile(r'bath'))
                sqft = details.find('span', text=re.compile(r'sqft'))
                
                property_data["details"] = {
                    "bedrooms": self._extract_number(beds.text if beds else ""),
                    "bathrooms": self._extract_number(baths.text if baths else ""),
                    "sqft": self._extract_number(sqft.text if sqft else "")
                }

            # Features
            features = soup.find_all('li', {'class': 'ds-home-fact-list-item'})
            property_data["features"] = [f.text.strip() for f in features if f.text.strip()]

        except Exception as e:
            property_data["error"] = str(e)

        return property_data

    def _parse_realtor(self, soup: BeautifulSoup) -> Dict:
        property_data = self._initialize_property_data()
        
        try:
            # Title/Address
            address_elem = soup.find('h1', {'class': 'listing-detail-title'})
            if address_elem:
                property_data["title"] = address_elem.text.strip()
                property_data["location"] = address_elem.text.strip()

            # Price
            price_elem = soup.find('div', {'class': 'listing-price'})
            if price_elem:
                property_data["price"] = self._clean_price(price_elem.text)

            # Details
            details = soup.find('div', {'class': 'listing-details'})
            if details:
                property_data["details"] = {
                    "bedrooms": self._extract_number(details.find('li', text=re.compile(r'bed')).text if details.find('li', text=re.compile(r'bed')) else ""),
                    "bathrooms": self._extract_number(details.find('li', text=re.compile(r'bath')).text if details.find('li', text=re.compile(r'bath')) else ""),
                    "sqft": self._extract_number(details.find('li', text=re.compile(r'sqft')).text if details.find('li', text=re.compile(r'sqft')) else "")
                }

            # Features
            features = soup.find_all('li', {'class': 'feature-item'})
            property_data["features"] = [f.text.strip() for f in features if f.text.strip()]

        except Exception as e:
            property_data["error"] = str(e)

        return property_data

    def _parse_redfin(self, soup: BeautifulSoup) -> Dict:
        property_data = self._initialize_property_data()
        
        try:
            # Title/Address
            address_elem = soup.find('h1', {'class': 'address-title'})
            if address_elem:
                property_data["title"] = address_elem.text.strip()
                property_data["location"] = address_elem.text.strip()

            # Price
            price_elem = soup.find('div', {'class': 'price-section'})
            if price_elem:
                property_data["price"] = self._clean_price(price_elem.text)

            # Details
            details = soup.find('div', {'class': 'home-details'})
            if details:
                property_data["details"] = {
                    "bedrooms": self._extract_number(details.find('div', text=re.compile(r'Beds')).text if details.find('div', text=re.compile(r'Beds')) else ""),
                    "bathrooms": self._extract_number(details.find('div', text=re.compile(r'Baths')).text if details.find('div', text=re.compile(r'Baths')) else ""),
                    "sqft": self._extract_number(details.find('div', text=re.compile(r'Sq Ft')).text if details.find('div', text=re.compile(r'Sq Ft')) else "")
                }

            # Features
            features = soup.find_all('div', {'class': 'feature-item'})
            property_data["features"] = [f.text.strip() for f in features if f.text.strip()]

        except Exception as e:
            property_data["error"] = str(e)

        return property_data

    def _parse_generic(self, soup: BeautifulSoup) -> Dict:
        """Generic parser for unknown websites"""
        property_data = self._initialize_property_data()
        
        try:
            # Try common patterns for property data
            # Title/Address
            title_candidates = [
                soup.find('h1'),
                soup.find('div', {'class': re.compile(r'address|location|title', re.I)}),
                soup.find('span', {'class': re.compile(r'address|location|title', re.I)})
            ]
            for candidate in title_candidates:
                if candidate and candidate.text.strip():
                    property_data["title"] = candidate.text.strip()
                    property_data["location"] = candidate.text.strip()
                    break

            # Price
            price_candidates = [
                soup.find(text=re.compile(r'\$[\d,]+')),
                soup.find('div', text=re.compile(r'\$[\d,]+')),
                soup.find('span', text=re.compile(r'\$[\d,]+'))
            ]
            for candidate in price_candidates:
                if candidate:
                    property_data["price"] = self._clean_price(candidate.text)
                    break

            # Details
            property_data["details"] = {
                "bedrooms": self._extract_number(str(soup.find(text=re.compile(r'bed', re.I)))),
                "bathrooms": self._extract_number(str(soup.find(text=re.compile(r'bath', re.I)))),
                "sqft": self._extract_number(str(soup.find(text=re.compile(r'sq.*ft|square.*feet', re.I))))
            }

        except Exception as e:
            property_data["error"] = str(e)

        return property_data

    def _initialize_property_data(self) -> Dict:
        return {
            "title": "",
            "price": "",
            "location": "",
            "details": {
                "bedrooms": None,
                "bathrooms": None,
                "sqft": None
            },
            "features": [],
            "error": None
        }

    def _clean_price(self, price_str: str) -> str:
        """Extract and clean price string"""
        if not price_str:
            return ""
        # Find price pattern
        match = re.search(r'\$[\d,]+(?:,\d{3})*(?:\.\d{2})?', price_str)
        if match:
            return match.group(0)
        return ""

    def _extract_number(self, text: str) -> float:
        """Extract numeric value from text"""
        if not text:
            return None
        match = re.search(r'[\d,.]+', text)
        if match:
            try:
                return float(match.group(0).replace(',', ''))
            except ValueError:
                return None
        return None

    def _run(self, url: str) -> Dict:
        """Execute the web scraping tool"""
        return self._scrape_website(url)

class RequestsTool(BaseTool):
    name: str = "RequestsTool"
    description: str = "Tool for making HTTP requests to property websites"

    def _run(self, url: str, method: str = "GET", headers: Dict = None) -> Dict:
        """Execute the HTTP request tool"""
        default_headers = {
            'User-Agent': os.getenv('USER_AGENT'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        headers = headers or default_headers
        
        try:
            # Add rate limiting
            time.sleep(float(os.getenv('RATE_LIMIT_DELAY', '2')))
            
            response = requests.request(
                method, 
                url, 
                headers=headers,
                timeout=int(os.getenv('REQUEST_TIMEOUT', '30'))
            )
            response.raise_for_status()
            return {
                "status_code": response.status_code,
                "content": response.text,
                "headers": dict(response.headers)
            }
        except Exception as e:
            return {"error": str(e)} 
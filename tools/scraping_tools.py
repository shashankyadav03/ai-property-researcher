from typing import Dict, List
import requests
from bs4 import BeautifulSoup
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

class BeautifulSoupTool(BaseTool):
    name = "BeautifulSoupTool"
    description = "Tool for scraping property listings using BeautifulSoup"

    def _scrape_website(self, url: str) -> Dict:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_property_data(soup)
        except Exception as e:
            return {"error": str(e)}

    def _parse_property_data(self, soup: BeautifulSoup) -> Dict:
        # Implement specific parsing logic for different websites
        property_data = {
            "title": "",
            "price": "",
            "location": "",
            "details": {},
            "features": []
        }
        
        # Example parsing (to be customized per website)
        title = soup.find('h1', class_='property-title')
        if title:
            property_data["title"] = title.text.strip()
            
        price = soup.find('div', class_='property-price')
        if price:
            property_data["price"] = price.text.strip()
            
        return property_data

    def _run(self, url: str) -> Dict:
        """Execute the web scraping tool"""
        return self._scrape_website(url)

class RequestsTool(BaseTool):
    name = "RequestsTool"
    description = "Tool for making HTTP requests to property websites"

    def _run(self, url: str, method: str = "GET", headers: Dict = None) -> Dict:
        """Execute the HTTP request tool"""
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        headers = headers or default_headers
        
        try:
            response = requests.request(method, url, headers=headers)
            response.raise_for_status()
            return {
                "status_code": response.status_code,
                "content": response.text,
                "headers": dict(response.headers)
            }
        except Exception as e:
            return {"error": str(e)} 
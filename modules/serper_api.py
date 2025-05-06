"""
Serper API Module for Google Search Results Integration
This module handles communication with the Serper.dev API to get search results.
"""
import json
import requests
from typing import Dict, List, Any, Optional, Union
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SerperAPI:
    """
    Client for interacting with the Serper.dev API to get Google search results.
    """
    BASE_URL = "https://google.serper.dev"
    
    def __init__(self, api_key: str):
        """
        Initialize the Serper API client.
        
        Args:
            api_key: The API key for authentication
        """
        self.api_key = api_key
        self.headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
    
    def search(self, query: str, search_type: str = "search", num_results: int = 10) -> Dict[str, Any]:
        """
        Perform a search using the Serper API.
        
        Args:
            query: The search query
            search_type: Type of search (search, news, images, places)
            num_results: Number of results to return
            
        Returns:
            Dict containing search results
            
        Raises:
            Exception: If the API request fails
        """
        endpoint = f"/{search_type}"
        
        payload = {
            "q": query,
            "num": num_results
        }
        
        try:
            logger.info(f"Sending search request to Serper API: {query}")
            response = requests.post(
                f"{self.BASE_URL}{endpoint}", 
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making Serper API request: {str(e)}")
            raise Exception(f"Failed to fetch search results: {str(e)}")
    
    def get_product_insights(self, product_name: str, num_results: int = 10) -> Dict[str, Any]:
        """
        Get web insights about a product by performing multiple specialized searches.
        
        Args:
            product_name: The name of the product
            num_results: Number of results per search
            
        Returns:
            Dict containing combined insights from multiple searches
        """
        insights = {}
        
        # Get general search results
        insights["general"] = self.search(product_name, num_results=num_results)
        
        # Get reviews from popular sites
        reviews_query = f"{product_name} reviews site:reddit.com OR site:trustpilot.com"
        insights["reviews"] = self.search(reviews_query, num_results=num_results)
        
        # Get news about the product
        news_query = f"{product_name} news"
        insights["news"] = self.search(news_query, search_type="news", num_results=num_results)
        
        return insights
    
    def extract_sentiment_keywords(self, search_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract keywords and basic sentiment from search results.
        This is a simple extraction - in a production environment, use NLP.
        
        Args:
            search_results: The search results from the API
            
        Returns:
            List of extracted keywords with sentiment indicators
        """
        keywords = []
        
        # Process organic results
        if "organic" in search_results:
            for result in search_results["organic"]:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                
                # Simple sentiment analysis based on keywords
                sentiment = "neutral"
                positive_words = ["great", "best", "amazing", "excellent", "good", "positive", "recommended", "better", "impressive", "powerful", "fast", "improved", "love", "perfect", "awesome", "worth", "superior"]
                negative_words = ["bad", "worst", "terrible", "poor", "negative", "avoid", "problems", "issues", "disappointing", "slow", "overpriced", "limited", "broken", "fails", "fails", "worse"]
                
                text = (title + " " + snippet).lower()
                
                pos_count = sum(1 for word in positive_words if word in text.split())
                neg_count = sum(1 for word in negative_words if word in text.split())
                
                if pos_count > neg_count:
                    sentiment = "positive"
                elif neg_count > pos_count:
                    sentiment = "negative"
                
                keywords.append({
                    "source": result.get("link", ""),
                    "title": title,
                    "snippet": snippet,
                    "sentiment": sentiment
                })
        
        return keywords
    
    def compare_products(self, product1: str, product2: str) -> Dict[str, Any]:
        """
        Compare two products based on search results.
        
        Args:
            product1: Name of first product
            product2: Name of second product
            
        Returns:
            Dict containing comparison data
        """
        comparison_query = f"{product1} vs {product2}"
        results = self.search(comparison_query, num_results=20)
        
        return {
            "query": comparison_query,
            "results": results,
            "keywords": self.extract_sentiment_keywords(results)
        }


# Function to create a formatted insight summary from Serper results
def format_insights(insights: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format insights from Serper API results into a structured summary.
    
    Args:
        insights: Raw insights from Serper API
        
    Returns:
        Formatted insights ready for dashboard display
    """
    formatted = {
        "top_sources": [],
        "sentiment_overview": {
            "positive": 0,
            "neutral": 0,
            "negative": 0
        },
        "key_phrases": [],
        "recent_news": []
    }
    
    # Extract top sources
    if "general" in insights and "organic" in insights["general"]:
        formatted["top_sources"] = [
            {
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "source": result.get("link", "").split("//")[1].split("/")[0],
                "snippet": result.get("snippet", "")
            }
            for result in insights["general"]["organic"][:5]
        ]
    
    # Extract sentiment from reviews
    serper_api = SerperAPI("")  # Empty API key for using just the extraction method
    if "reviews" in insights:
        keywords = serper_api.extract_sentiment_keywords(insights["reviews"])
        for keyword in keywords:
            formatted["sentiment_overview"][keyword["sentiment"]] += 1
    
    # Extract news
    if "news" in insights and "news" in insights["news"]:
        formatted["recent_news"] = [
            {
                "title": news.get("title", ""),
                "link": news.get("link", ""),
                "source": news.get("source", ""),
                "date": news.get("date", ""),
                "snippet": news.get("snippet", "")
            }
            for news in insights["news"]["news"][:5]
        ]
    
    return formatted 
"""
Test script for Serper API integration
"""
import sys
import os
import json
from pathlib import Path

# Add the parent directory to the path to import the modules
sys.path.append(str(Path(__file__).parent.parent))

from modules.serper_api import SerperAPI, format_insights

# API key
API_KEY = "888c639629fb510aceba71ba76270ee5ad8c8739"

def test_basic_search():
    """Test basic search functionality"""
    print("Testing basic search...")
    
    # Initialize the API client
    serper = SerperAPI(API_KEY)
    
    # Perform a basic search
    query = "MacBook Air M2"
    results = serper.search(query)
    
    # Print the results
    print(f"Search results for '{query}':")
    if "organic" in results:
        for i, result in enumerate(results["organic"][:3], 1):
            print(f"{i}. {result.get('title', 'No title')}")
            print(f"   URL: {result.get('link', 'No link')}")
            print(f"   Snippet: {result.get('snippet', 'No snippet')[:100]}...")
            print()
    else:
        print("No organic results found")
    
    return results

def test_product_insights():
    """Test product insights functionality"""
    print("\nTesting product insights...")
    
    # Initialize the API client
    serper = SerperAPI(API_KEY)
    
    # Get insights for a product
    product_name = "MacBook Air M2"
    insights = serper.get_product_insights(product_name, num_results=5)
    
    # Format the insights
    formatted = format_insights(insights)
    
    # Print sentiment overview
    print(f"Sentiment overview for '{product_name}':")
    for sentiment, count in formatted["sentiment_overview"].items():
        print(f"  {sentiment.capitalize()}: {count}")
    
    # Print recent news
    print("\nRecent news:")
    for i, news in enumerate(formatted["recent_news"][:3], 1):
        print(f"{i}. {news.get('title', 'No title')}")
        print(f"   Source: {news.get('source', 'No source')}")
        print(f"   Date: {news.get('date', 'No date')}")
        print()
    
    # Save the results to a file for inspection
    with open("serper_test_results.json", "w") as f:
        json.dump(formatted, f, indent=2)
    
    print(f"Full results saved to 'serper_test_results.json'")
    
    return formatted

def test_product_comparison():
    """Test product comparison functionality"""
    print("\nTesting product comparison...")
    
    # Initialize the API client
    serper = SerperAPI(API_KEY)
    
    # Compare two products
    product1 = "MacBook Air M2"
    product2 = "Dell XPS 13"
    comparison = serper.compare_products(product1, product2)
    
    # Print comparison results
    print(f"Comparison results for '{product1}' vs '{product2}':")
    for i, keyword in enumerate(comparison["keywords"][:5], 1):
        print(f"{i}. {keyword.get('title', 'No title')}")
        print(f"   Sentiment: {keyword.get('sentiment', 'No sentiment')}")
        print(f"   Snippet: {keyword.get('snippet', 'No snippet')[:100]}...")
        print()
    
    return comparison

if __name__ == "__main__":
    # Run all tests
    basic_results = test_basic_search()
    insights_results = test_product_insights()
    comparison_results = test_product_comparison()
    
    print("\nAll tests completed successfully!") 
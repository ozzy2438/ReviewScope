import pandas as pd
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os

class AmazonScraper:
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Set up headless Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode for server environment
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    
    def search_amazon(self, search_term, num_pages=1, output_file='amazon_products.csv', progress_callback=None):
        """
        Search Amazon for products and scrape results
        
        Args:
            search_term (str): The product to search for
            num_pages (int): Number of pages to scrape
            output_file (str): Path to save the CSV result
            progress_callback (function): Callback function for progress updates
        """
        try:
            self.driver = self.setup_driver()
            
            # Format the search term for URL
            formatted_search = search_term.replace(' ', '+')
            
            all_products = []
            
            for page in range(1, num_pages + 1):
                # Update progress
                if progress_callback:
                    progress_callback((page - 1) / num_pages)
                
                # Navigate to the search page
                search_url = f"https://www.amazon.com/s?k={formatted_search}&page={page}"
                self.driver.get(search_url)
                
                # Wait for results to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.s-result-item"))
                )
                
                # Extract product data
                products = self.extract_products()
                all_products.extend(products)
                
                # Add delay between pages to avoid detection
                time.sleep(2)
            
            # Convert to DataFrame and save
            df = pd.DataFrame(all_products)
            df.to_csv(output_file, index=False)
            
            # Update final progress
            if progress_callback:
                progress_callback(1.0)
                
            return len(all_products)
            
        finally:
            # Close the driver
            if self.driver:
                self.driver.quit()
    
    def extract_products(self):
        """Extract product data from the current page"""
        products = []
        
        # Get all product elements - güncellenen CSS selektör
        product_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.s-result-item[data-component-type='s-search-result']")
        
        for element in product_elements:
            try:
                # Extract product data
                product = {}
                
                # Title - güncellendi
                title_element = element.find_elements(By.CSS_SELECTOR, "h2 a span")
                if not title_element:
                    title_element = element.find_elements(By.CSS_SELECTOR, ".a-size-medium.a-color-base.a-text-normal")
                if not title_element:
                    title_element = element.find_elements(By.CSS_SELECTOR, ".a-size-base-plus.a-color-base.a-text-normal")
                product['title'] = title_element[0].text if title_element else "N/A"
                
                # URL - güncellendi
                url_element = element.find_elements(By.CSS_SELECTOR, "h2 a")
                if not url_element:
                    url_element = element.find_elements(By.CSS_SELECTOR, ".a-link-normal.s-no-outline")
                product['url'] = url_element[0].get_attribute("href") if url_element else "N/A"
                
                # Extract ASIN from URL
                asin = "N/A"
                if product['url'] != "N/A":
                    asin_match = re.search(r'/dp/([A-Z0-9]{10})', product['url'])
                    if not asin_match:
                        # Alternatif ASIN çıkarma
                        asin_match = re.search(r'dp%2F([A-Z0-9]{10})%2F', product['url'])
                    if asin_match:
                        asin = asin_match.group(1)
                product['asin'] = asin
                
                # Price - güncellendi
                price_element = element.find_elements(By.CSS_SELECTOR, ".a-price .a-offscreen")
                if not price_element:
                    price_element = element.find_elements(By.CSS_SELECTOR, ".a-price")
                product['price'] = price_element[0].get_attribute("textContent") if price_element else "N/A"
                
                # Rating - güncellendi
                rating_element = element.find_elements(By.CSS_SELECTOR, "i.a-icon-star-small span")
                if not rating_element:
                    rating_element = element.find_elements(By.CSS_SELECTOR, ".a-icon-alt")
                product['rating'] = rating_element[0].get_attribute("textContent") if rating_element else "N/A"
                
                # Review count - güncellendi
                review_element = element.find_elements(By.CSS_SELECTOR, "span.a-size-base.s-underline-text")
                if not review_element:
                    review_element = element.find_elements(By.CSS_SELECTOR, ".a-link-normal .a-size-base")
                product['review_count'] = review_element[0].text if review_element else "0"
                
                products.append(product)
                
            except Exception as e:
                # Skip items with errors and log
                print(f"Error extracting product data: {str(e)}")
                continue
        
        return products
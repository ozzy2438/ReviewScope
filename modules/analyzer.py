import pandas as pd
import numpy as np
from textblob import TextBlob
import json
import re
import os
from datetime import datetime

class AmazonAnalyzer:
    def __init__(self):
        """Initialize the analyzer"""
        pass
        
    def analyze_file(self, input_file, output_file=None, progress_callback=None):
        """
        Analyze Amazon product data from a CSV file
        
        Args:
            input_file (str): Path to input CSV file
            output_file (str): Path to save the analysis results (JSON)
            progress_callback (function): Callback function for progress updates
        """
        # Update progress
        if progress_callback:
            progress_callback(0.1)
            
        # Read the data
        try:
            df = pd.read_csv(input_file)
        except Exception as e:
            raise Exception(f"Error reading input file: {str(e)}")
            
        # Update progress
        if progress_callback:
            progress_callback(0.2)
            
        # Clean the data
        df = self.clean_data(df)
        
        # Update progress
        if progress_callback:
            progress_callback(0.4)
            
        # Perform analysis
        analysis_results = self.perform_analysis(df)
        
        # Update progress
        if progress_callback:
            progress_callback(0.8)
            
        # Save results if output file is specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(analysis_results, f, indent=2)
        
        # Update final progress
        if progress_callback:
            progress_callback(1.0)
            
        return analysis_results
    
    def clean_data(self, df):
        """Clean and prepare the data for analysis"""
        # Önce N/A string değerlerini gerçek NaN değerleriyle değiştirelim
        df = df.replace('N/A', np.nan)
        
        # Önce boş title değerlerini "Unknown" olarak değiştirelim, böylece hiçbir veri kaybedilmez
        df['title'] = df['title'].fillna('Unknown Product')
        
        # Clean price values - remove $ sign and convert to numeric
        df['price_clean'] = df['price'].str.replace('[$,]', '', regex=True)
        df['price_clean'] = pd.to_numeric(df['price_clean'], errors='coerce').fillna(0).astype(float)
        
        # Extract numeric ratings - handle NaN values and "X.X out of 5 stars" format
        try:
            df['rating_clean'] = df['rating'].str.extract(r'(\d+\.\d+)', expand=False)
            df['rating_clean'] = pd.to_numeric(df['rating_clean'], errors='coerce').fillna(0).astype(float)
        except Exception as e:
            print(f"Error extracting ratings: {str(e)}")
            # If extraction fails, create a column with zeros
            df['rating_clean'] = 0.0
        
        # Convert review counts to numeric - handle NaN and commas
        try:
            # First replace any NaN with '0'
            df['review_count'] = df['review_count'].fillna('0')
            # Then remove commas and convert to integer
            df['review_count_clean'] = df['review_count'].str.replace(',', '').str.strip()
            df['review_count_clean'] = pd.to_numeric(df['review_count_clean'], errors='coerce').fillna(0).astype(int)
        except Exception as e:
            print(f"Error cleaning review counts: {str(e)}")
            # If conversion fails, create a column with zeros
            df['review_count_clean'] = 0
        
        return df
    
    def perform_analysis(self, df):
        """Perform comprehensive analysis on the cleaned data"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'summary': {},
            'price_analysis': {},
            'rating_analysis': {},
            'review_analysis': {},
            'title_analysis': {},
            'correlations': {}
        }
        
        # Check if DataFrame is empty after cleaning
        if len(df) == 0:
            # Return basic results for empty dataset
            results['summary'] = {
                'total_products': 0,
                'average_price': 0,
                'average_rating': 0,
                'total_reviews': 0,
                'error': 'No valid products found after data cleaning'
            }
            return results
        
        # Summary statistics
        results['summary'] = {
            'total_products': len(df),
            'average_price': float(df['price_clean'].mean()),
            'average_rating': float(df['rating_clean'].mean()),
            'total_reviews': int(df['review_count_clean'].sum())
        }
        
        # Price analysis - safely handle potential NaN
        price_data = df['price_clean']
        results['price_analysis'] = {
            'min': float(price_data.min()),
            'max': float(price_data.max()),
            'mean': float(price_data.mean()),
            'median': float(price_data.median()),
            'std_dev': float(price_data.std()),
            'price_ranges': self.get_price_ranges(df)
        }
        
        # Rating analysis - safely handle potential NaN
        rating_data = df['rating_clean']
        results['rating_analysis'] = {
            'min': float(rating_data.min()),
            'max': float(rating_data.max()),
            'mean': float(rating_data.mean()),
            'median': float(rating_data.median()),
            'std_dev': float(rating_data.std()),
            'distribution': self.get_rating_distribution(df)
        }
        
        # Review analysis - safely handle potential NaN
        review_data = df['review_count_clean']
        results['review_analysis'] = {
            'min': int(review_data.min()),
            'max': int(review_data.max()),
            'mean': float(review_data.mean()),
            'median': float(review_data.median()),
            'std_dev': float(review_data.std()),
            'total': int(review_data.sum()),
            'distribution': self.get_review_distribution(df)
        }
        
        # Title analysis
        results['title_analysis'] = self.analyze_titles(df)
        
        # Correlations
        results['correlations'] = {
            'price_vs_rating': df[['price_clean', 'rating_clean']].corr().iloc[0,1],
            'price_vs_reviews': df[['price_clean', 'review_count_clean']].corr().iloc[0,1],
            'rating_vs_reviews': df[['rating_clean', 'review_count_clean']].corr().iloc[0,1]
        }
        
        return results
    
    def get_price_ranges(self, df):
        """Create price range distribution"""
        try:
            # Handle empty or all-zero dataframe
            if len(df) == 0 or df['price_clean'].max() == 0:
                return {
                    'ranges': ['<$25'],
                    'counts': [0]
                }
                
            ranges = [0, 25, 50, 100, 200, 500, 1000, float('inf')]
            labels = ['<$25', '$25-$50', '$50-$100', '$100-$200', '$200-$500', '$500-$1000', '>$1000']
            
            # Ensure price_clean is numeric and replace NaN with 0
            df['price_clean'] = pd.to_numeric(df['price_clean'], errors='coerce').fillna(0)
            
            price_counts = pd.cut(df['price_clean'], bins=ranges, labels=labels).value_counts().sort_index()
            
            return {
                'ranges': labels,
                'counts': price_counts.values.tolist()
            }
        except Exception as e:
            print(f"Error in price ranges: {str(e)}")
            return {
                'ranges': ['<$25'],
                'counts': [0],
                'error': str(e)
            }
    
    def get_rating_distribution(self, df):
        """Create rating distribution"""
        try:
            # Handle empty or all-zero dataframe
            if len(df) == 0 or df['rating_clean'].max() == 0:
                return {
                    'ratings': [0],
                    'counts': [0]
                }
                
            # Round ratings to nearest 0.5
            rounded_ratings = df['rating_clean'].apply(lambda x: round(x * 2) / 2 if not pd.isna(x) else 0)
            rating_counts = rounded_ratings.value_counts().sort_index()
            
            return {
                'ratings': rating_counts.index.tolist(),
                'counts': rating_counts.values.tolist()
            }
        except Exception as e:
            print(f"Error in rating distribution: {str(e)}")
            return {
                'ratings': [0],
                'counts': [0],
                'error': str(e)
            }
    
    def get_review_distribution(self, df):
        """Create review count distribution"""
        try:
            # Handle empty or all-zero dataframe
            if len(df) == 0 or df['review_count_clean'].max() == 0:
                return {
                    'ranges': ['0-10'],
                    'counts': [0]
                }
                
            # Create logarithmic bins for review counts
            review_ranges = [0, 10, 100, 1000, 10000, float('inf')]
            review_labels = ['0-10', '11-100', '101-1000', '1001-10000', '>10000']
            
            # Ensure review_count_clean is numeric and replace NaN with 0
            df['review_count_clean'] = pd.to_numeric(df['review_count_clean'], errors='coerce').fillna(0)
            
            review_counts = pd.cut(df['review_count_clean'], bins=review_ranges, labels=review_labels).value_counts().sort_index()
            
            return {
                'ranges': review_labels,
                'counts': review_counts.values.tolist()
            }
        except Exception as e:
            print(f"Error in review distribution: {str(e)}")
            return {
                'ranges': ['0-10'],
                'counts': [0],
                'error': str(e)
            }
    
    def analyze_titles(self, df):
        """Analyze product titles for common words and sentiment"""
        # Filter out 'Unknown Product' titles
        valid_titles = df[df['title'] != 'Unknown Product']['title']
        
        if len(valid_titles) == 0:
            # No valid titles, return default values
            return {
                'top_words': [{'no_data': 1}],
                'average_sentiment': 0,
                'positive_titles': 0,
                'neutral_titles': 0,
                'negative_titles': 0
            }
        
        all_titles = ' '.join(valid_titles)
        
        # Extract words, remove common stop words
        word_regex = re.compile(r'\b[a-zA-Z]{3,15}\b')
        words = word_regex.findall(all_titles.lower())
        
        # Count word frequencies
        stop_words = set(['with', 'for', 'and', 'the', 'this', 'that', 'new', 'from', 'are'])
        word_counts = {}
        
        for word in words:
            if word not in stop_words:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # If no words found after filtering
        if not word_counts:
            word_counts = {'no_data': 1}
        
        # Get top words
        top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        # Analyze sentiment of valid titles
        sentiments = [TextBlob(title).sentiment.polarity for title in valid_titles]
        
        # Handle empty sentiments list
        if not sentiments:
            avg_sentiment = 0
            positive_count = 0
            neutral_count = 0
            negative_count = 0
        else:
            avg_sentiment = sum(sentiments) / len(sentiments)
            positive_count = sum(1 for s in sentiments if s > 0.2)
            neutral_count = sum(1 for s in sentiments if -0.2 <= s <= 0.2)
            negative_count = sum(1 for s in sentiments if s < -0.2)
        
        return {
            'top_words': [{word: count} for word, count in top_words],
            'average_sentiment': avg_sentiment,
            'positive_titles': positive_count,
            'neutral_titles': neutral_count,
            'negative_titles': negative_count
        }

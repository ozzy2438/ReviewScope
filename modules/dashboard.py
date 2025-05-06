import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
from plotly.subplots import make_subplots

def generate_dashboard_data(analysis_results):
    """
    Generate Plotly visualization data for the dashboard
    
    Args:
        analysis_results (dict): Analysis results from the analyzer
        
    Returns:
        dict: Dashboard data with Plotly figures as JSON
    """
    dashboard_data = {
        'summary': analysis_results['summary'],
        'price_chart': create_price_chart(analysis_results),
        'rating_chart': create_rating_chart(analysis_results),
        'review_chart': create_review_chart(analysis_results),
        'word_cloud_data': create_word_cloud_data(analysis_results),
        'correlation_chart': create_correlation_chart(analysis_results)
    }
    
    return dashboard_data

def create_price_chart(analysis_results):
    """Create price distribution chart"""
    try:
        # Check if price_ranges exists in the results
        if 'price_analysis' not in analysis_results or 'price_ranges' not in analysis_results['price_analysis']:
            # Create default/empty chart if data is missing
            ranges = ['<$25', '$25-$50', '$50-$100', '$100-$200', '$200-$500', '$500-$1000', '>$1000']
            counts = [0] * len(ranges)
            
            fig = go.Figure(data=[
                go.Bar(
                    x=ranges,
                    y=counts,
                    marker_color='#4CAF50'
                )
            ])
        else:
            price_data = analysis_results['price_analysis']['price_ranges']
            
            fig = go.Figure(data=[
                go.Bar(
                    x=price_data['ranges'],
                    y=price_data['counts'],
                    marker_color='#4CAF50'
                )
            ])
        
        fig.update_layout(
            title='Price Distribution',
            xaxis_title='Price Range',
            yaxis_title='Number of Products',
            template='plotly_white'
        )
        
        return fig.to_json()
    except Exception as e:
        print(f"Error creating price chart: {str(e)}")
        # Return empty chart on error
        fig = go.Figure()
        fig.update_layout(
            title='Price Distribution (Error Loading Data)',
            template='plotly_white'
        )
        return fig.to_json()

def create_rating_chart(analysis_results):
    """Create rating distribution chart"""
    try:
        # Check if distribution exists in the results
        if 'rating_analysis' not in analysis_results or 'distribution' not in analysis_results['rating_analysis']:
            # Create default/empty chart if data is missing
            ratings = [0, 1, 2, 3, 4, 5]
            counts = [0] * len(ratings)
            
            fig = go.Figure(data=[
                go.Bar(
                    x=ratings,
                    y=counts,
                    marker_color='#2196F3'
                )
            ])
        else:
            rating_data = analysis_results['rating_analysis']['distribution']
            
            fig = go.Figure(data=[
                go.Bar(
                    x=rating_data['ratings'],
                    y=rating_data['counts'],
                    marker_color='#2196F3'
                )
            ])
        
        fig.update_layout(
            title='Rating Distribution',
            xaxis_title='Rating',
            yaxis_title='Number of Products',
            template='plotly_white'
        )
        
        return fig.to_json()
    except Exception as e:
        print(f"Error creating rating chart: {str(e)}")
        # Return empty chart on error
        fig = go.Figure()
        fig.update_layout(
            title='Rating Distribution (Error Loading Data)',
            template='plotly_white'
        )
        return fig.to_json()

def create_review_chart(analysis_results):
    """Create review count distribution chart"""
    try:
        # Check if distribution exists in the results
        if 'review_analysis' not in analysis_results or 'distribution' not in analysis_results['review_analysis']:
            # Create default/empty chart if data is missing
            ranges = ['0-10', '11-100', '101-1000', '1001-10000', '>10000']
            counts = [0] * len(ranges)
            
            fig = go.Figure(data=[
                go.Bar(
                    x=ranges,
                    y=counts,
                    marker_color='#FF9800'
                )
            ])
        else:
            review_data = analysis_results['review_analysis']['distribution']
            
            fig = go.Figure(data=[
                go.Bar(
                    x=review_data['ranges'],
                    y=review_data['counts'],
                    marker_color='#FF9800'
                )
            ])
        
        fig.update_layout(
            title='Review Count Distribution',
            xaxis_title='Number of Reviews',
            yaxis_title='Number of Products',
            template='plotly_white'
        )
        
        return fig.to_json()
    except Exception as e:
        print(f"Error creating review chart: {str(e)}")
        # Return empty chart on error
        fig = go.Figure()
        fig.update_layout(
            title='Review Count Distribution (Error Loading Data)',
            template='plotly_white'
        )
        return fig.to_json()

def create_word_cloud_data(analysis_results):
    """Create data for word cloud visualization"""
    try:
        word_data = []
        
        if 'title_analysis' in analysis_results and 'top_words' in analysis_results['title_analysis']:
            for word_obj in analysis_results['title_analysis']['top_words']:
                for word, count in word_obj.items():
                    word_data.append({
                        'text': word,
                        'value': count
                    })
        
        # If no words were found, add a placeholder
        if not word_data:
            word_data.append({
                'text': 'No words found',
                'value': 1
            })
        
        return word_data
    except Exception as e:
        print(f"Error creating word cloud data: {str(e)}")
        # Return placeholder on error
        return [{'text': 'Error', 'value': 1}]

def create_correlation_chart(analysis_results):
    """Create correlation heatmap"""
    try:
        # Check if correlations data exists
        if 'correlations' not in analysis_results:
            # Default zero correlations
            corr_matrix = [
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, 1]
            ]
        else:
            correlations = analysis_results['correlations']
            
            # Handle potential NaN values
            price_vs_rating = correlations.get('price_vs_rating', 0)
            price_vs_reviews = correlations.get('price_vs_reviews', 0)
            rating_vs_reviews = correlations.get('rating_vs_reviews', 0)
            
            # Convert potential NaN to 0
            if pd.isna(price_vs_rating): price_vs_rating = 0
            if pd.isna(price_vs_reviews): price_vs_reviews = 0
            if pd.isna(rating_vs_reviews): rating_vs_reviews = 0
            
            # Create correlation matrix
            corr_matrix = [
                [1, price_vs_rating, price_vs_reviews],
                [price_vs_rating, 1, rating_vs_reviews],
                [price_vs_reviews, rating_vs_reviews, 1]
            ]
        
        labels = ['Price', 'Rating', 'Reviews']
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix,
            x=labels,
            y=labels,
            colorscale='RdBu',
            zmid=0,
            text=[[round(val, 2) if not pd.isna(val) else 0 for val in row] for row in corr_matrix],
            texttemplate="%{text}",
            textfont={"size":14}
        ))
        
        fig.update_layout(
            title='Correlation Heatmap',
            template='plotly_white'
        )
        
        return fig.to_json()
    except Exception as e:
        print(f"Error creating correlation chart: {str(e)}")
        # Return empty chart on error
        fig = go.Figure()
        fig.update_layout(
            title='Correlation Heatmap (Error Loading Data)',
            template='plotly_white'
        )
        return fig.to_json()

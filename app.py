from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file, send_from_directory
import os
import json
import pandas as pd
from datetime import datetime
import threading
import time
import re
from pathlib import Path
from werkzeug.utils import secure_filename

# Import your modules
from modules.scraper import AmazonScraper
from modules.analyzer import AmazonAnalyzer
from modules.dashboard import generate_dashboard_data
from modules.serper_api import SerperAPI, format_insights

app = Flask(__name__)
app.secret_key = 'amazon_scraper_secret_key'  # Change this to a random string for security

# Configure application
app.config['UPLOAD_FOLDER'] = 'data/raw'
app.config['RESULTS_FOLDER'] = 'data/processed'
app.config['SERPER_API_KEY'] = '888c639629fb510aceba71ba76270ee5ad8c8739'

# Create necessary folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# Store active scraping jobs
active_jobs = {}
# Add a lock for thread safety
jobs_lock = threading.Lock()

# Initialize Serper API
serper_api = SerperAPI(app.config['SERPER_API_KEY'])

@app.route('/')
def index():
    """Home page with search form"""
    # Clear old sessions when returning to home page
    session.pop('current_job', None)
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Handle the search form submission"""
    search_term = request.form.get('search_term')
    num_pages = int(request.form.get('num_pages', 1))
    
    if not search_term:
        flash('Please enter a search term', 'danger')
        return redirect(url_for('index'))
    
    # Create a unique job ID
    job_id = f"{search_term.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Store job info in global dictionary with lock for thread safety
    with jobs_lock:
        active_jobs[job_id] = {
            'search_term': search_term,
            'num_pages': num_pages,
            'status': 'initializing',
            'progress': 0,
            'start_time': datetime.now().isoformat()
        }
    
    # Store job ID in session
    session['current_job'] = job_id
    
    # Start scraping in background thread
    job_thread = threading.Thread(
        target=run_scraper_job,
        args=(job_id, search_term, num_pages)
    )
    job_thread.daemon = True
    job_thread.start()
    
    # Redirect to results page
    return redirect(url_for('job_status', job_id=job_id))

@app.route('/job/<job_id>')
def job_status(job_id):
    """Show job status and results when completed"""
    with jobs_lock:
        if job_id not in active_jobs:
            flash('Job not found. If the server was restarted, your job may have been deleted. Please make a new search.', 'warning')
            return redirect(url_for('index'))
        
        job_info = active_jobs[job_id]
    
    return render_template('results.html', job_id=job_id, job_info=job_info)

@app.route('/api/job-status/<job_id>')
def get_job_status(job_id):
    """API endpoint to get current job status for AJAX updates"""
    with jobs_lock:
        if job_id not in active_jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        # Return a copy of job info to avoid potential race conditions
        return jsonify(dict(active_jobs[job_id]))

@app.route('/dashboard/<job_id>')
def dashboard(job_id):
    """Display analysis dashboard for completed job"""
    with jobs_lock:
        if job_id not in active_jobs or active_jobs[job_id]['status'] != 'completed':
            flash('Analysis not ready or job not found', 'warning')
            return redirect(url_for('job_status', job_id=job_id))
        
        job_info = dict(active_jobs[job_id])
    
    # Get analysis results
    result_file = os.path.join(app.config['RESULTS_FOLDER'], f"{job_id}_analysis.json")
    if not os.path.exists(result_file):
        flash('Analysis results not found', 'danger')
        return redirect(url_for('job_status', job_id=job_id))
    
    with open(result_file, 'r') as f:
        analysis_results = json.load(f)
    
    # Generate dashboard data
    dashboard_data = generate_dashboard_data(analysis_results)
    
    return render_template('dashboard.html', 
                          job_id=job_id, 
                          job_info=job_info,
                          dashboard_data=dashboard_data)

@app.route('/api/data/<job_id>')
def get_raw_data(job_id):
    """API endpoint to get raw data as JSON"""
    with jobs_lock:
        if job_id not in active_jobs or active_jobs[job_id]['status'] != 'completed':
            return jsonify({'error': 'Data not available'}), 404
    
    data_file = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_data.csv")
    if not os.path.exists(data_file):
        return jsonify({'error': 'Data file not found'}), 404
    
    try:
        df = pd.read_csv(data_file)
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/<job_id>')
def get_analysis_data(job_id):
    """API endpoint to get analysis results as JSON"""
    with jobs_lock:
        if job_id not in active_jobs or active_jobs[job_id]['status'] != 'completed':
            return jsonify({'error': 'Analysis not available'}), 404
    
    result_file = os.path.join(app.config['RESULTS_FOLDER'], f"{job_id}_analysis.json")
    if not os.path.exists(result_file):
        return jsonify({'error': 'Analysis file not found'}), 404
    
    try:
        with open(result_file, 'r') as f:
            analysis_results = json.load(f)
        return jsonify(analysis_results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/data/<job_id>')
def download_raw_data(job_id):
    """Download raw data as CSV"""
    with jobs_lock:
        if job_id not in active_jobs or active_jobs[job_id]['status'] != 'completed':
            flash('Data not available for download', 'warning')
            return redirect(url_for('job_status', job_id=job_id))
        
        search_term = active_jobs[job_id]['search_term']
    
    data_file = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_data.csv")
    if not os.path.exists(data_file):
        flash('Data file not found', 'danger')
        return redirect(url_for('job_status', job_id=job_id))
    
    return send_file(data_file, 
                    mimetype='text/csv',
                    download_name=f"amazon_products_{search_term.replace(' ', '_')}.csv",
                    as_attachment=True)

@app.route('/download/analysis/<job_id>')
def download_analysis(job_id):
    """Download analysis results as JSON"""
    with jobs_lock:
        if job_id not in active_jobs or active_jobs[job_id]['status'] != 'completed':
            flash('Analysis not available for download', 'warning')
            return redirect(url_for('job_status', job_id=job_id))
        
        search_term = active_jobs[job_id]['search_term']
    
    result_file = os.path.join(app.config['RESULTS_FOLDER'], f"{job_id}_analysis.json")
    if not os.path.exists(result_file):
        flash('Analysis file not found', 'danger')
        return redirect(url_for('job_status', job_id=job_id))
    
    return send_file(result_file, 
                    mimetype='application/json',
                    download_name=f"amazon_analysis_{search_term.replace(' ', '_')}.json",
                    as_attachment=True)

@app.route('/clear-jobs')
def clear_jobs():
    """Clear all jobs (admin function)"""
    with jobs_lock:
        active_jobs.clear()
    flash('All jobs have been cleared', 'success')
    return redirect(url_for('index'))

@app.context_processor
def inject_now():
    """Inject current date/time into templates"""
    return {'now': datetime.now()}

def run_scraper_job(job_id, search_term, num_pages):
    """Run the scraping and analysis process in background"""
    try:
        # Make sure job exists before continuing
        with jobs_lock:
            if job_id not in active_jobs:
                print(f"Job {job_id} not found in active jobs")
                return
            
        # Update job status
        with jobs_lock:
            active_jobs[job_id]['status'] = 'scraping'
        
        # Initialize scraper
        scraper = AmazonScraper()
        
        # Run scraper with progress callback
        output_file = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_data.csv")
        scraper.search_amazon(
            search_term=search_term,
            num_pages=num_pages,
            output_file=output_file,
            progress_callback=lambda p: update_progress(job_id, p, 0.5)  # First 50% is scraping
        )
        
        # Update job status
        with jobs_lock:
            active_jobs[job_id]['status'] = 'analyzing'
        
        # Initialize analyzer
        analyzer = AmazonAnalyzer()
        
        # Run analysis
        result_file = os.path.join(app.config['RESULTS_FOLDER'], f"{job_id}_analysis.json")
        analyzer.analyze_file(
            input_file=output_file,
            output_file=result_file,
            progress_callback=lambda p: update_progress(job_id, 0.5 + p * 0.5)  # Last 50% is analyzing
        )
        
        # Update job status
        with jobs_lock:
            active_jobs[job_id]['status'] = 'completed'
            active_jobs[job_id]['progress'] = 100
            active_jobs[job_id]['completion_time'] = datetime.now().isoformat()
            active_jobs[job_id]['result_file'] = result_file
            
            # Flask uygulama bağlamı içinde URL oluşturmak yerine basit bir bağıl URL oluştur
            active_jobs[job_id]['dashboard_url'] = f"/dashboard/{job_id}"
        
    except Exception as e:
        # Handle errors
        print(f"Error in job {job_id}: {str(e)}")
        try:
            with jobs_lock:
                if job_id in active_jobs:
                    active_jobs[job_id]['status'] = 'failed'
                    active_jobs[job_id]['error'] = str(e)
        except Exception as inner_e:
            print(f"Error updating job status: {str(inner_e)}")

def update_progress(job_id, progress, weight=1.0):
    """Update job progress"""
    with jobs_lock:
        if job_id in active_jobs:
            active_jobs[job_id]['progress'] = int(progress * 100 * weight)

# Add missing imports for file handling
from flask import send_file, send_from_directory

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('error.html', error_code=404, error_message="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('error.html', error_code=500, error_message="Server error"), 500

# Create error.html template if it doesn't exist
error_template_path = Path('templates/error.html')
if not error_template_path.exists():
    error_template_content = """
{% extends "layout.html" %}

{% block title %}Error {{ error_code }} - Amazon Scraper{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card shadow">
            <div class="card-header bg-danger text-white">
                <h3 class="mb-0"><i class="fas fa-exclamation-triangle me-2"></i>Error {{ error_code }}</h3>
            </div>
            <div class="card-body text-center">
                <h1 class="display-1 text-danger">{{ error_code }}</h1>
                <p class="lead">{{ error_message }}</p>
                <a href="{{ url_for('index') }}" class="btn btn-primary mt-3">
                    <i class="fas fa-home me-2"></i>Return to Home
                </a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""
    error_template_path.parent.mkdir(exist_ok=True)
    error_template_path.write_text(error_template_content)

@app.route('/analyze-csv/<filename>')
def analyze_csv(filename):
    """Analyze an existing CSV file and create a dashboard"""
    # CSV dosyasının tam yolunu oluştur
    csv_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(csv_file):
        flash(f'CSV dosyası bulunamadı: {filename}', 'danger')
        return redirect(url_for('index'))
    
    # İş kimliği oluştur (dosya adından uzantıyı çıkararak)
    job_id = os.path.splitext(filename)[0]
    
    # Dosya adından arama terimini çıkar
    search_parts = job_id.split('_')
    if len(search_parts) >= 2:
        search_term = ' '.join(search_parts[:-2])  # Son iki parçayı (tarih ve zaman) çıkar
    else:
        search_term = job_id
    
    # İş kaydı oluştur
    with jobs_lock:
        active_jobs[job_id] = {
            'search_term': search_term,
            'status': 'analyzing',
            'start_time': datetime.now().isoformat(),
            'progress': 50,
            'num_pages': 1  # Varsayılan olarak 1 sayfa
        }
    
    try:
        # Analiz et
        analyzer = AmazonAnalyzer()
        result_file = os.path.join(app.config['RESULTS_FOLDER'], f"{job_id}_analysis.json")
        
        # Analiz işlemini çalıştır
        analysis_results = analyzer.analyze_file(
            input_file=csv_file,
            output_file=result_file
        )
        
        # İş durumunu güncelle
        with jobs_lock:
            active_jobs[job_id]['status'] = 'completed'
            active_jobs[job_id]['progress'] = 100
            active_jobs[job_id]['completion_time'] = datetime.now().isoformat()
            active_jobs[job_id]['result_file'] = result_file
        
        # Dashboard'a yönlendir
        return redirect(url_for('dashboard', job_id=job_id))
        
    except Exception as e:
        flash(f'CSV analiz hatası: {str(e)}', 'danger')
        
        # İş durumunu güncelle
        with jobs_lock:
            active_jobs[job_id]['status'] = 'failed'
            active_jobs[job_id]['error'] = str(e)
        
        return redirect(url_for('index'))

# Ana sayfada mevcut CSV dosyalarını listele
@app.route('/existing-data')
def existing_data():
    """Display existing CSV files for analysis"""
    # Upload klasöründeki CSV dosyalarını bul
    csv_files = []
    for file in os.listdir(app.config['UPLOAD_FOLDER']):
        if file.endswith('.csv'):
            csv_files.append(file)
    
    return render_template('existing_data.html', csv_files=csv_files)

@app.route('/upload-csv', methods=['POST'])
def upload_csv():
    """Upload CSV file for analysis"""
    if 'csv_file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('index'))
    
    file = request.files['csv_file']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('index'))
    
    if file and file.filename.endswith('.csv'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        flash(f'File uploaded successfully: {filename}', 'success')
        return redirect(url_for('analyze_csv', filename=filename))
    else:
        flash('Invalid file type. Please upload a CSV file.', 'danger')
        return redirect(url_for('index'))

@app.route('/web-insights/<job_id>')
def web_insights(job_id):
    """Display web insights for a completed job"""
    with jobs_lock:
        if job_id not in active_jobs or active_jobs[job_id]['status'] != 'completed':
            flash('Analysis not ready or job not found', 'warning')
            return redirect(url_for('job_status', job_id=job_id))
        
        job_info = dict(active_jobs[job_id])
    
    # Get product name from job info
    product_name = job_info['search_term']
    
    try:
        # Check if insights are already cached
        insights_file = os.path.join(app.config['RESULTS_FOLDER'], f"{job_id}_web_insights.json")
        
        if os.path.exists(insights_file):
            # Load cached insights
            with open(insights_file, 'r') as f:
                web_insights = json.load(f)
        else:
            # Get web insights
            raw_insights = serper_api.get_product_insights(product_name, num_results=10)
            
            # Format insights for display
            web_insights = format_insights(raw_insights)
            
            # Cache the insights
            with open(insights_file, 'w') as f:
                json.dump(web_insights, f, indent=2)
        
        # Get analysis results for the dashboard
        result_file = os.path.join(app.config['RESULTS_FOLDER'], f"{job_id}_analysis.json")
        if not os.path.exists(result_file):
            flash('Analysis results not found', 'danger')
            return redirect(url_for('job_status', job_id=job_id))
        
        with open(result_file, 'r') as f:
            analysis_results = json.load(f)
        
        # Generate dashboard data
        dashboard_data = generate_dashboard_data(analysis_results)
        
        return render_template('web_insights.html', 
                              job_id=job_id, 
                              job_info=job_info,
                              dashboard_data=dashboard_data,
                              web_insights=web_insights)
    
    except Exception as e:
        flash(f'Error fetching web insights: {str(e)}', 'danger')
        return redirect(url_for('dashboard', job_id=job_id))

@app.route('/compare-products', methods=['POST'])
def compare_products():
    """Compare two products using Serper API"""
    product1 = request.form.get('product1', '')
    product2 = request.form.get('product2', '')
    
    if not product1 or not product2:
        flash('Please enter both product names', 'warning')
        return redirect(url_for('index'))
    
    try:
        # Get comparison data
        comparison = serper_api.compare_products(product1, product2)
        
        # Cache the comparison
        cache_file = os.path.join(app.config['RESULTS_FOLDER'], f"comparison_{product1}_{product2}.json".replace(' ', '_'))
        with open(cache_file, 'w') as f:
            json.dump(comparison, f, indent=2)
        
        # Redirect to comparison view
        return redirect(url_for('view_comparison', product1=product1, product2=product2))
    
    except Exception as e:
        flash(f'Error comparing products: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/comparison/<product1>/<product2>')
def view_comparison(product1, product2):
    """View product comparison results"""
    try:
        # Load cached comparison data
        cache_file = os.path.join(app.config['RESULTS_FOLDER'], f"comparison_{product1}_{product2}.json".replace(' ', '_'))
        
        if not os.path.exists(cache_file):
            # If not cached, generate new comparison
            comparison = serper_api.compare_products(product1, product2)
            
            # Cache the comparison
            with open(cache_file, 'w') as f:
                json.dump(comparison, f, indent=2)
        else:
            # Load from cache
            with open(cache_file, 'r') as f:
                comparison = json.load(f)
        
        return render_template('comparison.html',
                              product1=product1,
                              product2=product2,
                              comparison=comparison)
    
    except Exception as e:
        flash(f'Error loading comparison data: {str(e)}', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

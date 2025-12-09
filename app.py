from flask import Flask, render_template, jsonify, request
from data_processor import InventoryAnalyzer
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Use /tmp for uploads on Vercel (serverless), otherwise use uploads folder
if os.environ.get('VERCEL'):
    app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
else:
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

# Create uploads directory if it doesn't exist
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
except Exception:
    pass  # Ignore errors if directory creation fails

# Allowed file extensions
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize analyzer
EXCEL_FILE = os.getenv('EXCEL_FILE', 'Data Jul-Nov 2025.xlsx')
analyzer = None

def get_analyzer():
    """Get or create analyzer instance"""
    global analyzer, EXCEL_FILE
    try:
        if analyzer is None or not os.path.exists(EXCEL_FILE):
            # Try to find the file in uploads folder or current directory
            if not os.path.exists(EXCEL_FILE):
                # Look for any xlsx file in uploads folder
                uploads_dir = app.config['UPLOAD_FOLDER']
                if os.path.exists(uploads_dir):
                    try:
                        xlsx_files = [f for f in os.listdir(uploads_dir) if f.endswith(('.xlsx', '.xls'))]
                        if xlsx_files:
                            EXCEL_FILE = os.path.join(uploads_dir, xlsx_files[-1])  # Use most recent
                    except Exception:
                        pass
            
            if os.path.exists(EXCEL_FILE):
                analyzer = InventoryAnalyzer(EXCEL_FILE)
    except Exception as e:
        # Return None if analyzer can't be created - will be handled by error handlers
        print(f"Error creating analyzer: {e}")
        return None
    
    if analyzer is None:
        raise Exception("No Excel file found. Please upload a file first.")
    
    return analyzer

@app.route('/')
def index():
    """Main dashboard page"""
    try:
        # Try to get analyzer to check if file exists
        analyzer = get_analyzer()
        if analyzer is None:
            # Return a page with upload prompt
            return render_template('dashboard.html'), 200
    except Exception:
        # If analyzer fails, still show the page (user can upload)
        pass
    return render_template('dashboard.html')

@app.route('/api/dashboard/stats')
def dashboard_stats():
    """Get overall dashboard statistics"""
    try:
        analyzer = get_analyzer()
        if analyzer is None:
            return jsonify({'error': 'No Excel file found. Please upload a file first.'}), 404
        stats = analyzer.get_dashboard_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sites/summary')
def sites_summary():
    """Get summary statistics per site"""
    try:
        summary = get_analyzer().get_site_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/shortages')
def shortages():
    """Get shortage items"""
    try:
        # User requested all details, so we pass None to get all negative items
        shortages = get_analyzer().get_shortage_items(threshold_percentile=None)
        return jsonify(shortages)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/critical')
def critical_items():
    """Get critical items"""
    try:
        multiplier = request.args.get('multiplier', 2, type=float)
        critical = get_analyzer().get_critical_items(threshold_multiplier=multiplier)
        return jsonify(critical)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/abundant')
def abundant_items():
    """Get abundant items"""
    try:
        threshold = request.args.get('threshold', 90, type=int)
        abundant = get_analyzer().get_abundant_items(threshold_percentile=threshold)
        return jsonify(abundant)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommendations/shipping')
def shipping_recommendations():
    """Get shipping recommendations"""
    try:
        recommendations = get_analyzer().get_shipping_recommendations()
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/site/<site>/inventory')
def site_inventory(site):
    """Get inventory for a specific site"""
    try:
        inventory = get_analyzer().get_site_inventory(site=site)
        return jsonify(inventory)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/material/<material>/analysis')
def material_analysis(material):
    """Get analysis for a specific material"""
    try:
        analysis = get_analyzer().get_material_analysis(material=material)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/material/<material>/details')
def material_details(material):
    """Get detailed breakdown for a material"""
    try:
        details = get_analyzer().get_material_details(material=material)
        return jsonify(details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/bottlenecks')
def bottlenecks():
    """Get bottleneck analysis"""
    try:
        bottlenecks = get_analyzer().get_bottleneck_analysis()
        return jsonify(bottlenecks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/focus-areas')
def focus_areas():
    """Get focus areas analysis"""
    try:
        focus = get_analyzer().get_focus_areas()
        return jsonify(focus)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommendations/movements')
def movement_recommendations():
    """Get enhanced movement recommendations"""
    try:
        recommendations = get_analyzer().get_movement_recommendations()
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/top-shortages')
def top_shortages():
    """Get top shortages by value"""
    try:
        limit = request.args.get('limit', 10, type=int)
        data = get_analyzer().get_top_shortages_by_value(limit=limit)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/inactive-stock')
def inactive_stock():
    """Get inactive/obsolete stock"""
    try:
        days = request.args.get('days', 90, type=int)
        limit = request.args.get('limit', 20, type=int)
        data = get_analyzer().get_inactive_stock(days=days, limit=limit)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/inventory/all')
def all_inventory():
    """Get all inventory data"""
    try:
        inventory = get_analyzer().get_site_inventory()
        return jsonify(inventory)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle Excel file upload"""
    global analyzer, EXCEL_FILE
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload an Excel file (.xlsx or .xls)'}), 400
        
        # Save the file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Update global variables
        EXCEL_FILE = filepath
        analyzer = None  # Reset analyzer to force reload
        
        # Test if file can be processed
        try:
            test_analyzer = InventoryAnalyzer(EXCEL_FILE)
            stats = test_analyzer.get_dashboard_stats()
            
            return jsonify({
                'success': True,
                'message': 'File uploaded and processed successfully',
                'filename': filename,
                'stats': stats
            })
        except Exception as e:
            # If processing fails, delete the file
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': f'Failed to process file: {str(e)}'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

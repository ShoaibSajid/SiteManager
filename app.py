from flask import Flask, render_template, jsonify, request
from data_processor import InventoryAnalyzer
import os

app = Flask(__name__)

# Initialize analyzer
EXCEL_FILE = os.getenv('EXCEL_FILE', 'Data Jul-Nov 2025.xlsx')
analyzer = None

def get_analyzer():
    """Get or create analyzer instance"""
    global analyzer
    if analyzer is None:
        analyzer = InventoryAnalyzer(EXCEL_FILE)
    return analyzer

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/dashboard/stats')
def dashboard_stats():
    """Get overall dashboard statistics"""
    try:
        stats = get_analyzer().get_dashboard_stats()
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

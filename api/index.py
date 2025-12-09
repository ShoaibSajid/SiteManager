# Vercel serverless function handler for Flask app
import sys
import os

# Add parent directory to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Set Vercel environment variable before importing app
os.environ['VERCEL'] = '1'

# Import Flask app with error handling
try:
    from app import app
    handler = app
except ImportError as e:
    # If import fails, create a minimal error handler
    from flask import Flask, jsonify
    error_app = Flask(__name__)
    
    @error_app.route('/')
    def error_index():
        return f"""
        <html>
        <body>
            <h1>Import Error</h1>
            <p>Error importing app.py: {str(e)}</p>
            <p>Please check:</p>
            <ul>
                <li>All dependencies are in requirements.txt</li>
                <li>Excel file exists or can be uploaded</li>
                <li>Check Vercel logs for details</li>
            </ul>
        </body>
        </html>
        """, 500
    
    @error_app.route('/<path:path>')
    def error_handler(path):
        return jsonify({'error': f'Import error: {str(e)}'}), 500
    
    handler = error_app
    print(f"WARNING: Failed to import app.py: {e}")
    import traceback
    traceback.print_exc()

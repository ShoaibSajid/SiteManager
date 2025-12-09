# Vercel serverless function handler for Flask app
import sys
import os

# Add parent directory to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Set Vercel environment variable
os.environ['VERCEL'] = '1'

# Import and export Flask app - Vercel expects 'app' to be the Flask WSGI application
from app import app

import sys
from pathlib import Path
import os
from src.app import get_app

# ensure we are in the src directory so we can import the app
os.chdir(Path(__file__).parent / 'src')

print(os.getcwd())

# Import the app factory function and create the app

# Get the underlying Flask server for gunicorn
application = get_app().dash.server 
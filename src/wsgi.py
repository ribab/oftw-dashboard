import sys
from pathlib import Path
from app import get_app

# Get the underlying Flask server for gunicorn
application = get_app().dash.server
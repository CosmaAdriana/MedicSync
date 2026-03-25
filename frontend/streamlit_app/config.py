"""
MedicSync Frontend - Configuration
"""
import os

# Backend API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# App Configuration
APP_TITLE = "MedicSync - Health 4.0"
APP_ICON = "🏥"
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "collapsed"

# Theme colors
PRIMARY_COLOR = "#1f77b4"
BACKGROUND_COLOR = "#ffffff"
SECONDARY_BG_COLOR = "#f0f2f6"

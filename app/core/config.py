import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///focusai.sql')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Keys
    API_KEY = os.getenv('API_KEY')
    Provider_API_KEY = os.getenv('PROVIDER_API_KEY')
    
    # App Settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SCREENSHOT_INTERVAL = int(os.getenv('SCREENSHOT_INTERVAL', 300))  # 5 minutes
    SCREENSHOT_RETENTION_DAYS = int(os.getenv('SCREENSHOT_RETENTION_DAYS', 7))
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
    
    # WebSocket settings
    SOCKETIO_ASYNC_MODE = 'threading'


    # Root directory of the app
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Path to the config.py file
    APP_DIR = os.path.join(BASE_DIR, '../../../')  # App root (adjust if needed)
    
    # App-local data directory
    DATA_DIR = os.path.join(APP_DIR, 'FocusAI')
    SCREENSHOTS_DIR = os.path.join(DATA_DIR, 'screenshots')
    LOGS_DIR = os.path.join(DATA_DIR, 'logs')
    STORAGE_FILE = os.path.join(APP_DIR, 'backend', 'instance')
    STORAGE_FILE_JSON = os.path.join(STORAGE_FILE, 'Jsons')

    # # Paths
    # DATA_DIR = os.path.join(os.path.expanduser('~'), 'FocusAI')
    # SCREENSHOTS_DIR = os.path.join(DATA_DIR, 'screenshots')
    # LOGS_DIR = os.path.join(DATA_DIR, 'logs')
    # STORAGE_FILE= os.path.join(DATA_DIR, 'backend/instance')
    # STORAGE_FILE_JSON = os.path.join(DATA_DIR, 'backend/instance/Jsons')
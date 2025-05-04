import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/stock_management')
    
    # Flask-WTF settings
    WTF_CSRF_ENABLED = True
    
    # Custom settings
    ITEMS_PER_PAGE = 10 
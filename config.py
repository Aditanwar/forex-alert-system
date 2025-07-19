import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Forex API (Alpha Vantage)
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    BASE_URL = 'https://www.alphavantage.co/query'
    
    # Twilio Config
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
    
    # Flask Config
    SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///alerts.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

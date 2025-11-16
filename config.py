"""
設定ファイル
"""
import os
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()


class Config:
    """
    アプリケーション設定クラス
    """
    # Flask設定
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # データベース設定
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OpenWeatherMap API設定（Phase 2で使用）
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')
    OPENWEATHER_API_URL = 'https://api.openweathermap.org/data/2.5/weather'
    
    # Flask環境設定
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'








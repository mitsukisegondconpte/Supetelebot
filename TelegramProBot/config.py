import os
from datetime import timedelta

class Config:
    """Configuration de base pour l'application"""
    
    # Configuration Flask
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///chess_bot.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Configuration Telegram
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    OWNER_ID = int(os.environ.get('OWNER_ID', '0'))
    OWNER_USERNAME = os.environ.get('OWNER_USERNAME', 'admin')
    WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')
    
    # Configuration du moteur d'échecs
    STOCKFISH_PATH = os.environ.get('STOCKFISH_PATH', 'stockfish')
    DEFAULT_SKILL_LEVEL = int(os.environ.get('DEFAULT_SKILL_LEVEL', '5'))
    DEFAULT_AI_TIME = float(os.environ.get('DEFAULT_AI_TIME', '0.8'))
    
    # Configuration du monitoring
    ENABLE_REAL_TIME_MONITORING = os.environ.get('ENABLE_REAL_TIME_MONITORING', 'true').lower() == 'true'
    MONITORING_UPDATE_INTERVAL = int(os.environ.get('MONITORING_UPDATE_INTERVAL', '5'))  # secondes
    
    # Configuration des sessions
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Configuration Railway
    PORT = int(os.environ.get('PORT', '5000'))
    RAILWAY_DEPLOYMENT = os.environ.get('RAILWAY_STATIC_URL') is not None
    
    # Limites et quotas
    MAX_GAMES_PER_USER = int(os.environ.get('MAX_GAMES_PER_USER', '5'))
    MAX_PHOTOS_PER_USER = int(os.environ.get('MAX_PHOTOS_PER_USER', '100'))
    CLEANUP_INACTIVE_DAYS = int(os.environ.get('CLEANUP_INACTIVE_DAYS', '30'))
    
    @staticmethod
    def init_app(app):
        """Initialise la configuration spécifique à l'app"""
        pass

class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL', 'sqlite:///chess_bot_dev.db')

class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log vers stderr en production
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

class RailwayConfig(ProductionConfig):
    """Configuration spécifique pour Railway"""
    
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)
        
        # Configuration spécifique Railway
        import logging
        logging.basicConfig(level=logging.INFO)

# Mapping des configurations
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'railway': RailwayConfig,
    'default': DevelopmentConfig
}

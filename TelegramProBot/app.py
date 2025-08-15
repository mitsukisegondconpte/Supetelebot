import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
socketio = SocketIO(cors_allowed_origins="*")

# Créer l'application Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuration de la base de données
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///chess_bot.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configuration du bot Telegram
app.config["TELEGRAM_BOT_TOKEN"] = os.environ.get("TELEGRAM_BOT_TOKEN")
app.config["OWNER_ID"] = int(os.environ.get("OWNER_ID", "0"))
app.config["OWNER_USERNAME"] = os.environ.get("OWNER_USERNAME", "admin")
app.config["WEBHOOK_URL"] = os.environ.get("WEBHOOK_URL", "")

# Initialiser les extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'admin.login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
socketio.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    from models import AdminUser
    return AdminUser.query.get(int(user_id))

# Créer les tables et initialiser les données
with app.app_context():
    import models  # noqa: F401
    db.create_all()
    
    # Créer l'utilisateur admin par défaut
    from models import AdminUser
    from werkzeug.security import generate_password_hash
    
    admin = AdminUser.query.filter_by(username=app.config["OWNER_USERNAME"]).first()
    if not admin:
        admin = AdminUser(
            username=app.config["OWNER_USERNAME"],
            telegram_id=app.config["OWNER_ID"],
            password_hash=generate_password_hash("admin123"),
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        logger.info(f"Utilisateur admin créé: {app.config['OWNER_USERNAME']}")

# Importer les routes
from routes import main_bp
from admin_routes import admin_bp
from webhook_handler import webhook_bp

app.register_blueprint(main_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(webhook_bp, url_prefix='/webhook')

# Import du monitoring en temps réel
import real_time_monitor

logger.info("Application Flask initialisée avec succès")

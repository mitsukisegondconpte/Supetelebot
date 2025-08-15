from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship

class AdminUser(UserMixin, db.Model):
    """Modèle pour les utilisateurs administrateurs"""
    __tablename__ = 'admin_users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    telegram_id = Column(Integer, unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

class TelegramUser(db.Model):
    """Modèle pour les utilisateurs Telegram du bot"""
    __tablename__ = 'telegram_users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(64))
    first_name = Column(String(64))
    last_name = Column(String(64))
    language_code = Column(String(10))
    is_bot = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    games = relationship('ChessGame', back_populates='user', cascade='all, delete-orphan')
    activities = relationship('UserActivity', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<TelegramUser {self.telegram_id}: {self.first_name}>'

class ChessGame(db.Model):
    """Modèle pour les parties d'échecs"""
    __tablename__ = 'chess_games'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('telegram_users.id'), nullable=False)
    board_fen = Column(Text, nullable=False, default='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
    pgn_moves = Column(Text, default='')
    status = Column(String(20), default='active')  # active, finished, abandoned
    result = Column(String(20))  # white_wins, black_wins, draw, abandoned
    difficulty_level = Column(Integer, default=5)
    move_count = Column(Integer, default=0)
    ai_thinking_time = Column(Float, default=0.8)
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    
    # Relations
    user = relationship('TelegramUser', back_populates='games')
    moves = relationship('GameMove', back_populates='game', cascade='all, delete-orphan')
    photos = relationship('GamePhoto', back_populates='game', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ChessGame {self.id}: {self.status}>'

class GameMove(db.Model):
    """Modèle pour les coups de la partie"""
    __tablename__ = 'game_moves'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('chess_games.id'), nullable=False)
    move_number = Column(Integer, nullable=False)
    move_uci = Column(String(10), nullable=False)
    move_san = Column(String(20), nullable=False)
    player = Column(String(10), nullable=False)  # user, ai
    time_spent = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    game = relationship('ChessGame', back_populates='moves')
    
    def __repr__(self):
        return f'<GameMove {self.move_san} by {self.player}>'

class GamePhoto(db.Model):
    """Modèle pour les photos d'échiquier envoyées"""
    __tablename__ = 'game_photos'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('chess_games.id'), nullable=False)
    telegram_file_id = Column(String(255), nullable=False)
    file_size = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    game = relationship('ChessGame', back_populates='photos')

class UserActivity(db.Model):
    """Modèle pour traquer les activités des utilisateurs"""
    __tablename__ = 'user_activities'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('telegram_users.id'), nullable=False)
    activity_type = Column(String(50), nullable=False)  # command, move, export, etc.
    description = Column(Text)
    data = Column(Text)  # JSON data for additional info
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    user = relationship('TelegramUser', back_populates='activities')
    
    def __repr__(self):
        return f'<UserActivity {self.activity_type}: {self.description}>'

class SystemStats(db.Model):
    """Modèle pour les statistiques système"""
    __tablename__ = 'system_stats'
    
    id = Column(Integer, primary_key=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(20), default='counter')  # counter, gauge, histogram
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemStats {self.metric_name}: {self.metric_value}>'

class BotCommand(db.Model):
    """Modèle pour les commandes envoyées au bot"""
    __tablename__ = 'bot_commands'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('telegram_users.id'), nullable=False)
    command = Column(String(100), nullable=False)
    parameters = Column(Text)
    response_time = Column(Float)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    user = relationship('TelegramUser')
    
    def __repr__(self):
        return f'<BotCommand {self.command} by {self.user_id}>'

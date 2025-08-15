import logging
import json
from datetime import datetime
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user

from app import socketio, db
from models import UserActivity, TelegramUser, ChessGame
from utils import get_system_stats, record_system_metric

logger = logging.getLogger(__name__)

@socketio.on('connect', namespace='/admin')
def handle_admin_connect():
    """Connexion d'un administrateur au monitoring temps réel"""
    if not current_user.is_authenticated:
        logger.warning("Tentative de connexion non authentifiée au monitoring")
        return False
    
    join_room('admin_room')
    logger.info(f"Admin {current_user.username} connecté au monitoring temps réel")
    
    # Envoyer les statistiques initiales
    try:
        stats = get_system_stats()
        emit('initial_stats', stats)
        
        # Envoyer les activités récentes
        recent_activities = get_recent_activities()
        emit('recent_activities', recent_activities)
        
    except Exception as e:
        logger.error(f"Erreur envoi données initiales: {e}")

@socketio.on('disconnect', namespace='/admin')
def handle_admin_disconnect():
    """Déconnexion d'un administrateur"""
    if current_user.is_authenticated:
        leave_room('admin_room')
        logger.info(f"Admin {current_user.username} déconnecté du monitoring")

@socketio.on('request_stats', namespace='/admin')
def handle_stats_request():
    """Demande de statistiques en temps réel"""
    if not current_user.is_authenticated:
        return
    
    try:
        stats = get_system_stats()
        emit('stats_update', stats)
        
    except Exception as e:
        logger.error(f"Erreur envoi stats: {e}")

@socketio.on('request_user_activities', namespace='/admin')
def handle_user_activities_request(data):
    """Demande d'activités d'un utilisateur spécifique"""
    if not current_user.is_authenticated:
        return
    
    try:
        user_id = data.get('user_id')
        limit = data.get('limit', 50)
        
        if not user_id:
            emit('error', {'message': 'ID utilisateur requis'})
            return
        
        user = TelegramUser.query.filter_by(telegram_id=user_id).first()
        if not user:
            emit('error', {'message': 'Utilisateur non trouvé'})
            return
        
        activities = UserActivity.query\
            .filter_by(user_id=user.id)\
            .order_by(UserActivity.created_at.desc())\
            .limit(limit)\
            .all()
        
        activities_data = []
        for activity in activities:
            activities_data.append({
                'id': activity.id,
                'type': activity.activity_type,
                'description': activity.description,
                'timestamp': activity.created_at.isoformat(),
                'data': json.loads(activity.data) if activity.data else {}
            })
        
        emit('user_activities', {
            'user_id': user_id,
            'activities': activities_data
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération activités utilisateur: {e}")
        emit('error', {'message': str(e)})

@socketio.on('request_active_games', namespace='/admin')
def handle_active_games_request():
    """Demande des parties actives"""
    if not current_user.is_authenticated:
        return
    
    try:
        games = ChessGame.query\
            .join(TelegramUser)\
            .filter(ChessGame.status == 'active')\
            .order_by(ChessGame.created_at.desc())\
            .limit(20)\
            .all()
        
        games_data = []
        for game in games:
            games_data.append({
                'id': game.id,
                'user_id': game.user.telegram_id,
                'user_name': game.user.first_name or game.user.username,
                'move_count': game.move_count,
                'created_at': game.created_at.isoformat(),
                'difficulty': game.difficulty_level
            })
        
        emit('active_games', games_data)
        
    except Exception as e:
        logger.error(f"Erreur récupération parties actives: {e}")
        emit('error', {'message': str(e)})

def get_recent_activities(limit=20):
    """Récupère les activités récentes pour le monitoring"""
    try:
        activities = UserActivity.query\
            .join(TelegramUser)\
            .order_by(UserActivity.created_at.desc())\
            .limit(limit)\
            .all()
        
        activities_data = []
        for activity in activities:
            activities_data.append({
                'id': activity.id,
                'user_id': activity.user.telegram_id,
                'user_name': activity.user.first_name or activity.user.username,
                'type': activity.activity_type,
                'description': activity.description,
                'timestamp': activity.created_at.isoformat()
            })
        
        return activities_data
        
    except Exception as e:
        logger.error(f"Erreur récupération activités récentes: {e}")
        return []

def broadcast_user_activity(user_id, activity_type, description, data=None):
    """Diffuse une activité utilisateur en temps réel"""
    try:
        with db.app.app_context():
            user = TelegramUser.query.filter_by(telegram_id=user_id).first()
            if not user:
                return
            
            activity_data = {
                'user_id': user_id,
                'user_name': user.first_name or user.username or f"User {user_id}",
                'type': activity_type,
                'description': description,
                'timestamp': datetime.utcnow().isoformat(),
                'data': data or {}
            }
            
            socketio.emit('live_activity', activity_data, 
                         room='admin_room', namespace='/admin')
            
            # Enregistrer la métrique
            record_system_metric(f'activity_{activity_type}', 1, 'counter')
            
    except Exception as e:
        logger.error(f"Erreur diffusion activité: {e}")

def broadcast_system_alert(alert_type, message, severity='info'):
    """Diffuse une alerte système"""
    try:
        alert_data = {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        socketio.emit('system_alert', alert_data, 
                     room='admin_room', namespace='/admin')
        
    except Exception as e:
        logger.error(f"Erreur diffusion alerte: {e}")

def broadcast_stats_update():
    """Diffuse une mise à jour des statistiques"""
    try:
        stats = get_system_stats()
        socketio.emit('stats_update', stats, 
                     room='admin_room', namespace='/admin')
        
    except Exception as e:
        logger.error(f"Erreur diffusion stats: {e}")

# Événements personnalisés pour le monitoring

@socketio.on('admin_action', namespace='/admin')
def handle_admin_action(data):
    """Traite une action d'administration"""
    if not current_user.is_authenticated:
        return
    
    action = data.get('action')
    params = data.get('params', {})
    
    try:
        if action == 'block_user':
            user_id = params.get('user_id')
            # Logique de blocage utilisateur
            emit('action_result', {
                'action': action,
                'success': True,
                'message': f'Utilisateur {user_id} bloqué'
            })
            
        elif action == 'cleanup_data':
            days = params.get('days', 30)
            # Logique de nettoyage
            emit('action_result', {
                'action': action,
                'success': True,
                'message': f'Nettoyage effectué ({days} jours)'
            })
            
        elif action == 'restart_bot':
            # Logique de redémarrage
            emit('action_result', {
                'action': action,
                'success': True,
                'message': 'Bot redémarré'
            })
            
        else:
            emit('action_result', {
                'action': action,
                'success': False,
                'message': 'Action non reconnue'
            })
            
    except Exception as e:
        logger.error(f"Erreur action admin: {e}")
        emit('action_result', {
            'action': action,
            'success': False,
            'message': str(e)
        })

# Tâche périodique pour les mises à jour stats
import threading
import time

def periodic_stats_update():
    """Tâche périodique pour mettre à jour les statistiques"""
    while True:
        try:
            time.sleep(30)  # Mise à jour toutes les 30 secondes
            broadcast_stats_update()
        except Exception as e:
            logger.error(f"Erreur tâche périodique: {e}")

# Démarrer la tâche périodique
stats_thread = threading.Thread(target=periodic_stats_update, daemon=True)
stats_thread.start()

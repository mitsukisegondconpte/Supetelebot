from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
import logging
from datetime import datetime

from app import db
from models import TelegramUser, ChessGame, UserActivity
from utils import get_system_stats, is_owner

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Page d'accueil"""
    return render_template('base.html', 
                         title="Bot d'Échecs Professionnel",
                         content="Bienvenue sur le bot d'échecs Telegram avec monitoring en temps réel.")

@main_bp.route('/status')
def status():
    """Endpoint de statut pour Railway"""
    try:
        # Test de connexion à la base de données
        user_count = TelegramUser.query.count()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'users': user_count,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@main_bp.route('/api/stats')
def api_stats():
    """API pour récupérer les statistiques générales"""
    try:
        from flask import current_app
        with current_app.app_context():
            stats = get_system_stats()
            return jsonify(stats)
    except Exception as e:
        logger.error(f"Erreur API stats: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/users')
def api_users():
    """API pour lister les utilisateurs (propriétaire uniquement)"""
    if not hasattr(request, 'telegram_id') or not is_owner(getattr(request, 'telegram_id', 0)):
        return jsonify({'error': 'Accès refusé'}), 403
    
    try:
        users = TelegramUser.query.order_by(TelegramUser.last_activity.desc()).limit(50).all()
        users_data = []
        
        for user in users:
            users_data.append({
                'id': user.telegram_id,
                'name': user.first_name or user.username or f"User {user.telegram_id}",
                'username': user.username,
                'last_activity': user.last_activity.isoformat(),
                'total_games': len(user.games),
                'active_games': len([g for g in user.games if g.status == 'active'])
            })
        
        return jsonify(users_data)
        
    except Exception as e:
        logger.error(f"Erreur API users: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/activities')
def api_activities():
    """API pour récupérer les activités récentes"""
    if not hasattr(request, 'telegram_id') or not is_owner(getattr(request, 'telegram_id', 0)):
        return jsonify({'error': 'Accès refusé'}), 403
    
    try:
        limit = request.args.get('limit', 100, type=int)
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
        
        return jsonify(activities_data)
        
    except Exception as e:
        logger.error(f"Erreur API activities: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/games')
def api_games():
    """API pour récupérer les parties actives"""
    if not hasattr(request, 'telegram_id') or not is_owner(getattr(request, 'telegram_id', 0)):
        return jsonify({'error': 'Accès refusé'}), 403
    
    try:
        status_filter = request.args.get('status', 'active')
        games = ChessGame.query\
            .join(TelegramUser)\
            .filter(ChessGame.status == status_filter)\
            .order_by(ChessGame.created_at.desc())\
            .limit(50)\
            .all()
        
        games_data = []
        for game in games:
            games_data.append({
                'id': game.id,
                'user_id': game.user.telegram_id,
                'user_name': game.user.first_name or game.user.username,
                'status': game.status,
                'move_count': game.move_count,
                'created_at': game.created_at.isoformat(),
                'finished_at': game.finished_at.isoformat() if game.finished_at else None,
                'result': game.result
            })
        
        return jsonify(games_data)
        
    except Exception as e:
        logger.error(f"Erreur API games: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.errorhandler(404)
def not_found(error):
    """Page d'erreur 404"""
    return render_template('base.html', 
                         title="Page non trouvée",
                         content="La page demandée n'existe pas."), 404

@main_bp.errorhandler(500)
def internal_error(error):
    """Page d'erreur 500"""
    db.session.rollback()
    return render_template('base.html', 
                         title="Erreur interne",
                         content="Une erreur interne s'est produite."), 500

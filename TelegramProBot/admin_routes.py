from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
import logging
from datetime import datetime, timedelta

from app import db
from models import AdminUser, TelegramUser, ChessGame, UserActivity, SystemStats
from utils import get_system_stats, get_user_stats, cleanup_old_data

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion administrateur"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Nom d\'utilisateur et mot de passe requis', 'error')
            return render_template('login.html')
        
        admin = AdminUser.query.filter_by(username=username).first()
        
        if admin and admin.is_active and check_password_hash(admin.password_hash, password):
            login_user(admin)
            admin.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'Bienvenue {admin.username}', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Identifiants incorrects', 'error')
    
    return render_template('login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    """Déconnexion administrateur"""
    logout_user()
    flash('Vous êtes déconnecté', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard administrateur principal"""
    try:
        # Récupérer les statistiques système
        stats = get_system_stats()
        
        # Activités récentes
        recent_activities = UserActivity.query\
            .join(TelegramUser)\
            .order_by(UserActivity.created_at.desc())\
            .limit(20)\
            .all()
        
        # Parties actives
        active_games = ChessGame.query\
            .join(TelegramUser)\
            .filter(ChessGame.status == 'active')\
            .order_by(ChessGame.created_at.desc())\
            .limit(10)\
            .all()
        
        # Métriques d'aujourd'hui
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_stats = {
            'new_users': TelegramUser.query.filter(TelegramUser.created_at >= today_start).count(),
            'new_games': ChessGame.query.filter(ChessGame.created_at >= today_start).count(),
            'activities': UserActivity.query.filter(UserActivity.created_at >= today_start).count()
        }
        
        return render_template('admin_dashboard.html', 
                             stats=stats,
                             recent_activities=recent_activities,
                             active_games=active_games,
                             today_stats=today_stats)
        
    except Exception as e:
        logger.error(f"Erreur dashboard: {e}")
        flash('Erreur lors du chargement du dashboard', 'error')
        return render_template('admin_dashboard.html', stats={}, 
                             recent_activities=[], active_games=[], today_stats={})

@admin_bp.route('/monitor')
@login_required
def monitor():
    """Page de monitoring en temps réel"""
    return render_template('monitor.html')

@admin_bp.route('/users')
@login_required
def users():
    """Gestion des utilisateurs"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    users = TelegramUser.query\
        .order_by(TelegramUser.last_activity.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin_users.html', users=users)

@admin_bp.route('/user/<int:telegram_id>')
@login_required
def user_detail(telegram_id):
    """Détails d'un utilisateur"""
    user = TelegramUser.query.filter_by(telegram_id=telegram_id).first_or_404()
    user_stats = get_user_stats(user.id)
    
    # Activités récentes
    activities = UserActivity.query\
        .filter_by(user_id=user.id)\
        .order_by(UserActivity.created_at.desc())\
        .limit(50)\
        .all()
    
    # Parties
    games = ChessGame.query\
        .filter_by(user_id=user.id)\
        .order_by(ChessGame.created_at.desc())\
        .limit(20)\
        .all()
    
    return render_template('admin_user_detail.html', 
                         user=user, stats=user_stats, 
                         activities=activities, games=games)

@admin_bp.route('/games')
@login_required
def games():
    """Gestion des parties"""
    status = request.args.get('status', 'active')
    page = request.args.get('page', 1, type=int)
    per_page = 30
    
    games_query = ChessGame.query.join(TelegramUser)
    
    if status != 'all':
        games_query = games_query.filter(ChessGame.status == status)
    
    games = games_query\
        .order_by(ChessGame.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin_games.html', games=games, current_status=status)

@admin_bp.route('/api/realtime-stats')
@login_required
def realtime_stats():
    """API pour les statistiques en temps réel"""
    try:
        stats = get_system_stats()
        
        # Ajouter des métriques en temps réel
        now = datetime.utcnow()
        last_5min = now - timedelta(minutes=5)
        last_hour = now - timedelta(hours=1)
        
        realtime_data = {
            'current_time': now.isoformat(),
            'active_users_5min': UserActivity.query\
                .filter(UserActivity.created_at >= last_5min)\
                .distinct(UserActivity.user_id)\
                .count(),
            'activities_last_hour': UserActivity.query\
                .filter(UserActivity.created_at >= last_hour)\
                .count(),
            'games_today': ChessGame.query\
                .filter(ChessGame.created_at >= now.replace(hour=0, minute=0, second=0))\
                .count(),
            **stats
        }
        
        return jsonify(realtime_data)
        
    except Exception as e:
        logger.error(f"Erreur realtime stats: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/user-activity-chart')
@login_required
def user_activity_chart():
    """Données pour le graphique d'activité utilisateur"""
    try:
        # Activité par heure sur les dernières 24h
        now = datetime.utcnow()
        hours = []
        activity_counts = []
        
        for i in range(24):
            hour_start = now - timedelta(hours=i+1)
            hour_end = now - timedelta(hours=i)
            
            count = UserActivity.query\
                .filter(UserActivity.created_at >= hour_start)\
                .filter(UserActivity.created_at < hour_end)\
                .count()
            
            hours.append(hour_start.strftime('%H:00'))
            activity_counts.append(count)
        
        hours.reverse()
        activity_counts.reverse()
        
        return jsonify({
            'labels': hours,
            'data': activity_counts
        })
        
    except Exception as e:
        logger.error(f"Erreur activity chart: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/cleanup', methods=['POST'])
@login_required
def api_cleanup():
    """API pour nettoyer les anciennes données"""
    try:
        days = request.json.get('days', 30)
        result = cleanup_old_data(days)
        
        return jsonify({
            'success': True,
            'message': f'Nettoyage effectué: {result.get("activities_deleted", 0)} activités supprimées',
            'details': result
        })
        
    except Exception as e:
        logger.error(f"Erreur cleanup: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/block-user', methods=['POST'])
@login_required
def api_block_user():
    """API pour bloquer/débloquer un utilisateur"""
    try:
        telegram_id = request.json.get('telegram_id')
        block = request.json.get('block', True)
        
        user = TelegramUser.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        user.is_blocked = block
        db.session.commit()
        
        action = 'bloqué' if block else 'débloqué'
        return jsonify({
            'success': True,
            'message': f'Utilisateur {action} avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur block user: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/system-info')
@login_required
def api_system_info():
    """API pour les informations système"""
    try:
        import psutil
        import sys
        
        system_info = {
            'python_version': sys.version,
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'uptime': get_system_uptime()
        }
        
        return jsonify(system_info)
        
    except ImportError:
        return jsonify({
            'python_version': sys.version,
            'message': 'Monitoring système limité (psutil non disponible)'
        })
    except Exception as e:
        logger.error(f"Erreur system info: {e}")
        return jsonify({'error': str(e)}), 500

def get_system_uptime():
    """Calcule l'uptime du système"""
    try:
        import psutil
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        return str(uptime).split('.')[0]  # Enlever les microsecondes
    except ImportError:
        return "N/A"

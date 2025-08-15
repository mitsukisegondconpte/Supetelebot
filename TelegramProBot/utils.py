import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from telegram import User as TelegramUserAPI

from app import db
from models import TelegramUser, UserActivity, SystemStats

logger = logging.getLogger(__name__)

def get_or_create_user(telegram_user: TelegramUserAPI) -> TelegramUser:
    """Récupère ou crée un utilisateur Telegram"""
    user = TelegramUser.query.filter_by(telegram_id=telegram_user.id).first()
    
    if not user:
        user = TelegramUser(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            language_code=telegram_user.language_code,
            is_bot=telegram_user.is_bot,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        db.session.add(user)
        logger.info(f"Nouvel utilisateur créé: {telegram_user.id}")
    else:
        # Mettre à jour les informations
        user.username = telegram_user.username
        user.first_name = telegram_user.first_name
        user.last_name = telegram_user.last_name
        user.language_code = telegram_user.language_code
        user.last_activity = datetime.utcnow()
    
    db.session.commit()
    return user

def track_user_activity(user_id: int, activity_type: str, description: str, 
                       data: Optional[Dict[str, Any]] = None, ip_address: Optional[str] = None):
    """Enregistre une activité utilisateur"""
    try:
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            data=json.dumps(data) if data else None,
            ip_address=ip_address,
            created_at=datetime.utcnow()
        )
        db.session.add(activity)
        db.session.commit()
        
        logger.debug(f"Activité enregistrée: {activity_type} pour utilisateur {user_id}")
        
    except Exception as e:
        logger.error(f"Erreur enregistrement activité: {e}")
        db.session.rollback()

def record_system_metric(metric_name: str, value: float, metric_type: str = 'counter'):
    """Enregistre une métrique système"""
    try:
        metric = SystemStats(
            metric_name=metric_name,
            metric_value=value,
            metric_type=metric_type,
            recorded_at=datetime.utcnow()
        )
        db.session.add(metric)
        db.session.commit()
        
    except Exception as e:
        logger.error(f"Erreur enregistrement métrique: {e}")
        db.session.rollback()

def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Récupère les statistiques d'un utilisateur"""
    try:
        user = TelegramUser.query.get(user_id)
        if not user:
            return {}
        
        # Statistiques des parties
        total_games = len(user.games)
        active_games = len([g for g in user.games if g.status == 'active'])
        finished_games = len([g for g in user.games if g.status == 'finished'])
        
        # Résultats
        wins = len([g for g in user.games if g.result == 'white_wins'])
        losses = len([g for g in user.games if g.result == 'black_wins'])
        draws = len([g for g in user.games if g.result == 'draw'])
        
        # Statistiques des coups
        total_moves = sum([g.move_count for g in user.games if g.move_count])
        
        # Activité récente
        recent_activities = UserActivity.query.filter_by(user_id=user_id)\
            .filter(UserActivity.created_at >= datetime.utcnow() - timedelta(days=7))\
            .count()
        
        return {
            'total_games': total_games,
            'active_games': active_games,
            'finished_games': finished_games,
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'total_moves': total_moves,
            'win_rate': (wins / finished_games * 100) if finished_games > 0 else 0,
            'recent_activities': recent_activities,
            'member_since': user.created_at.strftime('%d/%m/%Y'),
            'last_activity': user.last_activity.strftime('%d/%m/%Y %H:%M')
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération stats utilisateur: {e}")
        return {}

def get_system_stats() -> Dict[str, Any]:
    """Récupère les statistiques système globales"""
    try:
        from app import app
        with app.app_context():
            from models import TelegramUser, ChessGame, GameMove, UserActivity
            
            # Statistiques générales
            total_users = TelegramUser.query.count()
            active_users = TelegramUser.query.filter(
                TelegramUser.last_activity >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            total_games = ChessGame.query.count()
            active_games = ChessGame.query.filter_by(status='active').count()
            finished_games = ChessGame.query.filter_by(status='finished').count()
            
            total_moves = GameMove.query.count()
            
            # Activité récente
            today_activities = UserActivity.query.filter(
                UserActivity.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
            ).count()
            
            # Top utilisateurs actifs
            top_users = db.session.query(TelegramUser)\
                .join(UserActivity)\
                .filter(UserActivity.created_at >= datetime.utcnow() - timedelta(days=7))\
                .group_by(TelegramUser.id)\
                .order_by(db.func.count(UserActivity.id).desc())\
                .limit(5)\
                .all()
            
            top_users_list = [
                {
                    'id': user.telegram_id,
                    'name': user.first_name or user.username or f"User {user.telegram_id}",
                    'activity_count': len([a for a in user.activities 
                                         if a.created_at >= datetime.utcnow() - timedelta(days=7)])
                } for user in top_users
            ]
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'total_games': total_games,
                'active_games': active_games,
                'finished_games': finished_games,
                'total_moves': total_moves,
                'today_activities': today_activities,
                'top_users': top_users_list,
                'uptime': get_uptime(),
                'last_updated': datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Erreur récupération stats système: {e}")
        return {}

def get_uptime() -> str:
    """Calcule le temps de fonctionnement du système"""
    # Simplification: calcul basé sur la première activité enregistrée
    try:
        first_activity = UserActivity.query.order_by(UserActivity.created_at.asc()).first()
        if first_activity:
            uptime = datetime.utcnow() - first_activity.created_at
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{days}j {hours}h {minutes}m"
        return "0j 0h 0m"
    except Exception:
        return "N/A"

def cleanup_old_data(days: int = 30):
    """Nettoie les anciennes données"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Supprimer les anciennes activités
        old_activities = UserActivity.query.filter(UserActivity.created_at < cutoff_date).count()
        UserActivity.query.filter(UserActivity.created_at < cutoff_date).delete()
        
        # Supprimer les anciennes métriques système
        old_metrics = SystemStats.query.filter(SystemStats.recorded_at < cutoff_date).count()
        SystemStats.query.filter(SystemStats.recorded_at < cutoff_date).delete()
        
        db.session.commit()
        
        logger.info(f"Nettoyage effectué: {old_activities} activités et {old_metrics} métriques supprimées")
        
        return {
            'activities_deleted': old_activities,
            'metrics_deleted': old_metrics
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage: {e}")
        db.session.rollback()
        return {'error': str(e)}

def format_user_display_name(user: TelegramUser) -> str:
    """Formate le nom d'affichage d'un utilisateur"""
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    elif user.username:
        return f"@{user.username}"
    else:
        return f"User {user.telegram_id}"

def is_owner(telegram_id: int) -> bool:
    """Vérifie si un utilisateur est le propriétaire"""
    from app import app
    return telegram_id == app.config.get('OWNER_ID', 0)

def log_error(error: Exception, context: str = ""):
    """Log une erreur avec contexte"""
    logger.error(f"{context}: {type(error).__name__}: {str(error)}")
    
    # Enregistrer comme métrique système
    record_system_metric('errors_count', 1, 'counter')

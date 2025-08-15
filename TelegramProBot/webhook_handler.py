from flask import Blueprint, request, jsonify
import logging
import asyncio
from telegram import Update

from app import app, socketio

logger = logging.getLogger(__name__)

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/telegram', methods=['POST'])
def telegram_webhook():
    """Endpoint webhook pour Telegram"""
    try:
        if not request.is_json:
            logger.warning("Webhook reçu sans JSON")
            return jsonify({'error': 'JSON requis'}), 400
        
        update_data = request.get_json()
        
        if not update_data:
            logger.warning("Webhook reçu avec JSON vide")
            return jsonify({'error': 'Données manquantes'}), 400
        
        # Import lazy pour éviter la référence circulaire
        from bot import chess_bot
        
        # Créer l'objet Update de python-telegram-bot
        update = Update.de_json(update_data, chess_bot.application.bot)
        
        if not update:
            logger.warning("Impossible de parser l'update Telegram")
            return jsonify({'error': 'Update invalide'}), 400
        
        # Traiter l'update de manière asynchrone
        asyncio.run(process_telegram_update(update))
        
        # Émettre l'événement en temps réel
        emit_webhook_event(update_data)
        
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"Erreur webhook Telegram: {e}")
        return jsonify({'error': 'Erreur interne'}), 500

async def process_telegram_update(update: Update):
    """Traite un update Telegram de manière asynchrone"""
    try:
        # Traiter l'update avec le bot
        await chess_bot.application.process_update(update)
        
    except Exception as e:
        logger.error(f"Erreur traitement update: {e}")

def emit_webhook_event(update_data):
    """Émet un événement webhook en temps réel"""
    try:
        event_data = {
            'type': 'webhook_received',
            'timestamp': update_data.get('date', 0),
            'update_id': update_data.get('update_id'),
            'has_message': 'message' in update_data,
            'has_callback_query': 'callback_query' in update_data
        }
        
        # Ajouter des informations sur l'utilisateur si disponible
        if 'message' in update_data and 'from' in update_data['message']:
            user = update_data['message']['from']
            event_data['user_id'] = user.get('id')
            event_data['user_name'] = user.get('first_name', 'Inconnu')
        elif 'callback_query' in update_data and 'from' in update_data['callback_query']:
            user = update_data['callback_query']['from']
            event_data['user_id'] = user.get('id')
            event_data['user_name'] = user.get('first_name', 'Inconnu')
        
        # Émettre vers le namespace admin
        socketio.emit('webhook_event', event_data, namespace='/admin')
        
    except Exception as e:
        logger.error(f"Erreur émission événement webhook: {e}")

@webhook_bp.route('/set-webhook', methods=['POST'])
def set_webhook():
    """Définit l'URL du webhook Telegram"""
    try:
        webhook_url = request.json.get('webhook_url')
        
        if not webhook_url:
            return jsonify({'error': 'URL webhook requise'}), 400
        
        # Définir le webhook avec l'API Telegram
        success = asyncio.run(set_telegram_webhook(webhook_url))
        
        if success:
            app.config['WEBHOOK_URL'] = webhook_url
            return jsonify({
                'success': True,
                'message': 'Webhook configuré avec succès',
                'webhook_url': webhook_url
            })
        else:
            return jsonify({'error': 'Erreur lors de la configuration du webhook'}), 500
        
    except Exception as e:
        logger.error(f"Erreur configuration webhook: {e}")
        return jsonify({'error': str(e)}), 500

async def set_telegram_webhook(webhook_url: str) -> bool:
    """Configure le webhook avec l'API Telegram"""
    try:
        if not chess_bot.application:
            await chess_bot.initialize()
        
        bot = chess_bot.application.bot
        webhook_endpoint = f"{webhook_url}/webhook/telegram"
        
        result = await bot.set_webhook(
            url=webhook_endpoint,
            allowed_updates=['message', 'callback_query']
        )
        
        logger.info(f"Webhook configuré: {webhook_endpoint}")
        return result
        
    except Exception as e:
        logger.error(f"Erreur set webhook: {e}")
        return False

@webhook_bp.route('/webhook-info')
def webhook_info():
    """Informations sur le webhook configuré"""
    try:
        webhook_url = app.config.get('WEBHOOK_URL', '')
        
        if not webhook_url:
            return jsonify({
                'configured': False,
                'message': 'Aucun webhook configuré'
            })
        
        return jsonify({
            'configured': True,
            'webhook_url': webhook_url,
            'endpoint': f"{webhook_url}/webhook/telegram"
        })
        
    except Exception as e:
        logger.error(f"Erreur info webhook: {e}")
        return jsonify({'error': str(e)}), 500

@webhook_bp.route('/test-webhook', methods=['POST'])
def test_webhook():
    """Test de connectivité du webhook"""
    try:
        test_data = {
            'update_id': 999999999,
            'message': {
                'message_id': 1,
                'date': 1234567890,
                'text': '/test',
                'from': {
                    'id': 123456789,
                    'is_bot': False,
                    'first_name': 'Test'
                },
                'chat': {
                    'id': 123456789,
                    'type': 'private'
                }
            }
        }
        
        # Simuler la réception d'un webhook
        emit_webhook_event(test_data)
        
        return jsonify({
            'success': True,
            'message': 'Test webhook effectué avec succès',
            'test_data': test_data
        })
        
    except Exception as e:
        logger.error(f"Erreur test webhook: {e}")
        return jsonify({'error': str(e)}), 500

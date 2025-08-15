import asyncio
import logging
import json
from datetime import datetime
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

from app import app, db, socketio
from models import TelegramUser, ChessGame, GameMove, UserActivity, BotCommand
from chess_engine import ChessEngine
from board_renderer import BoardRenderer
from utils import track_user_activity, get_or_create_user

logger = logging.getLogger(__name__)

class ChessBot:
    """Bot d'échecs Telegram amélioré avec monitoring complet"""
    
    def __init__(self):
        self.token = app.config['TELEGRAM_BOT_TOKEN']
        self.owner_id = app.config['OWNER_ID']
        self.chess_engine = ChessEngine()
        self.board_renderer = BoardRenderer()
        self.application = None
        
    async def initialize(self):
        """Initialise le bot Telegram"""
        if not self.token:
            raise ValueError("Token Telegram manquant dans la configuration")
            
        self.application = Application.builder().token(self.token).build()
        
        # Enregistrer les handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        logger.info("Bot Telegram initialisé avec succès")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /start avec interface moderne"""
        user = update.effective_user
        
        with app.app_context():
            # Enregistrer ou mettre à jour l'utilisateur
            telegram_user = get_or_create_user(user)
            
            # Tracker l'activité
            track_user_activity(
                telegram_user.id, 
                'command', 
                'Commande /start exécutée',
                {'command': '/start'}
            )
            
            # Émettre l'événement en temps réel
            socketio.emit('user_activity', {
                'user_id': telegram_user.telegram_id,
                'username': telegram_user.username or telegram_user.first_name,
                'activity': 'Démarrage du bot',
                'timestamp': datetime.utcnow().isoformat()
            }, namespace='/admin')
        
        welcome_message = f"""🏆 **Bot d'Échecs Professionnel** 🏆

Bonjour {user.first_name} !

Bienvenue dans votre bot d'échecs nouvelle génération avec monitoring avancé.

🎯 **Fonctionnalités Premium :**
♟️ Parties isolées avec IA Stockfish
🎨 Interface française intuitive
📊 Tracking complet des performances
🔄 Synchronisation en temps réel
📸 Exports haute qualité
🛡️ Sécurité renforcée

Utilisez les boutons ci-dessous pour commencer !"""

        keyboard = [
            [InlineKeyboardButton("🆕 Nouvelle Partie", callback_data="new_game")],
            [InlineKeyboardButton("♟️ Parties en Cours", callback_data="active_games")],
            [InlineKeyboardButton("📊 Mes Statistiques", callback_data="my_stats")],
            [InlineKeyboardButton("📖 Aide Complète", callback_data="help")]
        ]
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestionnaire principal des boutons avec monitoring"""
        query = update.callback_query
        await query.answer()
        
        user_telegram_id = query.from_user.id
        data = query.data
        
        with app.app_context():
            telegram_user = get_or_create_user(query.from_user)
            
            # Enregistrer la commande
            command = BotCommand(
                user_id=telegram_user.id,
                command=f"button:{data}",
                created_at=datetime.utcnow()
            )
            
            start_time = datetime.utcnow()
            
            try:
                # Router les actions
                if data == "new_game":
                    await self.handle_new_game(query, telegram_user)
                elif data == "active_games":
                    await self.handle_active_games(query, telegram_user)
                elif data == "my_stats":
                    await self.handle_user_stats(query, telegram_user)
                elif data == "help":
                    await self.handle_help(query, telegram_user)
                elif data.startswith("move_"):
                    move_uci = data[5:]
                    await self.handle_move(query, telegram_user, move_uci)
                elif data.startswith("game_"):
                    game_id = int(data[5:])
                    await self.handle_game_action(query, telegram_user, game_id)
                else:
                    await query.edit_message_text("❓ Action non reconnue")
                
                # Marquer comme succès
                command.success = True
                
            except Exception as e:
                logger.error(f"Erreur dans button_handler: {e}")
                command.success = False
                command.error_message = str(e)
                await query.answer("❌ Une erreur s'est produite")
            
            # Calculer le temps de réponse
            response_time = (datetime.utcnow() - start_time).total_seconds()
            command.response_time = response_time
            
            db.session.add(command)
            db.session.commit()
            
            # Émettre l'activité en temps réel
            socketio.emit('button_action', {
                'user_id': user_telegram_id,
                'action': data,
                'success': command.success,
                'response_time': response_time,
                'timestamp': datetime.utcnow().isoformat()
            }, namespace='/admin')
    
    async def handle_new_game(self, query, telegram_user):
        """Démarre une nouvelle partie avec monitoring"""
        # Vérifier le nombre de parties actives
        active_games = ChessGame.query.filter_by(
            user_id=telegram_user.id, 
            status='active'
        ).count()
        
        if active_games >= app.config.get('MAX_GAMES_PER_USER', 5):
            await query.edit_message_text(
                f"❌ **Limite atteinte**\n\nVous avez déjà {active_games} parties actives.\nTerminez une partie avant d'en commencer une nouvelle.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Créer une nouvelle partie
        game = ChessGame(
            user_id=telegram_user.id,
            status='active',
            created_at=datetime.utcnow()
        )
        db.session.add(game)
        db.session.commit()
        
        # Générer l'échiquier initial
        board_image = self.board_renderer.render_board(game.board_fen)
        
        # Tracker l'activité
        track_user_activity(
            telegram_user.id,
            'game_created',
            f'Nouvelle partie créée (ID: {game.id})',
            {'game_id': game.id}
        )
        
        # Interface de jeu
        keyboard = self.chess_engine.get_move_keyboard(game.board_fen, game.id)
        
        await query.message.reply_photo(
            photo=board_image,
            caption=f"🆕 **Nouvelle partie #{game.id}**\n\nVous jouez avec les blancs. À vous de jouer !",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
        
        await query.edit_message_text(
            "✅ Nouvelle partie créée ! Voir l'échiquier ci-dessus.",
            reply_markup=self.get_main_keyboard()
        )
        
        # Notification temps réel
        socketio.emit('new_game', {
            'user_id': telegram_user.telegram_id,
            'game_id': game.id,
            'timestamp': datetime.utcnow().isoformat()
        }, namespace='/admin')
    
    def get_main_keyboard(self):
        """Retourne le clavier principal"""
        keyboard = [
            [InlineKeyboardButton("🆕 Nouvelle Partie", callback_data="new_game")],
            [InlineKeyboardButton("♟️ Parties en Cours", callback_data="active_games")],
            [InlineKeyboardButton("📊 Mes Statistiques", callback_data="my_stats")],
            [InlineKeyboardButton("📖 Aide", callback_data="help")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def handle_move(self, query, telegram_user, move_uci):
        """Traite un coup avec monitoring complet"""
        # Récupérer la partie active
        game = ChessGame.query.filter_by(
            user_id=telegram_user.id,
            status='active'
        ).first()
        
        if not game:
            await query.answer("❌ Aucune partie active trouvée")
            return
        
        try:
            # Traiter le coup
            result = self.chess_engine.make_move(game, move_uci)
            
            if not result['success']:
                await query.answer(f"❌ {result['error']}")
                return
            
            # Sauvegarder le coup
            player_move = GameMove(
                game_id=game.id,
                move_number=game.move_count + 1,
                move_uci=move_uci,
                move_san=result['move_san'],
                player='user',
                created_at=datetime.utcnow()
            )
            db.session.add(player_move)
            
            # Coup de l'IA si la partie continue
            ai_result = None
            if result['game_continues']:
                ai_result = self.chess_engine.make_ai_move(game)
                if ai_result['success']:
                    ai_move = GameMove(
                        game_id=game.id,
                        move_number=game.move_count + 2,
                        move_uci=ai_result['move_uci'],
                        move_san=ai_result['move_san'],
                        player='ai',
                        time_spent=ai_result.get('thinking_time'),
                        created_at=datetime.utcnow()
                    )
                    db.session.add(ai_move)
            
            # Mettre à jour la partie
            game.board_fen = result['new_fen']
            game.move_count = result['move_count']
            game.status = result.get('status', 'active')
            
            if result.get('game_over'):
                game.finished_at = datetime.utcnow()
                game.result = result.get('result')
            
            db.session.commit()
            
            # Générer la nouvelle image
            board_image = self.board_renderer.render_board(game.board_fen)
            
            # Préparer le message
            message = f"Votre coup: **{result['move_san']}**"
            if ai_result and ai_result['success']:
                message += f"\nCoup de l'IA: **{ai_result['move_san']}**"
            
            if result.get('game_over'):
                message += f"\n\n🏁 **Partie terminée: {result.get('result_message')}**"
                keyboard = self.get_game_over_keyboard(game.id)
            else:
                message += f"\n\n♟️ **À votre tour**"
                keyboard = self.chess_engine.get_move_keyboard(game.board_fen, game.id)
            
            await query.message.reply_photo(
                photo=board_image,
                caption=message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Tracker l'activité
            track_user_activity(
                telegram_user.id,
                'move_played',
                f'Coup joué: {result["move_san"]}',
                {
                    'game_id': game.id,
                    'move_uci': move_uci,
                    'move_san': result['move_san']
                }
            )
            
            # Notification temps réel
            socketio.emit('move_played', {
                'user_id': telegram_user.telegram_id,
                'game_id': game.id,
                'move': result['move_san'],
                'ai_move': ai_result['move_san'] if ai_result and ai_result['success'] else None,
                'game_over': result.get('game_over', False),
                'timestamp': datetime.utcnow().isoformat()
            }, namespace='/admin')
            
        except Exception as e:
            logger.error(f"Erreur lors du coup: {e}")
            await query.answer("❌ Erreur lors du traitement du coup")
    
    def get_game_over_keyboard(self, game_id):
        """Clavier pour la fin de partie"""
        keyboard = [
            [InlineKeyboardButton("📸 Export PNG", callback_data=f"export_png_{game_id}")],
            [InlineKeyboardButton("📄 Export PGN", callback_data=f"export_pgn_{game_id}")],
            [InlineKeyboardButton("🆕 Nouvelle Partie", callback_data="new_game")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande admin pour le propriétaire"""
        user_id = update.effective_user.id
        
        if user_id != self.owner_id:
            await update.message.reply_text("❌ Accès refusé. Commande réservée au propriétaire.")
            return
        
        with app.app_context():
            # Statistiques rapides
            total_users = TelegramUser.query.count()
            active_games = ChessGame.query.filter_by(status='active').count()
            total_games = ChessGame.query.count()
            
            admin_message = f"""🛡️ **Panel Administrateur**

📊 **Statistiques en temps réel:**
👥 Utilisateurs totaux: {total_users}
♟️ Parties actives: {active_games}
🎮 Parties totales: {total_games}

🔗 **Accès Dashboard:** /admin
🌐 **Monitoring live:** Activé

⚡ **Statut système:** Opérationnel"""

            keyboard = [
                [InlineKeyboardButton("📊 Dashboard Web", url=f"{app.config.get('WEBHOOK_URL', '')}/admin")],
                [InlineKeyboardButton("📈 Statistiques Détaillées", callback_data="admin_detailed_stats")],
                [InlineKeyboardButton("🧹 Nettoyage Système", callback_data="admin_cleanup")],
                [InlineKeyboardButton("🔄 Redémarrer Bot", callback_data="admin_restart")]
            ]
            
            await update.message.reply_text(
                admin_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )

# Instance globale du bot
chess_bot = ChessBot()

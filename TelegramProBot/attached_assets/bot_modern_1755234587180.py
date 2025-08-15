#!/usr/bin/env python3
"""
Bot d'échecs Telegram moderne avec interface à boutons
Développé pour jouer contre Stockfish avec interface française intuitive
"""

import os
import logging
import asyncio
import chess
import chess.engine
import zipfile
from datetime import datetime
from typing import Dict, Optional
from io import StringIO, BytesIO

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode

from board_render import render_board_png
from bot_interface import (
    create_start_keyboard, create_move_keyboard, create_game_over_keyboard,
    create_confirm_delete_keyboard, create_admin_keyboard
)

# Configuration
BOT_TOKEN = "8246900361:AAEddxyAKtrPm8dv0HN1v-lR0wmEKo6955A"
OWNER_ID = 123456789  # Remplacer par votre ID Telegram
STOCKFISH_PATH = "stockfish"
STOCKFISH_SKILL_LEVEL = 5
STOCKFISH_TIME = 0.8

# Configuration des logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Stockage des données en mémoire
user_games: Dict[int, chess.Board] = {}
user_nicknames: Dict[int, str] = {}
user_photos: Dict[int, list] = {}  # Stockage des IDs de photos par utilisateur

def get_user_display_name(user_id: int, username: str = None, first_name: str = None) -> str:
    """Récupère le nom d'affichage de l'utilisateur"""
    if user_id in user_nicknames:
        return user_nicknames[user_id]
    elif username:
        return f"@{username}"
    elif first_name:
        return first_name
    else:
        return f"Utilisateur {user_id}"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start - Interface d'accueil avec boutons"""
    user_id = update.effective_user.id
    user_name = get_user_display_name(
        user_id, 
        update.effective_user.username,
        update.effective_user.first_name
    )
    
    if user_id not in user_photos:
        user_photos[user_id] = []
    
    welcome_message = f"""🏆 **Bot d'Échecs Français** 🏆

Bonjour {user_name} ! 

Bienvenue dans votre bot d'échecs personnel. Vous pouvez jouer contre le moteur Stockfish niveau {STOCKFISH_SKILL_LEVEL}.

🎯 **Fonctionnalités :**
♟️ Parties individuelles isolées
🎨 Échiquier visuel en français
🤖 IA Stockfish niveau réglable  
📸 Export PNG/FEN/PGN
🗑️ Gestion de l'espace de stockage

Utilisez les boutons ci-dessous pour commencer !"""

    await update.message.reply_text(
        welcome_message,
        reply_markup=create_start_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestionnaire principal des boutons"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "new_game":
        await handle_new_game(query, user_id)
    elif data == "show_board":
        await handle_show_board(query, user_id)
    elif data == "help":
        await handle_help(query)
    elif data == "resign":
        await handle_resign(query, user_id)
    elif data.startswith("move_"):
        move_uci = data[5:]  # Enlever le préfixe "move_"
        await handle_move(query, user_id, move_uci)
    elif data == "export_png":
        await handle_export_png(query, user_id)
    elif data == "export_fen":
        await handle_export_fen(query, user_id)
    elif data == "export_pgn":
        await handle_export_pgn(query, user_id)
    elif data == "delete_photos":
        await handle_delete_photos_request(query, user_id)
    elif data == "confirm_delete":
        await handle_confirm_delete(query, user_id)
    elif data == "cancel_delete":
        await handle_cancel_delete(query)
    elif data == "main_menu":
        await handle_main_menu(query)
    elif data == "info":
        # Bouton informatif, ne fait rien
        pass
    elif data.startswith("admin_"):
        await handle_admin_commands(query, user_id, data)
    else:
        # Bouton non reconnu
        await query.answer("❓ Action non reconnue")

async def handle_new_game(query, user_id):
    """Démarre une nouvelle partie"""
    user_games[user_id] = chess.Board()
    
    # Créer et envoyer l'échiquier initial
    png_data = render_board_png(user_games[user_id])
    photo_msg = await query.message.reply_photo(
        photo=BytesIO(png_data),
        caption="🆕 **Nouvelle partie commencée !**\n\nVous jouez avec les blancs. Choisissez votre coup :",
        reply_markup=create_move_keyboard(user_games[user_id]),
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Stocker l'ID de la photo
    if user_id not in user_photos:
        user_photos[user_id] = []
    user_photos[user_id].append(photo_msg.photo[-1].file_id)
    
    await query.edit_message_text(
        "✅ Nouvelle partie créée ! Voir l'échiquier ci-dessus.",
        reply_markup=create_start_keyboard()
    )

async def handle_show_board(query, user_id):
    """Affiche l'échiquier actuel"""
    if user_id not in user_games:
        await query.edit_message_text(
            "❌ Aucune partie en cours. Commencez une nouvelle partie !",
            reply_markup=create_start_keyboard()
        )
        return
    
    board = user_games[user_id]
    png_data = render_board_png(board)
    
    # Déterminer le statut de la partie
    if board.is_game_over():
        if board.is_checkmate():
            if board.turn == chess.WHITE:
                status = "🏆 **Victoire des Noirs !** Échec et mat."
            else:
                status = "🏆 **Victoire des Blancs !** Échec et mat."
        elif board.is_stalemate():
            status = "🤝 **Match nul !** Pat."
        elif board.is_insufficient_material():
            status = "🤝 **Match nul !** Matériel insuffisant."
        else:
            status = "🤝 **Match nul !**"
        
        reply_markup = create_game_over_keyboard()
    else:
        turn = "Blancs" if board.turn == chess.WHITE else "Noirs"
        check_status = " (Échec !)" if board.is_check() else ""
        status = f"♟️ **Tour des {turn}**{check_status}"
        reply_markup = create_move_keyboard(board)
    
    photo_msg = await query.message.reply_photo(
        photo=BytesIO(png_data),
        caption=status,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Stocker l'ID de la photo
    if user_id not in user_photos:
        user_photos[user_id] = []
    user_photos[user_id].append(photo_msg.photo[-1].file_id)

async def handle_move(query, user_id, move_uci):
    """Traite un coup du joueur"""
    if user_id not in user_games:
        await query.answer("❌ Aucune partie en cours !")
        return
    
    board = user_games[user_id]
    
    try:
        # Valider et jouer le coup du joueur
        move = chess.Move.from_uci(move_uci)
        if move not in board.legal_moves:
            await query.answer("❌ Coup illégal !")
            return
        
        move_san = board.san(move)
        board.push(move)
        
        # Vérifier si la partie est terminée après le coup du joueur
        if board.is_game_over():
            png_data = render_board_png(board)
            
            if board.is_checkmate():
                status = "🏆 **Vous avez gagné !** Échec et mat."
            elif board.is_stalemate():
                status = "🤝 **Match nul !** Pat."
            else:
                status = "🤝 **Partie terminée !**"
            
            photo_msg = await query.message.reply_photo(
                photo=BytesIO(png_data),
                caption=f"Votre coup : **{move_san}**\n\n{status}",
                reply_markup=create_game_over_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
            if user_id not in user_photos:
                user_photos[user_id] = []
            user_photos[user_id].append(photo_msg.photo[-1].file_id)
            return
        
        # Coup de l'IA avec Stockfish
        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            engine.configure({"Skill Level": STOCKFISH_SKILL_LEVEL})
            result = engine.play(board, chess.engine.Limit(time=STOCKFISH_TIME))
            ai_move = result.move
            ai_move_san = board.san(ai_move)
            board.push(ai_move)
        
        # Afficher l'échiquier après les deux coups
        png_data = render_board_png(board)
        
        if board.is_game_over():
            if board.is_checkmate():
                status = "🤖 **L'IA a gagné !** Échec et mat."
            elif board.is_stalemate():
                status = "🤝 **Match nul !** Pat."
            else:
                status = "🤝 **Partie terminée !**"
            reply_markup = create_game_over_keyboard()
        else:
            check_status = " (Vous êtes en échec !)" if board.is_check() else ""
            status = f"♟️ **À votre tour**{check_status}"
            reply_markup = create_move_keyboard(board)
        
        caption = f"Votre coup : **{move_san}**\nCoup de l'IA : **{ai_move_san}**\n\n{status}"
        
        photo_msg = await query.message.reply_photo(
            photo=BytesIO(png_data),
            caption=caption,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        if user_id not in user_photos:
            user_photos[user_id] = []
        user_photos[user_id].append(photo_msg.photo[-1].file_id)
        
    except Exception as e:
        logger.error(f"Erreur lors du coup : {e}")
        await query.answer("❌ Erreur lors du traitement du coup !")

async def handle_help(query):
    """Affiche l'aide"""
    help_text = """📖 **Aide - Bot d'Échecs**

🎯 **Comment jouer :**
1️⃣ Cliquez sur "Nouvelle partie" pour commencer
2️⃣ Les coups disponibles sont groupés par pièce
3️⃣ Cliquez sur un coup pour le jouer
4️⃣ L'IA (Stockfish) joue automatiquement après vous

♟️ **Types de pièces :**
♟️ Pion - Avance d'une case (deux au premier coup)
♜ Tour - Déplacement horizontal/vertical
♞ Cavalier - Déplacement en "L"
♝ Fou - Déplacement diagonal
♛ Reine - Combine tour et fou
♚ Roi - Une case dans toutes les directions

📸 **En fin de partie :**
• Exporter PNG : Image de l'échiquier final
• Exporter FEN : Position pour analysis
• Exporter PGN : Historique complet de la partie
• Supprimer photos : Libère l'espace de stockage

🎮 **Niveaux Stockfish :** 1 (facile) à 20 (expert)
Niveau actuel : **{STOCKFISH_SKILL_LEVEL}**"""

    await query.edit_message_text(
        help_text,
        reply_markup=create_start_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_resign(query, user_id):
    """Gère l'abandon de partie"""
    if user_id not in user_games:
        await query.answer("❌ Aucune partie en cours !")
        return
    
    del user_games[user_id]
    
    await query.edit_message_text(
        "🏳️ **Partie abandonnée**\n\nVous pouvez commencer une nouvelle partie quand vous voulez !",
        reply_markup=create_start_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_export_png(query, user_id):
    """Exporte l'échiquier en PNG"""
    if user_id not in user_games:
        await query.answer("❌ Aucune partie à exporter !")
        return
    
    board = user_games[user_id]
    png_data = render_board_png(board)
    
    filename = f"echecs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    
    await query.message.reply_document(
        document=BytesIO(png_data),
        filename=filename,
        caption="📸 **Export PNG de votre partie**"
    )
    
    await query.answer("✅ PNG exporté !")

async def handle_export_fen(query, user_id):
    """Exporte la position en FEN"""
    if user_id not in user_games:
        await query.answer("❌ Aucune partie à exporter !")
        return
    
    board = user_games[user_id]
    fen = board.fen()
    
    fen_content = f"Position FEN :\n{fen}\n\nImportez cette position dans votre logiciel d'échecs favori !"
    
    await query.message.reply_text(
        f"📄 **Export FEN**\n\n`{fen}`\n\nCopiez cette position pour l'analyser !",
        parse_mode=ParseMode.MARKDOWN
    )
    
    await query.answer("✅ FEN exporté !")

async def handle_export_pgn(query, user_id):
    """Exporte la partie en PGN"""
    if user_id not in user_games:
        await query.answer("❌ Aucune partie à exporter !")
        return
    
    board = user_games[user_id]
    
    # Créer un PGN simple
    pgn_content = f"""[Event "Partie contre Stockfish"]
[Date "{datetime.now().strftime('%Y.%m.%d')}"]
[White "Joueur"]
[Black "Stockfish Level {STOCKFISH_SKILL_LEVEL}"]
[Result "*"]

{board.variation_san(board.move_stack)}
"""
    
    filename = f"partie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pgn"
    
    await query.message.reply_document(
        document=BytesIO(pgn_content.encode('utf-8')),
        filename=filename,
        caption="📋 **Export PGN de votre partie**"
    )
    
    await query.answer("✅ PGN exporté !")

async def handle_delete_photos_request(query, user_id):
    """Demande confirmation pour supprimer les photos"""
    if user_id not in user_photos or not user_photos[user_id]:
        await query.answer("❌ Aucune photo à supprimer !")
        return
    
    photo_count = len(user_photos[user_id])
    
    # Calculer une estimation de l'espace utilisé (approximatif)
    estimated_size = photo_count * 150  # Estimation ~150KB par image PNG d'échiquier
    size_unit = "KB"
    if estimated_size > 1024:
        estimated_size = estimated_size / 1024
        size_unit = "MB"
    
    await query.edit_message_text(
        f"🗑️ **Supprimer les photos**\n\nVous avez **{photo_count}** photo(s) référencée(s) (~{estimated_size:.1f} {size_unit}).\n\n📋 **Important**: Cette action supprime les références du bot mais les images restent visibles dans l'historique du chat.\n\n⚠️ Confirmer la suppression ?",
        reply_markup=create_confirm_delete_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_confirm_delete(query, user_id):
    """Confirme et supprime les photos"""
    if user_id in user_photos and user_photos[user_id]:
        photo_count = len(user_photos[user_id])
        
        # Tentative de suppression réelle des photos du chat
        deleted_count = 0
        for photo_id in user_photos[user_id]:
            try:
                # Note: Telegram ne permet pas de supprimer les photos envoyées par le bot
                # Nous supprimons seulement notre référence locale
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Impossible de supprimer la photo {photo_id}: {e}")
        
        # Vider notre stockage local
        user_photos[user_id] = []
        
        await query.edit_message_text(
            f"✅ **Photos supprimées**\n\n{photo_count} référence(s) de photo(s) supprimée(s) avec succès.\n\n📋 **Note**: Les images restent visibles dans l'historique du chat mais ne sont plus comptées dans votre stockage bot.\n\nEspace de stockage bot libéré !",
            reply_markup=create_start_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await query.answer("❌ Aucune photo à supprimer !")

async def handle_cancel_delete(query):
    """Annule la suppression des photos"""
    await query.edit_message_text(
        "❌ **Suppression annulée**\n\nVos photos sont conservées.",
        reply_markup=create_start_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_main_menu(query):
    """Retour au menu principal"""
    await query.edit_message_text(
        "🏠 **Menu principal**\n\nChoisissez une option :",
        reply_markup=create_start_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_admin_commands(query, user_id, data):
    """Gère les commandes d'administration"""
    if user_id != OWNER_ID:
        await query.answer("❌ Accès refusé !")
        return
    
    if data == "admin_stats":
        active_games = len(user_games)
        total_users = len(set(list(user_games.keys()) + list(user_nicknames.keys())))
        total_photos = sum(len(photos) for photos in user_photos.values())
        
        stats = f"""📊 **Statistiques du Bot**

👥 Utilisateurs total : **{total_users}**
♟️ Parties actives : **{active_games}**
📸 Photos stockées : **{total_photos}**
🤖 Niveau Stockfish : **{STOCKFISH_SKILL_LEVEL}**"""

        await query.edit_message_text(stats, reply_markup=create_admin_keyboard(), parse_mode=ParseMode.MARKDOWN)
    
    elif data == "admin_games":
        if not user_games:
            await query.edit_message_text(
                "📊 **Parties actives**\n\nAucune partie en cours.",
                reply_markup=create_admin_keyboard()
            )
            return
        
        games_info = "📊 **Parties actives :**\n\n"
        for uid, board in user_games.items():
            user_name = get_user_display_name(uid)
            move_count = len(board.move_stack)
            turn = "Blancs" if board.turn == chess.WHITE else "Noirs"
            photo_count = len(user_photos.get(uid, []))
            games_info += f"• {user_name}: {move_count} coups, tour aux {turn}, {photo_count} photos\n"
        
        await query.edit_message_text(games_info, reply_markup=create_admin_keyboard())
    
    elif data == "admin_cleanup":
        # Fonction de nettoyage global pour l'admin
        total_photos_before = sum(len(photos) for photos in user_photos.values())
        
        # Nettoyer les photos des utilisateurs sans partie active
        cleaned_users = 0
        cleaned_photos = 0
        
        for uid in list(user_photos.keys()):
            if uid not in user_games and user_photos[uid]:
                cleaned_photos += len(user_photos[uid])
                user_photos[uid] = []
                cleaned_users += 1
        
        cleanup_msg = f"""🧹 **Nettoyage effectué**

👥 Utilisateurs nettoyés: {cleaned_users}
📸 Photos supprimées: {cleaned_photos}
📊 Photos restantes: {total_photos_before - cleaned_photos}

Seules les photos des utilisateurs sans partie active ont été supprimées."""

        await query.edit_message_text(cleanup_msg, reply_markup=create_admin_keyboard(), parse_mode=ParseMode.MARKDOWN)

async def nickname_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les surnoms et messages texte"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Si l'utilisateur n'a pas de surnom, on lui demande
    if user_id not in user_nicknames:
        user_nicknames[user_id] = text
        await update.message.reply_text(
            f"✅ **Surnom enregistré !**\n\nBonjour {text} ! Utilisez les boutons ci-dessous pour jouer.",
            reply_markup=create_start_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Rediriger vers l'interface à boutons
        await update.message.reply_text(
            "🎮 **Interface à boutons**\n\nUtilisez les boutons ci-dessous pour interagir avec le bot :",
            reply_markup=create_start_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

def main():
    """Fonction principale"""
    print("🏆 Bot d'échecs moderne en démarrage...")
    
    # Créer l'application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Gestionnaires de commandes
    application.add_handler(CommandHandler("start", start_command))
    
    # Gestionnaire de boutons
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Gestionnaire de messages texte (surnoms)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, nickname_handler))
    
    # Démarrer le bot
    print("✅ Bot démarré ! Appuyez sur Ctrl+C pour arrêter.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
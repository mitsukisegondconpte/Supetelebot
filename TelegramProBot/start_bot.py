#!/usr/bin/env python3
"""
Script pour démarrer le bot Telegram d'échecs
"""
import os
import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Point d'entrée principal pour démarrer le bot"""
    try:
        # Vérifier le token
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            logger.error("TELEGRAM_BOT_TOKEN non configuré")
            return
        
        # Importer le bot avec gestion des dépendances
        from bot import chess_bot
        
        logger.info(f"Bot Telegram @{chess_bot.bot.username} configuré")
        logger.info("Démarrage en mode polling pour les tests...")
        
        # Démarrer le bot en mode polling
        chess_bot.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Erreur démarrage bot: {e}")
        
if __name__ == '__main__':
    main()
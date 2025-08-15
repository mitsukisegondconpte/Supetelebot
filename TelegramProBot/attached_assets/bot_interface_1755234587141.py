# Interface avec boutons pour le bot d'échecs
import chess
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def create_start_keyboard():
    """Crée le clavier principal avec boutons de démarrage"""
    keyboard = [
        [InlineKeyboardButton("🆕 Nouvelle partie", callback_data="new_game")],
        [InlineKeyboardButton("♟️ Voir l'échiquier", callback_data="show_board")],
        [InlineKeyboardButton("📖 Aide", callback_data="help")],
        [InlineKeyboardButton("🏳️ Abandonner", callback_data="resign")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_move_keyboard(board):
    """Crée le clavier avec les coups disponibles groupés par type de pièce"""
    if board.is_game_over():
        return create_game_over_keyboard()
    
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return create_start_keyboard()
    
    # Grouper les coups par type de pièce
    moves_by_piece = {
        "Pion": [],
        "Tour": [],
        "Cavalier": [],
        "Fou": [],
        "Reine": [],
        "Roi": []
    }
    
    piece_names = {
        chess.PAWN: "Pion",
        chess.ROOK: "Tour", 
        chess.KNIGHT: "Cavalier",
        chess.BISHOP: "Fou",
        chess.QUEEN: "Reine",
        chess.KING: "Roi"
    }
    
    for move in legal_moves:
        piece = board.piece_at(move.from_square)
        if piece:
            piece_type = piece_names.get(piece.piece_type, "Pion")
            move_str = board.san(move)
            moves_by_piece[piece_type].append((move_str, f"move_{move.uci()}"))
    
    keyboard = []
    
    # Créer les boutons pour chaque type de pièce
    for piece_type, moves in moves_by_piece.items():
        if moves:
            # Ligne de titre pour le type de pièce
            piece_emoji = {
                "Pion": "♟️", "Tour": "♜", "Cavalier": "♞",
                "Fou": "♝", "Reine": "♛", "Roi": "♚"
            }
            keyboard.append([InlineKeyboardButton(f"{piece_emoji[piece_type]} {piece_type}", callback_data="info")])
            
            # Boutons des coups (max 3 par ligne)
            row = []
            for move_str, callback_data in moves:
                row.append(InlineKeyboardButton(move_str, callback_data=callback_data))
                if len(row) == 3:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)
    
    # Boutons d'actions générales
    keyboard.append([
        InlineKeyboardButton("🔄 Rafraîchir", callback_data="show_board"),
        InlineKeyboardButton("🏳️ Abandonner", callback_data="resign")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_game_over_keyboard():
    """Crée le clavier de fin de partie avec options d'export"""
    keyboard = [
        [InlineKeyboardButton("📸 Exporter PNG", callback_data="export_png")],
        [InlineKeyboardButton("📄 Exporter FEN", callback_data="export_fen")],
        [InlineKeyboardButton("📋 Exporter PGN", callback_data="export_pgn")],
        [InlineKeyboardButton("🗑️ Supprimer photos", callback_data="delete_photos")],
        [InlineKeyboardButton("🆕 Nouvelle partie", callback_data="new_game")],
        [InlineKeyboardButton("🏠 Menu principal", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_confirm_delete_keyboard():
    """Clavier de confirmation pour supprimer les photos"""
    keyboard = [
        [InlineKeyboardButton("✅ Oui, supprimer", callback_data="confirm_delete")],
        [InlineKeyboardButton("❌ Annuler", callback_data="cancel_delete")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_admin_keyboard():
    """Clavier d'administration pour le propriétaire"""
    keyboard = [
        [InlineKeyboardButton("📊 Statistiques", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Parties actives", callback_data="admin_games")],
        [InlineKeyboardButton("📦 Export global", callback_data="admin_export")],
        [InlineKeyboardButton("🧹 Nettoyage global", callback_data="admin_cleanup")]
    ]
    return InlineKeyboardMarkup(keyboard)
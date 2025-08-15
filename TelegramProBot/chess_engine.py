import chess
import chess.engine
import logging
from datetime import datetime
from typing import Dict, Optional, List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app import app

logger = logging.getLogger(__name__)

class ChessEngine:
    """Moteur d'échecs avec Stockfish et interface Telegram"""
    
    def __init__(self):
        self.stockfish_path = app.config.get('STOCKFISH_PATH', 'stockfish')
        self.default_skill = app.config.get('DEFAULT_SKILL_LEVEL', 5)
        self.default_time = app.config.get('DEFAULT_AI_TIME', 0.8)
    
    def make_move(self, game, move_uci: str) -> Dict:
        """Traite un coup du joueur"""
        try:
            board = chess.Board(game.board_fen)
            move = chess.Move.from_uci(move_uci)
            
            if move not in board.legal_moves:
                return {
                    'success': False,
                    'error': 'Coup illégal'
                }
            
            move_san = board.san(move)
            board.push(move)
            
            result = {
                'success': True,
                'move_san': move_san,
                'new_fen': board.fen(),
                'move_count': game.move_count + 1,
                'game_continues': not board.is_game_over()
            }
            
            if board.is_game_over():
                result.update({
                    'game_over': True,
                    'status': 'finished'
                })
                
                if board.is_checkmate():
                    if board.turn == chess.WHITE:
                        result['result'] = 'black_wins'
                        result['result_message'] = 'Victoire des Noirs par échec et mat'
                    else:
                        result['result'] = 'white_wins'
                        result['result_message'] = 'Victoire des Blancs par échec et mat'
                elif board.is_stalemate():
                    result['result'] = 'draw'
                    result['result_message'] = 'Match nul par pat'
                elif board.is_insufficient_material():
                    result['result'] = 'draw'
                    result['result_message'] = 'Match nul par matériel insuffisant'
                else:
                    result['result'] = 'draw'
                    result['result_message'] = 'Match nul'
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors du coup: {e}")
            return {
                'success': False,
                'error': f'Erreur interne: {str(e)}'
            }
    
    def make_ai_move(self, game) -> Dict:
        """Fait jouer l'IA avec Stockfish"""
        try:
            board = chess.Board(game.board_fen)
            
            if board.is_game_over():
                return {'success': False, 'error': 'Partie terminée'}
            
            start_time = datetime.utcnow()
            
            with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
                engine.configure({"Skill Level": game.difficulty_level or self.default_skill})
                result = engine.play(board, chess.engine.Limit(time=game.ai_thinking_time or self.default_time))
                ai_move = result.move
                
                if ai_move is None:
                    return {'success': False, 'error': 'IA ne peut pas jouer'}
                
                ai_move_san = board.san(ai_move)
                board.push(ai_move)
                
                thinking_time = (datetime.utcnow() - start_time).total_seconds()
                
                return {
                    'success': True,
                    'move_uci': ai_move.uci(),
                    'move_san': ai_move_san,
                    'new_fen': board.fen(),
                    'thinking_time': thinking_time
                }
                
        except FileNotFoundError:
            logger.error("Stockfish non trouvé")
            return {'success': False, 'error': 'Moteur d\'échecs indisponible'}
        except Exception as e:
            logger.error(f"Erreur IA: {e}")
            return {'success': False, 'error': f'Erreur IA: {str(e)}'}
    
    def get_move_keyboard(self, fen: str, game_id: int) -> InlineKeyboardMarkup:
        """Génère le clavier des coups possibles groupés par pièce"""
        try:
            board = chess.Board(fen)
            
            if board.is_game_over():
                return self._get_game_over_keyboard(game_id)
            
            legal_moves = list(board.legal_moves)
            if not legal_moves:
                return InlineKeyboardMarkup([[]])
            
            # Grouper les coups par type de pièce
            moves_by_piece = {
                "♟️ Pions": [],
                "♜ Tours": [],
                "♞ Cavaliers": [],
                "♝ Fous": [],
                "♛ Reine": [],
                "♚ Roi": []
            }
            
            piece_mapping = {
                chess.PAWN: "♟️ Pions",
                chess.ROOK: "♜ Tours",
                chess.KNIGHT: "♞ Cavaliers",
                chess.BISHOP: "♝ Fous",
                chess.QUEEN: "♛ Reine",
                chess.KING: "♚ Roi"
            }
            
            for move in legal_moves:
                piece = board.piece_at(move.from_square)
                if piece:
                    piece_type = piece_mapping.get(piece.piece_type, "♟️ Pions")
                    move_san = board.san(move)
                    moves_by_piece[piece_type].append((move_san, f"move_{move.uci()}"))
            
            keyboard = []
            
            # Créer les boutons pour chaque type de pièce
            for piece_type, moves in moves_by_piece.items():
                if moves:
                    # Ligne de titre pour le type de pièce
                    keyboard.append([InlineKeyboardButton(piece_type, callback_data="info")])
                    
                    # Boutons des coups (max 3 par ligne)
                    row = []
                    for move_san, callback_data in moves[:9]:  # Limiter à 9 coups par type
                        row.append(InlineKeyboardButton(move_san, callback_data=callback_data))
                        if len(row) == 3:
                            keyboard.append(row)
                            row = []
                    if row:
                        keyboard.append(row)
            
            # Boutons d'actions générales
            keyboard.append([
                InlineKeyboardButton("🔄 Actualiser", callback_data=f"refresh_{game_id}"),
                InlineKeyboardButton("🏳️ Abandonner", callback_data=f"resign_{game_id}")
            ])
            
            return InlineKeyboardMarkup(keyboard)
            
        except Exception as e:
            logger.error(f"Erreur génération clavier: {e}")
            return InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Erreur", callback_data="error")
            ]])
    
    def _get_game_over_keyboard(self, game_id: int) -> InlineKeyboardMarkup:
        """Clavier pour une partie terminée"""
        keyboard = [
            [InlineKeyboardButton("📸 Export PNG", callback_data=f"export_png_{game_id}")],
            [InlineKeyboardButton("📄 Export PGN", callback_data=f"export_pgn_{game_id}")],
            [InlineKeyboardButton("📊 Analyse", callback_data=f"analyze_{game_id}")],
            [InlineKeyboardButton("🆕 Nouvelle Partie", callback_data="new_game")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def analyze_position(self, fen: str, depth: int = 15) -> Dict:
        """Analyse une position avec Stockfish"""
        try:
            board = chess.Board(fen)
            
            with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
                info = engine.analyse(board, chess.engine.Limit(depth=depth))
                
                score = info.get('score')
                if score:
                    if score.is_mate():
                        evaluation = f"Mat en {abs(score.mate())}"
                    else:
                        cp_score = score.white().score(mate_score=10000)
                        evaluation = f"{cp_score/100:.2f}"
                else:
                    evaluation = "N/A"
                
                best_move = info.get('pv', [None])[0]
                best_move_san = board.san(best_move) if best_move else "N/A"
                
                return {
                    'success': True,
                    'evaluation': evaluation,
                    'best_move': best_move_san,
                    'depth': depth
                }
                
        except Exception as e:
            logger.error(f"Erreur analyse: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_opening_name(self, pgn_moves: str) -> str:
        """Identifie l'ouverture jouée"""
        # Dictionnaire des ouvertures populaires
        openings = {
            "1.e4 e5 2.Nf3": "Ouverture du Roi",
            "1.d4 d5": "Jeu de la Dame",
            "1.e4 c5": "Défense Sicilienne",
            "1.e4 e6": "Défense Française",
            "1.e4 c6": "Défense Caro-Kann",
            "1.Nf3": "Ouverture Réti",
            "1.c4": "Ouverture Anglaise"
        }
        
        for opening_moves, name in openings.items():
            if pgn_moves.startswith(opening_moves):
                return name
        
        return "Ouverture non identifiée"

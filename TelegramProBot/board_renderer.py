import io
import chess
import chess.svg
import logging
from typing import Optional

# Lazy import for cairosvg to handle missing Cairo dependencies
try:
    import cairosvg
    CAIRO_AVAILABLE = True
except ImportError:
    CAIRO_AVAILABLE = False
    cairosvg = None

logger = logging.getLogger(__name__)

class BoardRenderer:
    """Générateur d'images d'échiquier avec étiquettes françaises"""
    
    def __init__(self, size: int = 400):
        self.size = size
    
    def render_board(self, fen: str, orientation: chess.Color = chess.WHITE, 
                    highlight_moves: Optional[list] = None) -> io.BytesIO:
        """
        Génère une image PNG de l'échiquier
        
        Args:
            fen: Position FEN
            orientation: Orientation de l'échiquier
            highlight_moves: Coups à surligner
            
        Returns:
            io.BytesIO: Buffer contenant l'image PNG
        """
        try:
            board = chess.Board(fen)
            
            # Générer le SVG
            svg_data = chess.svg.board(
                board=board,
                orientation=orientation,
                coordinates=True,
                size=self.size,
                lastmove=highlight_moves[-1] if highlight_moves else None
            )
            
            # Ajouter les étiquettes françaises
            svg_with_labels = self._add_french_labels(svg_data, board)
            
            # Convertir en PNG (si Cairo disponible)
            if CAIRO_AVAILABLE:
                png_data = cairosvg.svg2png(
                    bytestring=svg_with_labels.encode('utf-8'),
                    output_width=self.size,
                    output_height=self.size + 80  # Espace pour les étiquettes
                )
            else:
                # Fallback: retourner le SVG comme bytes
                png_data = svg_with_labels.encode('utf-8')
            
            if png_data:
                png_buffer = io.BytesIO(png_data)
                png_buffer.seek(0)
                return png_buffer
            else:
                raise ValueError("Erreur lors de la conversion SVG vers PNG")
                
        except Exception as e:
            logger.error(f"Erreur rendu échiquier: {e}")
            return self._create_error_image()
    
    def _add_french_labels(self, svg_data: str, board: chess.Board) -> str:
        """Ajoute des étiquettes françaises au SVG"""
        try:
            # Informations de la position
            turn = "Blancs" if board.turn == chess.WHITE else "Noirs"
            check_status = " (Échec !)" if board.is_check() else ""
            move_count = board.fullmove_number
            
            # Extraire les dimensions
            width = self.size
            new_height = self.size + 80
            
            # Modifier la hauteur du SVG
            svg_modified = svg_data.replace(
                f'height="{self.size}"',
                f'height="{new_height}"'
            )
            
            # Ajouter le bandeau d'informations
            info_band = f'''
            <rect x="0" y="0" width="{width}" height="80" fill="#2c3e50" stroke="#34495e" stroke-width="1"/>
            <text x="10" y="25" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#ecf0f1">
                Tour: {turn}{check_status} | Coup: {move_count}
            </text>
            <text x="10" y="45" font-family="Arial, sans-serif" font-size="12" fill="#bdc3c7">
                ♔ Roi  ♕ Dame  ♖ Tour  ♗ Fou  ♘ Cavalier  ♙ Pion
            </text>
            <text x="10" y="65" font-family="Arial, sans-serif" font-size="12" fill="#bdc3c7">
                Bot d'Échecs Professionnel - Powered by Stockfish
            </text>
            '''
            
            # Décaler le plateau vers le bas
            plateau_shift = 80
            svg_start = svg_modified.find('>') + 1
            svg_content = svg_modified[svg_start:]
            
            # Wrapper le contenu dans un groupe décalé
            shifted_content = f'<g transform="translate(0, {plateau_shift})">{svg_content}</g>'
            
            # Reconstruire le SVG
            svg_header = svg_modified[:svg_start]
            final_svg = svg_header + info_band + shifted_content
            
            # Fermer proprement
            if not final_svg.endswith('</svg>'):
                final_svg = final_svg.rstrip('</g></svg>') + '</g></svg>'
            
            return final_svg
            
        except Exception as e:
            logger.error(f"Erreur ajout étiquettes: {e}")
            return svg_data  # Retourner le SVG original en cas d'erreur
    
    def _create_error_image(self) -> io.BytesIO:
        """Crée une image d'erreur"""
        error_svg = f'''
        <svg width="{self.size}" height="{self.size}" xmlns="http://www.w3.org/2000/svg">
            <rect width="{self.size}" height="{self.size}" fill="#e74c3c"/>
            <text x="{self.size//2}" y="{self.size//2}" text-anchor="middle" 
                  font-family="Arial" font-size="20" fill="white">
                Erreur de rendu
            </text>
        </svg>
        '''
        
        try:
            png_data = cairosvg.svg2png(bytestring=error_svg.encode('utf-8'))
            if png_data:
                png_buffer = io.BytesIO(png_data)
                png_buffer.seek(0)
                return png_buffer
        except Exception:
            pass
        
        # Fallback: image vide
        return io.BytesIO(b"")
    
    def render_analysis(self, fen: str, best_move: str, evaluation: str) -> io.BytesIO:
        """Génère une image avec analyse de position"""
        try:
            board = chess.Board(fen)
            move = chess.Move.from_uci(best_move) if best_move != "N/A" else None
            
            # Créer le SVG avec surlignage du meilleur coup
            arrows = []
            if move:
                arrows = [chess.svg.Arrow(move.from_square, move.to_square, color="#0080ff")]
            
            svg_data = chess.svg.board(
                board=board,
                coordinates=True,
                size=self.size,
                arrows=arrows
            )
            
            # Ajouter les informations d'analyse
            svg_with_analysis = self._add_analysis_info(svg_data, evaluation, best_move)
            
            # Convertir en PNG
            png_data = cairosvg.svg2png(
                bytestring=svg_with_analysis.encode('utf-8'),
                output_width=self.size,
                output_height=self.size + 100
            )
            
            if png_data:
                png_buffer = io.BytesIO(png_data)
                png_buffer.seek(0)
                return png_buffer
            else:
                return self._create_error_image()
                
        except Exception as e:
            logger.error(f"Erreur rendu analyse: {e}")
            return self._create_error_image()
    
    def _add_analysis_info(self, svg_data: str, evaluation: str, best_move: str) -> str:
        """Ajoute les informations d'analyse au SVG"""
        try:
            width = self.size
            new_height = self.size + 100
            
            svg_modified = svg_data.replace(
                f'height="{self.size}"',
                f'height="{new_height}"'
            )
            
            # Bandeau d'analyse
            analysis_band = f'''
            <rect x="0" y="0" width="{width}" height="100" fill="#34495e" stroke="#2c3e50" stroke-width="2"/>
            <text x="10" y="25" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#e67e22">
                📊 ANALYSE STOCKFISH
            </text>
            <text x="10" y="50" font-family="Arial, sans-serif" font-size="14" fill="#ecf0f1">
                Évaluation: {evaluation}
            </text>
            <text x="10" y="75" font-family="Arial, sans-serif" font-size="14" fill="#ecf0f1">
                Meilleur coup: {best_move}
            </text>
            '''
            
            # Décaler le plateau
            plateau_shift = 100
            svg_start = svg_modified.find('>') + 1
            svg_content = svg_modified[svg_start:]
            
            shifted_content = f'<g transform="translate(0, {plateau_shift})">{svg_content}</g>'
            
            svg_header = svg_modified[:svg_start]
            final_svg = svg_header + analysis_band + shifted_content
            
            if not final_svg.endswith('</svg>'):
                final_svg = final_svg.rstrip('</g></svg>') + '</g></svg>'
            
            return final_svg
            
        except Exception as e:
            logger.error(f"Erreur ajout analyse: {e}")
            return svg_data

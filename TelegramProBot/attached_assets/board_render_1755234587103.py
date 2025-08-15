#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de rendu du plateau d'échecs
Génère une image PNG du plateau avec étiquettes françaises
"""

import io
import chess
import chess.svg
import cairosvg
from typing import Optional

def render_board_png(board: chess.Board, size: int = 400) -> io.BytesIO:
    """
    Génère une image PNG du plateau d'échecs avec étiquettes françaises
    
    Args:
        board: L'objet chess.Board à rendre
        size: Taille de l'image en pixels
        
    Returns:
        io.BytesIO: Buffer contenant l'image PNG
    """
    
    # Générer le SVG du plateau avec coordonnées
    svg_data = chess.svg.board(
        board=board,
        coordinates=True,
        size=size
    )
    
    # Ajouter les étiquettes des pièces en français
    svg_with_labels = add_french_piece_labels(svg_data)
    
    # Convertir SVG en PNG
    png_data = cairosvg.svg2png(
        bytestring=svg_with_labels.encode('utf-8'),
        output_width=size,
        output_height=size + 60  # Extra space pour les étiquettes
    )
    
    # Retourner le buffer PNG
    if png_data is not None:
        png_buffer = io.BytesIO(png_data)
        png_buffer.seek(0)
        return png_buffer
    else:
        # Fallback si erreur de conversion
        raise ValueError("Erreur lors de la conversion SVG vers PNG")

def add_french_piece_labels(svg_data: str) -> str:
    """
    Ajoute une bande avec les noms des pièces en français au-dessus du plateau
    
    Args:
        svg_data: Données SVG du plateau
        
    Returns:
        str: SVG modifié avec les étiquettes
    """
    
    # Étiquettes des pièces en français avec symboles Unicode
    piece_labels = {
        'white': [
            "♔ Roi / King",
            "♕ Dame / Queen", 
            "♖ Tour / Rook",
            "♗ Fou / Bishop",
            "♘ Cavalier / Knight",
            "♙ Pion / Pawn"
        ],
        'black': [
            "♚ Roi / King",
            "♛ Dame / Queen",
            "♜ Tour / Rook", 
            "♝ Fou / Bishop",
            "♞ Cavalier / Knight",
            "♟ Pion / Pawn"
        ]
    }
    
    # Extraire les dimensions du SVG
    if 'width="' in svg_data and 'height="' in svg_data:
        width_start = svg_data.find('width="') + 7
        width_end = svg_data.find('"', width_start)
        width = int(svg_data[width_start:width_end])
        
        height_start = svg_data.find('height="') + 8
        height_end = svg_data.find('"', height_start)
        height = int(svg_data[height_start:height_end])
    else:
        width = height = 400  # Valeur par défaut
    
    # Créer la nouvelle hauteur avec espace pour les étiquettes
    new_height = height + 60
    
    # Modifier le SVG pour ajuster la hauteur
    svg_modified = svg_data.replace(
        f'height="{height}"',
        f'height="{new_height}"'
    )
    
    # Ajouter le rectangle de fond pour les étiquettes
    label_bg = f'''
    <rect x="0" y="0" width="{width}" height="60" fill="#f0f0f0" stroke="#ccc" stroke-width="1"/>
    '''
    
    # Ajouter les étiquettes des pièces blanches
    white_labels = ""
    x_offset = 5
    y_white = 15
    for label in piece_labels['white']:
        white_labels += f'<text x="{x_offset}" y="{y_white}" font-family="Arial, sans-serif" font-size="11" fill="#333">{label}</text>'
        x_offset += width // 6
        if x_offset > width - 80:
            break
    
    # Ajouter les étiquettes des pièces noires
    black_labels = ""
    x_offset = 5
    y_black = 35
    for label in piece_labels['black']:
        black_labels += f'<text x="{x_offset}" y="{y_black}" font-family="Arial, sans-serif" font-size="11" fill="#333">{label}</text>'
        x_offset += width // 6
        if x_offset > width - 80:
            break
    
    # Ajouter les étiquettes et décaler le plateau vers le bas
    plateau_shift = 60
    
    # Trouver la position d'insertion (après la balise d'ouverture svg)
    svg_start = svg_modified.find('>') + 1
    
    # Décaler tout le contenu existant vers le bas
    svg_content = svg_modified[svg_start:]
    
    # Wrapper le contenu existant dans un groupe décalé
    shifted_content = f'<g transform="translate(0, {plateau_shift})">{svg_content}</g>'
    
    # Reconstruire le SVG avec les étiquettes en haut
    svg_header = svg_modified[:svg_start]
    final_svg = svg_header + label_bg + white_labels + black_labels + shifted_content
    
    # Fermer proprement le SVG
    if not final_svg.endswith('</svg>'):
        final_svg = final_svg.rstrip('</g></svg>') + '</g></svg>'
    
    return final_svg

def create_test_board() -> None:
    """Fonction de test pour vérifier le rendu"""
    # Créer un plateau avec quelques coups
    board = chess.Board()
    board.push_san("e4")
    board.push_san("e5")
    board.push_san("Nf3")
    board.push_san("Nc6")
    
    # Générer l'image
    try:
        png_buffer = render_board_png(board)
        
        # Sauvegarder pour test
        with open("test_board.png", "wb") as f:
            f.write(png_buffer.getvalue())
        
        print("Image de test générée: test_board.png")
    except Exception as e:
        print(f"Erreur lors du test: {e}")

if __name__ == "__main__":
    # Test du module
    create_test_board()

import os
import sys


def resource_path(relative_path):
    """ Récupère le chemin absolu des ressources, fonctionne pour le dev et pour PyInstaller """
    try:
        # PyInstaller crée un dossier temporaire _MEIxxxx
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


APP_VERSION = "1.0.0"
AUTHOR = "M4l0tru"
APP_NAME = "SC LOG ANALYSER"

# Configuration
FONT_PATH = resource_path("./Data/Fonts/Jura-VariableFont_wght.ttf")
DEFAULT_PATH_LOGS = r"D:\Games\StarCitizen\LIVE\logbackups"
ICO = resource_path("./Pictures/STARCITIZEN_WHITE.png")
CACHE = resource_path("./Cache/graphique_temps_jeu.png")

#Theme
COLOR_DEFAULT_THEME = {
        "bg_color" : "#12171c",  # Bleu très sombre / Noir
        "accent_color" :"#00f2ff",  # Cyan néon (HUD)
        "text_color" : "#e0e0e0",  # Gris clair / Blanc
        "grid_color" : "#2c3e50" # Bleu gris discret
}


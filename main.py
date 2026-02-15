import os
import sys

from PyQt6.QtGui import QFontDatabase, QFont
from PyQt6.QtWidgets import QApplication
from UI import MyWindow
from config import FONT_PATH

CONFIG_FILE = "config.txt"
DEFAULT_PATH = r"C:\Program Files\Roberts Space Industries\StarCitizen\LIVE\logs"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return f.read().strip()
    return DEFAULT_PATH

def save_config(path):
    with open(CONFIG_FILE, "w") as f:
        f.write(path)

def main():
    app = QApplication(sys.argv)

    dark_stylesheet = """
            /* Fond de la fenêtre principale */
            QWidget {
                background-color: #0B0E12;
                color: #B0B8C1;
                font-family: 'Jura'; /* Ta nouvelle police par défaut */
            }

            /* Style des boutons */
            QPushButton {
                background-color: transparent;
                border: 1px solid #00EDFF;
                color: #00EDFF;
                padding: 8px 15px;
                border-radius: 2px;
                text-transform: uppercase;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: rgba(0, 237, 255, 0.1);
                border: 2px solid #00EDFF;
            }

            QPushButton:pressed {
                background-color: #00EDFF;
                color: #0B0E12;
            }

            QPushButton:disabled {
                border-color: #2C3E50;
                color: #2C3E50;
            }

            /* Style des textes d'information */
            QLabel {
                background: transparent;
            }

            #titleLabel {
                color: #00EDFF;
                font-size: 18px;
                letter-spacing: 2px;
            }

            #resultLabel {
                font-size: 24px; 
                font-weight: bold;
                letter-spacing: 3px; 
                line-height: 1.5; /* Espace entre les lignes */
                qproperty-alignment: 'AlignCenter'; /* Centrage via CSS */
            }

            QProgressBar {
                border: 1px solid #00EDFF;
                border-radius: 2px;
                background-color: rgba(0, 237, 255, 0.05);
                height: 10px;
            }

            QProgressBar::chunk {
                background-color: #00EDFF;
                width: 20px; /* Largeur du bloc qui bouge */
            }
        """
    app.setStyleSheet(dark_stylesheet)

    font_id = QFontDatabase.addApplicationFont(FONT_PATH)

    sc_ui_font = QFont("Jura", 10)

    if font_id == -1:
        print("Erreur : La police n'a pas pu être chargée.")
    else:
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        global_font = QFont(font_family, 10)  # Nom de la police et taille par défaut
        app.setFont(global_font)

    window = MyWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
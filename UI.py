import ctypes
import os.path
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QStackedWidget, \
    QFrame, QProgressBar, QMainWindow, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt
from AnalysisWorker import AnalysisWorker
from config import DEFAULT_PATH_LOGS, APP_VERSION, AUTHOR, APP_NAME, ICO, COLOR_DEFAULT_THEME as COLOR_THEME, CACHE


class MyWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # --- ASTUCE WINDOWS ---
        # Par défaut, Windows regroupe les scripts Python sous l'icône Python.
        # Cette ligne force Windows à considérer ton app comme un programme distinct.
        myappid = 'oaktechnicalites.scloganaizer.1.0.0'  # Une chaîne unique
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        # --- APPLIQUER L'ICÔNE ---
        self.setWindowIcon(QIcon(ICO))

        # 1. Propriétés de la fenêtre
        self.path_logs = DEFAULT_PATH_LOGS
        self.graphContainer = QLabel()
        self.setWindowTitle("My SC stats")
        self.resize(1080, 720)

        self.setup_menu()

        # --- 3. LE CONTENEUR CENTRAL ---
        # Dans une QMainWindow, on doit définir un central_widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Ton layout principal devient le layout du central_widget
        self.main_layout = QVBoxLayout(self.central_widget)

        # --- 4. TON CODE EXISTANT (Stack, Pages, Footer) ---
        self.setup_ui_content()

    def setup_menu(self):
        # La QMainWindow possède déjà une barre de menu vide accessible via .menuBar()
        menu_bar = self.menuBar()

        options_menu = menu_bar.addMenu("OPTIONS")
        action_path = options_menu.addAction("Set Log Path")
        action_path.triggered.connect(self.change_log_path)

        action_about = menu_bar.addAction("ABOUT")
        action_about.triggered.connect(self.show_about)

        help_menu = menu_bar.addMenu("?")
        action_about = help_menu.addAction("Help")
        action_about.triggered.connect(self.show_help)

    def setup_ui_content(self):
        # --- 1. LE CONTENEUR EMPILLÉ (STACK) ---
        # Utilise self. pour que les autres fonctions y aient accès !
        self.stack = QStackedWidget()

        # PAGE 1 : WELCOME
        self.page_welcome = QWidget()
        welcome_layout = QVBoxLayout(self.page_welcome)
        welcome_layout.addStretch()

        self.welcome_title = QLabel("Welcome on My SC Stats".upper())
        self.welcome_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_title.setFont(QFont("Jura", 18, QFont.Weight.Bold))

        self.welcome_text = QLabel("Extract your playing time")
        self.welcome_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # On utilise self. car on va en avoir besoin dans on_button_time_click
        self.button = QPushButton("Extract".upper())
        self.button.clicked.connect(self.on_button_time_click)
        self.button.setEnabled(os.path.exists(self.path_logs))

        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 0)
        self.progressBar.setVisible(False)
        self.progressBar.setTextVisible(False)

        welcome_layout.addWidget(self.welcome_title)
        welcome_layout.addWidget(self.welcome_text)
        welcome_layout.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(self.progressBar)
        welcome_layout.addStretch()

        # PAGE 2 : RESULTATS
        self.page_result = QWidget()

        main_v_layout = QVBoxLayout(self.page_result)
        result_layout = QHBoxLayout(self.page_result)

        self.result_info = QLabel("PLACEHOLDER")
        self.result_info.setObjectName("resultLabel")

        self.graph_label = QLabel("Shema (Graphique)")
        self.graph_label.setStyleSheet("border: 2px solid #00f2ff;")
        self.graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_back = QPushButton("BACK")
        self.btn_back.setFixedWidth(250)  # Pour qu'il ne prenne pas toute la largeur

        # Connexion : on demande au stack de revenir à l'index 0 (l'accueil)
        self.btn_back.clicked.connect(self.go_back_home)

        result_layout.addWidget(self.result_info, stretch=1)
        result_layout.addWidget(self.graph_label, stretch=2)

        main_v_layout.addWidget(self.btn_back, alignment=Qt.AlignmentFlag.AlignLeft)
        main_v_layout.addLayout(result_layout)

        # Ajout des pages au stack
        self.stack.addWidget(self.page_welcome)
        self.stack.addWidget(self.page_result)

        # --- 2. LE FOOTER ---
        footer_widget = QFrame()
        footer_layout = QHBoxLayout(footer_widget)

        footer_text = QLabel("This project is not endorsed by or affiliated with the Cloud Imperium or Roberts Space Industries group of companies. "
                             "All game content and materials are copyright Cloud Imperium Rights LLC and Cloud Imperium Rights Ltd.. "
                             "Star Citizen®, Squadron 42®, Roberts Space Industries®, and Cloud Imperium® are registered trademarks of Cloud Imperium Rights LLC. All rights reserved.")

        footer_text.setWordWrap(True)
        footer_text.setStyleSheet("font-size: 12px; color: gray;")

        self.footer_img = QLabel()
        self.footer_img.setScaledContents(True)
        self.footer_img.setPixmap(QPixmap("Pictures/MadeByTheCommunity_White.png"))
        self.footer_img.setFixedSize(100, 100)

        footer_layout.addWidget(footer_text, stretch=5)
        footer_layout.addWidget(self.footer_img, stretch=1)

        # --- 4. ASSEMBLAGE DANS LE LAYOUT CENTRAL ---
        # Ici on utilise self.main_layout (créé dans le __init__)
        self.main_layout.addWidget(self.stack)
        self.main_layout.addWidget(footer_widget)

    #FONCTIONS
    def on_button_time_click(self):

        print("Analyse du temps de jeu...")
        self.progressBar.setVisible(True)
        self.button.setText("PROCESSING...")
        self.button.setEnabled(False)
        self.button.setStyleSheet("background-color: orange; color: black;")
        QApplication.processEvents()

        # On crée le thread en lui passant le chemin des logs
        self.thread = AnalysisWorker(self.path_logs)
        # On lui dit : "Quand tu as fini, appelle la fonction on_analysis_finished"
        self.thread.finished.connect(self.on_analysis_finished)
        # On démarre !
        self.thread.start()

    def addGraphToLayout(self, image_path):
        pixmap = QPixmap(image_path)

        if not pixmap.isNull():
            # Optionnel : Redimensionner l'image si elle est trop grande (ex: 300px de large)
            pixmap = pixmap.scaledToWidth(800, Qt.TransformationMode.SmoothTransformation)
            pixmap = pixmap.scaledToHeight(500, Qt.TransformationMode.SmoothTransformation)
            self.graph_label.setPixmap(pixmap)

            # Ajuster la taille de la fenêtre pour accommoder le graphique
            self.adjustSize()
        else:
            print("Erreur : Impossible de charger l'image du graphique.")
        return

    def on_analysis_finished(self, df_play):

        global total_h
        # 2. On traite les résultats reçus du thread (df_play)
        if df_play is not None and not df_play.empty:

            # 1. On nettoie l'interface
            self.progressBar.setVisible(False)

            # Calcul du total
            total_h = df_play['Minutes'].sum() // 60

            # Mise à jour du texte
            self.result_info.setText(f"You played \n{int(total_h)} hours \nsince the first Log")
            self.result_info.setObjectName("resultLabel")

            self.addGraphToLayout(CACHE)
            # Changement de page
            self.stack.setCurrentIndex(1)
        else:
            print("Erreur : Aucune donnée trouvée.")
            self.button.setText("RETRY")

    def change_log_path(self):
            new_path = QFileDialog.getExistingDirectory(self, "Select Star Citizen Logs Folder")
            if new_path:
                self.path_logs = new_path
                print(f"Path updated to: {self.path_logs}")
                self.button.setEnabled(os.path.exists(self.path_logs))

    def show_help(self):
        help_box = QMessageBox(self)
        help_box.setWindowTitle("MANUAL - SC LOG ANALYSER")

        # Texte avec un peu de mise en forme HTML
        help_text = (
            "<h2 style='color: #00f2ff;'>HELP CENTER</h2>"
            "<p>This tool synchronizes with your Star Citizen flight logs to calculate your time spent in the Verse.</p>"
            "<hr>"
            "<b>HOW TO USE:</b>"
            "<ul>"
            "<li><b>Initialize:</b> In Options select your StarCitizen Logbackup folder.</li>"
            "<li><b>Extract:</b> Press Extract : it will scan the log folder.</li>"
            "<li><b>Analysis:</b> Detects 'Session Started' and 'Quit' markers.</li>"
            "<li><b>Graph:</b> Displays your activity grouped by month.</li>"
            "</ul>"
            "<br><i>Note: The app reads .log files, it does not modify your game data.</i>"
        )

        help_box.setText(help_text)

        # On applique le style pour que la fenêtre d'aide soit aussi en Dark Mode
        help_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {COLOR_THEME['bg_color']};
            }}
            QLabel {{
                color: {COLOR_THEME['text_color']};
                font-family: 'Jura';
            }}
            QPushButton {{
                background-color: {COLOR_THEME['accent_color']};
                color: {COLOR_THEME['bg_color']};
                font-weight: bold;
                border-radius: 3px;
                padding: 5px 15px;
            }}
        """)
        help_box.exec()

    def show_about(self):

        about_box = QMessageBox(self)
        about_box.setWindowTitle(f"About {APP_NAME}")

        # Design style "Plaque d'immatriculation de vaisseau"
        about_text = (
            f"<div style='text-align: center;'>"
            f"<h2 style='color: #00f2ff; margin-bottom: 0;'>{APP_NAME}</h2>"
            f"<p style='color: #e0e0e0; margin-top: 0;'>Version {APP_VERSION}</p>"
            f"<hr style='border: 0; border-top: 1px dashed #2c3e50;'>"
            f"<p>System developed for the community by</p>"
            f"<h3 style='color: #ffffff;'>[ {AUTHOR} ]</h3>"
            f"<p style='font-size: 9px; color: #555;'>Data processed from Game.log files</p>"
            f"</div>"
        )

        about_box.setText(about_text)
        about_box.setStyleSheet(f"""
            QMessageBox {{ background-color: {COLOR_THEME['bg_color']}; }}
            QLabel {{ color: {COLOR_THEME['text_color']}; font-family: 'Jura'; }}
            QPushButton {{ 
                background-color: {COLOR_THEME['accent_color']}; 
                color: {COLOR_THEME['bg_color']}; 
                font-weight: bold; 
                border: none; padding: 5px 20px; 
            }}
        """)
        about_box.exec()

    def go_back_home(self):
        # On change de page
        self.stack.setCurrentIndex(0)
        self.button.setEnabled(True)
        self.button.setText("Extract")
import os
import re
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib import font_manager
from pandas import DataFrame
from config import FONT_PATH, CACHE , COLOR_DEFAULT_THEME as COLOR_THEME
import matplotlib as mpl
import shutil

if os.path.exists(mpl.get_cachedir()):
    shutil.rmtree(mpl.get_cachedir())

class SCLogAnalyst:
    def __init__(self, log_path):
        plt.rcParams['font.family'] = 'Jura'
        self.log_path = log_path
        self._init_regex()

    def _init_regex(self):
        """Initialisation interne des patterns Regex"""
        self.re_crime_part1 = re.compile(r'<(?P<ts>[^>]+)>.*?Crime Committed: (?P<crime>[^\n\r]+)')
        self.re_crime_part2 = re.compile(r'against (?P<victim>[^:]+): " \[(?P<id>\d+)\]')
        self.re_crime_direct = re.compile(
            r'<(?P<ts>[^>]+)>.*?Added notification "(?P<killer>[^"]+) committed (?P<crime>[^"]+) against you"')
        self.re_death = re.compile(
            r'<(?P<ts>[^>]+)>.*?<Actor Death> CActor::Kill: \'(?P<v>[^\']+)\' .*? killed by \'(?P<k>[^\']+)\' .*? type \'(?P<d>[^\']+)\'')
        self.re_ts = re.compile(r'^<(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})')
        self.re_cleanup_npc = re.compile(r'^(PU_|NPC_|vlk_|Kopion_)(.*)(_\d+)$')

    def clean_name(self, name):
        """Nettoie les IDs des entités"""
        name = name.strip()
        match = self.re_cleanup_npc.match(name)
        return f"{match.group(1)}{match.group(2)}" if match else name

    def run_exports(self):
        """Exécute l'extraction des crimes et des morts vers CSV"""
        if not os.path.exists(self.log_path): return False

        deaths, crimes = [], []
        files = [f for f in os.listdir(self.log_path) if f.endswith(".log")]

        for file in files:
            with open(os.path.join(self.log_path, file), "r", encoding="latin-1", errors="ignore") as f:
                prev_line = ""
                for line in f:
                    # Logique Crimes
                    if "against" in line and "Crime Committed" in prev_line:
                        m1, m2 = self.re_crime_part1.search(prev_line), self.re_crime_part2.search(line)
                        if m1 and m2:
                            crimes.append(
                                [m1.group('ts')[:10], m1.group('crime').strip(), self.clean_name(m2.group('victim')),
                                 m2.group('id'), 'Standard'])
                    elif "against you" in line:
                        m = self.re_crime_direct.search(line)
                        if m:
                            crimes.append([m.group('ts')[:10], m.group('crime'), 'YOU', 'N/A', 'Direct Alert'])
                    # Logique Morts
                    elif "<Actor Death>" in line:
                        m = self.re_death.search(line)
                        if m:
                            deaths.append(
                                [m.group('ts')[:10], self.clean_name(m.group('v')), self.clean_name(m.group('k')),
                                 m.group('d')])
                    prev_line = line

        # Sauvegarde physique
        pd.DataFrame(deaths, columns=['Date', 'Victime', 'Tueur', 'Type Degats']).to_csv('deaths_export.csv',
                                                                                         index=False)
        pd.DataFrame(crimes, columns=['Date', 'Crime', 'Cible', 'ID', 'Type_Alerte']).to_csv('crimes_export.csv',
                                                                                             index=False)
        return True

    def get_playtime_df(self) -> DataFrame:
        """Calcule et retourne le DataFrame du temps de jeu"""
        stats = []

        # Liste les fichiers avant la boucle pour éviter les modifications en cours de route
        log_files = [f for f in os.listdir(self.log_path) if f.endswith(".log")]

        for file in log_files:
            first_ts, last_ts = None, None
            file_path = os.path.join(self.log_path, file)

            try:
                with open(file_path, "r", encoding="latin-1", errors="ignore") as f:
                    for line in f:
                        match = self.re_ts.search(line)
                        if match:
                            ts = datetime.strptime(match.group('ts'), '%Y-%m-%dT%H:%M:%S')
                            if first_ts is None: first_ts = ts
                            last_ts = ts

                if first_ts and last_ts:
                    duration = (last_ts - first_ts).total_seconds() / 60
                    stats.append({'Date': first_ts.strftime('%Y-%m-%d'), 'Minutes': duration})
            except Exception as e:
                print(f"Erreur sur le fichier {file}: {e}")
        return pd.DataFrame(stats)

    def generate_graph(self, df_playtime):

        # On définit les couleurs "Star Citizen style"
        bg_color = COLOR_THEME["bg_color"]  # Bleu très sombre / Noir
        accent_color = COLOR_THEME["accent_color"]  # Cyan néon (HUD)
        text_color = COLOR_THEME["text_color"] # Gris clair / Blanc
        grid_color = COLOR_THEME["grid_color"]  # Bleu gris discret

        prop = font_manager.FontProperties(fname=FONT_PATH)

        """Génère et sauvegarde le graphique"""
        df_playtime['Date'] = pd.to_datetime(df_playtime['Date'])
        df_playtime.set_index('Date', inplace=True)
        df_monthly = df_playtime['Minutes'].resample('ME').sum()

        fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg_color)
        ax.set_facecolor(bg_color)

        bars = ax.bar(df_monthly.index.strftime('%b %Y'),
                      df_monthly.values / 60,
                      color=accent_color,
                      alpha=0.7,
                      edgecolor=accent_color,
                      linewidth=1)


        # --- FORCER LA POLICE SUR LES AXES ---
        # C'est ici que le "fontname" échoue souvent, on utilise set_fontproperties
        for label in ax.get_xticklabels():
            label.set_fontproperties(prop)
            label.set_color(text_color)
            label.set_rotation(45)

        for label in ax.get_yticklabels():
            label.set_fontproperties(prop)
            label.set_color(text_color)

        # --- TITRES ET LABELS ---
        # Note : on utilise ax.set_... au lieu de plt.... pour être cohérent avec subplots
        ax.set_title("STAR CITIZEN - MONTHLY PLAYTIME", fontproperties=prop,
                         fontsize=25, color=accent_color, pad=20)

        ax.set_xlabel("PERIOD", fontproperties=prop, fontsize=14, color=text_color)
        ax.set_ylabel("HOURS IN VERSE", fontproperties=prop, fontsize=14, color=text_color)

        # Nettoyage des bordures
        ax.spines['bottom'].set_color(text_color)
        ax.spines['left'].set_color(text_color)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Grille
        ax.yaxis.grid(True, linestyle='--', alpha=0.2, color="#2c3e50")

        plt.tight_layout()
        plt.savefig(CACHE, facecolor=bg_color, dpi=120)
        plt.close()
        print("Graphique sauvegardé.")

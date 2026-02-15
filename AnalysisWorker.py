from PyQt6.QtCore import QThread, pyqtSignal
from SCLogAnalysEngine import SCLogAnalyst


class AnalysisWorker(QThread):
    finished = pyqtSignal(object)

    def __init__(self, path_to_logs):
        super().__init__()
        self.path_to_logs = path_to_logs  # On mémorise le chemin reçu

    def run(self):
        # Le calcul lourd se fait ici, sans bloquer l'UI
        analyst = SCLogAnalyst(self.path_to_logs)
        df = analyst.get_playtime_df()
        analyst.generate_graph(df)
        self.finished.emit(df)
import sys
import logging
from qtpy.QtWidgets import (
    QMainWindow,
    QApplication,
)
from qtpy.QtCore import Qt, QDir
from pyqt_code_editor.widgets import TabSplitter, ProjectExplorer
from pyqt_code_editor.worker import manager

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("MainWindow initialized")
        self.setWindowTitle("PyQt Code Editor")

        # Import TabSplitter from your existing code (already in the workspace).
        self._tab_splitter = TabSplitter()
        self.setCentralWidget(self._tab_splitter)

        # Create the project explorer dock
        self._project_explorer = ProjectExplorer(self._tab_splitter, root_path=QDir.currentPath())
        self.addDockWidget(Qt.LeftDockWidgetArea, self._project_explorer)

        
    def closeEvent(self, event):
        manager.stop_all_workers()
        super().closeEvent(event)        


def main():
    logging.basicConfig(level=logging.INFO, force=True)
    logger.info("Starting application")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1200, 800)
    window.show()
    logger.info("Entering main event loop")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyqt_code_editor import watchdog
from qtpy.QtWidgets import QApplication, QVBoxLayout, QWidget
from pyqt_code_editor.components.jupyter_console import JupyterConsole
from pyqt_code_editor.components.workspace_explorer import WorkspaceExplorer


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQtCodeEditor")
        layout = QVBoxLayout()        
        workspace_explorer = WorkspaceExplorer()
        layout.addWidget(workspace_explorer)
        jupyter_console = JupyterConsole()
        jupyter_console.workspace_updated.connect(workspace_explorer.update)
        layout.addWidget(jupyter_console)
        self.setLayout(layout)

    def closeEvent(self, event):
        watchdog.shutdown()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

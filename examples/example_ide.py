import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyqt_code_editor.app import launch_app

if __name__ == "__main__":
    launch_app()

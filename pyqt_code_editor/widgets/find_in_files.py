import os
import multiprocessing
from qtpy.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, \
    QLabel, QLineEdit, QCheckBox, QPushButton, QTreeWidget, QTreeWidgetItem, \
    QAbstractItemView, QShortcut
from qtpy.QtCore import Qt, QTimer, Signal
from qtpy.QtGui import QKeySequence

def search_in_files_worker(files, search_text, case_sensitive, whole_word, regex, output_queue):
    """
    Runs in a separate process; scans 'files' for 'search_text' and
    posts partial results to 'output_queue'.
    """
    import re

    flags = 0
    pattern_text = search_text
    if not case_sensitive:
        flags = re.IGNORECASE
    if whole_word:
        # a naive approach with word boundaries
        pattern_text = r"\b" + pattern_text + r"\b"
    
    try:
        compiled_pattern = re.compile(pattern_text, flags=flags) if regex else re.compile(re.escape(pattern_text), flags=flags)
        
        for file_path in files:
            matches_for_file = []
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f):
                        if compiled_pattern.search(line):
                            matches_for_file.append((i+1, line.rstrip("\n")))
            except Exception:
                # Just skip unreadable files or handle differently
                continue
            
            if matches_for_file:
                # Post partial result
                output_queue.put(("found", file_path, matches_for_file))
    except Exception as e:
        # If something goes drastically wrong, we can post an error
        output_queue.put(("error", str(e)))
    
    # Signal we are done
    output_queue.put(("done", None))

class FindInFiles(QDockWidget):
    
    open_file_requested = Signal(str, int)
    
    def __init__(self, files_list, parent=None, needle=None):
        super().__init__("Find in Files", parent)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        self._files = files_list[:]  # store a copy
        self._search_process = None
        self._output_queue = None
        
        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setWidget(central)
        
        # Search Controls
        controls_layout = QHBoxLayout()
        layout.addLayout(controls_layout)
        
        self.searchInput = QLineEdit(self)
        self.searchInput.setPlaceholderText("Search …")
        if needle is not None:
            self.searchInput.setText(needle)
        self.searchInput.returnPressed.connect(self._start_search)
        self.caseBox = QCheckBox("Case", self)
        self.wholeWordBox = QCheckBox("Word", self)
        self.regexBox = QCheckBox("Regex", self)
        self.searchBtn = QPushButton("Search", self)
        
        controls_layout.addWidget(self.searchInput)
        controls_layout.addWidget(self.caseBox)
        controls_layout.addWidget(self.wholeWordBox)
        controls_layout.addWidget(self.regexBox)
        controls_layout.addWidget(self.searchBtn)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tree Widget for results
        self.resultsTree = QTreeWidget(self)
        self.resultsTree.setHeaderLabels(["File / Line", "Preview"])
        self.resultsTree.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.resultsTree)
        
        self.searchBtn.clicked.connect(self._start_search)
        self.resultsTree.itemClicked.connect(self._on_item_clicked)        
        
        # Timer to poll queue
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_worker)
        
        self._timer.setInterval(300)  # every 300 ms
        self._timer.start()
        
    def showEvent(self, event):
        """Override showEvent to set focus when widget is shown"""
        super().showEvent(event)
        self.searchInput.setFocus()        
    
    def _start_search(self):
        # Kill any existing worker first
        if self._search_process and self._search_process.is_alive():
            self._search_process.terminate()
        
        # Clear old results
        self.resultsTree.clear()
        
        # Prepare
        self._output_queue = multiprocessing.Queue()
        args = (
            self._files,
            self.searchInput.text(),
            self.caseBox.isChecked(),
            self.wholeWordBox.isChecked(),
            self.regexBox.isChecked(),
            self._output_queue
        )
        
        # Start process
        self._search_process = multiprocessing.Process(target=search_in_files_worker, args=args)
        self._search_process.start()
    
    def _poll_worker(self):
        if self._search_process is not None:
            # Check if the process crashed
            if not self._search_process.is_alive() and self._output_queue.empty():
                # Worker done or crashed with nothing reported
                self._search_process = None
                return
            
            # Grab everything from the queue
            while not self._output_queue.empty():
                msg = self._output_queue.get()
                if not msg:
                    continue
                kind = msg[0]
                
                if kind == "found":
                    # we have file + list of (line_num, text)
                    file_path = msg[1]
                    lines = msg[2]
                    self._add_file_matches(file_path, lines)
                elif kind == "error":
                    # The worker had an internal error
                    error_msg = msg[1]
                    # You can log or show a message box
                elif kind == "done":
                    # done means the worker finished scanning
                    self._search_process = None
    
    def _add_file_matches(self, file_path, lines):
        # Create a top-level item for file
        topItem = QTreeWidgetItem(self.resultsTree)
        topItem.setText(0, os.path.basename(file_path))
        topItem.setText(1, file_path)  # store path in second column
        topItem.setData(0, Qt.UserRole, ("file", file_path))
        
        for (line_no, preview) in lines:
            child = QTreeWidgetItem(topItem)
            child.setText(0, str(line_no))
            child.setText(1, preview)
            child.setData(0, Qt.UserRole, ("line", file_path, line_no))
        
        topItem.setExpanded(True)
    
    def _on_item_clicked(self, item, column):
        user_data = item.data(0, Qt.UserRole)
        if not user_data:
            return
        kind = user_data[0]
        
        if kind == "file":
            path = user_data[1]
            self._open_file(path, line_no=0)
        elif kind == "line":
            path = user_data[1]
            line_no = user_data[2]
            self._open_file(path, line_no)
    
    def _open_file(self, path, line_no=0):
        """
        Dummy method: In production, integrate with your editor logic.
        """
        print(f"Opening file: {path}, line {line_no}")
        self.open_file_requested.emit(path, line_no)
    
    def closeEvent(self, event):
        # Terminate worker process, if any
        if self._search_process and self._search_process.is_alive():
            self._search_process.terminate()
        self._search_process = None
        super().closeEvent(event)
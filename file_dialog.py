import sys
from PyQt5 import QtWidgets
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QFileDialog, QApplication


class FileDialog(QtWidgets.QWidget):

    def __init__(self):
        super(FileDialog, self).__init__()
        loadUi('init_log_analysis.ui', self)

        self.pushButton.clicked.connect(self.get_file)
        self.pushButton_3.clicked.connect(self.close)
        self.file_name = None

    def get_file(self):
        file_name = QFileDialog.getOpenFileName(self, 'Open file', ' ', "log files (*.log)")
        win_format_path = file_name[0].replace('/', '\\')
        self.textEdit.setPlainText(win_format_path)
        self.file_name = win_format_path

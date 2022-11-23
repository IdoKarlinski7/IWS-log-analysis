import tree_gui_threaded as tg
from PyQt5.QtWidgets import QApplication
import sys


if __name__ == '__main__':
    app = QApplication(tg.sys.argv)
    window = tg.LogWidgetWindow()
    window.show()
    app.exec_()
    sys.exit()

import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QBrush, QColor
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QTreeWidgetItem, QFileDialog
import tree_im, file_dialog as dialog, log_parser_threaded as threaded


class LogWidgetWindow(QMainWindow):

    parse_log = QtCore.pyqtSignal(str)

    def __init__(self):
        super(LogWidgetWindow, self).__init__()
        loadUi('log.ui', self)
        self.resize(self.sizeHint())
        self.link_menu_bar_functions()
        self.set_tree_widget()
        self.set_search_widget()
        self.init_threading()
        self.curr = None

    def init_threading(self):
        self.parser = threaded.Parser()
        self.parsing_thread = QtCore.QThread()
        self.parser.moveToThread(self.parsing_thread)
        self.parsing_thread.start()
        self.parser.parsed.connect(self.log_file_input)
        self.parse_log.connect(self.parser.file_to_parse)

    def init_dialog(self):
        self.textEdit.clear()
        self.dialog_win.pushButton_2.clicked.connect(self.on_dialog_click)
        self.dialog_win.show()

    def set_tree_widget(self):
        self.treeWidget.setStyleSheet(STYLESHEET)
        self.treeWidget.itemClicked.connect(self.set_curr)
        self.treeWidget.itemDoubleClicked.connect(self.on_tree_double_click)

    def set_search_widget(self):
        self.searchWidget.setPlaceholderText('Type function name, time threshold or index')
        if self.treeWidget:
            self.searchWidget.textEdited.connect(self.search)
        self.listWidget.itemDoubleClicked.connect(self.on_list_click)

    def link_menu_bar_functions(self):
        self.actionOpen.triggered.connect(self.on_dialog_click)
        self.actionClear.triggered.connect(self.clear_all)
        self.actionExpand_All.triggered.connect(self.treeWidget.expandAll)
        self.actionCollapse_All.triggered.connect(self.treeWidget.collapseAll)

    def log_file_input(self, function_list):
        if not function_list:
            self.textEdit.setText('Log file is corrupted, please select different file')
        self.treeWidget.clear()
        self.function_list = function_list
        if self.function_list:
            self.gen_tree()
            self.pushButton.clicked.connect(self.next)
        else:
            self.textEdit.setText('Log file is corrupted, please select different file')
        self.textEdit.clear()

    """ interactive methods """
    def on_dialog_click(self):
        self.textEdit.setPlainText("Loading Log File GUI...")
        file_name = QFileDialog.getOpenFileName(self, 'Open file', ' ', "log files (*.log)")
        if file_name:
            win_format_path = file_name[0].replace('/', '\\')
            self.parse_log.emit(win_format_path)
        else:
            self.textEdit.setPlainText("Please Select Log File")

    def on_list_click(self):
        self.textEdit.clear()
        self.treeWidget.collapseItem(self.treeWidget.currentItem())
        current = self.listWidget.currentItem()
        searchable_text = current.text().split('.')[0]
        node = self.treeWidget.findItems(searchable_text, QtCore.Qt.MatchStartsWith | QtCore.Qt.MatchRecursive, 0)
        self.treeWidget.scrollToItem(node[0])
        self.treeWidget.expandItem(node[0])
        self.textEdit.setText(self.get_path(node[0]))

    def on_tree_double_click(self):
        self.textEdit.clear()
        current = self.treeWidget.currentItem()
        self.textEdit.setText(self.get_path(current) + '\n' + current.toolTip(1))

    def next(self):
        if self.curr:
            curr_index = int(self.curr.text(0).split('.')[0]) - 1
            if curr_index == len(self.function_list) - 1:
                self.textEdit.setText('last call at log file')
            else:
                next_index = curr_index + 1
                next_str = str(next_index + 1) + '. '
                self.textEdit.setText(next_str)
                curr_func = self.function_list[curr_index]
                self.textEdit.clear()
                if curr_func.call_list:
                    self.textEdit.setText(curr_func.name + ' calls ' + self.function_list[next_index].name)
                else:
                    self.textEdit.setText(curr_func.name + ' is a leaf function, next call is ' + self.function_list[next_index].name)
                self.curr = self.treeWidget.findItems(next_str, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive, 0)[0]
            self.treeWidget.scrollToItem(self.curr)
            self.treeWidget.expandItem(self.curr)
        else:
            self.textEdit.setText('please click on a function call')

    def search(self, text):
        self.listWidget.clear()
        if text.isdigit():
            self.search_by_threshold(text)
        elif text.endswith('.'):
            self.search_by_index(text)
        else:
            self.search_by_name(text)

    """ initialization methods """
    def gen_tree(self):
        self.treeWidget.setHeaderLabels(['Index', 'Name', 'Time stamp', 'Duration'])
        self.treeWidget.setColumnWidth(0, 250)
        self.treeWidget.setColumnWidth(1, 350)
        self.gen_roots(threaded.called_by_main(self.function_list))

    def gen_roots(self, called_by_main):
        roots = []
        for func in called_by_main:
            func_root = QTreeWidgetItem([str(func.index) + '. ', func.name, func.in_time, str(func.duration)])
            func_root.setToolTip(1, func.get_output())
            validate_ret(func, func_root)
            roots.append(func_root)
            self.attach(func_root, func)
        self.treeWidget.addTopLevelItems(roots)

    def attach(self, root, function):
        for func in function.get_callees():
            self.attach_call(func, root)

    def attach_call(self, child, root):
        child_branch = QTreeWidgetItem(root, [str(child.index) + '. ', child.name, child.in_time, str(child.duration)])
        validate_ret(child, child_branch)
        child_branch.setToolTip(1, child.get_output())
        self.attach(child_branch, child)

    def set_curr(self):
        self.curr = self.treeWidget.currentItem()

    def clear_all(self):
        self.treeWidget.clear()
        self.listWidget.clear()
        self.searchWidget.clear()
        self.textEdit.clear()

    """  auxiliary for tree widget double click on item """
    @staticmethod
    def get_path(node):
        def rec_get_path(func, path_string):
            if func.parent() is None:
                return path_string
            if func.parent().text(1) != func.text(1):
                path_string = func.parent().text(1) + "/" + path_string
            return rec_get_path(func.parent(), path_string)
        path = rec_get_path(node, node.text(1)) + ': ' + '\n'
        return path

    """ auxiliary for search """
    def search_by_threshold(self, text):
        self.listWidget.clear()
        over_threshold = []
        for func in self.function_list:
            if func.duration >= int(text):
                over_threshold.append(func)
        for func in over_threshold:
            self.listWidget.addItem(str(func.index) + '.' + func.name + ' dur - ' + str(func.duration))

    def search_by_name(self, text):
        self.listWidget.clear()
        list_of_items = self.treeWidget.findItems(text, QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive, 1)
        for item in list_of_items:
            self.listWidget.addItem(item.text(0) + ' ' + item.text(1) + ' duration is ' + str(item.text(3)))

    def search_by_index(self, text):
        self.listWidget.clear()
        list_of_index = self.treeWidget.findItems(text, QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive, 0)
        func = list_of_index[0]
        self.listWidget.addItem(func.text(0) + func.text(1) + ' duration is ' + str(func.text(3)))


def validate_ret(func, func_item):
    if func.out_time == -1:
        func_item.setForeground(1, QBrush(QColor(150, 0, 0)))


STYLESHEET = '''
QTreeView {
    background: base;
}

QTreeView::branch:has-siblings:!adjoins-item {
    border-image: url(:/vline.png) 0;
}

QTreeView::branch:has-siblings:adjoins-item {
    border-image: url(:/branch-more.png) 0;
}

QTreeView::branch:!has-children:!has-siblings:adjoins-item {
    border-image: url(:/branch-end.png) 0;
}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
        border-image: none;
        image: url(:/branch-closed.png);
}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings  {
        border-image: none;
        image: url(:/branch-open.png);
}
'''

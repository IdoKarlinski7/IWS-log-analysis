from tqdm import tqdm
import node
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class Parser(QObject):

    parsed = pyqtSignal(list)

    @pyqtSlot(str)
    def file_to_parse(self, log_file):
        data_from_file = file_to_data(log_file)
        if not data_from_file:
            self.parsed.emit([])
        else:
            function_call_list = get_node_list(data_from_file)
            function_list = link_call_lists(function_call_list)
            self.parsed.emit(function_list)


def file_to_data(FILE):
    try:
        with open(FILE, 'r') as file:
            file_lines = file.readlines()
        split_lines = []
        for line in file_lines:
            '''try:
                verification = line[0:8]
                for i in verification:
                    if not i.isdigit() and i != ':' and i !='':
                        raise UnicodeError
            except UnicodeError:
                return []'''
            if line[10:13] == 'In:' or line[10:14] == 'Out:':
                split_lines.append(line.split())
            else:
                split_lines.append(line.split(' ', 1))
    except FileNotFoundError:
        return None
    return split_lines


def update_node_list(nodes, line, index):
    output = check_params_format(line)
    line = line[:3]
    to_add = node.Node(line[2], line[0], index)
    to_add.add_output(output)
    nodes.append(to_add)
    line.append(to_add)
    index += 1
    return index


def get_node_list(data_list):
    node_list = []
    function_call_list = []
    index = 1
    for i in tqdm(range(len(data_list)), desc='get functions'):
        # get only function calls
        if len(data_list[i]) >= 3:
            if data_list[i][1] == "In:":
                out_counter = 1
                output = check_params_format(data_list[i])
                data_list[i] = data_list[i][:3]
                to_add = node.Node(data_list[i][2], data_list[i][0], index)
                to_add.add_output(output)
                node_list.append(to_add)
                data_list[i].append(to_add)
                index += 1
            else:
                out_counter += 1
            function_call_list.append(data_list[i])
        # put relevant function data in the matching node
        if len(data_list[i]) == 2 and len(node_list) > 0:
            relevant_func_index = len(node_list) - out_counter
            node_list[relevant_func_index].add_output(data_list[i][1])
    return function_call_list


def link_call_lists(calls_list):
    parent = None
    node_list = []
    for index in tqdm(range(len(calls_list)), desc='link calls'):
        in_main = False
        if calls_list[index][1] == "Out:":  # out of function
            if parent is not None:
                if parent.name != calls_list[index][2]:
                    print('function '+parent.name+' at '+parent.in_time +
                          ' call number '+str(parent.index)+' did not return.')
                    return None
                parent.add_out_time(calls_list[index][0])
                parent = parent.get_prev()

        # going in a function
        if calls_list[index][1] == "In:" and parent is None:  # called by main
            parent = calls_list[index][3]
            in_main = True
            node_list.append(calls_list[index][3])

        elif calls_list[index][1] == "In:" and not in_main:  # called by another function
            parent.add_callee(calls_list[index][3])
            parent = calls_list[index][3]
            node_list.append(calls_list[index][3])
    return node_list


""" not in use """
# get the names of functions called by specific function (name is unique)
def callee_names(function):
    names = []
    for callee in function.call_list:
        if callee.name not in names:
            names.append(callee.name)
    return sorted(names)


""" not in use """
# match calls to names, a given name might contain several calls
def sort_calls(function):
    callees = callee_names(function)
    calls = {name: [] for name in callees}
    for call in function.call_list:
        calls.get(call.name).append(call)
    return calls


# format of function with params in line
def check_params_format(line):
    output = ''
    if line[2].endswith(','):
        line[2] = line[2].strip(',')
        output = line[3] + line[4]
    return output


# list of the function with no parent function
def called_by_main(node_list):
    called_by_main_list = [func for func in node_list if func.called_by is None]
    return called_by_main_list


def log_to_function_list(log_file):
    data_from_file = file_to_data(log_file)
    function_call_list = get_node_list(data_from_file)
    function_list = link_call_lists(function_call_list)
    return function_list

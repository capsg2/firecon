from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QLineEdit, QCompleter
from PyQt6.uic import loadUi
import sqlite3
import pandas as pd
from PyQt6.QtCore import Qt, QAbstractTableModel, QStringListModel, QSortFilterProxyModel, pyqtSignal
from PyQt6 import uic
import os  
import sys

class PandasModel(QAbstractTableModel):
    def __init__(self, data, table_window):
        super(PandasModel, self).__init__()
        self._data = data
        self.table_window = table_window

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._data.columns[col]
        return None

    def setData(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

ui_directory = os.path.dirname(os.path.abspath(__file__))
ui_file_path = os.path.join(ui_directory, '..', 'UI', 'viewCases.ui')
viewCases_ui, classinfo = uic.loadUiType(ui_file_path)


class TableWindow(QMainWindow, viewCases_ui):
    selectedRow = pyqtSignal(dict)
    def __init__(self, conn):
        super().__init__()
        self.setupUi(self)
        self.searchbar.setPlaceholderText("CaseNumber or Name")
        self.searchbar.returnPressed.connect(self.loaddata)

        self.conn = conn
        self.cursor = self.conn.cursor

        self.completer = QCompleter()
        self.searchbar.setCompleter(self.completer)

        self.loaddata()

        self.viewcases.doubleClicked.connect(self.on_selectionChanged)

    def on_selectionChanged(self, index):
        row = index.row()
        column = index.column()

        data = {}

        for column in range(self.model.columnCount()):
            column_name = self.model._data.columns[column]
            cell_data = self.model.data(index.sibling(row, column), Qt.ItemDataRole.DisplayRole)
            data[column_name] = cell_data

        self.selectedRow.emit(data)

    def loaddata(self):
        searchbar = self.searchbar.text()
        
        query1 = "SELECT * FROM ER_ENTRIES WHERE caseNumber = ? OR name = ?;"
        self.cursor.execute(query1, (searchbar, searchbar,))

        data = self.cursor.fetchall()
        columns = self.cursor.description

        df = pd.DataFrame(data, columns=[i[0] for i in columns])


        search_query = self.searchbar.text()
        if search_query:
            df = df[df.apply(lambda row: row.astype(str).str.contains(search_query).any(), axis=1)]

        self.model = PandasModel(df, self)
        self.viewcases.setModel(self.model)

        self.viewcases.resizeColumnsToContents()

        


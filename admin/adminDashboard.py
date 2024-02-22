from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QStackedWidget, QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout, QMessageBox
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.uic import loadUi
from admin.addUser import AddUserForm
from Database.firebase_sync import cloud_sync
from admin.updateUser import UpdateUserForm
from admin.deleteUser import delete_user_confirmation
from Database.connect import DBConnection
from admin.logs_handler import LogsHandler
from PyQt6 import uic
import os 
import sqlite3

ui_directory = os.path.dirname(os.path.abspath(__file__))
ui_file_path = os.path.join(ui_directory, '..', 'UI', 'adminDashboard.ui')
adminDashboard_ui, classinfo = uic.loadUiType(ui_file_path)

class AdminDashboard(QMainWindow, adminDashboard_ui):
    logout_signal = pyqtSignal()

    def __init__(self, user_id, name, username, position):
        super().__init__()
        self.conn = DBConnection()
        self.cursor = self.conn.cursor
        self.logs_handler = LogsHandler(self.conn)
        self.firebase_sync = cloud_sync(self.conn)

        self.current_user_id = user_id
        self.current_username = username
        self.current_name = name 
        self.current_position = position

        # Load the UI from the XML file
        self.setupUi(self)

        # Connect the buttons to their respective pages
        self.viewUsers_button.clicked.connect(lambda: self.content.setCurrentIndex(1))
        self.viewLogs_button.clicked.connect(lambda: self.content.setCurrentIndex(2))
        self.addUsers_button.clicked.connect(self.addUserForm)
        self.update_button.clicked.connect(lambda: self.openUpdateUserForm())
        self.delete_button.clicked.connect(self.deleteUser)

        # Connect the setup_table function to be called when viewUsers_page1 is shown
        self.content.currentChanged.connect(self.on_page_changed)
        self.viewUsers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # Connect the logout signal from AdminDashboard
        self.logout_button.clicked.connect(self.logout)

    def addUserForm(self):
        self.addUser = AddUserForm(self.current_user_id, self.current_name, self.current_username, self.current_position)
        self.addUser.userAdded.connect(self.viewUsers)
        self.addUser.show()

    def updateUserForm(self, user_id, name, username, position, user_role, department):
        self.updateUser = UpdateUserForm(self.current_user_id, self.current_name, self.current_username, self.current_position)
        # Set the data in the UpdateUserForm
        self.updateUser.fullname_lineedit.setText(name)
        self.updateUser.username_lineedit.setText(username)
        self.updateUser.userid_lineedit.setText(user_id)
        self.updateUser.position_lineedit.setText(position)
        self.updateUser.roles.setCurrentIndex(self.updateUser.roles.findText(user_role))
        self.updateUser.department.setCurrentIndex(self.updateUser.department.findText(department))
        self.updateUser.userUpdated.connect(self.viewUsers)  # Connect to viewUsers method
        # Show the form
        self.updateUser.show()

    def openUpdateUserForm(self):
        selected_row = self.viewUsers_table.currentRow()
        if selected_row >= 0:
            user_id = self.viewUsers_table.item(selected_row, 0).text()
            name = self.viewUsers_table.item(selected_row, 1).text()
            username = self.viewUsers_table.item(selected_row, 2).text()
            position = self.viewUsers_table.item(selected_row, 3).text()
            user_role = self.viewUsers_table.item(selected_row, 4).text()
            department = self.viewUsers_table.item(selected_row, 5).text()

            # Open the UpdateUserForm and populate the fields
            self.updateUserForm(user_id, name, username, position, user_role, department)

    def deleteUser(self):
        selected_row = self.viewUsers_table.currentRow()
        if selected_row >= 0:
            user_id = self.viewUsers_table.item(selected_row, 0).text()
            username = self.viewUsers_table.item(selected_row, 1).text()

            # Call the integrated delete_user_confirmation function
            if delete_user_confirmation(username):
                # Execute the delete query
                self.cursor.execute("DELETE FROM Users WHERE userId=?", (user_id,))
                self.conn.commit()

                # Inform the user about successful deletion
                QMessageBox.information(self, 'Success', f'account {username} deleted successfully.')
                self.insertUserlog(self.current_user_id, self.current_name, self.current_username, f"Deleted an account: {username}", self.current_position)
                # Refresh the user view
                self.viewUsers()

    def insertUserlog(self, user_id, name, username, action, position):
        self.logs_handler.insert_log(self.current_user_id, self.current_name, self.current_username, action, self.current_position)
        self.firebase_sync.sync_logs_to_firebase()

    def userLogs(self):
        # Execute the query
        query = "SELECT logId, userId, Name, username, action, Position, logTime FROM UserLogs ORDER BY datetime(logTime, 'unixepoch') DESC"

        self.cursor.execute(query)
        data = self.cursor.fetchall()

        # Clear the existing items in the QTableWidget
        self.viewLogs_table.clearContents()
        self.viewLogs_table.setRowCount(0)

        # Check if there are any rows returned
        if not data:
            return

        # Specify the order of columns in the table
        column_order = ["Log ID", "User ID", "Name", "Username", "Action", "Position", "TimeStamp"]
        column_indices = {col: index for index, col in enumerate(column_order)}

        self.viewLogs_table.setColumnCount(len(column_order))
        self.viewLogs_table.setHorizontalHeaderLabels(column_order)

        # Populate the QTableWidget manually in reverse order
        for row_data in reversed(data):
            row_num = self.viewLogs_table.rowCount()
            self.viewLogs_table.insertRow(row_num)

            for col_num, col_name in enumerate(column_order):
                value = row_data[column_indices[col_name]]
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.viewLogs_table.setItem(row_num, col_num, item)

        self.viewLogs_table.resizeColumnsToContents()


    def viewUsers(self):
        # Execute the query
        query = "SELECT userId, Name, username, Position, userRole, department, dateCreated FROM Users"
        self.cursor.execute(query)
        data = self.cursor.fetchall()

        # Clear the existing items in the QTableWidget
        self.viewUsers_table.clearContents()
        self.viewUsers_table.setRowCount(0)

        # Specify the order of columns in the table
        column_headers = ["User ID", "Name", "Username", "Position", "User Role", "Department", "Date Created"]

        self.viewUsers_table.setColumnCount(len(column_headers))
        self.viewUsers_table.setHorizontalHeaderLabels(column_headers)
        self.viewUsers_table.verticalHeader().setVisible(False)

        # Populate the QTableWidget manually
        for row_num, row_data in enumerate(data):
            self.viewUsers_table.insertRow(row_num)
            for col_num, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.viewUsers_table.setItem(row_num, col_num, item)

        self.viewUsers_table.resizeColumnsToContents()


    def on_page_changed(self, index):
        if index == 1:
            self.viewUsers()
        elif index == 2:
            self.userLogs()

    def logout(self):
        # Handle logout functionality here
        reply = QMessageBox.question(self, 'Logout', 'Are you sure you want to logout?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.insertUserlog(self.current_user_id, self.current_name, self.current_username, "Logged Out", self.current_position)
            self.conn.close()
            self.logout_signal.emit()
            self.close()

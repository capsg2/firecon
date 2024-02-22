from PyQt6.QtWidgets import QWidget, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QComboBox
from PyQt6.QtCore import pyqtSignal, QDateTime
from Database.firebase_sync import cloud_sync
from admin.logs_handler import LogsHandler
from Database.connect import DBConnection
from PyQt6.uic import loadUi
from PyQt6 import uic
import os 
import sys
import sqlite3
import hashlib

ui_directory = os.path.dirname(os.path.abspath(__file__))
ui_file_path = os.path.join(ui_directory, '..', 'UI', 'updateUser.ui')
updateUser_ui, classinfo = uic.loadUiType(ui_file_path)

class UpdateUserForm(QWidget, updateUser_ui):
    userUpdated = pyqtSignal()
    
    def __init__(self, user_id, name, username, position):
        super().__init__()
        self.setupUi(self)

        self.conn = DBConnection()  # Assuming DBConnection handles the context correctly
        self.cursor = self.conn.cursor

        self.current_user_id = user_id
        self.current_name = name 
        self.current_username = username
        self.current_position = position

        # Connect UI elements to variables
        self.fullname_lineedit = self.findChild(QLineEdit, 'lineEdit_4')
        self.position_lineedit = self.findChild(QLineEdit, 'lineEdit_5')
        self.username_lineedit = self.findChild(QLineEdit, 'lineEdit')
        self.password_lineedit = self.findChild(QLineEdit, 'lineEdit_2')
        self.roles = self.findChild(QComboBox, 'roles')
        self.department = self.findChild(QComboBox, 'department')
        self.userid_lineedit = self.findChild(QLineEdit, 'userID_lineedit')
        self.userid_lineedit.setVisible(False)
        self.confirm_password_lineedit = self.findChild(QLineEdit, 'lineEdit_3')
        self.update_button = self.findChild(QPushButton, 'pushButton')

        # Connect button click event to method
        self.update_button.clicked.connect(self.update_user)

        self.logs_handler = LogsHandler(self.conn)
        self.firebase_sync = cloud_sync(self.conn)

    def hash_password(self, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        return hashed_password

    def insertUserlog(self, current_user_id, current_name, current_username, action, current_position):
        self.logs_handler.insert_log(self.current_user_id, self.current_name, self.current_username, action, self.current_position)
        self.firebase_sync.sync_logs_to_firebase()

    def update_user(self):
        try:
            userID = self.userid_lineedit.text()
            name = self.fullname_lineedit.text()
            role = self.roles.currentText()
            department = self.department.currentText()
            position = self.position_lineedit.text()
            username = self.username_lineedit.text()
            password = self.password_lineedit.text()
            confirm_password = self.confirm_password_lineedit.text()

            dateCreated = QDateTime.currentDateTime().toString('dd/MM/yyyy | h:mm AP')

            # Get existing user information
            existing_user_info = self.get_user_info(userID)

            # Flags to check if each field is updated
            username_updated = False
            role_updated = False
            department_updated = False
            password_updated = False
            name_updated = False
            position_updated = False

            # Update name
            if name != existing_user_info['name']:
                self.cursor.execute("UPDATE Users SET Name=?, dateCreated=? WHERE userId=?", (name, dateCreated, userID))
                QMessageBox.information(self, 'Success', f'Name updated successfully.')
                self.insertUserlog(self.current_user_id, self.current_name, self.current_username, f'Name of account "{existing_user_info["username"]}" updated to {name}', self.current_position)
                name_updated = True

            # Update username
            if username != existing_user_info['username']:
                self.cursor.execute("UPDATE Users SET username=?, dateCreated=? WHERE userId=?", (username, dateCreated, userID))
                QMessageBox.information(self, 'Success', f'Username updated successfully.')
                self.insertUserlog(self.current_user_id, self.current_name, self.current_username, f"Username {existing_user_info['username']} updated to {username} successfully", self.current_position)
                self.firebase_sync.sync_users_to_firebase()
                username_updated = True

            # Update position
            if position != existing_user_info['position']:
                self.cursor.execute("UPDATE Users SET Position=?, dateCreated=? WHERE userId=?", (position, dateCreated, userID))
                QMessageBox.information(self, 'Success', f'Position updated successfully.')
                self.insertUserlog(self.current_user_id, self.current_name, self.current_username, f'Position of account "{existing_user_info["username"]}" updated to {position}', self.current_position)
                self.firebase_sync.sync_users_to_firebase()
                position_updated = True

            # Update role
            if role != existing_user_info['role']:
                self.cursor.execute("UPDATE Users SET userRole=?, dateCreated=? WHERE userId=?", (role, dateCreated, userID))
                QMessageBox.information(self, 'Success', f'Role updated successfully.')
                self.insertUserlog(self.current_user_id, self.current_name, self.current_username, f'Account "{existing_user_info["username"]}" role changed to {role}', self.current_position)
                self.firebase_sync.sync_users_to_firebase()
                role_updated = True

            if department != existing_user_info['department']:
                self.cursor.execute("UPDATE Users SET department=?, dateCreated=? WHERE userId=?", (department, dateCreated, userID))
                QMessageBox.information(self, 'Success', f'Department updated successfully.')
                self.insertUserlog(self.current_user_id, self.current_name, self.current_username, f'Account "{existing_user_info["username"]}" department changed to {department}', self.current_position)
                self.firebase_sync.sync_users_to_firebase()
                department_updated = True

            # Update password
            if password and password == confirm_password:
                hashed_password = self.hash_password(password)
                self.cursor.execute("UPDATE Users SET \"password\"=?, dateCreated=? WHERE userId=?", (hashed_password, dateCreated, userID))
                QMessageBox.information(self, 'Success', f'Password updated successfully.')
                self.insertUserlog(self.current_user_id, self.current_name, self.current_username, f'Changed Account:"{username}" password successfully', self.current_position)
                self.firebase_sync.sync_users_to_firebase()
                password_updated = True
            elif password and password != confirm_password:
                QMessageBox.critical(self, 'Error', 'Passwords do not match. Please re-enter.')

            # Commit changes at the end
            self.conn.commit()
            self.userUpdated.emit()

        except Exception as e:
            # Handle exceptions
            print(f"An error occurred: {str(e)}")

        finally:
            # Close the connection in the finally block
            self.conn.close()
            self.close()

    def get_user_info(self, userID):
        self.cursor.execute("SELECT username, userRole, Name, Position, department FROM Users WHERE userId=?", (userID,))
        user_info = self.cursor.fetchone()
        return {'username': user_info[0], 'role': user_info[1], 'name': user_info[2], 'position': user_info[3], 'department': user_info[4]}

from PyQt6.QtWidgets import QWidget, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
from PyQt6.QtCore import pyqtSignal, QDateTime, QTimeZone
from PyQt6.QtNetwork import *
from Database.firebase_sync import cloud_sync
from Database.connect import DBConnection
from admin.logs_handler import LogsHandler
from PyQt6.uic import loadUi
from PyQt6 import uic
import os 
import sys
import sqlite3
import hashlib

ui_directory = os.path.dirname(os.path.abspath(__file__))
ui_file_path = os.path.join(ui_directory, '..', 'UI', 'addUser.ui')
addUser_ui, classinfo = uic.loadUiType(ui_file_path)


class AddUserForm(QWidget, addUser_ui):
    userAdded = pyqtSignal()
    def __init__(self, user_id, name, username, position):
        super().__init__()
        self.setupUi(self)

        self.conn = DBConnection()
        self.cursor = self.conn.cursor

        self.current_user_id = user_id
        self.current_name = name 
        self.current_username = username
        self.current_position = position

        # Connect UI elements to variables
        self.fullName_lineedit = self.findChild(QLineEdit, 'lineEdit_5')
        self.position_lineedit = self.findChild(QLineEdit, 'lineEdit_4')
        self.username_lineedit = self.findChild(QLineEdit, 'lineEdit')
        self.password_lineedit = self.findChild(QLineEdit, 'lineEdit_2')
        self.confirm_password_lineedit = self.findChild(QLineEdit, 'lineEdit_3')
        self.add_button = self.findChild(QPushButton, 'pushButton')

        # Connect button click event to method
        self.add_button.clicked.connect(self.add_user)

        self.logs_handler = LogsHandler(self.conn)
        self.firebase_sync = cloud_sync(self.conn)

    def hash_password(self, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        return hashed_password

    def add_user(self): 
        role = self.roles.currentText()
        department = self.department.currentText()
        name = self.fullName_lineedit.text()
        position = self.position_lineedit.text()
        username = self.username_lineedit.text()
        password = self.password_lineedit.text()
        confirm_password = self.confirm_password_lineedit.text()

        if password == confirm_password:
            
            # Check if the username already exists
            self.cursor.execute("SELECT * FROM Users WHERE username=?", (username,))
            existing_user = self.cursor.fetchone()

            if existing_user:
                QMessageBox.critical(self, 'Error', 'Username already exists. Choose another username.')
            else:
                dateCreated = QDateTime.currentDateTime().toString('dd/MM/yyyy | h:mm AP')

                hashed_password = self.hash_password(password)

                # Insert the new user into the database
                self.cursor.execute("INSERT INTO Users (Name, username, password, Position, userRole, department, dateCreated) VALUES (?, ?, ?, ?, ?, ?, ?)", (name, username, hashed_password, position, role, department, dateCreated))
                self.conn.commit()
                self.firebase_sync.sync_users_to_firebase()
                self.userAdded.emit()
                QMessageBox.information(self, 'Success', f'User {username} added successfully.')
                self.insertUserlog(self.current_user_id, self.current_name, self.current_username, f"Created an account: {username}", self.current_position)
                
                self.close()
                self.conn.close()
        else:
            QMessageBox.critical(self, 'Error', 'Passwords do not match. Please re-enter.')

    def insertUserlog(self, current_user_id, current_name, current_username, action, current_position):
        self.logs_handler.insert_log(self.current_user_id, self.current_name, self.current_username, action, self.current_position)
        self.firebase_sync.sync_logs_to_firebase()

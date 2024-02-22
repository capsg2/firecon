from PyQt6.QtWidgets import QApplication, QWidget, QMessageBox
from admin.adminDashboard import AdminDashboard
from User.main_interface import MainInterface
from Database.connect import DBConnection
from admin.logs_handler import LogsHandler
from Database.firebase_sync import cloud_sync
from PyQt6.QtCore import Qt
from PyQt6 import uic
import sqlite3
import hashlib
import os


ui_directory = os.path.dirname(os.path.abspath(__file__))
ui_file_path = os.path.join(ui_directory, '..', 'UI', 'login1.ui')
login_ui, classinfo = uic.loadUiType(ui_file_path)

class LoginSystem(QWidget, login_ui):
    def __init__(self):
        super().__init__()
        
        self.setupUi(self)
        self.login_button.clicked.connect(self.login)
        self.conn = DBConnection()
        self.cursor = self.conn.cursor
        self.logs_handler = LogsHandler(self.conn)
        self.firebase_sync = cloud_sync(self.conn)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint) 
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("no title") 

    def hash_password(self, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        return hashed_password

    def login(self):
        username = self.username.text()
        password = self.password.text()

        hashed_password = self.hash_password(password)

        # Your login authentication logic goes here
        query = "SELECT * FROM Users WHERE username=? AND password=?"
        self.cursor.execute(query, (username, hashed_password))
        result = self.cursor.fetchone()

        if result:
            current_user_id = result[0]
            current_name = result[1]
            current_username = result[2]
            current_position = result[4]
            user_role = result[5]

            # Redirect to the appropriate interface based on userRole
            if user_role == 'ADMIN':
                self.main_interface = AdminDashboard(current_user_id, current_name, current_username, current_position)
                self.insertUserlog(current_user_id, current_name, current_username, f'Logged In', current_position)
            elif user_role == 'USER':
                self.main_interface = MainInterface(current_user_id, current_name, current_username, current_position)
                self.insertUserlog(current_user_id, current_name, current_username, f'Logged In', current_position)
            else:
                QMessageBox.critical(self, 'Invalid userRole', 'User is neither an ADMIN or a USER')
                return

            self.main_interface.logout_signal.connect(self.show_login_window)

            self.close()
            self.main_interface.show()
        else:
            QMessageBox.critical(self, 'Login Failed', 'Invalid username or password')
            # Add code here to handle failed login, for example, showing an error label on the UI

    def insertUserlog(self, current_user_id, current_name, current_username, action, current_position):
        self.logs_handler.insert_log(current_user_id, current_name, current_username, action, current_position)
        self.firebase_sync.sync_logs_to_firebase()

    def show_login_window(self):
        self.login_window = LoginSystem()
        self.login_window.show()

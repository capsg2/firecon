from PyQt6.QtWidgets import QMessageBox
from Database.connect import DBConnection
from PyQt6.QtCore import QDateTime
import sqlite3

class LogsHandler:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = self.conn.cursor

    def insert_log(self, user_id, name, username, action, position):
        try:
            dateCreated = QDateTime.currentDateTime().toString('dd/MM/yyyy | h:mm AP')

            # Insert a user log entry into the UserLogs table
            query = "INSERT INTO UserLogs (userId, Name, username, action, Position, logtime) VALUES (?, ?, ?, ?, ?, ?)"
            self.cursor.execute(query, (user_id, name, username, action, position, dateCreated))
            self.conn.commit()
        except sqlite3.Error as e:
            self.handle_error("Failed to insert user log:", e)

    def handle_error(self, message, error):
        QMessageBox.critical(None, "Error", f"{message}\nError Details: {str(error)}")

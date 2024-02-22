from PyQt6.QtWidgets import QMessageBox
import os 
import sys
import sqlite3
import pyrebase

class DBConnection:
    def __init__(self):
        self.connect_sqlite()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def connect_sqlite(self):
        database_directory = os.path.dirname(os.path.abspath(__file__))
        database_file_path = os.path.join(database_directory, '..', 'Database', 'ER_Entries.sqlite')

        try:
            self.db_connection = sqlite3.connect(database_file_path)
            self.cursor = self.db_connection.cursor()
            self.db_connection.execute("SELECT 1")
        except sqlite3.Error as e:
            QMessageBox.critical(
                None,
                "FireOps - Error!",
                f"SQLite Database Connection Error:{str(e)}",
            )

    def commit(self):
        try:
            if self.db_connection:
                self.db_connection.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(
                None,
                "FireOps - Error!",
                f"SQLite Database Commit Error:{str(e)}",
            )
        
    def close(self):
        try:
            if self.db_connection:
                self.db_connection.close()
        except sqlite3.Error as e:
            QMessageBox.critical(
                None,
                "FireOps - Error!",
                f"SQLite Database Close Error:{str(e)}",
            )

    def isOpen(self):
        try:
            if self.db_connection:
                self.db_connection.execute("SELECT 1")
                return True
            else:
                return False
        except sqlite3.Error:
            return False


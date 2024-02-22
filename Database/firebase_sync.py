from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import QMessageBox
from Database.connect import DBConnection
import sqlite3
import pyrebase
import requests

class cloud_sync:
    def __init__(self, conn):
        self.data_list = []
        self.data_listDict = []
        self.conn = conn
        self.cursor = self.conn.cursor

        config = {
		  "apiKey": "AIzaSyDqcahpxAwtlOCxuihEwgsiQIElAtLtR6I",
		  "authDomain": "capstone-project-197cb.firebaseapp.com",
		  "databaseURL": "https://capstone-project-197cb-default-rtdb.firebaseio.com",
		  "projectId": "capstone-project-197cb",
		  "storageBucket": "capstone-project-197cb.appspot.com",
		  "messagingSenderId": "822954502605",
		  "appId": "1:822954502605:web:48b142877e81a32dab7c84",
		  "measurementId": "G-F5J4490QX8"
		};

        self.firebase = pyrebase.initialize_app(config)
        self.db = self.firebase.database()

        if not self.conn.isOpen():
            self.conn.open()

        if not self.conn.isOpen():
            QMessageBox.critical(
                None,
                "App Name - Error!",
                "Database Error: %s" % self.conn.lastError().databaseText(),
            )

    def check_connectivity(self):
        try:
            firebase_database_url = "https://capstone-project-197cb-default-rtdb.firebaseio.com"
            response = requests.get(firebase_database_url, timeout=5)
            return response.status_code == 200
        except requests.ConnectionError:
            return False

    def sync_cases_to_firebase(self):
        try:
            if not self.check_connectivity():
                print("No connectivity. Sync aborted.")
                return

            if not self.conn.isOpen():
                self.conn.open()

            select_query = "SELECT * FROM ER_ENTRIES WHERE cloudSync = 0 or cloudSync IS NULL"
            self.cursor.execute(select_query)
            records_cases = self.cursor.fetchall()

            for record in records_cases:
                id_value = record[2]
                data_dict = {
					"Date": record[1],
					"CaseNumber": record[2],
					"Location": record[3],
					"NumberOfKM": record[4],
					"TypeOfIncident": record[5],
					"Involved": record[6],
					"Informant": record[7],
					"RespondingTeam": record[8],
					"OtherAgency": record[9],
					"TimeOfCall": record[10],
					"OutOfStation": record[11],
					"ArriveAtScene": record[12],
					"BackToStation": record[13],
					"ResponseTime": record[14],
					"Name": record[15],
					"Age": record[16],
					"Gender": record[17],
					"DevtMilestone": record[18],
					"ChiefComplaints": record[19],
					"GenImpression": record[20],
					"ActionsTaken": record[21],
					"HospRef": record[22],
					"DutyEMS": record[23]
                }

                self.data_listDict.append((id_value, data_dict))

                firebase_record = self.db.child("CaseNumber").child(str(id_value)).get()
                if firebase_record is not None:
                    print(f"Case with ID {id_value} already exists in Firebase. Updating...")
                    self.db.child("CaseNumber").child(str(id_value)).update(data_dict)
                else:
                    print(f"Case with ID {id_value} doesn't exist in Firebase. Uploading...")
                    self.db.child("CaseNumber").child(str(id_value)).set(data_dict)

                # Update sync status in SQLite
                update_query = "UPDATE ER_ENTRIES SET cloudSync = 1 WHERE caseNumber = ?"
                self.cursor.execute(update_query, (record[2],))
                self.conn.commit()
                print(f"Case with ID {id_value} updated successfully.")

        except sqlite3.Error as e:
            print("Error syncing to Firebase:", str(e))

    def sync_users_to_firebase(self):
        try:
            if not self.check_connectivity():
                print("No connectivity. Sync aborted.")
                return

            if not self.conn.isOpen():
                self.conn.open()

            select_query = "SELECT * FROM Users WHERE cloudSync = 0 or cloudSync IS NULL"
            self.cursor.execute(select_query)
            records_users = self.cursor.fetchall()

            for record in records_users:
                id_value = record[0]
                data_dict = {
					"UserID": record[0],
					"Name": record[1],
					"Username": record[2],
					"Password": record[3],
					"Position": record[4],
					"UserRole": record[5],
					"Department": record[6]
                }

                self.data_listDict.append((id_value, data_dict))

                firebase_record = self.db.child("Users").child(str(id_value)).get()
                if firebase_record is not None:
                    print(f"User with ID {id_value} already exists in Firebase. Updating...")
                    self.db.child("Users").child(str(id_value)).update(data_dict)
                else:
                    print(f"User with ID {id_value} doesn't exist in Firebase. Uploading...")
                    self.db.child("Users").child(str(id_value)).set(data_dict)

                # Update sync status in SQLite
                update_query = "UPDATE Users SET cloudSync = 1 WHERE userId = ?"
                self.cursor.execute(update_query, (record[1],))
                self.conn.commit()
                print(f"User with ID {id_value} updated successfully.")

        except sqlite3.Error as e:
            print("Error syncing to Firebase:", str(e))

    def sync_logs_to_firebase(self):
	    try:
	        if not self.check_connectivity():
	            print("No connectivity. Sync aborted.")
	            return

	        if not self.conn.isOpen():
	            self.conn.open()

	        select_query = "SELECT * FROM UserLogs WHERE cloudSync = 0 or cloudSync IS NULL"
	        self.cursor.execute(select_query)
	        records_logs = self.cursor.fetchall()

	        # Get all log IDs to fetch existing logs in bulk
	        log_ids = [record[0] for record in records_logs]

	        # Fetch existing logs from Firebase in bulk
	        firebase_records = self.db.child("UserLogs").get().val()

	        # Check if firebase_records is None, treat it as an empty dictionary
	        firebase_records = firebase_records or {}

	        for record in records_logs:
	            id_value = record[0]
	            data_dict = {
	                "LogID": record[0],
	                "UserID": record[1],
	                "Name": record[2],
	                "Username": record[3],
	                "Action": record[4],
	                "Position": record[5],
	                "LogTime": record[6]
	            }

	            self.data_listDict.append((id_value, data_dict))

	            # Check if log exists in Firebase
	            if str(id_value) in firebase_records:
	                print(f"UserLog with ID {id_value} already exists in Firebase. Ignoring...")
	            else:
	                print(f"UserLog with ID {id_value} doesn't exist in Firebase. Uploading...")
	                self.db.child("UserLogs").child(str(id_value)).set(data_dict)

	                # Update sync status in SQLite
	                update_query = "UPDATE UserLogs SET cloudSync = 1 WHERE logId = ?"
	                self.cursor.execute(update_query, (record[0],))
	                self.conn.commit()
	                print(f"UserLog with ID {id_value} uploaded successfully.")

	    except sqlite3.Error as e:
	        print("Error syncing to Firebase:", str(e))


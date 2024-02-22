import sqlite3
from PyQt6.QtWidgets import QMessageBox
from admin.logs_handler import LogsHandler
from Database.firebase_sync import cloud_sync

class UserCRUD:
    def __init__(self, conn, user_id, name, username, position):
        self.conn = conn
        self.cursor = self.conn.cursor

        self.logs_handler = LogsHandler(self.conn)
        self.firebase_sync = cloud_sync(self.conn)
        self.current_user_id = user_id
        self.current_username = username
        self.current_name = name 
        self.current_position = position

    def insertUserlog(self, current_user_id, current_name, current_username, action, current_position):
        self.logs_handler.insert_log(self.current_user_id, self.current_name, self.current_username, action, self.current_position)


    def case_number_exists(self, case_number):
        if self.conn is not None:
            try:
                self.cursor.execute("SELECT 1 FROM ER_ENTRIES WHERE caseNumber=?", (case_number,))
                return bool(self.cursor.fetchone())  # Returns True if the case number exists, False otherwise
            except sqlite3.Error as e:
                print("Error checking case number existence:", str(e))
            
        else:
            QMessageBox.critical(
                None,
                "App Name - Error!",
                "Database connection is None",
            )
            return False

    def insert_data(self, case_number, data_list):
        if self.conn is not None:
            try:
                # Assuming data_list contains the correct number of elements for each column in the table
                self.cursor.execute("""
                    INSERT INTO ER_ENTRIES 
                    (date, caseNumber, location, numOfKM, incidentType, involved, informant, respondingTeam, 
                    otherAgency, dutyEMS, timeOfCall, outOfStation, arriveAtScene, backToStation, responseTime, 
                    name, age, gender, devtMilestone, chiefComplaints, genImpression, actionsTaken, hospRef, cloudSync) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, data_list)
                self.conn.commit()
                print("Case added successfully")
                self.insertUserlog(self.current_user_id, self.current_name, self.current_username, f'Added initial logs case number:{case_number}', self.current_position)
                self.firebase_sync.sync_cases_to_firebase()
            except sqlite3.Error as e:
                print("Error inserting data:", str(e))
        else:
            QMessageBox.critical(
                None,
                "App Name - Error!",
                "Database connection is None", 
            )

    def update_data(self, case_number, data_list):
        if self.conn is not None:
            try:
            # Convert data_list to a tuple before concatenating
                self.cursor.execute("""
                UPDATE ER_ENTRIES SET 
                    date=?, caseNumber=?, location=?, numOfKM=?, incidentType=?, involved=?, informant=?, 
                    respondingTeam=?, otherAgency=?, dutyEMS=?, timeOfCall=?, outOfStation=?, 
                    arriveAtScene=?, backToStation=?, responseTime=?, name=?, age=?, gender=?, 
                    devtMilestone=?, chiefComplaints=?, genImpression=?, actionsTaken=?, hospRef=?, cloudSync=? 
                    WHERE caseNumber=?
                """, tuple(data_list) + (case_number,))
                print("Updated successfully")

                self.conn.commit()
                self.insertUserlog(self.current_user_id, self.current_name, self.current_username, f'Updated initial logs case number:{case_number}', self.current_position)
                self.firebase_sync.sync_cases_to_firebase()
            except sqlite3.Error as e:
                print("Error updating data:", e)
        else:
            QMessageBox.critical(
            None,
            "App Name - Error!",
            "Database connection is None",
            )


    def delete_data(self, case_number):
        if self.conn is not None:
            try:
                self.cursor.execute("DELETE FROM ER_ENTRIES WHERE caseNumber=?", (case_number,))
                self.conn.commit()
                self.insertUserlog(self.current_user_id, self.current_name, self.current_username, f'Deleted initial logs case number:{case_number}', self.current_position)
            except sqlite3.Error as e:
                print("Error deleting data:", str(e))
            
        else:
            QMessageBox.critical(
                None,
                "App Name - Error!",
                "Database connection is None",
            )

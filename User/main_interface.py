from PyQt6.QtWidgets import QMainWindow, QLineEdit, QMessageBox
from PyQt6.QtCore import QDate, pyqtSignal
from User.crud import UserCRUD
from PyQt6.uic import loadUi
from Database.connect import DBConnection
from User.viewCases import TableWindow
from User.comparativeReport import ComparativeReport
from PyQt6.QtSql import QSqlQuery
from Database.connect import DBConnection
from admin.logs_handler import LogsHandler
from PyQt6 import uic
import os
import sys
import sqlite3

ui_directory = os.path.dirname(os.path.abspath(__file__))
ui_file_path = os.path.join(ui_directory, '..', 'UI', 'mainWindowInterface.ui')
mainInterface_ui, classinfo = uic.loadUiType(ui_file_path)

class MainInterface(QMainWindow, mainInterface_ui):
    logout_signal = pyqtSignal()

    def __init__(self, user_id, name, username, position):
        super().__init__()
        self.data_list = []
        self.setupUi(self)
        self.conn = DBConnection()
        self.cursor = self.conn.cursor
        self.logs_handler = LogsHandler(self.conn)

        self.current_user_id = user_id
        self.current_username = username
        self.current_name = name
        self.current_position = position

        self.check_user_permissions()

        self.user_crud = UserCRUD(self.conn, self.current_user_id, self.current_name, self.current_username,
                                  self.current_position)

        self.save_button.clicked.connect(self.save_data)
        self.delete_button.clicked.connect(self.delete_data)
        self.viewCases_button.clicked.connect(self.viewTable)
        self.comparativeReport_button.clicked.connect(self.openComparativeReport)

        self.searchbar = QLineEdit()
        self.searchbar.returnPressed.connect(self.search)

        self.logout_button.clicked.connect(self.logout)

    def logout(self):
        reply = QMessageBox.question(self, 'Logout', 'Are you sure you want to logout?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.insertUserlog(self.current_user_id, self.current_name, self.current_username, "Logged Out",
                                "self.current_position")
            self.conn.close()
            self.logout_signal.emit()
            self.close()

    def insertUserlog(self, current_user_id, current_name, current_username, action, current_position):
        self.logs_handler.insert_log(self.current_user_id, self.current_name, self.current_username, action,
                                     self.current_position)

    def check_user_permissions(self):
        query = "SELECT userRole, department FROM Users WHERE userId=?"
        self.cursor.execute(query, (self.current_user_id,))
        result = self.cursor.fetchone()

        if result:
            user_role, department = result

            if user_role == 'ADMIN' or department == 'EMS':
                self.pcr_button.show()
            else:
                self.pcr_button.hide()

    def save_data(self):
        date = self.date_input.text()
        casenumber = self.casenum_input.text()
        location = self.location_input.text()
        numOfKM = self.numkm_input.text()
        incidentType = self.incident_input.currentText()
        involved = self.involved_input.text()
        informant = self.informant_input.text()
        respondingTeam = self.resteam_input.text()
        otherAgency = self.othagency_input.text()
        dutyEms = self.dutyems_input.text()
        timeOfCall = self.calltime_input.text()
        outOfStation = self.stationout_input.text()
        arriveAtScene = self.scenearrive_input.text()
        backToStation = self.backstation_input.text()
        responseTime = self.restime_input.text()
        name = self.name_input.text()
        age = self.age_input.text()
        gender = self.gender_input.currentText()
        devtMilestone = self.devmiles_input.text()
        chiefComplaints = self.chcomplaints_input.text()
        genImpression = self.genimpress_input.text()
        actionsTaken = self.actionstake_input.text()
        hospRef = self.hospref_input.text()
        cloudSync = 0

        current_data = (date, casenumber, location, numOfKM, incidentType, involved, informant, respondingTeam,
                        otherAgency, dutyEms, timeOfCall, outOfStation, arriveAtScene, backToStation, responseTime,
                        name, age, gender, devtMilestone, chiefComplaints, genImpression, actionsTaken, hospRef, cloudSync)

        self.data_list = [current_data]

        if self.user_crud.case_number_exists(casenumber):
            self.user_crud.update_data(casenumber, self.data_list[0])
        else:
            self.user_crud.insert_data(casenumber, self.data_list[0])

    def delete_data(self):
        casenumber = self.casenum_input.text()
        reply = QMessageBox.question(self, 'Delete Record', f'Are you sure you want to delete record with Case Number {casenumber}?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.user_crud.delete_data(casenumber)
            self.clear_input_fields()

    def clear_input_fields(self):
        self.date_input.setDate(QDate.currentDate())
        self.casenum_input.clear()
        self.location_input.clear()
        self.numkm_input.clear()
        self.incident_input.setCurrentIndex(0)
        self.involved_input.clear()
        self.informant_input.clear()
        self.resteam_input.clear()
        self.othagency_input.clear()
        self.dutyems_input.clear()
        self.calltime_input.clear()
        self.stationout_input.clear()
        self.scenearrive_input.clear()
        self.backstation_input.clear()
        self.restime_input.clear()
        self.name_input.clear()
        self.age_input.clear()
        self.gender_input.setCurrentIndex(0)
        self.devmiles_input.clear()
        self.chcomplaints_input.clear()
        self.genimpress_input.clear()
        self.actionstake_input.clear()
        self.hospref_input.clear()

    def openComparativeReport(self):
        self.compRep = ComparativeReport(self.conn)
        self.compRep.show()

    def viewTable(self):
        self.table_window = TableWindow(self.conn)
        self.table_window.selectedRow.connect(self.on_rowSelected)
        self.table_window.show()

    def on_rowSelected(self, data):
        qdate = QDate.fromString(data['date'], "dd/MMM/yyyy")
        self.date_input.setDisplayFormat("dd/MMM/yyyy")
        self.date_input.setDate(qdate)

        self.casenum_input.setText(data['caseNumber'])
        self.location_input.setText(data['location'])
        self.numkm_input.setText(data['numOfKM'])
        self.incident_input.setCurrentText(data['incidentType'])
        self.involved_input.setText(data['involved'])
        self.informant_input.setText(data['informant'])
        self.resteam_input.setText(data['respondingTeam'])
        self.othagency_input.setText(data['otherAgency'])
        self.dutyems_input.setText(data['dutyEMS'])
        self.calltime_input.setText(data['timeOfCall'])
        self.stationout_input.setText(data['outOfStation'])
        self.scenearrive_input.setText(data['arriveAtScene'])
        self.backstation_input.setText(data['backToStation'])
        self.restime_input.setText(data['responseTime'])
        self.name_input.setText(data['name'])
        self.age_input.setText(data['age'])
        self.gender_input.setCurrentText(data['gender'])
        self.devmiles_input.setText(data['devtMilestone'])
        self.chcomplaints_input.setText(data['chiefComplaints'])
        self.genimpress_input.setText(data['genImpression'])
        self.actionstake_input.setText(data['actionsTaken'])
        self.hospref_input.setText(data['hospRef'])

    def search(self):
        searchbar = self.searchbar.text()
        query1 = "SELECT * FROM ER_ENTRIES WHERE caseNumber = ?;"
        self.cursor.execute(query1, (searchbar,))

        fill = self.cursor.fetchall()

        if fill and fill is not None:
            print(fill)
            for index, fillOutput in enumerate(fill):
                qdate = QDate.fromString(fillOutput[1], "d-MMM-yyyy")
                self.date_input.setDisplayFormat("d-MMM-yyyy")
                self.date_input.setDate(qdate)

                self.casenum_input.setText(str(fillOutput[2]))
                self.location_input.setText(str(fillOutput[3]))
                self.numkm_input.setText(str(fillOutput[4]))
                self.incident_input.setCurrentText(str(fillOutput[5]))
                self.involved_input.setText(str(fillOutput[6]))
                self.informant_input.setText(str(fillOutput[7]))
                self.resteam_input.setText(str(fillOutput[8]))
                self.othagency_input.setText(str(fillOutput[9]))
                self.dutyems_input.setText(str(fillOutput[10]))
                self.calltime_input.setText(str(fillOutput[11]))
                self.stationout_input.setText(str(fillOutput[12]))
                self.scenearrive_input.setText(str(fillOutput[13]))
                self.backstation_input.setText(str(fillOutput[14]))
                self.restime_input.setText(str(fillOutput[15]))
                self.name_input.setText(str(fillOutput[16]))
                self.age_input.setText(str(fillOutput[17]))
                self.gender_input.setCurrentText(str(fillOutput[18]))
                self.devmiles_input.setText(str(fillOutput[19]))
                self.chcomplaints_input.setText(str(fillOutput[20]))
                self.genimpress_input.setText(str(fillOutput[21]))
                self.actionstake_input.setText(str(fillOutput[22]))
                self.hospref_input.setText(str(fillOutput[23]))

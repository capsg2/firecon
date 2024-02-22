from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QFileDialog, QMessageBox
from PyQt6.QtGui import QTextDocument
from PyQt6.QtCore import Qt
from PyQt6.uic import loadUi
from PyQt6 import uic 
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import sqlite3
import sys
import os

ui_directory = os.path.dirname(os.path.abspath(__file__))
ui_file_path = os.path.join(ui_directory, '..', 'UI', 'comparativeReport.ui')
comparativeReport_ui, classinfo = uic.loadUiType(ui_file_path)


class ComparativeReport(QMainWindow, comparativeReport_ui):
    def __init__(self, conn):
        super().__init__()

        self.conn = conn 
        self.cursor = self.conn.cursor

        # Load the UI from the XML file
        self.setupUi(self)

        # Connect the filter button to the function
        self.filter_button.clicked.connect(self.filter_data)

        # Add "Generate Report" button
        self.generate_report_button = QPushButton("Generate Report", self)
        self.generate_report_button.clicked.connect(self.generate_report_button_clicked)

        # Add button to the layout
        layout = QHBoxLayout()
        layout.addWidget(self.generate_report_button)
        layout.addStretch()
        self.verticalLayout.addLayout(layout)

    def generate_report_button_clicked(self):
        # Triggered when the "Generate Report" button is clicked
        self.filter_data()
        self.generate_pdf_report(self.counts, [self.year1, self.year2, self.year3])

    def filter_data(self):
        # Get the years from lineedits
        self.year1 = self.year1_lineedit.text()
        self.year2 = self.year2_lineedit.text()
        self.year3 = self.year3_lineedit.text()

        # Execute the queries
        self.counts = self.get_counts(self.year1, self.year2, self.year3)

        # Display the counts in the table
        self.display_table(self.counts, [self.year1, self.year2, self.year3])

    def get_counts(self, year1, year2, year3):
        # Get all distinct incident types
        incident_types_query = "SELECT DISTINCT incidentType FROM ER_ENTRIES"
        all_incident_types = [row[0] for row in self.cursor.execute(incident_types_query).fetchall()]

        # Initialize counts for each year
        counts1 = {incident_type: 0 for incident_type in all_incident_types}
        counts2 = {incident_type: 0 for incident_type in all_incident_types}
        counts3 = {incident_type: 0 for incident_type in all_incident_types}

        # Debugging query to check if there are any records for each year
        debug_query = "SELECT COUNT(*) FROM ER_ENTRIES WHERE date LIKE ?"

        print("Debug Query 1 result:", self.cursor.execute(debug_query, (f'{year1}%',)).fetchall())
        print("Debug Query 2 result:", self.cursor.execute(debug_query, (f'{year2}%',)).fetchall())
        print("Debug Query 3 result:", self.cursor.execute(debug_query, (f'{year3}%',)).fetchall())

        # ... (rest of the code remains the same)


        # Execute the queries and update counts
        query1 = "SELECT incidentType, COUNT(*) FROM ER_ENTRIES WHERE date LIKE ? GROUP BY incidentType"
        query2 = "SELECT incidentType, COUNT(*) FROM ER_ENTRIES WHERE date LIKE ? GROUP BY incidentType"
        query3 = "SELECT incidentType, COUNT(*) FROM ER_ENTRIES WHERE date LIKE ? GROUP BY incidentType"

        print("Query 1 result:", self.cursor.execute(query1, (f'{year1}%',)).fetchall())
        counts1.update(dict(self.cursor.execute(query1, (f'{year1}%',)).fetchall()))

        print("Query 2 result:", self.cursor.execute(query2, (f'{year2}%',)).fetchall())
        counts2.update(dict(self.cursor.execute(query2, (f'{year2}%',)).fetchall()))

        print("Query 3 result:", self.cursor.execute(query3, (f'{year3}%',)).fetchall())
        counts3.update(dict(self.cursor.execute(query3, (f'{year3}%',)).fetchall()))

        return counts1, counts2, counts3


    def display_table(self, counts, years):
        # Set side headers
        side_headers = ["MEDICAL", "VEHICULAR", "TRAUMA"]
        self.comparativeReport_table.setRowCount(len(side_headers))
        self.comparativeReport_table.setColumnCount(len(years))

        # Set horizontal headers with year values
        self.comparativeReport_table.setHorizontalHeaderLabels([f"{year}" for year in years])

        # Set vertical headers with incident types
        self.comparativeReport_table.setVerticalHeaderLabels(side_headers)

        # Iterate through each year
        for col, year in enumerate(years):
            # Iterate through each incident type (side headers)
            for row, header in enumerate(side_headers):
                # Get the count for the corresponding incident type and year
                count = counts[col].get(header, 0)

                # Create a new item with the count
                item = QTableWidgetItem(str(count))
                item.setTextAlignment(Qt.AlignCenter)
                self.comparativeReport_table.setItem(row, col, item)

    def generate_pdf_report(self, counts, years):
        # Get a filename from the user (you can customize the file dialog options)
        filename, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", "", "PDF Files (*.pdf)")

        if filename:
            # Create a PDF document
            pdf = canvas.Canvas(filename, pagesize=letter)

            # Set the font for the document (you can customize font options)
            pdf.setFont("Helvetica", 12)

            # Write the title
            title = "Comparative Report"
            pdf.drawCentredString(letter[0] / 2, letter[1] - 20, title)

            # Write the header row
            col_width = letter[0] / len(years)
            row_height = 20

            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(10, letter[1] - 50, "Incident Type")

            for col, year in enumerate(years):
                pdf.drawString(10 + col * col_width, letter[1] - 50, str(year))
            
            pdf.setFont("Helvetica", 12)

            # Iterate through each incident type
            for row, incident_type in enumerate(counts[0].keys()):
                pdf.drawString(10, letter[1] - 70 - row * row_height, incident_type)

                # Write a row for each incident type
                for col in range(len(years)):
                    count = counts[col].get(incident_type, 0)
                    pdf.drawString(10 + col * col_width, letter[1] - 70 - row * row_height, str(count))

            # Save the PDF file
            pdf.save()

            QMessageBox.information(self, "PDF Report Generated", f"PDF Report saved to {filename}", QMessageBox.Ok)

import sys
from PyQt6.QtWidgets import QApplication
from login_system.login import LoginSystem

app = QApplication(sys.argv)

window = LoginSystem()

window.show()

sys.exit(app.exec())

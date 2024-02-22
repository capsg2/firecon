from PyQt6.QtWidgets import QMessageBox

def delete_user_confirmation(username):
    reply = QMessageBox.question(None, 'Delete User', f'Are you sure you want to delete user {username}?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    return reply == QMessageBox.StandardButton.Yes

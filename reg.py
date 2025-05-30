from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout
from user import UserWindow
from admin import AdminWindow

class RegistrationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Выбор роли")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        user_btn = QPushButton("Войти как пользователь")
        admin_btn = QPushButton("Войти как администратор")

        user_btn.clicked.connect(self.open_user_window)
        admin_btn.clicked.connect(self.open_admin_window)

        layout.addWidget(user_btn)
        layout.addWidget(admin_btn)
        self.setLayout(layout)

    def open_user_window(self):
        self.user_window = UserWindow(login_window=self)
        self.user_window.show()
        self.hide()


    def open_admin_window(self):
        self.admin_window = AdminWindow(login_window=self)
        self.admin_window.show()
        self.close()

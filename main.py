import sys
from PyQt5.QtWidgets import QApplication
from reg import RegistrationWindow

def main():
    app = QApplication(sys.argv)
    registration = RegistrationWindow()
    registration.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

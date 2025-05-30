import sys
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt
from datetime import datetime, timedelta
import pyqtgraph as pg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

COLUMN_TRANSLATIONS = {
    "id": "ID",
    "name": "Название",
    "number": "Номер",
    "model": "Модель",
    "property": "Собственность",
    "country": "Страна",
    "foundation": "Дата основания",
    "surname": "Фамилия",
    "experience": "Стаж",
    "contract_start": "Начало контракта",
    "contract_end": "Окончание контракта",
    "plane": "Самолёт",
    "pilot": "Пилот",
    "departure": "Отправление",
    "destination": "Прибытие",
    "airline": "Авиакомпания",
    "duration": "Длительность"
}

class UserWindow(QMainWindow):
    def __init__(self, login_window=None):
        super().__init__()
        self.login_window = login_window
        self.setWindowTitle("Просмотр данных")
        self.resize(1000, 600)

        self.conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="airlines_db",
            user="postgres",
            password="1234"
        )

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.layout.addWidget(QLabel("Выберите таблицу для просмотра:"))

        button_layout = QHBoxLayout()
        for name in ["pilot", "airline", "plane", "country", "airport", "flight"]:
            btn = QPushButton(name.capitalize())
            btn.clicked.connect(lambda _, table=name: self.load_table(table))
            button_layout.addWidget(btn)

        logout_btn = QPushButton("Выход")
        logout_btn.clicked.connect(self.logout)
        button_layout.addWidget(logout_btn)

        self.layout.addLayout(button_layout)

        self.table_widget = QTableWidget()
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows) 
        self.layout.addWidget(self.table_widget)

        self.report_buttons_layout = QHBoxLayout()
        self.reports = [
            ("Часы налета по самолетам", self.report_flights_by_plane),
            ("Часы налета пилотов", self.report_flight_hours_by_pilot),
            ("Пилоты с истекающим контрактом", self.report_pilots_with_expiring_contract)
        ]

        for report_name, report_function in self.reports:
            btn = QPushButton(report_name)
            btn.clicked.connect(report_function)
            self.report_buttons_layout.addWidget(btn)

        self.layout.addLayout(self.report_buttons_layout)

    def logout(self):
        self.login_window.show()
        self.close()

    def load_table(self, table_name):
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY id")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            self.table_widget.clear()
            self.table_widget.setRowCount(len(rows))
            self.table_widget.setColumnCount(len(columns))
            rus_colnames = [COLUMN_TRANSLATIONS.get(col, col) for col in columns]
            self.table_widget.setHorizontalHeaderLabels(rus_colnames)

            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    self.table_widget.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

            cursor.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить таблицу:\n{e}")

    def report_flights_by_plane(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT p.model, SUM(f.duration) AS total_hours
                FROM flight f
                JOIN plane p ON f.plane = p.number
                GROUP BY p.model
                ORDER BY total_hours DESC
            """)
            rows = cursor.fetchall()
            cursor.close()

            if not rows:
                QMessageBox.information(self, "Отчет", "Нет данных по налету самолетов.")
                return

            self.report_window = QWidget()
            self.report_window.setWindowTitle("Налет по моделям самолетов")
            layout = QVBoxLayout()

            table = QTableWidget()
            table.setRowCount(len(rows))
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["Модель", "Часы налета"])

            for i, (model, hours) in enumerate(rows):
                table.setItem(i, 0, QTableWidgetItem(str(model)))
                table.setItem(i, 1, QTableWidgetItem(str(hours)))

            layout.addWidget(table)

            models = [row[0] for row in rows]
            hours = [row[1] for row in rows]

            fig = Figure(figsize=(5, 4))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            ax.pie(hours, labels=models, autopct='%1.1f%%', startangle=140)
            ax.set_title("Доля налета по моделям самолетов")
            ax.axis('equal')  

            layout.addWidget(canvas)
            self.report_window.setLayout(layout)
            self.report_window.resize(800, 600)
            self.report_window.show()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка при создании отчета", str(e))
    
    def report_flight_hours_by_pilot(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT pilot, SUM(duration) as total_hours
                FROM flight
                GROUP BY pilot
                ORDER BY total_hours DESC
            """)
            rows = cursor.fetchall()
            cursor.close()

            if not rows:
                QMessageBox.information(self, "Отчет", "Нет данных о налете пилотов.")
                return
            
            self.report_window = QWidget()
            self.report_window.setWindowTitle("Часы налета пилотов")
            layout = QVBoxLayout()

            report_table = QTableWidget()
            report_table.setRowCount(len(rows))
            report_table.setColumnCount(2)
            report_table.setHorizontalHeaderLabels(["Пилот", "Часы налета"])
            for row_idx, row in enumerate(rows):
                report_table.setItem(row_idx, 0, QTableWidgetItem(str(row[0])))
                report_table.setItem(row_idx, 1, QTableWidgetItem(str(row[1])))
            layout.addWidget(report_table)

            bar_chart = pg.PlotWidget()
            bar_chart.setTitle("Налет по пилотам")
            bar_chart.setLabel('left', "Часы налета")
            bar_chart.setLabel('bottom', "Пилоты")
            bar_chart.showGrid(x=True, y=True)

            pilot_names = [str(row[0]) for row in rows]
            flight_hours = [row[1] for row in rows]
            x = list(range(len(pilot_names)))
            bg = pg.BarGraphItem(x=x, height=flight_hours, width=0.6, brush='skyblue')
            bar_chart.addItem(bg)

            axis = bar_chart.getAxis('bottom')
            axis.setTicks([list(zip(x, pilot_names))])

            layout.addWidget(bar_chart)
            self.report_window.setLayout(layout)
            self.report_window.resize(800, 600)
            self.report_window.show()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка при создании отчета", str(e))

        
    def report_pilots_with_expiring_contract(self):
        try:
            current_date = datetime.now()

            one_year_later = current_date + timedelta(days=365)

            query = """
                SELECT surname, contract_end
                FROM pilot
                WHERE contract_end >= %s AND contract_end <= %s
            """
            cursor = self.conn.cursor()
            cursor.execute(query, (current_date.date(), one_year_later.date()))
            pilots = cursor.fetchall()
            cursor.close()

            if not pilots:
                QMessageBox.information(self, "Отчет", "Нет пилотов, чьи контракты заканчиваются в течение года.")
                return

            self.report_window = QWidget()
            self.report_window.setWindowTitle("Отчет по пилотам с контрактами, заканчивающимися через год")
            layout = QVBoxLayout()

            report_table = QTableWidget()
            report_table.setRowCount(len(pilots))
            report_table.setColumnCount(2)
            report_table.setHorizontalHeaderLabels(["Фамилия", "Дата окончания контракта"])

            for row, pilot in enumerate(pilots):
                report_table.setItem(row, 0, QTableWidgetItem(pilot[0]))
                report_table.setItem(row, 1, QTableWidgetItem(pilot[1].strftime('%Y-%m-%d')))

            layout.addWidget(report_table)
            self.report_window.setLayout(layout)
            self.report_window.resize(600, 400)
            self.report_window.show()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка при создании отчета", str(e))

    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UserWindow()
    window.show()
    sys.exit(app.exec_())

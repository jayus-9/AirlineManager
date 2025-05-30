from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QApplication, QMessageBox, QLineEdit, QFormLayout, QScrollArea
)
from PyQt5.QtCore import Qt
import psycopg2
import sys

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


class AdminWindow(QWidget):
    def __init__(self, login_window=None):
        super().__init__()
        self.login_window = login_window
        self.setWindowTitle("Admin Interface")
        self.resize(1000, 600)

        self.conn = psycopg2.connect(
            dbname="airlines_db",
            user="postgres",
            password="1234",
            host="localhost",
            port="5432"
        )
        self.cur = self.conn.cursor()

        self.layout = QHBoxLayout(self)

        self.left_panel = QVBoxLayout()
        self.layout.addLayout(self.left_panel, stretch=1)

        self.right_panel = QVBoxLayout()
        self.layout.addLayout(self.right_panel, stretch=2)

        self.label = QLabel("Выберите таблицу для редактирования:")
        self.left_panel.addWidget(self.label)

        self.table_buttons = []
        for table_name in ["pilot", "airline", "plane", "country", "airport", "flight"]:
            btn = QPushButton(table_name.capitalize())
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda _, name=table_name: self.load_table(name))
            self.left_panel.addWidget(btn)
            self.table_buttons.append(btn)

        self.table = QTableWidget()
        self.table.itemSelectionChanged.connect(self.populate_edit_fields)
        self.right_panel.addWidget(self.table)

        self.edit_form = QFormLayout()
        self.edit_fields = {}
        self.edit_widget = QWidget()
        self.edit_widget.setLayout(self.edit_form)
        self.right_panel.addWidget(self.edit_widget)

        self.button_layout = QHBoxLayout()
        self.right_panel.addLayout(self.button_layout)

        self.add_btn = QPushButton("Добавить запись")
        self.add_btn.clicked.connect(self.add_record)
        self.button_layout.addWidget(self.add_btn)

        self.save_btn = QPushButton("Сохранить изменения")
        self.save_btn.clicked.connect(self.save_changes)
        self.button_layout.addWidget(self.save_btn)

        self.delete_btn = QPushButton("Удалить запись")
        self.delete_btn.clicked.connect(self.delete_record)
        self.button_layout.addWidget(self.delete_btn)

        self.logout_btn = QPushButton("Выход")
        self.logout_btn.clicked.connect(self.logout)
        self.button_layout.addWidget(self.logout_btn)
        
        self.current_table = None
        self.current_data = []

    def logout(self):
        self.login_window.show()
        self.close()

    def load_table(self, table_name):
        try:
            self.cur.execute(f"SELECT * FROM {table_name} ORDER BY id")
            records = self.cur.fetchall()
            colnames = [desc[0] for desc in self.cur.description]
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки", str(e))
            return

        self.table.setRowCount(len(records))
        self.table.setColumnCount(len(colnames))
        rus_colnames = [COLUMN_TRANSLATIONS.get(col, col) for col in colnames]
        self.table.setHorizontalHeaderLabels(rus_colnames)


        for row_idx, row_data in enumerate(records):
            for col_idx, value in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

        self.current_table = table_name
        self.current_data = colnames
        self.populate_edit_fields()

    def populate_edit_fields(self):
        for i in reversed(range(self.edit_form.rowCount())):
            self.edit_form.removeRow(i)
        self.edit_fields.clear()

        selected = self.table.currentRow()
        if selected == -1:
            return

        for col in range(self.table.columnCount()):
            original_col_name = self.current_data[col]

            if original_col_name.lower() == 'id':
                continue  

            label_text = COLUMN_TRANSLATIONS.get(original_col_name, original_col_name)

            value = self.table.item(selected, col).text()
            line_edit = QLineEdit(value)
            self.edit_form.addRow(QLabel(label_text), line_edit)

            self.edit_fields[original_col_name] = line_edit


    def save_changes(self):
        if self.current_table is None:
            return

        selected = self.table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Предупреждение", "Выберите строку для редактирования")
            return

        try:
            record_id = self.table.item(selected, 0).text()  

            set_clause = ", ".join([f"{key} = %s" for key in self.edit_fields.keys() if key.lower() != "id"])
            values = [field.text() for key, field in self.edit_fields.items() if key.lower() != "id"]

            query = f"UPDATE {self.current_table} SET {set_clause} WHERE id = %s"
            self.cur.execute(query, values + [record_id])
            self.conn.commit()

            self.load_table(self.current_table)
            self.table.selectRow(selected)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка при сохранении", str(e))
            self.conn.rollback()




    def delete_record(self):
        if self.current_table is None:
            return

        selected = self.table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Предупреждение", "Выберите строку для удаления")
            return

        try:
            record_id = self.table.item(selected, 0).text()
            self.cur.execute(f"DELETE FROM {self.current_table} WHERE id = %s", (record_id,))
            self.conn.commit()
            self.load_table(self.current_table)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка при удалении", str(e))
            self.conn.rollback()

    def add_record(self):
        if self.current_table is None:
            return

        try:
            fields = list(self.edit_fields.keys())
            if 'ID' in fields:
                fields.remove('ID')

            values = [self.edit_fields[key].text() for key in fields]
            placeholders = ", ".join(["%s"] * len(values))
            field_clause = ", ".join(fields)

            self.cur.execute(
                f"INSERT INTO {self.current_table} ({field_clause}) VALUES ({placeholders})",
                values
            )
            self.conn.commit()
            self.load_table(self.current_table)
            self.table.selectRow(self.table.rowCount() - 1)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка при добавлении", str(e))
            self.conn.rollback()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = AdminWindow()
    win.show()
    sys.exit(app.exec_())

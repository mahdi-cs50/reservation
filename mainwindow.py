import sys
import re
import sqlite3
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import Qt, QAbstractTableModel, QDate
from ui_form import Ui_MainWindow
from PySide6.QtCore import QTimer, QTime
import datetime

connect1 = sqlite3.connect("database.db")
cursor1 = connect1.cursor()

cursor1.execute(""" CREATE TABLE IF NOT EXISTS finance (Id INTEGER PRIMARY KEY AUTOINCREMENT, Bank_Name TEXT NOT NULL, Amount REAL NOT NULL, Date TEXT NOT NULL, Nec INTEGER NOT NULL, Done INTEGER NOT NULL DEFAULT 0)""")
connect1.commit()

connect2 = sqlite3.connect("banks.db")
cursor2 = connect2.cursor()

cursor2.execute(""" CREATE TABLE IF NOT EXISTS bank (Id INTEGER PRIMARY KEY AUTOINCREMENT, Bank_Name TEXT NOT NULL, Deposit REAL NOT NULL, Date TEXT NOT NULL, Gets_APR INTEGER NOT NULL, Rate REAL, Rate_Type TEXT, Days INTEGER)""")
connect2.commit()


class SQLiteTableModel(QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        self._data = data
        self._headers = headers

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return str(self._data[index.row()][index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._headers[section]
            else:
                return section + 1


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.add_income_expense_button.clicked.connect(self.goto_income_expense)
        self.ui.add_bank_account_button.clicked.connect(self.goto_bank_account)
        self.ui.back_to_summary_bank_account_button.clicked.connect(self.goto_summary)
        self.ui.back_to_summary_income_expense_button.clicked.connect(self.goto_summary)


        self.ui.add_record_button.clicked.connect(self.add_finance_record)
        self.ui.add_bank_button.clicked.connect(self.add_bank_record)
        self.ui.update_balances_button.clicked.connect(self.update_balances)
        self.ui.update_balances_button_income_expense.clicked.connect(self.update_balances)
        self.ui.delete_record_income_expense_button.clicked.connect(self.delete_finance_record)
        self.ui.delete_record_bank_button.clicked.connect(self.delete_bank_record)

        self.load_finance_data()
        self.load_bank_data()
        self.update_summary()
        self.load_banks_into_combobox()
        self.start_daily_check()

    def goto_income_expense(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.income_expense)

    def goto_bank_account(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.bank_account)

    def goto_summary(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.summary)

    def load_banks_into_combobox(self):
        try:
            conn = sqlite3.connect("banks.db")
            cur = conn.cursor()
            cur.execute("SELECT bank_name FROM bank")
            banks = cur.fetchall()
            conn.close()

            self.ui.bank_choose_field.clear()
            for bank in banks:
                self.ui.bank_choose_field.addItem(bank[0])
        except Exception as e:
            print("Error loading banks:", e)

    def load_finance_data(self):
        try:
            conn = sqlite3.connect("database.db")
            cur = conn.cursor()
            cur.execute("SELECT * FROM finance")
            rows = cur.fetchall()
            headers = [desc[0] for desc in cur.description]
            conn.close()

            model = SQLiteTableModel(rows, headers)
            self.ui.sql_tableview.setModel(model)
        except Exception as e:
            print("Error loading database.db:", e)

    def add_finance_record(self):
        amount_pattern = re.compile(r'^-?\d+(\.\d+)?$')
        #date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        #nec_pattern = re.compile(r'^(yes|no|y|n)$', re.IGNORECASE)

        amount = self.ui.amount_entry_field.text().strip()
        bank = self.ui.bank_choose_field.currentText()
        date = self.ui.date_selector_income_expense.date().toString("yyyy-MM-dd")
        necessity = 1 if self.ui.necessity_choose_field.currentText() == "Yes" else 0

        if not amount or not bank:
            QMessageBox.warning(self, "Error", "Please fill in all fields.")
            return
        if not amount_pattern.match(amount):
            QMessageBox.warning(self, "warning", "Invalid amount format! Please enter a number.")
            return
        try:
            amount = float(amount)
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter the amount as a number.")
            return
        if amount == 0:
            QMessageBox.warning(self, "warning", "Amount cannot be zero.")
            return

        try:
            connect1 = sqlite3.connect("database.db")
            cursor1 = connect1.cursor()
            cursor1.execute(""" CREATE TABLE IF NOT EXISTS finance (Id INTEGER PRIMARY KEY AUTOINCREMENT, Bank_Name TEXT NOT NULL, Amount REAL NOT NULL, Date TEXT NOT NULL, Nec INTEGER NOT NULL, Done INTEGER NOT NULL DEFAULT 0)""")
            cursor1.execute(""" INSERT INTO finance (Amount, Bank_Name, Date, Nec) VALUES (?, ?, ?, ?)""", (amount, bank, date, 1 if necessity else 0))
            connect1.commit()
            import calculate
            calculate.cal_bank()
            self.load_bank_data()
            connect1.close()

            self.load_finance_data()
            self.clear_inputs()
            self.update_summary()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))

    def delete_finance_record(self):
        amount_text = self.ui.amount_entry_field.text().strip()
        bank = self.ui.bank_choose_field.currentText()
        date = self.ui.date_selector_income_expense.date().toString("yyyy-MM-dd")

        if not amount_text or not bank:
            QMessageBox.warning(self, "Error", "To delete a record, please enter the bank, amount, and date.")
            return

        try:
            amount = float(amount_text)
        except ValueError:
            QMessageBox.warning(self, "Error", "Amount must be a number.")
            return

        try:
            conn = sqlite3.connect("database.db")
            cur = conn.cursor()

            cur.execute("""
                SELECT Id, Done FROM finance
                WHERE ABS(Amount - ?) < 0.0001 AND Bank_Name = ? AND Date = ?
                ORDER BY Id DESC LIMIT 1
            """, (amount, bank, date))
            record = cur.fetchone()

            if not record:
                QMessageBox.warning(self, "Not Found", "No record with these details was found.")
                conn.close()
                return

            record_id, done_status = record

            cur.execute("DELETE FROM finance WHERE Id = ?", (record_id,))
            conn.commit()
            conn.close()

            if done_status == 1:
                import calculate
                if hasattr(calculate, "undo_finance_effects"):
                    calculate.undo_finance_effects(bank, amount)
                QMessageBox.information(self, "Deleted", "Record deleted and bank changes have been reverted.")
            else:
                QMessageBox.information(self, "Deleted", "Record deleted (it was not applied).")

            self.load_finance_data()
            self.update_summary()

        except Exception as e:
            QMessageBox.critical(self, "Error deleting record", str(e))




    def clear_inputs(self):
        self.ui.amount_entry_field.clear()
        self.ui.bank_choose_field.setCurrentIndex(0)
        self.ui.necessity_choose_field.setCurrentIndex(0)
        self.ui.date_selector_income_expense.setDate(QDate.currentDate())


    #next_page


    def add_bank_record(self):
        bank_pattern = re.compile(r'^[A-Za-z ]+$')
        number_pattern = re.compile(r'^\d+(\.\d+)?$')
        #date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')

        name = self.ui.bank_name_entry_field.text().strip()
        deposit = self.ui.deposit_amount_entry_field.text().strip()
        date = self.ui.date_selector_bank.date().toString("yyyy-MM-dd")
        gets_apr = 1 if self.ui.yesradio.isChecked() else 0
        if gets_apr == 1:
            apr_rate = self.ui.apr_rate_entry_field.text().strip()
            apr_type = self.ui.apr_choose_field.currentText()
            days = self.ui.days_spinbox.value()
            if not number_pattern.match(apr_rate):
                QMessageBox.warning(self, "warning", "Invalid APR format! Please enter a number.")
                return
            try:
                apr_rate = float(apr_rate)
            except ValueError:
                QMessageBox.warning(self, "warning", "APR must be greater than zero.")
                return
            if apr_rate <= 0:
                QMessageBox.warning(self, "warning", "APR must be greater than zero.")
                return
            if days <= 0:
                QMessageBox.warning(self, "warning", "Days must be greater than zero.")
                return
        else:
            apr_rate = None
            apr_type = None
            days = None

        if not name or not deposit:
            QMessageBox.warning(self, "Error", "Bank name and deposit amount are required.")
            return
        if not bank_pattern.match(name):
            QMessageBox.warning(self, "warning", "Bank name can only contain letters and spaces.")
            return
        if not number_pattern.match(deposit):
            QMessageBox.warning(self, "warning", "Invalid amount format! Please enter a number.")
            return
        try:
            deposit = float(deposit)
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter the deposit amount as a number.")
            return
        if deposit <= 0:
            QMessageBox.warning(self, "warning", "Amount must be greater than zero.")
            return
        
        try:
            connect2 = sqlite3.connect("banks.db")
            cursor2 = connect2.cursor()
            cursor2.execute(""" CREATE TABLE IF NOT EXISTS bank (Id INTEGER PRIMARY KEY AUTOINCREMENT, Bank_Name TEXT NOT NULL, Deposit REAL NOT NULL, Date TEXT NOT NULL, Gets_APR INTEGER NOT NULL, Rate REAL, Rate_Type TEXT, Days INTEGER)""")
            cursor2.execute(""" INSERT INTO bank (Bank_Name, Deposit, Date, Gets_APR, Rate, Rate_Type, Days) VALUES (?, ?, ?, ?, ?, ?, ?)""", (name, deposit, date, 1 if gets_apr else 0, apr_rate, apr_type, days))
            connect2.commit()
            import calculate
            calculate.cal_rate()
            self.load_finance_data()
            connect2.close()

            self.load_bank_data()
            self.load_banks_into_combobox()
            self.clear_bank_inputs()
            self.update_summary()

        except Exception as e:
            QMessageBox.critical(self, "Error adding bank", str(e))

    def delete_bank_record(self):
        name = self.ui.bank_name_entry_field.text().strip()

        if not name:
            QMessageBox.warning(self, "Error", "Please enter or select the bank name.")
            return

        try:
            conn_bank = sqlite3.connect("banks.db")
            cur_bank = conn_bank.cursor()

            conn_finance = sqlite3.connect("database.db")
            cur_finance = conn_finance.cursor()

            cur_bank.execute("SELECT Id FROM bank WHERE Bank_Name = ?", (name,))
            bank_record = cur_bank.fetchone()

            if not bank_record:
                QMessageBox.warning(self, "Not Found", f"No bank named \"{name}\" exists in the database.")
                conn_bank.close()
                conn_finance.close()
                return

            cur_finance.execute("SELECT COUNT(*) FROM finance WHERE Bank_Name = ?", (name,))
            finance_count = cur_finance.fetchone()[0]

            msg = f"Are you sure you want to delete the bank \"{name}\"?"
            if finance_count > 0:
                msg += f"\n\n⚠️ Warning: {finance_count} related transaction(s) in the finance table will also be deleted."

            confirm = QMessageBox.question(
                self,
                "Confirm Delete Bank",
                msg,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if confirm == QMessageBox.No:
                conn_bank.close()
                conn_finance.close()
                return

            cur_bank.execute("DELETE FROM bank WHERE Bank_Name = ?", (name,))
            conn_bank.commit()

            if finance_count > 0:
                cur_finance.execute("DELETE FROM finance WHERE Bank_Name = ?", (name,))
                conn_finance.commit()

            conn_bank.close()
            conn_finance.close()

            QMessageBox.information(
                self,
                "Deleted",
                f"Bank \"{name}\" and all related transactions have been successfully deleted."
                if finance_count > 0
                else f"Bank \"{name}\" has been deleted successfully."
            )

            self.load_bank_data()
            self.load_banks_into_combobox()
            self.load_finance_data()
            self.update_summary()
            self.clear_bank_inputs()

        except Exception as e:
            QMessageBox.critical(self, "Error deleting bank", str(e))



    def load_bank_data(self):
        try:
            conn = sqlite3.connect("banks.db")
            cur = conn.cursor()
            cur.execute("SELECT * FROM bank")
            rows = cur.fetchall()
            headers = [desc[0] for desc in cur.description]
            conn.close()

            model = SQLiteTableModel(rows, headers)
            self.ui.bank_account_tableView.setModel(model)
        except Exception as e:
            print("Error loading banks.db:", e)

    def clear_bank_inputs(self):
        self.ui.bank_name_entry_field.clear()
        self.ui.deposit_amount_entry_field.clear()
        self.ui.apr_rate_entry_field.clear()
        self.ui.yesradio.setChecked(False)
        self.ui.noradio.setChecked(False)
        self.ui.apr_choose_field.setCurrentIndex(0)
        self.ui.days_spinbox.setValue(0)
        self.ui.date_selector_bank.setDate(QDate.currentDate())


    def update_summary(self):
        try:
            conn1 = sqlite3.connect("database.db")
            cur1 = conn1.cursor()
            cur1.execute("SELECT IFNULL(SUM(Amount), 0) FROM finance WHERE Amount > 0")
            total_income = cur1.fetchone()[0] or 0
            cur1.execute("SELECT IFNULL(SUM(ABS(Amount)), 0) FROM finance WHERE Amount < 0 AND Nec = 1")
            total_necessary_expense = cur1.fetchone()[0] or 0
            cur1.execute("SELECT IFNULL(SUM(ABS(Amount)), 0) FROM finance WHERE Amount < 0 AND Nec = 0")
            total_unnecessary_expense = cur1.fetchone()[0] or 0
            conn1.close()
            total_expense = total_necessary_expense + total_unnecessary_expense
            self.ui.total_revenue_number_output.setText(f"{total_income:,.0f} تومان")
            self.ui.total_necessary_spending_number_output.setText(f"{total_necessary_expense:,.0f} تومان")
            self.ui.total_unnecessary_spendingnumber_holder.setText(f"{total_unnecessary_expense:,.0f} تومان")
            self.ui.total_spending_number_holder.setText(f"{total_expense:,.0f} تومان")
        except Exception as e:
            print("Error updating Summary page:", e)



    def update_balances(self):
        try:
            import calculate
            calculate.check_income_expense()
            self.load_bank_data()
            self.load_finance_data()
            self.update_summary()
            QMessageBox.information(self, "Update Complete", "Accounts and transactions have been checked and updated successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error updating", str(e))

    def start_daily_check(self):
        self.run_daily_check(initial=True)

        now = QTime.currentTime()
        target_time = QTime(0, 0) 
        seconds_until_midnight = now.secsTo(target_time)
        if seconds_until_midnight <= 0:
            seconds_until_midnight += 24 * 3600

        QTimer.singleShot(seconds_until_midnight * 1000, self.run_daily_check)

    def run_daily_check(self, initial=False):
        try:
            import calculate
            calculate.check_income_expense()
            self.load_bank_data()
            self.load_finance_data()
            self.update_summary()

            if initial:
                print(f"[{datetime.datetime.now()}] Initial check completed (on startup).")
            else:
                print(f"[{datetime.datetime.now()}] Daily midnight check completed.")

        except Exception as e:
            print("Error checking transactions:", e)

        if not initial:
            QTimer.singleShot(24 * 3600 * 1000, self.run_daily_check)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

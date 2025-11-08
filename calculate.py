import sqlite3
from PySide6.QtWidgets import QMessageBox

connect1 = sqlite3.connect("database.db")
cursor1 = connect1.cursor()

cursor1.execute("SELECT Amount, Nec FROM finance")
amounts = [row for row in cursor1.fetchall()]

connect2 = sqlite3.connect("banks.db")
cursor2 = connect2.cursor()

cursor2.execute("SELECT * FROM bank")
rows2 = cursor2.fetchall()
columns2 = [description[0] for description in cursor2.description]

def arrange_income (amounts):
    Income = {"Necessary": [], "Not_Necessary": []}
    Expense = {"Necessary": [], "Not_Necessary": []}
    for amount, nec in amounts:
        if amount > 0:
            if nec == 1:
                Income["Necessary"].append(amount)
            else:
                Income["Not_Necessary"].append(amount)
        else:
            if nec == 1:
                Expense["Necessary"].append(amount)
            else:
                Expense["Not_Necessary"].append(amount)
    return Income, Expense



def arrange_banks (rows2, columns2):
    banks = {}
    for row in rows2:
        row_dict = dict(zip(columns2, row))
        row_id = row_dict['Id']
        banks[row_id] = row_dict
    return banks


def cal_income (data):
    result = {}
    for key, value in data.items():
        total = sum(value)
        avrage = total/len(value) if value else 0
        result[key] = {"total": total, "average": avrage}
    result["all"] = {
        "total": sum([sum(v) for v in data.values()]),
        "average": sum([sum(v) for v in data.values()]) / sum([len(v) for v in data.values()]) if sum([len(v) for v in data.values()]) > 0 else 0}
    return result


def cal_reserve(banks, Income_cal, Expense_cal):
    reserve = sum(row['Deposit'] for row in banks.values()) + Income_cal['all']['total'] + Expense_cal['all']['total']
    return reserve


def cal_bank ():
    from datetime import date
    today = date.today()

    cursor1.execute("SELECT Id, Amount, Bank_Name, Date FROM finance WHERE Done = 0 ORDER BY Id DESC LIMIT 1")
    last_row = cursor1.fetchone()
    if not last_row:
        print("هیچ تراکنشی در جدول وجود ندارد.")
        return
    
    Id, amount, bank_name, target_date_str = last_row
    target_date = date.fromisoformat(target_date_str)
    if today >= target_date:
        cursor2.execute("SELECT Deposit FROM bank WHERE Bank_Name = ?", (bank_name,))
        bank = cursor2.fetchone()
        if bank:
            new_deposit = bank[0] + amount
            if new_deposit >= 0:
                cursor2.execute("UPDATE bank SET Deposit = ? WHERE Bank_Name = ?", (new_deposit, bank_name))
                connect2.commit()
                cursor1.execute("UPDATE finance SET Done = 1 WHERE Amount = ? AND Date = ? AND Bank_name = ? AND Id = ?", (amount, target_date, bank_name, Id))
                connect1.commit()
                QMessageBox.information(None, "تغییر موجودی" ,f"موجودی {bank_name} به {new_deposit} در تاریخ {target_date} تغییر یافت")
            else:
                cursor1.execute("DELETE FROM finance WHERE Id = (SELECT Id FROM finance ORDER BY Id DESC LIMIT 1)")
                connect1.commit()
                QMessageBox.warning(None, "هشدار موجودی" ,"موجودی حساب کافی نیست")
        else:
            cursor1.execute("DELETE FROM finance WHERE Id = ?", (Id,))
            connect1.commit()
            QMessageBox.warning(None, "هشدار حساب", "بانک وجود ندارد")
    else:
        if amount < 0:
            QMessageBox.information(None, "هزینه جاری", f"هزینه با مقدار {abs(amount)} در بانک {bank_name} به معوقات در تاریخ {target_date} اضافه شد.")
        else:
            QMessageBox.information(None, "درآمد جاری", f"درآمد با مقدار {amount} در بانک {bank_name} به معوقات در تاریخ {target_date} اضافه شد.")
    check_income_expense()


def check_income_expense():
    from datetime import date

    cursor1.execute("SELECT Id, Amount, Bank_Name, Date FROM finance WHERE Done = 0")
    rows = cursor1.fetchall()
    if not rows:
        print("هیچ تراکنشی برای آپدیت در جدول وجود ندارد.")

    today = date.today()

    printed = False
    for row in rows:
        Id, amount, bank_name, target_date_str = row
        target_date = date.fromisoformat(target_date_str)

        if today >= target_date:
            cursor2.execute("SELECT Deposit FROM bank WHERE Bank_Name = ?", (bank_name,))
            bank = cursor2.fetchone()
            if bank:
                new_deposit = bank[0] + amount
                if new_deposit >= 0:
                    cursor2.execute("UPDATE bank SET Deposit = ? WHERE Bank_Name = ?", (new_deposit, bank_name))
                    connect2.commit()
                    cursor1.execute("UPDATE finance SET Done = 1 WHERE Amount = ? AND Date = ? AND Bank_name = ? AND Id = ?", (amount, target_date, bank_name, Id))
                    connect1.commit()
                    QMessageBox.information(None, "درآمد جاری", f"موجودی {bank_name} به {new_deposit} در تاریخ {target_date} تغییر یافت")
                else:
                    cursor1.execute("DELETE FROM finance WHERE Id = ?", (Id,))
                    connect1.commit()
                    QMessageBox.warning(None, "هشدار", "موجودی حساب کافی نیست")
            else:
                print("بانک وجود ندارد")
        #else:
            #if not printed:
                #print("تغییری در حساب داده نشد")
                #printed = True
            


def cal_rate():
    cursor2.execute(""" SELECT * FROM bank WHERE Id = (SELECT MAX(Id) FROM bank) AND Gets_APR = 1 """)
    row = cursor2.fetchone()
    if not row:
        print("بانک بانرخ سود در ردیف آخر وجود ندارد")
        QMessageBox.information(None, "ثبت شد" ,"حساب با موفقیت ثبت شد")
    else:
        Id, Bank_Name, Deposit, Date, Gets_APR, Rate, Rate_Type, Days = row
        if Rate_Type.lower() in ["a", "annually"]:
            if Days >= 365:
                profit_a = Deposit * (Rate/100)

                cursor1.execute("INSERT INTO finance (Bank_Name, Amount, Date, Nec, Done) VALUES (? , ?, Date(?, '+1 year'), 1, 0)", (Bank_Name, profit_a, Date))
                connect1.commit()
                QMessageBox.information(None, "سود جاری", f"سود حساب در بانک {Bank_Name} 365 روز دیگر به حسابتان واریز خواهد شد.")
            else:
                cursor2.execute("DELETE FROM bank WHERE Id = ?", (Id,))
                connect2.commit()
                QMessageBox.warning(None, "هشدار تعداد روز", "تعداد روز سپرده گذاری باید بیشتر از ۳۶۵ روز باشد")
        else:
            cursor2.execute("SELECT * FROM bank WHERE Gets_APR = 1 ORDER BY Id DESC LIMIT 1")
            row = cursor2.fetchone()

            Id, Bank_Name, Deposit, Date, Gets_APR, Rate, Rate_Type, Days = row

            profit_d = Deposit * (Rate / 100) / 365
            full_months = Days // 30
            extra_days = Days % 30

            for i in range(1, full_months + 1):
                profit_m = profit_d * 30
                cursor1.execute(""" INSERT INTO finance (Bank_Name, Amount, Date, Nec, Done) VALUES (?, ?, DATE(?, '+' || ? || ' days'), 1, 0) """, (Bank_Name, profit_m, Date, i * 30))

            if extra_days > 0:
                profit_extra = profit_d * extra_days
                cursor1.execute(""" INSERT INTO finance (Bank_Name, Amount, Date, Nec, Done) VALUES (?, ?, DATE(?, '+' || ? || ' days'), 1, 0) """, (Bank_Name, profit_extra, Date, full_months * 30 + extra_days))
            
            connect1.commit()
            QMessageBox.information(None, "سود جاری", f"سود حساب در بانک {Bank_Name} به مدت {Days} روز به صورت ماهانه واریز خواهد شد.")
            
    check_income_expense()


def undo_finance_effects(bank_name, amount):
    import sqlite3
    conn = sqlite3.connect("banks.db")
    cur = conn.cursor()
    cur.execute("UPDATE bank SET Deposit = Deposit - ? WHERE Bank_Name = ?", (amount, bank_name))
    conn.commit()
    conn.close()


Income , Expense = arrange_income(amounts)
Income_cal = cal_income(Income)
Expense_cal = cal_income(Expense)

banks = arrange_banks (rows2, columns2)
reserve = cal_reserve(banks, Income_cal, Expense_cal)


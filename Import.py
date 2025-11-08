import sqlite3
import schedule
import time
from data_collect import income_collect
from data_collect import bank_collect




connect1 = sqlite3.connect("database.db")
cursor1 = connect1.cursor()

cursor1.execute(""" CREATE TABLE IF NOT EXISTS finance (Id INTEGER PRIMARY KEY AUTOINCREMENT, Bank_Name TEXT NOT NULL, Amount REAL NOT NULL, Date TEXT NOT NULL, Nec INTEGER NOT NULL, Done INTEGER NOT NULL DEFAULT 0)""")
connect1.commit()

connect2 = sqlite3.connect("banks.db")
cursor2 = connect2.cursor()

cursor2.execute(""" CREATE TABLE IF NOT EXISTS bank (Id INTEGER PRIMARY KEY AUTOINCREMENT, Bank_Name TEXT NOT NULL, Deposit REAL NOT NULL, Date TEXT NOT NULL, Gets_APR INTEGER NOT NULL, Rate REAL, Rate_Type TEXT, Days INTEGER)""")
connect2.commit()


def Import_income_expense():
    Amount, name, Date, Nec = income_collect()
    cursor1.execute(""" INSERT INTO finance (Amount, Bank_Name, Date, Nec) VALUES (?, ?, ?, ?)""", (Amount, name, Date, 1 if Nec else 0))
    connect1.commit()
    #print("ثبت شد.")
    from calculate import cal_bank
    cal_bank ()

        

def Import_bank():
    Bank_Name, Deposit, Date, Gets_APR, Rate, Rate_Type, Days = bank_collect()
    cursor2.execute(""" INSERT INTO bank (Bank_Name, Deposit, Date, Gets_APR, Rate, Rate_Type, Days) VALUES (?, ?, ?, ?, ?, ?, ?)""", (Bank_Name, Deposit, Date, 1 if Gets_APR else 0, Rate, Rate_Type, Days))
    connect2.commit()
    #print("ثبت شد.")
    from calculate import cal_rate
    cal_rate()


#try:
    #Import_bank()
    #Import_income_expense()
#except Exception as e:
    #print("خطا:", e)


#schedule.every().day.at("00:00").do(check_income_expense)
#while True:
    #schedule.run_pending()
    #time.sleep(60)

connect1.close()
connect2.close()

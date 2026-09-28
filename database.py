import sqlite3

def create_database():
    connection = sqlite3.connect("bills.db")

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            bill_number TEXT,
            bill_date TEXT,
            total_amount REAL
        )
    """)

    connection.commit()
    connection.close()

def save_bill(filename, bill_number, bill_date, total_amount):
    connection = sqlite3.connect("bills.db")

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO bills (filename, bill_number, bill_date, total_amount)
        VALUES (?, ?, ?, ?)
    """, (filename, bill_number, bill_date, total_amount))

    connection.commit()
    connection.close()

def get_bills():
    connection = sqlite3.connect("bills.db")

    cursor = connection.cursor()

    cursor.execute("SELECT * FROM bills")

    bills = cursor.fetchall()

    connection.close()

    return bills

def add_expense(amount):
    connection = sqlite3.connect("bills.db")
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO bills(filename,total_amount)
        VALUES(?,?)
    """, ("manual", str(amount)))

    connection.commit()
    connection.close()

def clear_bills():
    connection = sqlite3.connect("bills.db")
    cursor = connection.cursor()

    cursor.execute("DELETE FROM bills")

    connection.commit()
    connection.close()
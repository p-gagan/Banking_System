# Import modules
import mysql.connector
from mysql.connector import Error
from bcrypt import hashpw, gensalt, checkpw
import random
import datetime
from dotenv import load_dotenv
import os

load_dotenv()

# Database setup and connection
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}
db_config1 = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

def setup_database():
    try:
        # Connect to MySQL server
        db = mysql.connector.connect(**db_config)

        cursor = db.cursor()

        # Create the database if it does not exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS banking_system")
        print("Database created or verified successfully.")
        db.commit()

        # Connect to the banking_system database
        db = mysql.connector.connect(**db_config1)
        cursor = db.cursor()

        # Create the users table
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                account_number VARCHAR(10) UNIQUE NOT NULL,
                dob DATE NOT NULL,
                city VARCHAR(50) NOT NULL,
                password VARCHAR(255) NOT NULL,
                balance FLOAT NOT NULL,
                contact_number VARCHAR(15) NOT NULL,
                email VARCHAR(100) NOT NULL,
                address VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE 
            )"""
        )

        # Create transactions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            account_number VARCHAR(10),
            transaction_type VARCHAR(10),
            amount FLOAT,
            date DATETIME,
            details VARCHAR(255),
            FOREIGN KEY (account_number) REFERENCES users(account_number)
        )
        """)
        db.commit()

        print("Users ans Transaction tables created or verified successfully.")
        db.commit()

        

    except Error as e:
        print(f"MySQL Error: {e}")

    finally:
        # Close the database connection
        if db.is_connected():
            cursor.close()
            db.close()
            print("Database connection closed.")
# Utility functions
def generate_account_number():
    return str(random.randint(1000000000, 9999999999))


def hash_password(password):
    return hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')


def validate_password(password, hashed):
    return checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def validate_email(email):
    if '@' not in email or '.' not in email:
        return False
    return True


# Banking operations
def add_user(cursor, db):
    name = input("Enter name: ")
    dob = input("Enter date of birth (YYYY-MM-DD): ")
    city = input("Enter city: ")
    password = input("Enter password: ")
    balance = float(input("Enter initial balance (minimum 2000): "))
    contact_number = input("Enter contact number: ")
    email = input("Enter email: ")
    address = input("Enter address: ")

    if balance < 2000:
        print("Initial balance must be at least 2000.")
        return
    if not validate_email(email):
        print("Invalid email format.")
        return

    account_number = generate_account_number()
    hashed_password = hash_password(password)

    try:
        cursor.execute("""
            INSERT INTO users (name, account_number, dob, city, password, balance, contact_number, email, address)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, account_number, dob, city, hashed_password, balance, contact_number, email, address))
        db.commit()
        print(f"User added successfully. Account number: {account_number}")
    except Exception as e:
        print(f"Error: {e}")


def show_user(cursor):
    account_number = input("Enter account number: ")
    cursor.execute("SELECT * FROM users WHERE account_number = %s", (account_number,))
    user = cursor.fetchone()
    if user:
        user.pop('password')  # Remove password for security
        for key, value in user.items():
            print(f"{key}: {value}")
    else:
        print("User not found.")


def login(cursor, db):
    account_number = input("Enter account number: ")
    password = input("Enter password: ")

    cursor.execute("SELECT * FROM users WHERE account_number = %s", (account_number,))
    user = cursor.fetchone()

    if user and validate_password(password, user['password']):
        print(f"Welcome, {user['name']}.")
        while True:
            print("""
            1. Show Balance
            2. Show Transactions
            3. Credit Amount
            4. Debit Amount
            5. Transfer Amount
            6. Change Password
            7. Update Profile
            8. Logout
            """)
            choice = input("Enter your choice: ")

            if choice == '1':
                print(f"Your balance is: {user['balance']}")
            elif choice == '2':
                show_transactions(cursor, account_number)
            elif choice == '3':
                credit_amount(cursor, db, account_number)
            elif choice == '4':
                debit_amount(cursor, db, account_number)
            elif choice == '5':
                transfer_amount(cursor, db, account_number)
            elif choice == '6':
                change_password(cursor, db, account_number)
            elif choice == '7':
                update_profile(cursor, db, account_number)
            elif choice == '8':
                print("Logged out successfully.")
                break
            else:
                print("Invalid choice.")
    else:
        print("Invalid credentials.")


def show_transactions(cursor, account_number):
    cursor.execute("SELECT * FROM transactions WHERE account_number = %s", (account_number,))
    transactions = cursor.fetchall()
    if transactions:
        for transaction in transactions:
            print(transaction)
    else:
        print("No transactions found.")


def credit_amount(cursor, db, account_number):
    amount = float(input("Enter amount to credit: "))
    cursor.execute("UPDATE users SET balance = balance + %s WHERE account_number = %s", (amount, account_number))
    cursor.execute("""
        INSERT INTO transactions (account_number, transaction_type, amount, date, details)
        VALUES (%s, 'Credit', %s, %s, 'Amount credited')
    """, (account_number, amount, datetime.datetime.now()))
    db.commit()
    print("Amount credited successfully.")


def debit_amount(cursor, db, account_number):
    amount = float(input("Enter amount to debit: "))
    cursor.execute("SELECT balance FROM users WHERE account_number = %s", (account_number,))
    user = cursor.fetchone()
    if user['balance'] < amount:
        print("Insufficient balance.")
        return
    cursor.execute("UPDATE users SET balance = balance - %s WHERE account_number = %s", (amount, account_number))
    cursor.execute("""
        INSERT INTO transactions (account_number, transaction_type, amount, date, details)
        VALUES (%s, 'Debit', %s, %s, 'Amount debited')
    """, (account_number, amount, datetime.datetime.now()))
    db.commit()
    print("Amount debited successfully.")


def transfer_amount(cursor, db, from_account):
    to_account = input("Enter recipient's account number: ")
    amount = float(input("Enter amount to transfer: "))
    cursor.execute("SELECT balance FROM users WHERE account_number = %s", (from_account,))
    from_user = cursor.fetchone()

    if from_user['balance'] < amount:
        print("Insufficient balance.")
        return

    cursor.execute("UPDATE users SET balance = balance - %s WHERE account_number = %s", (amount, from_account))
    cursor.execute("UPDATE users SET balance = balance + %s WHERE account_number = %s", (amount, to_account))
    cursor.execute("""
        INSERT INTO transactions (account_number, transaction_type, amount, date, details)
        VALUES (%s, 'Transfer', %s, %s, 'Transferred to %s')
    """, (from_account, amount, datetime.datetime.now(), to_account))
    cursor.execute("""
        INSERT INTO transactions (account_number, transaction_type, amount, date, details)
        VALUES (%s, 'Transfer', %s, %s, 'Received from %s')
    """, (to_account, amount, datetime.datetime.now(), from_account))
    db.commit()
    print("Transfer successful.")


def change_password(cursor, db, account_number):
    new_password = input("Enter new password: ")
    hashed_password = hash_password(new_password)
    cursor.execute("UPDATE users SET password = %s WHERE account_number = %s", (hashed_password, account_number))
    db.commit()
    print("Password updated successfully.")


def update_profile(cursor, db, account_number):
    name = input("Enter new name: ")
    city = input("Enter new city: ")
    contact_number = input("Enter new contact number: ")
    email = input("Enter new email: ")
    address = input("Enter new address: ")

    cursor.execute("""
        UPDATE users
        SET name = %s, city = %s, contact_number = %s, email = %s, address = %s
        WHERE account_number = %s
    """, (name, city, contact_number, email, address, account_number))
    db.commit()
    print("Profile updated successfully.")


# Main menu
def main():
    db, cursor = setup_database()

    while True:
        print("""
        1. Add User
        2. Show User
        3. Login
        4. Exit
        """)
        choice = input("Enter your choice: ")

        if choice == '1':
            add_user(cursor, db)
        elif choice == '2':
            show_user(cursor)
        elif choice == '3':
            login(cursor, db)
        elif choice == '4':
            print("Exiting the system.")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
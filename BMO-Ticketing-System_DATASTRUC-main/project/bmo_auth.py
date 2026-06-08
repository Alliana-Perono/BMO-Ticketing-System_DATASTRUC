'''
Program Name: bmo_auth.py
Program Description: This program handles user authentication for the BMO Sports Complex ticketing system. It allows users to register, login, and logout.
Programmer Name: Ello, Iligan, Ocier, Perono
Date: May 19, 2026
=====================================================================================================================================
                                                   History
=====================================================================================================================================
Date                                             Description                                        Programmer
------------------------------------------------------------------------------------------------------------------------------------
05/19/2026                               Initial implementation of ticketing system           Ello, Iligan, Ocier, Perono
'''
import csv
import os


def setup_users():
    """Creates the data folder and users.csv if missing"""
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists('data/users.csv'):
        with open('data/users.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['id_number', 'name', 'email', 'password', 'role'])
            writer.writerow(['ADMIN01', 'BMO Admin', 'admin@bmo.com', 'admin123', 'admin'])

    if not os.path.exists('data/tickets.csv'):
        with open('data/tickets.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Student Name', 'ID Number', 'Item Borrowed', 'Quantity', 'Status'])


class User:
    def __init__(self, id_number, name, email, role):
        self.id_number = id_number
        self.name = name
        self.email = email
        self.role = role


class AuthSystem:
    def __init__(self):
        self.users = []
        self.current_user = None
        setup_users()
        self.load_users()

    def load_users(self):
        self.users = []
        with open('data/users.csv', mode='r') as file:
            dict_reader = csv.DictReader(file)
            for row in dict_reader:
                self.users.append({
                    "id": row['id_number'],
                    "name": row['name'],
                    "email": row['email'],
                    "password": row['password'],
                    "role": row['role']
                })

    def register_user(self, id_number, name, email, password):
        for user in self.users:
            if user['id'] == id_number:
                print("\n❌ Error: This ID number is already registered.")
                return False

        with open('data/users.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            # Appending data matching the new CSV header layout
            writer.writerow([id_number, name, email, password, 'student'])

        print(f"\n✅ Registration successful! Welcome, {name}.")
        self.load_users()
        return True

    def login(self, id_number, password):
        for user in self.users:
            if user['id'] == id_number and user['password'] == password:
                self.current_user = User(user['id'], user['name'], user['email'], user['role'])
                print(f"\n✅ Welcome to the BMO Dashboard, {self.current_user.name}!")
                return True
        print("\n❌ Invalid credentials.")
        return False

    def logout(self):
        if self.current_user:
            print(f"\nLogging out... Goodbye, {self.current_user.name}!")
            self.current_user = None

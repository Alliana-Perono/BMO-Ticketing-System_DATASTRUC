'''
Program Name: bmo_main.py
Program Description: This program is a ticketing system for the BMO Sports Complex. It allows students to view available sports equipment, reserve items, and logs all transactions. Admins can manage inventory and process reservation requests using a queue data structure (FIFO). The system uses CSV files for data storage and includes user authentication.
Programmer Name: Ello, Iligan, Ocier, Perono
Date: May 18, 2026
=====================================================================================================================================
                                                   History
=====================================================================================================================================
Date                                             Description                                        Programmer
------------------------------------------------------------------------------------------------------------------------------------
05/18/2026                               Initial implementation of ticketing system           Ello, Iligan, Ocier, Perono
'''
import csv
import os

# ==========================================
# 1. AUTO-SETUP: CREATE FOLDERS AND CSV FILES
# ==========================================
def setup_files():
    if not os.path.exists('data'):
        os.makedirs('data')

    if not os.path.exists('data/users.csv'):
        with open('data/users.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['id_number', 'name', 'password', 'role'])
            writer.writerow(['ADMIN01', 'BMO Admin', 'admin123', 'admin'])

    if not os.path.exists('data/inventory.csv'):
        with open('data/inventory.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['item_id', 'item_name', 'total_stock', 'available_stock'])
            writer.writerows([
                ['101', 'Badminton Racket', 15, 15],
                ['102', 'Basketball', 10, 10],
                ['103', 'Volleyball', 8, 8]
            ])

    if not os.path.exists('data/tickets.csv'):
        with open('data/tickets.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Student Name', 'ID Number', 'Item Borrowed', 'Status'])


# ==========================================
# 2. DATA STRUCTURES & OOP (Chapters 2 & 5)
# ==========================================
class TicketQueue:
    def __init__(self):
        self.tickets = []

    def enqueue(self, ticket):
        self.tickets.append(ticket) # Adds to the back of the line

    def dequeue(self):
        if not self.is_empty():
            return self.tickets.pop(0) # Removes from the front of the line
        return None

    def is_empty(self):
        return len(self.tickets) == 0

class User:
    def __init__(self, id_number, name, role):
        self.id_number = id_number
        self.name = name
        self.role = role

class InventoryItem:
    def __init__(self, item_id, name, total_stock, available_stock):
        self.item_id = str(item_id)
        self.name = name
        self.total_stock = int(total_stock)
        self.available_stock = int(available_stock)

    def __str__(self):
        return f"[{self.item_id}] {self.name} - Available: {self.available_stock}/{self.total_stock}"


# ==========================================
# 3. CORE SYSTEM LOGIC
# ==========================================
class BMOSystem:
    def __init__(self):
        self.users = []
        self.inventory = []
        self.pending_tickets = TicketQueue() # Chapter 5 Queue!
        self.current_user = None
        
        self.load_users()
        self.load_inventory()

    # --- FILE HANDLING: LOADING DATA ---
    def load_users(self):
        self.users = []
        with open('data/users.csv', mode='r') as file:
            dict_reader = csv.DictReader(file)
            for row in dict_reader:
                self.users.append({
                    "id": row['id_number'], "name": row['name'],
                    "password": row['password'], "role": row['role']
                })

    def load_inventory(self):
        self.inventory = []
        with open('data/inventory.csv', mode='r') as file:
            dict_reader = csv.DictReader(file)
            for row in dict_reader:
                self.inventory.append(InventoryItem(
                    row['item_id'], row['item_name'], 
                    row['total_stock'], row['available_stock']
                ))

    # --- AUTHENTICATION ---
    def register_user(self, id_number, name, password):
        for user in self.users:
            if user['id'] == id_number:
                print("\n❌ Error: This ID number is already registered.")
                return
        with open('data/users.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([id_number, name, password, "student"])
        print(f"\n✅ Registration successful! Welcome, {name}.")
        self.load_users()

    def login(self, id_number, password):
        for user in self.users:
            if user['id'] == id_number and user['password'] == password:
                self.current_user = User(user['id'], user['name'], user['role'])
                print(f"\n✅ Welcome to the BMO Dashboard, {self.current_user.name}!")
                return True
        print("\n❌ Invalid credentials.")
        return False

    def logout(self):
        print(f"\nLogging out... Goodbye, {self.current_user.name}!")
        self.current_user = None

    # --- TICKETING & RESERVATION LOGIC ---
    def display_inventory(self):
        print("\n--- 🏀 AVAILABLE SPORTS EQUIPMENT 🏸 ---")
        for item in self.inventory:
            print(item)
        print("----------------------------------------")

    def reserve_item(self, item_id):
        """Student adds a request to the Queue"""
        for item in self.inventory:
            if item.item_id == str(item_id):
                if item.available_stock > 0:
                    # Create the ticket using the logged-in user's details
                    ticket = {
                        "student_name": self.current_user.name,
                        "student_id": self.current_user.id_number,
                        "item": item
                    }
                    self.pending_tickets.enqueue(ticket)
                    print(f"\n✅ Success! Your request for a {item.name} has been added to the waiting queue.")
                    print("An admin will process it shortly.")
                    return
                else:
                    print(f"\n❌ Sorry, {item.name} is completely out of stock right now.")
                    return
        print("\n❌ Item ID not found. Please check the inventory list and try again.")

    def update_inventory_file(self):
        """Rewrites the inventory file to save the new stock numbers"""
        with open('data/inventory.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['item_id', 'item_name', 'total_stock', 'available_stock'])
            for item in self.inventory:
                writer.writerow([item.item_id, item.name, item.total_stock, item.available_stock])

    def process_queue(self):
        """Admin processes all pending tickets (FIFO)"""
        if self.pending_tickets.is_empty():
            print("\n✅ The queue is empty! No pending requests.")
            return

        print("\n--- ⚙️ PROCESSING TICKETS... ---")
        while not self.pending_tickets.is_empty():
            # Get the oldest ticket
            ticket = self.pending_tickets.dequeue()
            item = ticket["item"]
            
            # Double check stock just in case
            if item.available_stock > 0:
                item.available_stock -= 1 # Deduct stock in memory
                
                # Append the approved ticket to the tickets.csv log
                with open('data/tickets.csv', mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([ticket["student_name"], ticket["student_id"], item.name, "BORROWED"])
                
                print(f"✔️  Approved: {ticket['student_name']} borrowed a {item.name}.")
            else:
                print(f"❌ Declined: {item.name} ran out of stock for {ticket['student_name']}.")
        
        # Save the updated stock numbers to the CSV
        self.update_inventory_file()
        print("---------------------------------")
        print("All pending tickets processed! Inventory has been updated.")


# ==========================================
# 4. MAIN PROGRAM LOOP (UI)
# ==========================================
if __name__ == '__main__':
    setup_files()
    app = BMOSystem()
    
    while True:
        # --- STATE 1: LOGGED OUT ---
        if app.current_user is None:
            print("\n=== 🏢 BMO TICKETING SYSTEM ===")
            print("1. Login")
            print("2. Register (Students)")
            print("3. Exit")
            choice = input("Select: ")
            
            if choice == '1':
                app.login(input("ID Number: "), input("Password: "))
            elif choice == '2':
                app.register_user(input("ID Number: "), input("Full Name: "), input("Password: "))
            elif choice == '3':
                break

        # --- STATE 2: STUDENT MENU ---
        elif app.current_user.role == 'student':
            print(f"\n=== 🎓 STUDENT MENU ({app.current_user.name}) ===")
            print("1. View Available Equipment")
            print("2. Borrow / Reserve an Item")
            print("3. Logout")
            choice = input("Select: ")
            
            if choice == '1':
                app.display_inventory()
            elif choice == '2':
                app.display_inventory()
                app.reserve_item(input("\nEnter the ID of the item you want: "))
            elif choice == '3':
                app.logout()

        # --- STATE 3: ADMIN MENU ---
        elif app.current_user.role == 'admin':
            print(f"\n=== 🛠️ ADMIN MENU ({app.current_user.name}) ===")
            print("1. View Inventory Stock")
            print("2. Process Pending Queue Requests")
            print("3. Logout")
            choice = input("Select: ")
            
            if choice == '1':
                app.display_inventory()
            elif choice == '2':
                app.process_queue()
            elif choice == '3':
                app.logout()

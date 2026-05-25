from flask import Flask, render_template, request, redirect, url_for
from bmo_auth import AuthSystem, setup_users
import csv
import os

app = Flask(__name__)
auth = AuthSystem()


def setup_files():
    setup_users()  # Trigger the auth files verification setup hook

    if not os.path.exists('data/inventory.csv'):
        with open('data/inventory.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['item_id', 'item_name', 'total_stock', 'available_stock'])
            writer.writerows([
                ['101', 'Badminton Racket', 15, 15],
                ['102', 'Basketball ball', 10, 10],
                ['103', 'Volleyball ball', 8, 8]
            ])


setup_files()


# HOME ROUTE
@app.route('/')
def home():
    return render_template('index.html')


# LOGIN ROUTE
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        id_number = request.form['id']
        password = request.form['password']

        auth.load_users()  # Refresh runtime authentication list cache

        if auth.login(id_number, password):
            if auth.current_user.role == 'student':
                return redirect(url_for('student'))
            elif auth.current_user.role == 'admin':
                return redirect(url_for('admin'))
        return "Invalid Credentials"
    return render_template('login.html')


# REGISTER ROUTE
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        id_number = request.form['id']
        name = request.form['name']
        email = request.form['email']  # Grabbing email from input field
        password = request.form['password']

        auth.load_users()
        # Hand down email variable parameter matching bmo_auth structure updates
        auth.register_user(id_number, name, email, password)
        return redirect(url_for('login'))
    return render_template('register.html')


# STUDENT DASHBOARD
@app.route('/student')
def student():
    if not auth.current_user:
        return redirect(url_for('login'))

    inventory = []
    with open('data/inventory.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            inventory.append(row)

    return render_template('student.html', inventory=inventory, user=auth.current_user)


# CONNECT STRINGS: PROCESS STUDENT ACTIONS INTO DATABASE
@app.route('/borrow', methods=['POST'])
def borrow_item():
    if not auth.current_user:
        return redirect(url_for('login'))

    item_id = request.form.get('item_id')
    quantity = request.form.get('quantity', 1)

    # Track down name string from item list
    item_name = "Unknown Equipment"
    with open('data/inventory.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['item_id'] == item_id:
                item_name = row['item_name']
                break

    # Write request line string with PENDING state to tickets.csv
    with open('data/tickets.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([auth.current_user.name, auth.current_user.id_number, item_name, quantity, "PENDING"])

    return redirect(url_for('student'))


# ADMIN INTERFACE PORTAL
@app.route('/admin')
def admin():
    if not auth.current_user or auth.current_user.role != 'admin':
        return redirect(url_for('login'))

    inventory = []
    with open('data/inventory.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            inventory.append(row)

    pending_requests = []
    knowledge_base = []

    if os.path.exists('data/tickets.csv'):
        with open('data/tickets.csv', 'r') as file:
            reader = csv.reader(file)
            next(reader, None)  # Skip line 1 schema definition keys

            for idx, row in enumerate(reader, start=1):
                if not row: continue
                ticket = {
                    "index": idx, "student_name": row[0], "student_id": row[1],
                    "item_name": row[2], "quantity": row[3], "status": row[4]
                }
                if row[4] == "PENDING":
                    pending_requests.append(ticket)
                else:
                    knowledge_base.append(ticket)

    return render_template('admin.html', inventory=inventory, pending=pending_requests, kb_logs=knowledge_base,
                           user=auth.current_user)


# ADMINISTRATIVE STATE WRITER
@app.route('/admin/action/<int:row_index>/<string:action>')
def admin_action(row_index, action):
    if not auth.current_user or auth.current_user.role != 'admin':
        return redirect(url_for('login'))

    with open('data/tickets.csv', 'r') as file:
        lines = list(csv.reader(file))

    target_row = lines[row_index]
    item_name = target_row[2]
    qty = int(target_row[3])

    if action == "approve":
        inv_data = []
        with open('data/inventory.csv', 'r') as file:
            reader = csv.reader(file)
            inv_data.append(next(reader))
            for row in reader:
                if row[1] == item_name:
                    row[3] = str(max(0, int(row[3]) - qty))  # Deduct matching units
                inv_data.append(row)
        with open('data/inventory.csv', 'w', newline='') as file:
            csv.writer(file).writerows(inv_data)
        lines[row_index][4] = "BORROWED"

    elif action == "decline":
        lines[row_index][4] = "DECLINED"

    elif action == "return":
        inv_data = []
        with open('data/inventory.csv', 'r') as file:
            reader = csv.reader(file)
            inv_data.append(next(reader))
            for row in reader:
                if row[1] == item_name:
                    row[3] = str(int(row[3]) + qty)  # Restock units back
                inv_data.append(row)
        with open('data/inventory.csv', 'w', newline='') as file:
            csv.writer(file).writerows(inv_data)
        lines[row_index][4] = "RETURNED"

    with open('data/tickets.csv', 'w', newline='') as file:
        csv.writer(file).writerows(lines)

    return redirect(url_for('admin'))


@app.route('/logout')
def logout():
    auth.logout()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
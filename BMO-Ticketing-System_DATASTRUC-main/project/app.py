from flask import Flask, render_template, request, redirect, url_for, session
from bmo_auth import AuthSystem, setup_users
import csv
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_me_in_production' 
auth = AuthSystem()

class SessionUser:
    def __init__(self, id_number, name, role):
        self.id_number = id_number
        self.name = name
        self.role = role

def get_current_user():
    """Retrieves the current user specific to the browser making the request."""
    if 'user_id' in session:
        return SessionUser(
            id_number=session['user_id'], 
            name=session['user_name'], 
            role=session['role']
        )
    return None

def setup_files():
    setup_users()
    if not os.path.exists('data/inventory.csv'):
        with open('data/inventory.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['item_id', 'item_name', 'total_stock', 'available_stock'])
            writer.writerows([
                ['101', 'Badminton Racket', 15, 15],
                ['102', 'Basketball', 10, 10],
                ['103', 'Volleyball', 8, 8]
            ])

setup_files()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        id_number = request.form['id']
        password = request.form['password']
        auth.load_users()

        if auth.login(id_number, password):
            session['user_id'] = auth.current_user.id_number
            session['user_name'] = auth.current_user.name
            session['role'] = auth.current_user.role

            if session['role'] == 'student':
                return redirect(url_for('student'))
            elif session['role'] == 'admin':
                return redirect(url_for('admin'))

        return "Invalid Credentials"

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        id_number = request.form['id']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        auth.load_users()
        auth.register_user(id_number, name, email, password)

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/student')
def student():
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))

    # Load inventory
    inventory = []
    with open('data/inventory.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            inventory.append(row)

    
    active_requests = []
    returned_items = []

    if os.path.exists('data/tickets.csv'):
        with open('data/tickets.csv', 'r') as file:
            reader = csv.reader(file)
            next(reader, None)

            for row in reader:
                if not row:
                    continue

                if row[1] == current_user.id_number:
                    data = {
                        "item_name": row[2],
                        "quantity": row[3],
                        "status": row[4]
                    }

                    if row[4] == "PENDING" or row[4] == "BORROWED":
                        active_requests.append(data)

                    elif row[4] == "RETURNED":
                        returned_items.append(data)

    return render_template(
        'student.html',
        inventory=inventory,
        user=current_user,
        requests=active_requests,
        returned_items=returned_items
    )


@app.route('/borrow', methods=['POST'])
def borrow_item():
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))

    item_id = request.form.get('item_id')
    quantity = request.form.get('quantity', 1)

    item_name = "Unknown Equipment"

    with open('data/inventory.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['item_id'] == item_id:
                item_name = row['item_name']
                break

    with open('data/tickets.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            current_user.name,
            current_user.id_number,
            item_name,
            quantity,
            "PENDING"
        ])

    return redirect(url_for('student'))


@app.route('/admin')
def admin():
    current_user = get_current_user()
    if not current_user or current_user.role != 'admin':
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
            next(reader, None)

            for idx, row in enumerate(reader, start=1):
                if not row:
                    continue

                ticket = {
                    "index": idx,
                    "student_name": row[0],
                    "student_id": row[1],
                    "item_name": row[2],
                    "quantity": row[3],
                    "status": row[4]
                }

                if row[4] == "PENDING":
                    pending_requests.append(ticket)
                else:
                    knowledge_base.append(ticket)

    return render_template(
        'admin.html',
        inventory=inventory,
        pending=pending_requests,
        kb_logs=knowledge_base,
        user=current_user
    )


@app.route('/admin/inventory/add', methods=['POST'])
def web_add_item():
    current_user = get_current_user()
    if not current_user or current_user.role != 'admin':
        return redirect(url_for('login'))

    item_id = request.form.get('item_id')
    item_name = request.form.get('item_name')
    total_stock = request.form.get('total_stock')

    with open('data/inventory.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([item_id, item_name, total_stock, total_stock])

    return redirect(url_for('admin'))


@app.route('/admin/inventory/update', methods=['POST'])
def web_update_item():
    current_user = get_current_user()
    if not current_user or current_user.role != 'admin':
        return redirect(url_for('login'))

    item_id = request.form.get('item_id')
    new_total = request.form.get('total_stock')
    new_avail = request.form.get('available_stock')

    updated_rows = []

    with open('data/inventory.csv', 'r') as file:
        reader = csv.reader(file)
        updated_rows.append(next(reader))

        for row in reader:
            if row[0] == item_id:
                row[2] = new_total
                row[3] = new_avail
            updated_rows.append(row)

    with open('data/inventory.csv', 'w', newline='') as file:
        csv.writer(file).writerows(updated_rows)

    return redirect(url_for('admin'))


@app.route('/admin/inventory/delete', methods=['POST'])
def web_delete_item():
    current_user = get_current_user()
    if not current_user or current_user.role != 'admin':
        return redirect(url_for('login'))

    item_id = request.form.get('item_id')

    updated_rows = []

    with open('data/inventory.csv', 'r') as file:
        reader = csv.reader(file)
        updated_rows.append(next(reader))

        for row in reader:
            if row[0] != item_id:
                updated_rows.append(row)

    with open('data/inventory.csv', 'w', newline='') as file:
        csv.writer(file).writerows(updated_rows)

    return redirect(url_for('admin'))


@app.route('/admin/action/<int:row_index>/<string:action>')
def admin_action(row_index, action):
    current_user = get_current_user()
    if not current_user or current_user.role != 'admin':
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
                    row[3] = str(max(0, int(row[3]) - qty))
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
                    row[3] = str(int(row[3]) + qty)
                inv_data.append(row)

        with open('data/inventory.csv', 'w', newline='') as file:
            csv.writer(file).writerows(inv_data)

        lines[row_index][4] = "RETURNED"

    with open('data/tickets.csv', 'w', newline='') as file:
        csv.writer(file).writerows(lines)

    return redirect(url_for('admin'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, request, jsonify, session, redirect
import json, os, hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'hardiduct_secret_2024'
DATA_FILE = 'data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "users": [
            {"id": 1, "name": "المدير", "email": "harditrade234@gmail.com",
             "password": hashlib.md5("harditradehardiduct1".encode()).hexdigest(),
             "role": "admin"},
            {"id": 2, "name": "المسؤول", "email": "supervisor@hardiduct.com",
             "password": hashlib.md5("supervisor123".encode()).hexdigest(),
             "role": "supervisor"}
        ],
        "customers": [],
        "orders": []
    }

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        d = request.json
        data = load_data()
        pwd = hashlib.md5(d['password'].encode()).hexdigest()
        user = next((u for u in data['users'] if u['email'] == d['email'] and u['password'] == pwd), None)
        if user:
            session['user'] = user
            return jsonify({'ok': True, 'role': user['role'], 'name': user['name']})
        return jsonify({'ok': False})
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/api/me')
def me():
    if 'user' not in session:
        return jsonify({'ok': False}), 401
    return jsonify(session['user'])

# ===== USERS =====
@app.route('/api/users', methods=['GET'])
def get_users():
    if session.get('user', {}).get('role') not in ['admin', 'supervisor']:
        return jsonify([])
    data = load_data()
    return jsonify([{k: v for k, v in u.items() if k != 'password'} for u in data['users']])

@app.route('/api/users', methods=['POST'])
def add_user():
    if session.get('user', {}).get('role') != 'admin':
        return jsonify({'ok': False})
    data = load_data()
    d = request.json
    new_id = max([u['id'] for u in data['users']], default=0) + 1
    data['users'].append({
        'id': new_id, 'name': d['name'], 'email': d['email'],
        'password': hashlib.md5(d['password'].encode()).hexdigest(),
        'role': d.get('role', 'employee')
    })
    save_data(data)
    return jsonify({'ok': True})

@app.route('/api/users/<int:uid>', methods=['PUT'])
def update_user(uid):
    if session.get('user', {}).get('role') != 'admin':
        return jsonify({'ok': False})
    data = load_data()
    d = request.json
    for u in data['users']:
        if u['id'] == uid:
            u['name'] = d.get('name', u['name'])
            u['email'] = d.get('email', u['email'])
            u['role'] = d.get('role', u['role'])
            if d.get('password'):
                u['password'] = hashlib.md5(d['password'].encode()).hexdigest()
            break
    save_data(data)
    return jsonify({'ok': True})

@app.route('/api/users/<int:uid>', methods=['DELETE'])
def delete_user(uid):
    if session.get('user', {}).get('role') != 'admin':
        return jsonify({'ok': False})
    data = load_data()
    data['users'] = [u for u in data['users'] if u['id'] != uid]
    save_data(data)
    return jsonify({'ok': True})

# ===== CUSTOMERS =====
@app.route('/api/customers', methods=['GET'])
def get_customers():
    if 'user' not in session:
        return jsonify([]), 401
    data = load_data()
    return jsonify(data['customers'])

@app.route('/api/customers', methods=['POST'])
def add_customer():
    if 'user' not in session:
        return jsonify({'ok': False}), 401
    data = load_data()
    d = request.json
    new_id = max([c['id'] for c in data['customers']], default=0) + 1
    data['customers'].append({
        'id': new_id, 'name': d['name'], 'phone': d['phone'],
        'paid': False, 'delivered': False, 'done': False,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'added_by': session['user']['name']
    })
    save_data(data)
    return jsonify({'ok': True})

@app.route('/api/customers/<int:cid>', methods=['PUT'])
def update_customer(cid):
    if 'user' not in session:
        return jsonify({'ok': False}), 401
    data = load_data()
    d = request.json
    for c in data['customers']:
        if c['id'] == cid:
            c.update(d)
            break
    save_data(data)
    return jsonify({'ok': True})

@app.route('/api/customers/<int:cid>', methods=['DELETE'])
def delete_customer(cid):
    if 'user' not in session:
        return jsonify({'ok': False}), 401
    data = load_data()
    data['customers'] = [c for c in data['customers'] if c['id'] != cid]
    save_data(data)
    return jsonify({'ok': True})

# ===== ORDERS =====
@app.route('/api/orders', methods=['GET'])
def get_orders():
    if 'user' not in session:
        return jsonify([]), 401
    data = load_data()
    return jsonify(data['orders'])

@app.route('/api/orders', methods=['POST'])
def add_order():
    if 'user' not in session:
        return jsonify({'ok': False}), 401
    data = load_data()
    d = request.json
    new_id = max([o['id'] for o in data['orders']], default=0) + 1
    qty = float(d.get('qty', 1))
    price = float(d.get('price', 0))
    data['orders'].append({
        'id': new_id, 'product': d['product'], 'customer': d['customer'],
        'qty': qty, 'price': price, 'total': qty * price,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'added_by': session['user']['name']
    })
    save_data(data)
    return jsonify({'ok': True})

@app.route('/api/orders/<int:oid>', methods=['DELETE'])
def delete_order(oid):
    if 'user' not in session:
        return jsonify({'ok': False}), 401
    data = load_data()
    data['orders'] = [o for o in data['orders'] if o['id'] != oid]
    save_data(data)
    return jsonify({'ok': True})

# ===== STATS =====
@app.route('/api/stats')
def stats():
    if 'user' not in session:
        return jsonify({}), 401
    data = load_data()
    customers = data['customers']
    orders = data['orders']
    return jsonify({
        'total_customers': len(customers),
        'paid': sum(1 for c in customers if c.get('paid')),
        'delivered': sum(1 for c in customers if c.get('delivered')),
        'done': sum(1 for c in customers if c.get('done')),
        'total_orders': len(orders),
        'total_revenue': sum(o.get('total', 0) for o in orders),
        'orders_by_product': _group_by(orders, 'product', 'total'),
    })

def _group_by(items, key, val):
    result = {}
    for item in items:
        k = item.get(key, 'أخرى')
        result[k] = result.get(k, 0) + item.get(val, 0)
    return result

if __name__ == '__main__':
    if not os.path.exists(DATA_FILE):
        save_data(load_data())
    print("\n✅ Hardi Duct يعمل!")
    print("📱 افتح المتصفح على: http://127.0.0.1:5000")
    print("📱 من الموبايل: http://<IP الحاسوب>:5000\n")
    app.run(debug=True, host='0.0.0.0', port=5000)

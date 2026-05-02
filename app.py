from flask import Flask, render_template, request, jsonify, session, redirect
from pymongo import MongoClient
from bson.objectid import ObjectId
import hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'hardiduct_secret_2024'

# ===== اتصال MongoDB =====
MONGO_URI = "mongodb+srv://newtexth_db_user:hGZq1ROdxxFTfRDV@hardiduct.atxmovk.mongodb.net/?appName=Hardiduct"
client = MongoClient(MONGO_URI)
db = client['hardiduct']

users_col = db['users']
customers_col = db['customers']
orders_col = db['orders']

def init_db():
    if users_col.count_documents({}) == 0:
        users_col.insert_many([
            {
                "name": "المدير",
                "email": "harditrade234@gmail.com",
                "password": hashlib.md5("harditradehardiduct1".encode()).hexdigest(),
                "role": "admin"
            },
            {
                "name": "المسؤول",
                "email": "supervisor@hardiduct.com",
                "password": hashlib.md5("supervisor123".encode()).hexdigest(),
                "role": "supervisor"
            }
        ])
        print("✅ تم إنشاء المستخدمين الافتراضيين")

def doc_to_dict(doc):
    if doc is None:
        return None
    doc['id'] = str(doc['_id'])
    del doc['_id']
    return doc

@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        d = request.json
        pwd = hashlib.md5(d['password'].encode()).hexdigest()
        user = users_col.find_one({'email': d['email'], 'password': pwd})
        if user:
            user_data = {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'role': user['role']
            }
            session['user'] = user_data
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
    users = list(users_col.find({}, {'password': 0}))
    return jsonify([doc_to_dict(u) for u in users])

@app.route('/api/users', methods=['POST'])
def add_user():
    if session.get('user', {}).get('role') != 'admin':
        return jsonify({'ok': False})
    d = request.json
    users_col.insert_one({
        'name': d['name'],
        'email': d['email'],
        'password': hashlib.md5(d['password'].encode()).hexdigest(),
        'role': d.get('role', 'employee')
    })
    return jsonify({'ok': True})

@app.route('/api/users/<uid>', methods=['PUT'])
def update_user(uid):
    if session.get('user', {}).get('role') != 'admin':
        return jsonify({'ok': False})
    d = request.json
    update = {
        'name': d.get('name'),
        'email': d.get('email'),
        'role': d.get('role')
    }
    if d.get('password'):
        update['password'] = hashlib.md5(d['password'].encode()).hexdigest()
    users_col.update_one({'_id': ObjectId(uid)}, {'$set': update})
    return jsonify({'ok': True})

@app.route('/api/users/<uid>', methods=['DELETE'])
def delete_user(uid):
    if session.get('user', {}).get('role') != 'admin':
        return jsonify({'ok': False})
    users_col.delete_one({'_id': ObjectId(uid)})
    return jsonify({'ok': True})

# ===== CUSTOMERS =====
@app.route('/api/customers', methods=['GET'])
def get_customers():
    if 'user' not in session:
        return jsonify([]), 401
    customers = list(customers_col.find())
    return jsonify([doc_to_dict(c) for c in customers])

@app.route('/api/customers', methods=['POST'])
def add_customer():
    if 'user' not in session:
        return jsonify({'ok': False}), 401
    d = request.json
    customers_col.insert_one({
        'name': d['name'],
        'phone': d['phone'],
        'arboon': d.get('arboon', 0),
        'baqui': d.get('baqui', 0),
        'delivered': False,
        'done': False,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'added_by': session['user']['name']
    })
    return jsonify({'ok': True})

@app.route('/api/customers/<cid>', methods=['PUT'])
def update_customer(cid):
    if 'user' not in session:
        return jsonify({'ok': False}), 401
    d = request.json
    customers_col.update_one({'_id': ObjectId(cid)}, {'$set': d})
    return jsonify({'ok': True})

@app.route('/api/customers/<cid>', methods=['DELETE'])
def delete_customer(cid):
    if 'user' not in session:
        return jsonify({'ok': False}), 401
    customers_col.delete_one({'_id': ObjectId(cid)})
    return jsonify({'ok': True})

# ===== ORDERS =====
@app.route('/api/orders', methods=['GET'])
def get_orders():
    if 'user' not in session:
        return jsonify([]), 401
    orders = list(orders_col.find())
    return jsonify([doc_to_dict(o) for o in orders])

@app.route('/api/orders', methods=['POST'])
def add_order():
    if 'user' not in session:
        return jsonify({'ok': False}), 401
    d = request.json
    qty = float(d.get('qty', 1))
    price = float(d.get('price', 0))
    orders_col.insert_one({
        'product': d['product'],
        'customer': d['customer'],
        'qty': qty,
        'price': price,
        'total': qty * price,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'added_by': session['user']['name']
    })
    return jsonify({'ok': True})

@app.route('/api/orders/<oid>', methods=['DELETE'])
def delete_order(oid):
    if 'user' not in session:
        return jsonify({'ok': False}), 401
    orders_col.delete_one({'_id': ObjectId(oid)})
    return jsonify({'ok': True})

# ===== STATS =====
@app.route('/api/stats')
def stats():
    if 'user' not in session:
        return jsonify({}), 401
    customers = list(customers_col.find())
    orders = list(orders_col.find())
    orders_by_product = {}
    for o in orders:
        k = o.get('product', 'أخرى')
        orders_by_product[k] = orders_by_product.get(k, 0) + o.get('total', 0)
    return jsonify({
        'total_customers': len(customers),
        'paid': sum(1 for c in customers if c.get('arboon', 0) > 0),
        'delivered': sum(1 for c in customers if c.get('delivered')),
        'done': sum(1 for c in customers if c.get('done')),
        'total_orders': len(orders),
        'total_revenue': sum(o.get('total', 0) for o in orders),
        'orders_by_product': orders_by_product,
    })

if __name__ == '__main__':
    init_db()
    print("\n✅ Hardi Duct يعمل مع MongoDB!")
    print("📱 افتح المتصفح على: http://127.0.0.1:5000\n")
    app.run(debug=True, host='0.0.0.0', port=5000)

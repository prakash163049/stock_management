from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from bson import ObjectId
from config import Config
import bcrypt
from datetime import datetime, timedelta

app = Flask(__name__)
app.config.from_object(Config)

# MongoDB setup
client = MongoClient('mongodb+srv://prakash:prakash16@cluster-personel.pcshs.mongodb.net/')
db = client['users']

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.user_data = user_data
        
    def get_id(self):
        return str(self.user_data['_id'])

@login_manager.user_loader
def load_user(user_id):
    user_data = db.users.find_one({'_id': ObjectId(user_id)})
    return User(user_data) if user_data else None

# Routes
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/inventory')
@login_required
def inventory():
    # Get all categories
    categories = db.products.distinct('category')
    
    # Get category filter
    selected_category = request.args.get('category', 'all')
    
    # Build query
    query = {}
    if selected_category != 'all':
        query['category'] = selected_category
    
    # Get inventory items with optional category filter
    inventory_items = list(db.products.find(query).sort('name', 1))
    
    # Get all active clients for the sale modal
    clients = list(db.clients.find({'status': 'Active'}).sort('name', 1))
    
    # Calculate category totals
    category_totals = {}
    for item in db.products.find():
        cat = item.get('category', 'Uncategorized')
        if cat not in category_totals:
            category_totals[cat] = {
                'count': 0,
                'total_quantity': 0,
                'total_value': 0
            }
        category_totals[cat]['count'] += 1
        category_totals[cat]['total_quantity'] += item.get('quantity', 0)
        category_totals[cat]['total_value'] += item.get('quantity', 0) * item.get('price', 0)
    
    return render_template('inventory.html',
                         inventory_items=inventory_items,
                         categories=categories,
                         selected_category=selected_category,
                         category_totals=category_totals,
                         clients=clients)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = db.users.find_one({'email': email})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            login_user(User(user))
            return redirect(url_for('index'))
        flash('Invalid email or password')
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if db.users.find_one({'email': email}):
            flash('Email already registered')
            return redirect(url_for('register'))
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user_data = {
            'email': email,
            'password': hashed_password,
            'role': 'user'
        }
        db.users.insert_one(user_data)
        flash('Registration successful')
        return redirect(url_for('login'))
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Product routes
@app.route('/products')
@login_required
def products():
    page = int(request.args.get('page', 1))
    per_page = app.config['ITEMS_PER_PAGE']
    skip = (page - 1) * per_page
    
    products = list(db.products.find().skip(skip).limit(per_page))
    total = db.products.count_documents({})
    
    return render_template('products/list.html', 
                         products=products,
                         page=page,
                         pages=(total + per_page - 1) // per_page)

@app.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        product_data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'quantity': int(request.form.get('quantity', 0)),
            'price': float(request.form.get('price', 0)),
            'category': request.form.get('category'),
            'supplier_name': request.form.get('supplier_name')
        }
        db.products.insert_one(product_data)
        flash('Product added successfully')
        return redirect(url_for('products'))
    return render_template('products/add.html')

@app.route('/products/<id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = db.products.find_one({'_id': ObjectId(id)})
    if not product:
        flash('Product not found')
        return redirect(url_for('products'))
    
    if request.method == 'POST':
        updated_data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'quantity': int(request.form.get('quantity', 0)),
            'price': float(request.form.get('price', 0)),
            'category': request.form.get('category'),
            'supplier_name': request.form.get('supplier_name')
        }
        db.products.update_one({'_id': ObjectId(id)}, {'$set': updated_data})
        flash('Product updated successfully')
        return redirect(url_for('products'))
    
    return render_template('products/edit.html', product=product)

@app.route('/products/<id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    result = db.products.delete_one({'_id': ObjectId(id)})
    if result.deleted_count:
        return jsonify({'success': True})
    return jsonify({'success': False}), 404

@app.route('/update_quantity', methods=['POST'])
@login_required
def update_quantity():
    data = request.get_json()
    product_id = data.get('product_id')
    new_quantity = data.get('quantity')
    change = data.get('change')
    
    if not product_id:
        return jsonify({'success': False, 'error': 'Missing product ID'})
    
    try:
        product = db.products.find_one({'_id': ObjectId(product_id)})
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'})
        
        # If change is provided, calculate new quantity based on change
        if change is not None:
            current_quantity = product.get('quantity', 0)
            new_quantity = max(0, current_quantity + change)
        # Otherwise use the provided new_quantity
        elif new_quantity is None:
            return jsonify({'success': False, 'error': 'Missing quantity data'})
        
        db.products.update_one(
            {'_id': ObjectId(product_id)},
            {'$set': {'quantity': new_quantity}}
        )
        
        return jsonify({
            'success': True,
            'new_quantity': new_quantity,
            'min_stock': product.get('min_stock', 0)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_category_stats')
@login_required
def get_category_stats():
    try:
        pipeline = [
            {
                '$group': {
                    '_id': '$category',
                    'count': {'$sum': 1},
                    'total_quantity': {'$sum': '$quantity'},
                    'total_value': {
                        '$sum': {'$multiply': ['$price', '$quantity']}
                    }
                }
            }
        ]
        
        stats = {}
        for result in db.products.aggregate(pipeline):
            category = result['_id']
            stats[category] = {
                'count': result['count'],
                'total_quantity': result['total_quantity'],
                'total_value': result['total_value']
            }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Client routes
@app.route('/clients')
@login_required
def clients():
    page = int(request.args.get('page', 1))
    per_page = app.config['ITEMS_PER_PAGE']
    skip = (page - 1) * per_page
    
    # Get clients with pagination
    clients_cursor = db.clients.find().skip(skip).limit(per_page)
    total = db.clients.count_documents({})
    
    # Calculate total orders and value for each client
    clients_list = []
    for client in clients_cursor:
        orders = list(db.orders.find({'client_id': client['_id']}))
        client['total_orders'] = len(orders)
        client['total_value'] = sum(order.get('total_value', 0) for order in orders)
        clients_list.append(client)
    
    return render_template('clients/list.html',
                         clients=clients_list,
                         page=page,
                         pages=(total + per_page - 1) // per_page)

@app.route('/clients/add', methods=['GET', 'POST'])
@login_required
def add_client():
    if request.method == 'POST':
        client_data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'address': request.form.get('address'),
            'status': request.form.get('status', 'Active')
        }
        db.clients.insert_one(client_data)
        flash('Client added successfully')
        return redirect(url_for('clients'))
    return render_template('clients/form.html')

@app.route('/clients/<id>')
@login_required
def view_client(id):
    client = db.clients.find_one({'_id': ObjectId(id)})
    if not client:
        flash('Client not found')
        return redirect(url_for('clients'))
    
    # Get client's sales history
    sales = list(db.sales.find({'client_id': ObjectId(id)}).sort('date', -1))
    
    # Calculate statistics
    total_value = sum(sale.get('total_value', 0) for sale in sales)
    average_value = total_value / len(sales) if sales else 0
    
    return render_template('clients/view.html',
                         client=client,
                         sales=sales,
                         total_value=total_value,
                         average_value=average_value)

@app.route('/clients/<id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(id):
    client = db.clients.find_one({'_id': ObjectId(id)})
    if not client:
        flash('Client not found')
        return redirect(url_for('clients'))
    
    if request.method == 'POST':
        updated_data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'address': request.form.get('address'),
            'status': request.form.get('status')
        }
        db.clients.update_one({'_id': ObjectId(id)}, {'$set': updated_data})
        flash('Client updated successfully')
        return redirect(url_for('view_client', id=id))
    
    return render_template('clients/form.html', client=client)

@app.route('/clients/<id>/delete', methods=['POST'])
@login_required
def delete_client(id):
    # Check if client has orders
    if db.orders.find_one({'client_id': ObjectId(id)}):
        return jsonify({
            'success': False,
            'error': 'Cannot delete client with existing orders'
        })
    
    result = db.clients.delete_one({'_id': ObjectId(id)})
    if result.deleted_count:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Client not found'})

@app.route('/make_sale', methods=['POST'])
@login_required
def make_sale():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 0))
    client_id = data.get('client_id')
    notes = data.get('notes', '')
    
    if not product_id or not quantity or not client_id:
        return jsonify({'success': False, 'error': 'Missing required data'})
    
    try:
        # Get product and client
        product = db.products.find_one({'_id': ObjectId(product_id)})
        client = db.clients.find_one({'_id': ObjectId(client_id)})
        
        if not product or not client:
            return jsonify({'success': False, 'error': 'Product or client not found'})
        
        current_quantity = product.get('quantity', 0)
        if current_quantity < quantity:
            return jsonify({'success': False, 'error': 'Insufficient stock'})
        
        # Calculate sale values
        unit_price = float(product.get('price', 0))
        total_value = quantity * unit_price
        
        # Update product quantity
        new_quantity = current_quantity - quantity
        db.products.update_one(
            {'_id': ObjectId(product_id)},
            {'$set': {'quantity': new_quantity}}
        )
        
        # Record the sale with all required fields
        sale_data = {
            'product_id': ObjectId(product_id),
            'client_id': ObjectId(client_id),
            'quantity': quantity,
            'unit_price': unit_price,
            'total_value': total_value,
            'notes': notes,
            'date': datetime.now(),
            'product_name': product.get('name', 'Unknown Product'),
            'client_name': client.get('name', 'Unknown Client')
        }
        db.sales.insert_one(sale_data)
        
        return jsonify({
            'success': True,
            'new_quantity': new_quantity
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/sales/history')
@login_required
def sales_history():
    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    client_id = request.args.get('client_id')
    
    # Build query
    query = {}
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        query['date'] = {'$gte': start}
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        if 'date' in query:
            query['date']['$lt'] = end
        else:
            query['date'] = {'$lt': end}
    if client_id and client_id != 'all':
        query['client_id'] = ObjectId(client_id)
    
    # Get sales with filters
    sales = list(db.sales.find(query).sort('date', -1))
    
    # Get all active clients for filter dropdown
    clients = list(db.clients.find({'status': 'Active'}).sort('name', 1))
    
    return render_template('sales/history.html',
                         sales=sales,
                         clients=clients)

if __name__ == '__main__':
    # Create indexes
    db.users.create_index('email', unique=True)
    db.products.create_index('name')
    db.clients.create_index('email', unique=True)
    db.clients.create_index([('name', 1)])
    db.sales.create_index('date')
    
    app.run(debug=True) 
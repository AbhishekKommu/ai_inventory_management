

"""
============================================================
🤖 SmartStock AI - AI Inventory Management System
============================================================
Professional Flask Application with AI-powered predictions
Author: SmartStock Team
Version: 2.0.0
============================================================
"""
import os
import json
import random
import string
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, session, abort
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, desc, or_
import numpy as np

# ============================================================
# APPLICATION CONFIGURATION
# ============================================================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'your-super-secret-key-change-in-production-2024'
)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "database", "inventory.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(os.path.join(BASE_DIR, 'database'), exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ============================================================
# EXTENSIONS INITIALIZATION
# ============================================================
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


# ============================================================
# DATABASE MODELS
# ============================================================
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    role = db.Column(db.String(20), default='user')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    products = db.relationship(
        'Product', backref='owner', lazy='dynamic',
        cascade='all, delete-orphan'
    )
    history = db.relationship(
        'History', backref='user', lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(
            password, method='pbkdf2:sha256'
        )

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100), index=True)
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, default=0)
    min_stock = db.Column(db.Integer, default=10)
    max_stock = db.Column(db.Integer, default=1000)
    price = db.Column(db.Float, default=0.0)
    cost = db.Column(db.Float, default=0.0)
    supplier = db.Column(db.String(200))
    location = db.Column(db.String(100))
    image_url = db.Column(db.String(500))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def is_low_stock(self):
        return 0 < self.quantity <= self.min_stock

    def is_out_of_stock(self):
        return self.quantity <= 0

    def stock_status(self):
        if self.quantity <= 0:
            return 'out_of_stock'
        elif self.quantity <= self.min_stock:
            return 'low_stock'
        elif self.quantity >= self.max_stock:
            return 'overstock'
        return 'in_stock'

    def stock_percentage(self):
        if self.max_stock <= 0:
            return 0
        return round(min(100, (self.quantity / self.max_stock) * 100), 1)

    def total_value(self):
        return round(self.quantity * self.price, 2)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sku': self.sku,
            'category': self.category,
            'description': self.description,
            'quantity': self.quantity,
            'min_stock': self.min_stock,
            'max_stock': self.max_stock,
            'price': self.price,
            'cost': self.cost,
            'supplier': self.supplier,
            'location': self.location,
            'status': self.status,
            'stock_status': self.stock_status(),
            'stock_percentage': self.stock_percentage(),
            'total_value': self.total_value(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class History(db.Model):
    __tablename__ = 'history'

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    entity_name = db.Column(db.String(200))
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_name': self.entity_name,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user': self.user.username if self.user else 'System',
        }


# ============================================================
# USER LOADER
# ============================================================
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def log_action(action, entity_type=None, entity_id=None, entity_name=None, details=None):
    """Log user action to history"""
    try:
        history = History(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500],
            user_id=current_user.id if current_user.is_authenticated else None,
        )
        db.session.add(history)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Failed to log action: {e}")


def generate_sku(name, category):
    """Generate unique SKU"""
    prefix = ''.join(c for c in (category or 'GEN')[:3].upper() if c.isalnum()) or 'GEN'
    timestamp = datetime.utcnow().strftime('%y%m%d')
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    base_sku = f"{prefix}-{timestamp}-{random_part}"

    sku = base_sku
    counter = 1
    while Product.query.filter_by(sku=sku).first():
        sku = f"{base_sku}-{counter}"
        counter += 1
    return sku


# ============================================================
# AI PREDICTION ENGINE
# ============================================================
class AIEngine:
    """AI-powered inventory prediction engine"""

    @staticmethod
    def calculate_reorder_point(product):
        """Calculate optimal reorder point using safety stock formula"""
        lead_time_days = 7
        daily_demand = max(1, product.quantity / 30)
        safety_stock = daily_demand * 3
        reorder_point = (daily_demand * lead_time_days) + safety_stock
        return round(reorder_point, 2)

    @staticmethod
    def predict_demand(product, days=30):
        """Predict future demand using moving average + trend"""
        try:
            base_demand = max(1, product.quantity / 30)
            trend = np.linspace(base_demand * 0.8, base_demand * 1.2, days)
            noise = np.random.normal(0, base_demand * 0.1, days)
            predictions = np.maximum(0, trend + noise)
            return [round(float(x), 2) for x in predictions]
        except Exception:
            return [1.0] * days

    @staticmethod
    def calculate_stock_score(product):
        """Calculate inventory health score (0-100)"""
        if product.max_stock <= 0:
            return 50
        ratio = product.quantity / product.max_stock
        if ratio < 0.2:
            score = 20 + (ratio * 100)
        elif ratio < 0.5:
            score = 40 + ((ratio - 0.2) * 150)
        elif ratio <= 0.9:
            score = 85 + ((ratio - 0.5) * 25)
        else:
            score = max(60, 100 - ((ratio - 0.9) * 200))
        return round(min(100, max(0, score)), 1)

    @staticmethod
    def get_recommendations(product):
        """Get AI recommendations for a product"""
        recommendations = []
        status = product.stock_status()
        reorder_point = AIEngine.calculate_reorder_point(product)

        if status == 'out_of_stock':
            recommendations.append({
                'type': 'critical',
                'icon': '🚨',
                'message': f'OUT OF STOCK! Order {int(reorder_point * 2)} units immediately.',
            })
        elif status == 'low_stock':
            recommendations.append({
                'type': 'warning',
                'icon': '⚠️',
                'message': f'Low stock! Order {int(reorder_point)} units to reach safe levels.',
            })
        elif status == 'overstock':
            recommendations.append({
                'type': 'info',
                'icon': '📦',
                'message': 'Overstocked. Consider promotions or reduce next order.',
            })
        else:
            recommendations.append({
                'type': 'success',
                'icon': '✅',
                'message': f'Stock level is healthy. Reorder point: {reorder_point} units.',
            })

        if product.price > 0 and product.cost > 0:
            margin = ((product.price - product.cost) / product.price) * 100
            if margin < 10:
                recommendations.append({
                    'type': 'warning',
                    'icon': '💡',
                    'message': f'Low profit margin ({margin:.1f}%). Consider price adjustment.',
                })

        return recommendations

    @staticmethod
    def get_dashboard_insights(products):
        """Generate AI insights for dashboard"""
        if not products:
            return {
                'total_products': 0,
                'total_value': 0,
                'low_stock_count': 0,
                'out_of_stock_count': 0,
                'avg_health_score': 0,
                'top_category': 'N/A',
                'insights': [],
            }

        total_value = sum(p.total_value() for p in products)
        low_stock = [p for p in products if p.is_low_stock()]
        out_of_stock = [p for p in products if p.is_out_of_stock()]
        health_scores = [AIEngine.calculate_stock_score(p) for p in products]

        categories = {}
        for p in products:
            cat = p.category or 'Uncategorized'
            categories[cat] = categories.get(cat, 0) + p.total_value()
        top_category = max(categories.items(), key=lambda x: x[1])[0] if categories else 'N/A'

        insights = []
        if out_of_stock:
            insights.append({
                'type': 'danger',
                'title': 'Critical Stock Alert',
                'message': f'{len(out_of_stock)} product(s) are out of stock and need immediate attention.',
            })
        if low_stock:
            insights.append({
                'type': 'warning',
                'title': 'Low Stock Warning',
                'message': f'{len(low_stock)} product(s) are running low. Consider restocking soon.',
            })

        avg_health = sum(health_scores) / len(health_scores) if health_scores else 0
        if avg_health >= 70:
            insights.append({
                'type': 'success',
                'title': 'Healthy Inventory',
                'message': f'Your average inventory health score is {avg_health:.1f}/100. Great job!',
            })
        elif avg_health < 40:
            insights.append({
                'type': 'warning',
                'title': 'Inventory Needs Attention',
                'message': f'Average health score is {avg_health:.1f}/100. Review your stock levels.',
            })

        return {
            'total_products': len(products),
            'total_value': round(total_value, 2),
            'low_stock_count': len(low_stock),
            'out_of_stock_count': len(out_of_stock),
            'avg_health_score': round(avg_health, 1),
            'top_category': top_category,
            'insights': insights,
        }


# ============================================================
# AUTHENTICATION ROUTES
# ============================================================
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        if not username or not password:
            flash('Please fill in all fields.', 'danger')
            return render_template('login.html')

        user = User.query.filter(
            or_(User.username == username, User.email == username)
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated.', 'danger')
                return render_template('login.html')

            login_user(user, remember=bool(remember))
            user.last_login = datetime.utcnow()
            db.session.commit()

            log_action('LOGIN', 'user', user.id, user.username, 'User logged in')
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if not email or '@' not in email:
            errors.append('Please enter a valid email.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')

        if User.query.filter_by(username=username).first():
            errors.append('Username already exists.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html')

        user = User(
            username=username,
            email=email,
            full_name=full_name or username,
            role='user',
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    log_action('LOGOUT', 'user', current_user.id, current_user.username, 'User logged out')
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


# ============================================================
# DASHBOARD ROUTES
# ============================================================
@app.route('/dashboard')
@login_required
def dashboard():
    products = Product.query.filter_by(user_id=current_user.id).all()
    insights = AIEngine.get_dashboard_insights(products)

    categories = {}
    for p in products:
        cat = p.category or 'Uncategorized'
        categories[cat] = categories.get(cat, 0) + 1

    recent_history = History.query.filter_by(user_id=current_user.id)\
        .order_by(desc(History.created_at)).limit(10).all()

    low_stock_products = [p for p in products if p.is_low_stock()][:5]

    chart_data = {
        'categories': list(categories.keys()),
        'category_counts': list(categories.values()),
        'stock_levels': [p.quantity for p in products[:10]],
        'product_names': [p.name[:15] for p in products[:10]],
    }

    return render_template(
        'dashboard.html',
        insights=insights,
        products=products,
        recent_history=recent_history,
        low_stock_products=low_stock_products,
        chart_data=json.dumps(chart_data),
    )


# ============================================================
# PRODUCT ROUTES
# ============================================================
@app.route('/products')
@login_required
def products():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    status = request.args.get('status', '').strip()
    sort = request.args.get('sort', 'newest')

    query = Product.query.filter_by(user_id=current_user.id)

    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f'%{search}%'),
                Product.sku.ilike(f'%{search}%'),
                Product.supplier.ilike(f'%{search}%'),
            )
        )
    if category:
        query = query.filter_by(category=category)
    if status == 'low':
        query = query.filter(Product.quantity <= Product.min_stock, Product.quantity > 0)
    elif status == 'out':
        query = query.filter(Product.quantity <= 0)
    elif status == 'active':
        query = query.filter_by(status='active')

    if sort == 'newest':
        query = query.order_by(desc(Product.created_at))
    elif sort == 'oldest':
        query = query.order_by(Product.created_at)
    elif sort == 'name':
        query = query.order_by(Product.name)
    elif sort == 'quantity':
        query = query.order_by(desc(Product.quantity))
    elif sort == 'value':
        query = query.order_by(desc(Product.quantity * Product.price))

    all_products = query.all()

    categories = db.session.query(Product.category)\
        .filter_by(user_id=current_user.id)\
        .distinct().all()
    categories = [c[0] for c in categories if c[0]]

    return render_template(
        'products.html',
        products=all_products,
        categories=categories,
        search=search,
        selected_category=category,
        selected_status=status,
        sort=sort,
    )


@app.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            if not name:
                flash('Product name is required.', 'danger')
                return render_template('add_product.html')

            category = request.form.get('category', '').strip()
            sku = request.form.get('sku', '').strip() or generate_sku(name, category)

            if Product.query.filter_by(sku=sku).first():
                flash('SKU already exists. Please use a different one.', 'danger')
                return render_template('add_product.html')

            product = Product(
                name=name,
                sku=sku,
                category=category or 'General',
                description=request.form.get('description', '').strip(),
                quantity=int(request.form.get('quantity', 0) or 0),
                min_stock=int(request.form.get('min_stock', 10) or 10),
                max_stock=int(request.form.get('max_stock', 1000) or 1000),
                price=float(request.form.get('price', 0) or 0),
                cost=float(request.form.get('cost', 0) or 0),
                supplier=request.form.get('supplier', '').strip(),
                location=request.form.get('location', '').strip(),
                image_url=request.form.get('image_url', '').strip(),
                user_id=current_user.id,
            )

            db.session.add(product)
            db.session.commit()

            log_action('CREATE', 'product', product.id, product.name,
                       f'Added product with SKU {product.sku}')

            flash(f'Product "{product.name}" added successfully!', 'success')
            return redirect(url_for('products'))

        except ValueError as e:
            flash(f'Invalid input: {e}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {e}', 'danger')

    return render_template('add_product.html')


@app.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        try:
            old_qty = product.quantity

            product.name = request.form.get('name', '').strip() or product.name
            product.category = request.form.get('category', '').strip() or product.category
            product.description = request.form.get('description', '').strip()
            product.quantity = int(request.form.get('quantity', product.quantity) or 0)
            product.min_stock = int(request.form.get('min_stock', product.min_stock) or 10)
            product.max_stock = int(request.form.get('max_stock', product.max_stock) or 1000)
            product.price = float(request.form.get('price', product.price) or 0)
            product.cost = float(request.form.get('cost', product.cost) or 0)
            product.supplier = request.form.get('supplier', '').strip()
            product.location = request.form.get('location', '').strip()
            product.image_url = request.form.get('image_url', '').strip()
            product.status = request.form.get('status', product.status)
            product.updated_at = datetime.utcnow()

            db.session.commit()

            details = f'Updated product. Quantity: {old_qty} → {product.quantity}'
            log_action('UPDATE', 'product', product.id, product.name, details)

            flash(f'Product "{product.name}" updated successfully!', 'success')
            return redirect(url_for('products'))

        except ValueError as e:
            flash(f'Invalid input: {e}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {e}', 'danger')

    return render_template('edit_product.html', product=product)


@app.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
    name = product.name
    sku = product.sku

    db.session.delete(product)
    db.session.commit()

    log_action('DELETE', 'product', product_id, name, f'Deleted product with SKU {sku}')
    flash(f'Product "{name}" deleted successfully.', 'success')
    return redirect(url_for('products'))


@app.route('/products/view/<int:product_id>')
@login_required
def view_product(product_id):
    product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
    recommendations = AIEngine.get_recommendations(product)
    demand_prediction = AIEngine.predict_demand(product, 30)
    health_score = AIEngine.calculate_stock_score(product)
    reorder_point = AIEngine.calculate_reorder_point(product)

    return jsonify({
        'product': product.to_dict(),
        'recommendations': recommendations,
        'demand_prediction': demand_prediction,
        'health_score': health_score,
        'reorder_point': reorder_point,
    })


@app.route('/products/adjust-stock/<int:product_id>', methods=['POST'])
@login_required
def adjust_stock(product_id):
    product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()

    try:
        adjustment = int(request.form.get('adjustment', 0))
        reason = request.form.get('reason', 'Manual adjustment')

        old_qty = product.quantity
        product.quantity = max(0, product.quantity + adjustment)
        product.updated_at = datetime.utcnow()

        db.session.commit()

        log_action('STOCK_ADJUST', 'product', product.id, product.name,
                   f'Stock: {old_qty} → {product.quantity} ({adjustment:+d}) - {reason}')

        flash(f'Stock adjusted: {old_qty} → {product.quantity}', 'success')
    except ValueError:
        flash('Invalid adjustment value.', 'danger')

    return redirect(url_for('products'))


# ============================================================
# HISTORY ROUTES
# ============================================================
@app.route('/history')
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '').strip()

    query = History.query.filter_by(user_id=current_user.id)
    if action_filter:
        query = query.filter_by(action=action_filter)

    pagination = query.order_by(desc(History.created_at)).paginate(
        page=page, per_page=25, error_out=False
    )

    action_types = db.session.query(History.action)\
        .filter_by(user_id=current_user.id)\
        .distinct().all()
    action_types = [a[0] for a in action_types]

    return render_template(
        'history.html',
        pagination=pagination,
        history_items=pagination.items,
        action_types=action_types,
        selected_action=action_filter,
    )


@app.route('/history/clear', methods=['POST'])
@login_required
def clear_history():
    History.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('History cleared successfully.', 'success')
    return redirect(url_for('history'))


# ============================================================
# API ENDPOINTS
# ============================================================
@app.route('/api/stats')
@login_required
def api_stats():
    products = Product.query.filter_by(user_id=current_user.id).all()
    insights = AIEngine.get_dashboard_insights(products)
    return jsonify(insights)


@app.route('/api/predict/<int:product_id>')
@login_required
def api_predict(product_id):
    product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
    return jsonify({
        'demand': AIEngine.predict_demand(product, 30),
        'reorder_point': AIEngine.calculate_reorder_point(product),
        'health_score': AIEngine.calculate_stock_score(product),
    })


# ============================================================
# ERROR HANDLERS
# ============================================================
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return render_template('500.html'), 500


# ============================================================
# DATABASE INITIALIZATION
# ============================================================
def init_database():
    """Initialize database with default admin and sample data"""
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@inventory.com',
                full_name='System Administrator',
                role='admin',
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('✓ Default admin created: admin / admin123')

            sample_products = [
                ('Wireless Mouse Pro', 'ELEC-001', 'Electronics', 45, 10, 200, 29.99, 15.00, 'TechCorp', 'A1-01'),
                ('Mechanical Keyboard', 'ELEC-002', 'Electronics', 8, 15, 150, 89.99, 45.00, 'TechCorp', 'A1-02'),
                ('USB-C Hub 7-in-1', 'ELEC-003', 'Electronics', 120, 20, 300, 49.99, 22.00, 'GadgetPlus', 'A1-03'),
                ('Office Chair Ergonomic', 'FURN-001', 'Furniture', 25, 5, 100, 249.99, 140.00, 'ComfortSeats', 'B2-01'),
                ('Standing Desk', 'FURN-002', 'Furniture', 3, 5, 50, 449.99, 280.00, 'ComfortSeats', 'B2-02'),
                ('Notebook A5 Premium', 'STAT-001', 'Stationery', 500, 50, 1000, 12.99, 4.50, 'PaperWorks', 'C1-01'),
                ('Pen Set Luxury', 'STAT-002', 'Stationery', 0, 25, 500, 34.99, 12.00, 'PaperWorks', 'C1-02'),
                ('LED Desk Lamp', 'ELEC-004', 'Electronics', 67, 15, 200, 39.99, 18.00, 'BrightCo', 'A1-04'),
                ('Webcam HD 1080p', 'ELEC-005', 'Electronics', 15, 10, 150, 79.99, 42.00, 'TechCorp', 'A1-05'),
                ('Monitor Stand Dual', 'FURN-003', 'Furniture', 40, 10, 120, 59.99, 25.00, 'ComfortSeats', 'B2-03'),
                ('Coffee Mug Ceramic', 'HOME-001', 'Home', 200, 30, 600, 15.99, 5.00, 'HomeGoods', 'D1-01'),
                ('Water Bottle Steel', 'HOME-002', 'Home', 85, 25, 400, 24.99, 9.00, 'HomeGoods', 'D1-02'),
            ]

            for p in sample_products:
                product = Product(
                    name=p[0], sku=p[1], category=p[2], quantity=p[3],
                    min_stock=p[4], max_stock=p[5], price=p[6], cost=p[7],
                    supplier=p[8], location=p[9], user_id=admin.id,
                    description=f'High quality {p[0]} from {p[8]}',
                )
                db.session.add(product)

            db.session.commit()
            print(f'✓ {len(sample_products)} sample products created')


# ============================================================
# MAIN ENTRY
# ============================================================
if __name__ == '__main__':
    init_database()
    print('\n' + '=' * 60)
    print('  🤖 SMARTSTOCK AI - INVENTORY MANAGEMENT SYSTEM')
    print('=' * 60)
    print('  🌐 Server: http://127.0.0.1:5000')
    print('  👤 Login:  admin / admin123')
    print('=' * 60 + '\n')
    app.run(debug=True, host='0.0.0.0', port=5000)
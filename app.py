from flask import Flask, render_template, request, jsonify 
import os
from supabase import create_client
from dotenv import load_dotenv
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import uuid
import jwt
from datetime import datetime, timedelta
from flask import send_from_directory


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('search_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a12345')  # Replace 'your-secret-key' with a secure key
app.config['JWT_EXPIRATION_DELTA'] = timedelta(days=7)  # Configure JWT expiration

@app.route('/')
def home():
    """Render the home page with search form"""
    # Fetch distinct categories for dropdown
    try:
        response = supabase.table('products')\
            .select('category')\
            .execute()
        categories = sorted(list(set(item['category'] for item in response.data)))
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        categories = []
    
    return render_template('index.html', categories=categories, suggestions=[])


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.template_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']
            name = request.form['name']
            
            # Check if user already exists
            existing_user = supabase.table('users')\
                .select('id')\
                .eq('email', email)\
                .execute()
            
            if existing_user.data:
                flash('Email already registered')
                return redirect(url_for('register'))
            
            # Create new user
            new_user = supabase.table('users')\
                .insert({
                    'email': email,
                    'password_hash': generate_password_hash(password),
                    'name': name
                })\
                .execute()
            
            # Create default wishlist for user
            supabase.table('wishlists')\
                .insert({
                    'user_id': new_user.data[0]['id'],
                    'name': 'My Wishlist'
                })\
                .execute()
            
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            flash('Registration failed')
            return redirect(url_for('register'))
            
    return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']
            
            # Get user from database
            user = supabase.table('users')\
                .select('*')\
                .eq('email', email)\
                .execute()
            
            if user.data and check_password_hash(user.data[0]['password_hash'], password):
                session['user_id'] = user.data[0]['id']
                return redirect(url_for('home'))
            else:
                flash('Invalid email or password')
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('Login failed')
            
    return render_template('login.html')

# User logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

# Wishlist routes
@app.route('/wishlist')
@login_required
def wishlist():
    try:
        # Get user's wishlist
        wishlist = supabase.table('wishlists')\
            .select('id, name')\
            .eq('user_id', session['user_id'])\
            .single()\
            .execute()
        
        # Get wishlist items with product details
        items = supabase.table('wishlist_items')\
            .select(
                'id, products(id, name, image_url, price_history!inner(price, recorded_date))'
            )\
            .eq('wishlist_id', wishlist.data['id'])\
            .execute()
        
        # Process items to get current prices
        wishlist_items = []
        total_price = 0
        
        for item in items.data:
            product = item['products']
            price_history = sorted(
                product['price_history'],
                key=lambda x: x['recorded_date'],
                reverse=True
            )
            current_price = price_history[0]['price'] if price_history else 0
            total_price += current_price
            
            wishlist_items.append({
                'id': item['id'],
                'product_id': product['id'],
                'name': product['name'],
                'image_url': product['image_url'],
                'current_price': current_price
            })
        
        return render_template(
            'wishlist.html',
            wishlist=wishlist.data,
            items=wishlist_items,
            total_price=total_price
        )
        
    except Exception as e:
        logger.error(f"Wishlist error: {str(e)}")
        flash('Error loading wishlist')
        return redirect(url_for('home'))

# Add item to wishlist
@app.route('/wishlist/add/<product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    try:
        # Get user's wishlist
        wishlist = supabase.table('wishlists')\
            .select('id')\
            .eq('user_id', session['user_id'])\
            .single()\
            .execute()
        
        # Add item to wishlist
        supabase.table('wishlist_items')\
            .insert({
                'wishlist_id': wishlist.data['id'],
                'product_id': product_id
            })\
            .execute()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Add to wishlist error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Remove item from wishlist
@app.route('/wishlist/remove/<item_id>', methods=['POST'])
@login_required
def remove_from_wishlist(item_id):
    try:
        supabase.table('wishlist_items')\
            .delete()\
            .eq('id', item_id)\
            .execute()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Remove from wishlist error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Route for About Us page
@app.route('/about')
def about():
    return render_template('about.html')

# Route for Contact Us page
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Route for Privacy Policy page
@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')


@app.route('/autocomplete')
def autocomplete():
    """Return autocomplete suggestions based on search query"""
    try:
        query = request.args.get('q', '').strip()
        response = supabase.table('products')\
            .select('name')\
            .ilike('name', f'%{query}%')\
            .limit(10)\
            .execute()
        suggestions = [item['name'] for item in response.data]
        return jsonify({'suggestions': suggestions})
    except Exception as e:
        logger.error(f"Error fetching autocomplete suggestions: {str(e)}")
        return jsonify({'suggestions': []}), 500

@app.route('/search')
def search():
    """Handle search requests"""
    try:
        # Get search parameters
        query = request.args.get('query', '').strip()
        
        # Build base query
        search_query = supabase.table('products')\
            .select(
                'id',
                'name',
                'category',
                'product_url',
                'image_url',
                'price_history!inner(price, recorded_date)',
                'count:price_history(id)'
            )
        
        # Apply filters
        if query:
            search_query = search_query.ilike('name', f'%{query}%')
        
        # Execute query
        response = search_query.execute()
        
        # Process results
        products = []
        for item in response.data:
            # Get latest price
            price_history = sorted(
                item['price_history'],
                key=lambda x: x['recorded_date'],
                reverse=True
            )
            current_price = price_history[0]['price'] if price_history else None
            
            # Calculate price trends
            if len(price_history) > 1:
                price_change = current_price - price_history[-1]['price']
                price_change_pct = (price_change / price_history[-1]['price']) * 100
            else:
                price_change = 0
                price_change_pct = 0
            
            products.append({
                'id': item['id'],
                'name': item['name'],
                'category': item['category'],
                'product_url': item['product_url'],
                'image_url': item['image_url'],
                'current_price': current_price,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'price_history_count': item['count']
            })
        
        return jsonify({
            'success': True,
            'products': products
        })
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/product/<int:product_id>/history')
def price_history(product_id):
    """Get price history for a specific product"""
    try:
        response = supabase.table('price_history')\
            .select('price', 'recorded_date')\
            .eq('product_id', product_id)\
            .order('recorded_date')\
            .execute()
        
        history = [{
            'price': item['price'],
            'date': item['recorded_date']
        } for item in response.data]
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        logger.error(f"Error fetching price history: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



    

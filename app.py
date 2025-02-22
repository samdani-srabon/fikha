from flask import Flask, render_template, request, jsonify
import os
from supabase import create_client
from dotenv import load_dotenv
import logging
from datetime import datetime

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
    

    
app.run(host="0.0.0.0",port=80)
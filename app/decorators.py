from functools import wraps
from flask import jsonify, session, redirect, request, url_for, flash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))  
        return f(*args, **kwargs)
    return decorated_function

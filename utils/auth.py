import sqlite3
import hashlib
import os
import secrets
from datetime import datetime

def hash_password(password, salt=None):
    """Hash a password with a salt for secure storage."""
    if salt is None:
        salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256(salt.encode() + password.encode())
    return hash_obj.hexdigest(), salt

def authenticate(username, password):
    """Authenticate a user with username and password."""
    conn = sqlite3.connect('community.db')
    cursor = conn.cursor()
    
    # Get user with matching username
    cursor.execute('SELECT id, username, password, role, salt FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    if user:
        user_id, username, stored_password, role, salt = user
        # Hash the provided password with the stored salt
        password_hash, _ = hash_password(password, salt)
        
        # Check if the hashed password matches
        if password_hash == stored_password:
            # Update last login timestamp
            cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                          (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))
            conn.commit()
            conn.close()
            return (user_id, username, password, role)
    
    conn.close()
    return None

def create_user(username, email, password, role="user"):
    """Create a new user account."""
    conn = sqlite3.connect('community.db')
    cursor = conn.cursor()
    
    # Check if username or email already exists
    cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
    if cursor.fetchone():
        conn.close()
        return False
    
    # Hash the password with a new salt
    password_hash, salt = hash_password(password)
    
    # Insert new user
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO users (username, email, password, salt, role, created_at, last_login)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (username, email, password_hash, salt, role, created_at, created_at))
    
    # Create empty profile for the user
    user_id = cursor.lastrowid
    cursor.execute('''
        INSERT INTO profiles (user_id, bio, interests)
        VALUES (?, ?, ?)
    ''', (user_id, "", ""))
    
    conn.commit()
    conn.close()
    return True

def is_admin(user_id):
    """Check if a user has admin role."""
    conn = sqlite3.connect('community.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user and user[0] == 'admin':
        return True
    return False

def get_user_profile(user_id):
    """Get a user's profile information."""
    conn = sqlite3.connect('community.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.username, u.email, p.bio, p.interests, p.photo_path
        FROM users u
        LEFT JOIN profiles p ON u.id = p.user_id
        WHERE u.id = ?
    ''', (user_id,))
    profile = cursor.fetchone()
    conn.close()
    
    return profile

def update_profile(user_id, bio, interests, photo_path=None):
    """Update a user's profile information."""
    conn = sqlite3.connect('community.db')
    cursor = conn.cursor()
    
    if photo_path:
        cursor.execute('''
            UPDATE profiles
            SET bio = ?, interests = ?, photo_path = ?
            WHERE user_id = ?
        ''', (bio, interests, photo_path, user_id))
    else:
        cursor.execute('''
            UPDATE profiles
            SET bio = ?, interests = ?
            WHERE user_id = ?
        ''', (bio, interests, user_id))
    
    conn.commit()
    conn.close()
    return True

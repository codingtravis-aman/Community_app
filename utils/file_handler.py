import os
import base64
import streamlit as st
from datetime import datetime
import sqlite3
from PIL import Image
import io

def save_uploaded_file(uploaded_file, directory='uploads', allowed_types=None):
    """
    Save an uploaded file to the specified directory.
    Returns the file path if successful, None otherwise.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Check file type if allowed_types is specified
    if allowed_types and uploaded_file.type.split('/')[1] not in allowed_types:
        return None
    
    # Create a unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{uploaded_file.name}"
    file_path = os.path.join(directory, filename)
    
    # Save the file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def get_image_base64(image_path):
    """
    Convert an image file to a base64 encoded string for displaying in HTML.
    Returns the base64 string if successful, None otherwise.
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return None

def save_profile_photo(user_id, uploaded_file):
    """
    Save a profile photo and update the user's profile.
    Returns True if successful, False otherwise.
    """
    if uploaded_file is None:
        return False
    
    # Validate file is an image
    if uploaded_file.type.split('/')[0] != 'image':
        st.error("Please upload an image file.")
        return False
    
    # Create uploads/profile_photos directory if it doesn't exist
    profile_dir = os.path.join('uploads', 'profile_photos')
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
    
    # Process the image - resize if needed
    try:
        img = Image.open(uploaded_file)
        # Resize to a reasonable profile picture size
        img = img.resize((300, 300))
        
        # Save the processed image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"profile_{user_id}_{timestamp}.jpg"
        file_path = os.path.join(profile_dir, filename)
        
        img.save(file_path, "JPEG")
        
        # Update the user's profile in the database
        conn = sqlite3.connect('community.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE profiles
            SET photo_path = ?
            WHERE user_id = ?
        ''', (file_path, user_id))
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return False

def save_resource_file(user_id, title, description, uploaded_file, resource_type):
    """
    Save a resource file and add it to the resources database.
    Returns True if successful, False otherwise.
    """
    if uploaded_file is None:
        return False
    
    # Create uploads/resources directory if it doesn't exist
    resource_dir = os.path.join('uploads', 'resources')
    if not os.path.exists(resource_dir):
        os.makedirs(resource_dir)
    
    # Save the file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{uploaded_file.name}"
    file_path = os.path.join(resource_dir, filename)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Add to database
    try:
        conn = sqlite3.connect('community.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO resources (user_id, title, description, resource_type, file_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, title, description, resource_type, file_path, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving resource to database: {e}")
        return False

def save_resource_link(user_id, title, description, url, resource_type='link'):
    """
    Save a resource link to the resources database.
    Returns True if successful, False otherwise.
    """
    try:
        conn = sqlite3.connect('community.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO resources (user_id, title, description, resource_type, url, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, title, description, resource_type, url, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving resource link to database: {e}")
        return False

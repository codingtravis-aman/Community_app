import streamlit as st
import sqlite3
from PIL import Image
import os
from utils.auth import get_user_profile, update_profile
from utils.file_handler import save_profile_photo

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None

def app():
    st.title("User Profile")
    
    if not st.session_state.authenticated:
        st.warning("Please login to view your profile.")
        st.stop()
    
    # Get user profile information
    profile = get_user_profile(st.session_state.user_id)
    
    if not profile:
        st.error("Error retrieving profile information.")
        return
    
    username, email, bio, interests, photo_path = profile
    
    # Display profile
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Profile Photo")
        if photo_path and os.path.exists(photo_path):
            try:
                img = Image.open(photo_path)
                st.image(img, width=200)
            except Exception as e:
                st.error(f"Error loading profile image: {e}")
                st.image("https://via.placeholder.com/200?text=No+Photo", width=200)
        else:
            st.image("https://via.placeholder.com/200?text=No+Photo", width=200)
        
        uploaded_file = st.file_uploader("Upload a new profile photo", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            if st.button("Save Photo"):
                if save_profile_photo(st.session_state.user_id, uploaded_file):
                    st.success("Profile photo updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to update profile photo.")
    
    with col2:
        st.subheader("Profile Information")
        st.write(f"**Username:** {username}")
        st.write(f"**Email:** {email}")
        
        # Profile editing form
        with st.form("profile_form"):
            new_bio = st.text_area("Bio", bio if bio else "", height=150)
            new_interests = st.text_area("Interests (comma separated)", interests if interests else "", height=100)
            
            submit = st.form_submit_button("Update Profile")
            
            if submit:
                if update_profile(st.session_state.user_id, new_bio, new_interests):
                    st.success("Profile updated successfully!")
                else:
                    st.error("Failed to update profile.")
    
    # Display user activity
    st.markdown("---")
    st.header("Your Activity")
    
    tab1, tab2, tab3 = st.tabs(["Discussions", "Events", "Resources"])
    
    with tab1:
        conn = sqlite3.connect('community.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, category, created_at 
            FROM discussions 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (st.session_state.user_id,))
        discussions = cursor.fetchall()
        
        if discussions:
            for disc in discussions:
                st.write(f"**{disc[1]}** - {disc[2]} - {disc[3][:10]}")
        else:
            st.info("You haven't started any discussions yet.")
        conn.close()
    
    with tab2:
        conn = sqlite3.connect('community.db')
        cursor = conn.cursor()
        
        # Events created by user
        st.subheader("Events You Created")
        cursor.execute("""
            SELECT id, title, event_date, location 
            FROM events 
            WHERE user_id = ? 
            ORDER BY event_date DESC
        """, (st.session_state.user_id,))
        created_events = cursor.fetchall()
        
        if created_events:
            for event in created_events:
                st.write(f"**{event[1]}** on {event[2]} at {event[3]}")
        else:
            st.info("You haven't created any events yet.")
        
        # Events user is attending
        st.subheader("Events You're Attending")
        cursor.execute("""
            SELECT e.id, e.title, e.event_date, e.location 
            FROM events e
            JOIN rsvps r ON e.id = r.event_id
            WHERE r.user_id = ? AND r.status = 'attending'
            ORDER BY e.event_date DESC
        """, (st.session_state.user_id,))
        attending_events = cursor.fetchall()
        
        if attending_events:
            for event in attending_events:
                st.write(f"**{event[1]}** on {event[2]} at {event[3]}")
        else:
            st.info("You haven't RSVP'd to any events yet.")
        
        conn.close()
    
    with tab3:
        conn = sqlite3.connect('community.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, resource_type, created_at 
            FROM resources 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (st.session_state.user_id,))
        resources = cursor.fetchall()
        
        if resources:
            for res in resources:
                st.write(f"**{res[1]}** - {res[2]} - {res[3][:10]}")
        else:
            st.info("You haven't shared any resources yet.")
        conn.close()

if __name__ == "__main__":
    app()

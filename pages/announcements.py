import streamlit as st
import sqlite3
from datetime import datetime
from utils.auth import is_admin

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
    st.title("Community Announcements")
    
    if not st.session_state.authenticated:
        st.warning("Please login to view announcements.")
        st.stop()
    
    # Sidebar filters
    st.sidebar.subheader("Filter Announcements")
    
    # Date filter
    time_filter = st.sidebar.selectbox(
        "Time Period", 
        ["All Time", "Today", "This Week", "This Month"]
    )
    
    # Main content
    tab1, tab2 = st.tabs(["View Announcements", "Create Announcement"])
    
    with tab1:
        # Construct the query based on filters
        query = """
            SELECT a.id, a.title, a.content, a.created_at, u.username
            FROM announcements a
            JOIN users u ON a.user_id = u.id
        """
        
        # Add WHERE clauses for time filter
        params = []
        
        if time_filter != "All Time":
            today = datetime.now().strftime('%Y-%m-%d')
            if time_filter == "Today":
                query += " WHERE date(a.created_at) = ?"
                params.append(today)
            elif time_filter == "This Week":
                query += " WHERE date(a.created_at) >= date(?, '-7 days')"
                params.append(today)
            elif time_filter == "This Month":
                query += " WHERE date(a.created_at) >= date(?, '-30 days')"
                params.append(today)
        
        # Order by most recent first
        query += " ORDER BY a.created_at DESC"
        
        # Execute query and display results
        conn = sqlite3.connect('community.db')
        cursor = conn.cursor()
        cursor.execute(query, params)
        announcements = cursor.fetchall()
        conn.close()
        
        if not announcements:
            st.info("No announcements found for the selected time period.")
        else:
            for announce in announcements:
                announce_id, title, content, created_at, username = announce
                
                with st.expander(f"{title} - Posted by {username} on {created_at[:10]}"):
                    st.write(content)
                    
                    # Only show delete button for admins
                    if is_admin(st.session_state.user_id):
                        if st.button("Delete Announcement", key=f"delete_{announce_id}"):
                            conn = sqlite3.connect('community.db')
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM announcements WHERE id = ?", (announce_id,))
                            conn.commit()
                            conn.close()
                            st.success("Announcement deleted.")
                            st.rerun()
    
    with tab2:
        # Only admins can create announcements
        if not is_admin(st.session_state.user_id):
            st.info("Only administrators can create announcements.")
        else:
            st.subheader("Create a New Announcement")
            
            with st.form("create_announcement_form", clear_on_submit=True):
                title = st.text_input("Title")
                content = st.text_area("Content", height=200)
                
                submit = st.form_submit_button("Post Announcement")
                
                if submit:
                    if title and content:
                        try:
                            conn = sqlite3.connect('community.db')
                            cursor = conn.cursor()
                            
                            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            cursor.execute("""
                                INSERT INTO announcements (user_id, title, content, created_at)
                                VALUES (?, ?, ?, ?)
                            """, (st.session_state.user_id, title, content, now))
                            
                            conn.commit()
                            conn.close()
                            
                            st.success("Announcement posted successfully!")
                            # Clear form and refresh
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error posting announcement: {e}")
                    else:
                        st.warning("Please fill in all fields.")

if __name__ == "__main__":
    app()

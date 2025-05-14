import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from utils.auth import is_admin, hash_password

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
    st.title("Admin Dashboard")
    
    if not st.session_state.authenticated:
        st.warning("Please login to access this page.")
        st.stop()
    
    # Check if user is admin
    if not is_admin(st.session_state.user_id):
        st.error("You don't have permission to access this page.")
        st.stop()
    
    # Admin dashboard with tabs for different management areas
    tab1, tab2, tab3 = st.tabs(["User Management", "Content Management", "Site Settings"])
    
    with tab1:
        st.subheader("User Management")
        
        # Get all users
        conn = sqlite3.connect('community.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.username, u.email, u.role, u.created_at, u.last_login,
                   (SELECT COUNT(*) FROM discussions WHERE user_id = u.id) as discussion_count,
                   (SELECT COUNT(*) FROM comments WHERE user_id = u.id) as comment_count,
                   (SELECT COUNT(*) FROM resources WHERE user_id = u.id) as resource_count
            FROM users u
            ORDER BY u.username
        """)
        users = cursor.fetchall()
        
        # Convert to DataFrame for better display
        users_df = pd.DataFrame(users, columns=[
            'ID', 'Username', 'Email', 'Role', 'Created At', 'Last Login',
            'Discussions', 'Comments', 'Resources'
        ])
        
        st.write(users_df)
        
        # User actions
        st.markdown("---")
        st.subheader("User Actions")
        
        action = st.selectbox(
            "Select Action",
            ["Create New User", "Edit User Role", "Reset User Password", "Delete User"]
        )
        
        if action == "Create New User":
            with st.form("create_user_form"):
                new_username = st.text_input("Username")
                new_email = st.text_input("Email")
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Role", ["user", "admin"])
                
                submit = st.form_submit_button("Create User")
                
                if submit:
                    if new_username and new_email and new_password:
                        try:
                            # Check if username or email already exists
                            cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", 
                                          (new_username, new_email))
                            if cursor.fetchone():
                                st.error("Username or email already exists.")
                            else:
                                # Create new user
                                password_hash, salt = hash_password(new_password)
                                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                
                                cursor.execute("""
                                    INSERT INTO users (username, email, password, salt, role, created_at, last_login)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (new_username, new_email, password_hash, salt, new_role, now, now))
                                
                                user_id = cursor.lastrowid
                                cursor.execute("""
                                    INSERT INTO profiles (user_id, bio, interests)
                                    VALUES (?, ?, ?)
                                """, (user_id, "", ""))
                                
                                conn.commit()
                                st.success(f"User '{new_username}' created successfully!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error creating user: {e}")
                    else:
                        st.warning("Please fill in all fields.")
        
        elif action == "Edit User Role":
            user_to_edit = st.selectbox(
                "Select User",
                users_df[['ID', 'Username']].values.tolist(),
                format_func=lambda x: f"{x[1]} (ID: {x[0]})"
            )
            
            new_role = st.selectbox("New Role", ["user", "admin"])
            
            if st.button("Update Role"):
                try:
                    cursor.execute("UPDATE users SET role = ? WHERE id = ?", 
                                  (new_role, user_to_edit[0]))
                    conn.commit()
                    st.success(f"Role updated for {user_to_edit[1]}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating role: {e}")
        
        elif action == "Reset User Password":
            user_to_reset = st.selectbox(
                "Select User",
                users_df[['ID', 'Username']].values.tolist(),
                format_func=lambda x: f"{x[1]} (ID: {x[0]})",
                key="reset_password_user"
            )
            
            new_password = st.text_input("New Password", type="password")
            
            if st.button("Reset Password"):
                if new_password:
                    try:
                        password_hash, salt = hash_password(new_password)
                        
                        cursor.execute("""
                            UPDATE users 
                            SET password = ?, salt = ? 
                            WHERE id = ?
                        """, (password_hash, salt, user_to_reset[0]))
                        
                        conn.commit()
                        st.success(f"Password reset for {user_to_reset[1]}!")
                    except Exception as e:
                        st.error(f"Error resetting password: {e}")
                else:
                    st.warning("Please enter a new password.")
        
        elif action == "Delete User":
            user_to_delete = st.selectbox(
                "Select User",
                users_df[['ID', 'Username']].values.tolist(),
                format_func=lambda x: f"{x[1]} (ID: {x[0]})",
                key="delete_user"
            )
            
            st.warning(f"Deleting a user will also delete all their content, including discussions, comments, resources, and events!")
            
            if st.button("Delete User", key="confirm_delete_user"):
                try:
                    # Start a transaction
                    cursor.execute("BEGIN TRANSACTION")
                    
                    # Delete all user data
                    tables = [
                        "comments", "discussions", "events", "messages", 
                        "profiles", "resources", "rsvps", "announcements"
                    ]
                    
                    for table in tables:
                        try:
                            # For tables with user_id
                            cursor.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_to_delete[0],))
                        except:
                            # For tables with sender_id/receiver_id
                            try:
                                cursor.execute(f"DELETE FROM {table} WHERE sender_id = ? OR receiver_id = ?", 
                                             (user_to_delete[0], user_to_delete[0]))
                            except:
                                pass
                    
                    # Finally delete the user
                    cursor.execute("DELETE FROM users WHERE id = ?", (user_to_delete[0],))
                    
                    # Commit the transaction
                    cursor.execute("COMMIT")
                    
                    st.success(f"User {user_to_delete[1]} has been deleted!")
                    st.rerun()
                except Exception as e:
                    # Rollback in case of error
                    cursor.execute("ROLLBACK")
                    st.error(f"Error deleting user: {e}")
    
    with tab2:
        st.subheader("Content Management")
        
        content_type = st.selectbox(
            "Select Content Type",
            ["Discussions", "Resources", "Events", "Announcements"]
        )
        
        if content_type == "Discussions":
            cursor.execute("""
                SELECT d.id, d.title, u.username, d.category, d.created_at,
                       (SELECT COUNT(*) FROM comments WHERE discussion_id = d.id) as comment_count
                FROM discussions d
                JOIN users u ON d.user_id = u.id
                ORDER BY d.created_at DESC
            """)
            discussions = cursor.fetchall()
            
            discussions_df = pd.DataFrame(discussions, columns=[
                'ID', 'Title', 'Author', 'Category', 'Created At', 'Comments'
            ])
            
            st.write(discussions_df)
            
            # Actions on discussions
            discussion_to_delete = st.selectbox(
                "Select Discussion to Delete",
                discussions_df[['ID', 'Title']].values.tolist(),
                format_func=lambda x: f"{x[1]} (ID: {x[0]})"
            )
            
            if st.button("Delete Discussion"):
                try:
                    # Delete comments first
                    cursor.execute("DELETE FROM comments WHERE discussion_id = ?", (discussion_to_delete[0],))
                    # Then delete the discussion
                    cursor.execute("DELETE FROM discussions WHERE id = ?", (discussion_to_delete[0],))
                    conn.commit()
                    st.success(f"Discussion '{discussion_to_delete[1]}' deleted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting discussion: {e}")
        
        elif content_type == "Resources":
            cursor.execute("""
                SELECT r.id, r.title, u.username, r.resource_type, r.created_at
                FROM resources r
                JOIN users u ON r.user_id = u.id
                ORDER BY r.created_at DESC
            """)
            resources = cursor.fetchall()
            
            resources_df = pd.DataFrame(resources, columns=[
                'ID', 'Title', 'Author', 'Type', 'Created At'
            ])
            
            st.write(resources_df)
            
            # Actions on resources
            resource_to_delete = st.selectbox(
                "Select Resource to Delete",
                resources_df[['ID', 'Title']].values.tolist(),
                format_func=lambda x: f"{x[1]} (ID: {x[0]})"
            )
            
            if st.button("Delete Resource"):
                try:
                    cursor.execute("DELETE FROM resources WHERE id = ?", (resource_to_delete[0],))
                    conn.commit()
                    st.success(f"Resource '{resource_to_delete[1]}' deleted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting resource: {e}")
        
        elif content_type == "Events":
            cursor.execute("""
                SELECT e.id, e.title, u.username, e.event_date, e.location,
                       (SELECT COUNT(*) FROM rsvps WHERE event_id = e.id) as rsvp_count
                FROM events e
                JOIN users u ON e.user_id = u.id
                ORDER BY e.event_date DESC
            """)
            events = cursor.fetchall()
            
            events_df = pd.DataFrame(events, columns=[
                'ID', 'Title', 'Organizer', 'Date', 'Location', 'RSVPs'
            ])
            
            st.write(events_df)
            
            # Actions on events
            event_to_delete = st.selectbox(
                "Select Event to Delete",
                events_df[['ID', 'Title']].values.tolist(),
                format_func=lambda x: f"{x[1]} (ID: {x[0]})"
            )
            
            if st.button("Delete Event"):
                try:
                    # Delete RSVPs first
                    cursor.execute("DELETE FROM rsvps WHERE event_id = ?", (event_to_delete[0],))
                    # Then delete the event
                    cursor.execute("DELETE FROM events WHERE id = ?", (event_to_delete[0],))
                    conn.commit()
                    st.success(f"Event '{event_to_delete[1]}' deleted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting event: {e}")
        
        elif content_type == "Announcements":
            cursor.execute("""
                SELECT a.id, a.title, u.username, a.created_at
                FROM announcements a
                JOIN users u ON a.user_id = u.id
                ORDER BY a.created_at DESC
            """)
            announcements = cursor.fetchall()
            
            announcements_df = pd.DataFrame(announcements, columns=[
                'ID', 'Title', 'Author', 'Created At'
            ])
            
            st.write(announcements_df)
            
            # Actions on announcements
            announcement_to_delete = st.selectbox(
                "Select Announcement to Delete",
                announcements_df[['ID', 'Title']].values.tolist(),
                format_func=lambda x: f"{x[1]} (ID: {x[0]})"
            )
            
            if st.button("Delete Announcement"):
                try:
                    cursor.execute("DELETE FROM announcements WHERE id = ?", (announcement_to_delete[0],))
                    conn.commit()
                    st.success(f"Announcement '{announcement_to_delete[1]}' deleted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting announcement: {e}")
    
    with tab3:
        st.subheader("Site Settings")
        
        # Create uploads directories if they don't exist
        if st.button("Initialize Upload Directories"):
            import os
            
            dirs = [
                'uploads',
                'uploads/profile_photos',
                'uploads/resources'
            ]
            
            created = []
            for directory in dirs:
                if not os.path.exists(directory):
                    os.makedirs(directory)
                    created.append(directory)
            
            if created:
                st.success(f"Created directories: {', '.join(created)}")
            else:
                st.info("All directories already exist.")
        
        # Database maintenance
        st.markdown("---")
        st.subheader("Database Maintenance")
        
        if st.button("Run Database Integrity Check"):
            try:
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                if result[0] == "ok":
                    st.success("Database integrity check passed!")
                else:
                    st.error(f"Database integrity issues found: {result[0]}")
            except Exception as e:
                st.error(f"Error checking database integrity: {e}")
        
        if st.button("Vacuum Database"):
            try:
                conn.close()  # Need to close and reopen with special flag
                conn = sqlite3.connect('community.db', isolation_level=None)
                cursor = conn.cursor()
                cursor.execute("VACUUM")
                st.success("Database vacuumed successfully!")
            except Exception as e:
                st.error(f"Error vacuuming database: {e}")
    
    conn.close()

if __name__ == "__main__":
    app()

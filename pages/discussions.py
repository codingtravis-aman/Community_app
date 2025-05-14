import streamlit as st
import sqlite3
from datetime import datetime

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
    st.title("Community Discussions")
    
    if not st.session_state.authenticated:
        st.warning("Please login to view discussions.")
        st.stop()
    
    # Sidebar for filters
    st.sidebar.subheader("Filter Discussions")
    
    # Get categories for filter
    conn = sqlite3.connect('community.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM discussions ORDER BY category")
    categories = [cat[0] for cat in cursor.fetchall()]
    conn.close()
    
    # Add "All" option to categories
    categories = ["All"] + categories
    
    # Category filter
    selected_category = st.sidebar.selectbox("Category", categories)
    
    # Time filter
    time_filter = st.sidebar.selectbox(
        "Time Period", 
        ["All Time", "Today", "This Week", "This Month"]
    )
    
    # Sort options
    sort_option = st.sidebar.selectbox(
        "Sort By", 
        ["Newest First", "Oldest First", "Most Comments"]
    )
    
    # Main content area with tabs
    tab1, tab2 = st.tabs(["Browse Discussions", "Start New Discussion"])
    
    with tab1:
        # Construct the query based on filters
        query = """
            SELECT d.id, d.title, d.content, d.category, d.created_at, 
                   u.username, COUNT(c.id) as comment_count
            FROM discussions d
            JOIN users u ON d.user_id = u.id
            LEFT JOIN comments c ON d.id = c.discussion_id
        """
        
        # Add WHERE clauses for filters
        where_clauses = []
        params = []
        
        if selected_category != "All":
            where_clauses.append("d.category = ?")
            params.append(selected_category)
        
        if time_filter != "All Time":
            today = datetime.now().strftime('%Y-%m-%d')
            if time_filter == "Today":
                where_clauses.append("date(d.created_at) = ?")
                params.append(today)
            elif time_filter == "This Week":
                where_clauses.append("date(d.created_at) >= date(?, '-7 days')")
                params.append(today)
            elif time_filter == "This Month":
                where_clauses.append("date(d.created_at) >= date(?, '-30 days')")
                params.append(today)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        # Group by and order by
        query += " GROUP BY d.id"
        
        if sort_option == "Newest First":
            query += " ORDER BY d.created_at DESC"
        elif sort_option == "Oldest First":
            query += " ORDER BY d.created_at ASC"
        elif sort_option == "Most Comments":
            query += " ORDER BY comment_count DESC"
        
        # Execute query and display results
        conn = sqlite3.connect('community.db')
        cursor = conn.cursor()
        cursor.execute(query, params)
        discussions = cursor.fetchall()
        
        if not discussions:
            st.info("No discussions found with the selected filters.")
        else:
            for disc in discussions:
                disc_id, title, content, category, created_at, username, comment_count = disc
                
                with st.expander(f"{title} - {category} - Posted by {username} on {created_at[:10]}"):
                    st.write(content)
                    st.write(f"**Comments:** {comment_count}")
                    
                    # Show comments button
                    if st.button(f"View Comments", key=f"view_comments_{disc_id}"):
                        st.session_state.show_comments = disc_id
                    
                    # Display comments if button is clicked
                    if 'show_comments' in st.session_state and st.session_state.show_comments == disc_id:
                        cursor.execute("""
                            SELECT c.content, u.username, c.created_at
                            FROM comments c
                            JOIN users u ON c.user_id = u.id
                            WHERE c.discussion_id = ?
                            ORDER BY c.created_at ASC
                        """, (disc_id,))
                        comments = cursor.fetchall()
                        
                        st.subheader("Comments")
                        if comments:
                            for comment in comments:
                                st.text_area(
                                    f"{comment[1]} on {comment[2][:10]}",
                                    comment[0],
                                    height=80,
                                    key=f"comment_{comment[2]}",
                                    disabled=True
                                )
                        else:
                            st.info("No comments yet. Be the first to comment!")
                        
                        # Add comment form
                        with st.form(key=f"add_comment_form_{disc_id}", clear_on_submit=True):
                            comment_text = st.text_area("Add a comment", height=100)
                            submit_comment = st.form_submit_button("Post Comment")
                            
                            if submit_comment and comment_text:
                                # Insert comment into database
                                try:
                                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    cursor.execute("""
                                        INSERT INTO comments (discussion_id, user_id, content, created_at)
                                        VALUES (?, ?, ?, ?)
                                    """, (disc_id, st.session_state.user_id, comment_text, now))
                                    conn.commit()
                                    st.success("Comment posted successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error posting comment: {e}")
                            elif submit_comment:
                                st.warning("Please enter a comment.")
        
    with tab2:
        st.subheader("Start a New Discussion")
        
        # Get available categories or add a new one
        conn = sqlite3.connect('community.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM discussions ORDER BY category")
        existing_categories = [cat[0] for cat in cursor.fetchall()]
        conn.close()
        
        # If no categories exist yet, provide defaults
        if not existing_categories:
            existing_categories = ["General", "Questions", "Announcements", "Events", "Resources"]
        
        # New discussion form
        with st.form(key="new_discussion_form", clear_on_submit=True):
            title = st.text_input("Title")
            
            # Category options
            category_option = st.radio(
                "Category",
                ["Choose existing", "Create new"]
            )
            
            if category_option == "Choose existing":
                category = st.selectbox("Select Category", existing_categories)
            else:
                category = st.text_input("Enter New Category")
            
            content = st.text_area("Content", height=200)
            
            submit_discussion = st.form_submit_button("Post Discussion")
            
            if submit_discussion:
                if title and content and category:
                    try:
                        conn = sqlite3.connect('community.db')
                        cursor = conn.cursor()
                        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        cursor.execute("""
                            INSERT INTO discussions (user_id, title, content, category, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (st.session_state.user_id, title, content, category, now, now))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success("Discussion posted successfully!")
                        # Clear form and refresh discussions
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error posting discussion: {e}")
                else:
                    st.warning("Please fill in all fields.")

if __name__ == "__main__":
    app()

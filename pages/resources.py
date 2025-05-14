import streamlit as st
import sqlite3
from datetime import datetime
import os
from utils.file_handler import save_resource_file, save_resource_link

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
    st.title("Community Resources")
    
    if not st.session_state.authenticated:
        st.warning("Please login to view resources.")
        st.stop()
    
    # Sidebar filters
    st.sidebar.subheader("Filter Resources")
    
    # Get resource types for filter
    conn = sqlite3.connect('community.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT resource_type FROM resources ORDER BY resource_type")
    types = [t[0] for t in cursor.fetchall()]
    conn.close()
    
    # Add "All" option to types
    types = ["All"] + (types if types else ["File", "Link", "Note"])
    
    # Type filter
    selected_type = st.sidebar.selectbox("Resource Type", types)
    
    # Search feature
    search_term = st.sidebar.text_input("Search Resources")
    
    # Sort options
    sort_option = st.sidebar.selectbox(
        "Sort By", 
        ["Newest First", "Oldest First", "Title A-Z"]
    )
    
    # Main content area with tabs
    tab1, tab2 = st.tabs(["Browse Resources", "Share Resource"])
    
    with tab1:
        # Construct the query based on filters
        query = """
            SELECT r.id, r.title, r.description, r.resource_type, r.file_path, r.url, 
                   r.created_at, u.username
            FROM resources r
            JOIN users u ON r.user_id = u.id
        """
        
        # Add WHERE clauses for filters
        where_clauses = []
        params = []
        
        if selected_type != "All":
            where_clauses.append("r.resource_type = ?")
            params.append(selected_type)
        
        if search_term:
            where_clauses.append("(r.title LIKE ? OR r.description LIKE ?)")
            search_param = f"%{search_term}%"
            params.extend([search_param, search_param])
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        # Add ORDER BY clause
        if sort_option == "Newest First":
            query += " ORDER BY r.created_at DESC"
        elif sort_option == "Oldest First":
            query += " ORDER BY r.created_at ASC"
        elif sort_option == "Title A-Z":
            query += " ORDER BY r.title ASC"
        
        # Execute query and display results
        conn = sqlite3.connect('community.db')
        cursor = conn.cursor()
        cursor.execute(query, params)
        resources = cursor.fetchall()
        conn.close()
        
        if not resources:
            st.info("No resources found with the selected filters.")
        else:
            # Display resources in a grid layout
            for i in range(0, len(resources), 2):
                cols = st.columns(2)
                
                for j in range(2):
                    idx = i + j
                    if idx < len(resources):
                        res = resources[idx]
                        res_id, title, description, res_type, file_path, url, created_at, username = res
                        
                        with cols[j]:
                            st.markdown(f"### {title}")
                            st.write(f"**Type:** {res_type}")
                            st.write(f"**Shared by:** {username} on {created_at[:10]}")
                            
                            if description:
                                with st.expander("Description"):
                                    st.write(description)
                            
                            # Resource access based on type
                            if res_type.lower() == 'file' and file_path and os.path.exists(file_path):
                                file_name = os.path.basename(file_path)
                                
                                # Display download link or preview based on file type
                                file_ext = os.path.splitext(file_path)[1].lower()
                                
                                if file_ext in ['.txt', '.md', '.py', '.js', '.html', '.css']:
                                    with st.expander("Preview"):
                                        try:
                                            with open(file_path, 'r') as f:
                                                content = f.read()
                                            st.code(content)
                                        except Exception as e:
                                            st.error(f"Error displaying file preview: {e}")
                                
                                # For security, we're not directly exposing the file path
                                # Instead, create a button to download the file
                                # This works for small files, but for large files a more sophisticated
                                # approach might be needed
                                try:
                                    with open(file_path, 'rb') as f:
                                        file_content = f.read()
                                    
                                    download_button = st.download_button(
                                        label=f"Download {file_name}",
                                        data=file_content,
                                        file_name=file_name,
                                        key=f"download_{res_id}"
                                    )
                                except Exception as e:
                                    st.error(f"Error accessing file: {e}")
                            
                            elif res_type.lower() == 'link' and url:
                                st.markdown(f"[Open Link]({url})")
                            
                            elif res_type.lower() == 'note':
                                with st.expander("View Note"):
                                    st.write(description)
                            
                            st.markdown("---")
    
    with tab2:
        st.subheader("Share a New Resource")
        
        # Resource type selection
        resource_type = st.selectbox(
            "Resource Type",
            ["File", "Link", "Note"]
        )
        
        # Form for adding a new resource
        with st.form(key="new_resource_form", clear_on_submit=True):
            title = st.text_input("Title")
            description = st.text_area("Description (optional)")
            
            # Fields specific to resource type
            if resource_type == "File":
                uploaded_file = st.file_uploader("Upload File", type=["txt", "pdf", "doc", "docx", "xls", "xlsx", "csv", "py", "js", "html", "css"])
                url = None
            elif resource_type == "Link":
                uploaded_file = None
                url = st.text_input("URL")
            else:  # Note
                uploaded_file = None
                url = None
                if not description:
                    st.info("For notes, please provide the content in the description field.")
            
            submit_resource = st.form_submit_button("Share Resource")
            
            if submit_resource:
                if title:
                    try:
                        if resource_type == "File" and uploaded_file:
                            # Save the uploaded file
                            if save_resource_file(st.session_state.user_id, title, description, uploaded_file, "File"):
                                st.success("File resource shared successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to save file resource.")
                        
                        elif resource_type == "Link" and url:
                            # Save the link
                            if save_resource_link(st.session_state.user_id, title, description, url, "Link"):
                                st.success("Link resource shared successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to save link resource.")
                        
                        elif resource_type == "Note" and description:
                            # Save the note
                            if save_resource_link(st.session_state.user_id, title, description, None, "Note"):
                                st.success("Note resource shared successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to save note resource.")
                        
                        else:
                            if resource_type == "File" and not uploaded_file:
                                st.warning("Please upload a file.")
                            elif resource_type == "Link" and not url:
                                st.warning("Please enter a URL.")
                            elif resource_type == "Note" and not description:
                                st.warning("Please enter note content in the description field.")
                    
                    except Exception as e:
                        st.error(f"Error sharing resource: {e}")
                else:
                    st.warning("Please enter a title for the resource.")

if __name__ == "__main__":
    app()

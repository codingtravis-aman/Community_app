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
    st.title("Direct Messages")
    
    if not st.session_state.authenticated:
        st.warning("Please login to use the messaging system.")
        st.stop()
    
    # Initialize session state for selected user conversation
    if 'selected_conversation' not in st.session_state:
        st.session_state.selected_conversation = None
    
    # Get list of users for messaging
    conn = sqlite3.connect('community.db')
    cursor = conn.cursor()
    
    # Get all users except current user
    cursor.execute("""
        SELECT id, username FROM users 
        WHERE id != ? 
        ORDER BY username
    """, (st.session_state.user_id,))
    users = cursor.fetchall()
    
    # Get conversation summary (latest message with each user)
    cursor.execute("""
        SELECT 
            u.id,
            u.username,
            MAX(m.created_at) as latest_time,
            (SELECT COUNT(*) FROM messages 
             WHERE sender_id = u.id AND receiver_id = ? AND is_read = 0) as unread_count
        FROM users u
        LEFT JOIN messages m ON (m.sender_id = u.id AND m.receiver_id = ?) 
                             OR (m.sender_id = ? AND m.receiver_id = u.id)
        WHERE u.id != ?
        GROUP BY u.id
        ORDER BY latest_time DESC NULLS LAST, u.username
    """, (st.session_state.user_id, st.session_state.user_id, st.session_state.user_id, st.session_state.user_id))
    conversations = cursor.fetchall()
    
    # Layout with sidebar for conversations list
    st.sidebar.subheader("Conversations")
    
    # New message button
    if st.sidebar.button("New Message"):
        st.session_state.selected_conversation = "new"
        st.rerun()
    
    # Display conversations in sidebar
    for convo in conversations:
        user_id, username, latest_time, unread_count = convo
        
        if unread_count > 0:
            button_label = f"{username} ({unread_count})"
        else:
            button_label = username
        
        if st.sidebar.button(button_label, key=f"convo_{user_id}"):
            st.session_state.selected_conversation = user_id
            st.rerun()
    
    # Main content area - display selected conversation or new message form
    if st.session_state.selected_conversation == "new":
        st.subheader("New Message")
        
        # User selection dropdown
        selected_user = st.selectbox("Select User", 
                                   [(u[0], u[1]) for u in users],
                                   format_func=lambda x: x[1])
        
        # Message input
        with st.form("new_message_form", clear_on_submit=True):
            message_text = st.text_area("Message", height=100)
            send_button = st.form_submit_button("Send Message")
            
            if send_button and message_text and selected_user:
                try:
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute("""
                        INSERT INTO messages (sender_id, receiver_id, content, is_read, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (st.session_state.user_id, selected_user[0], message_text, 0, now))
                    conn.commit()
                    
                    st.success(f"Message sent to {selected_user[1]}!")
                    # Switch to the conversation with this user
                    st.session_state.selected_conversation = selected_user[0]
                    st.rerun()
                except Exception as e:
                    st.error(f"Error sending message: {e}")
    
    elif st.session_state.selected_conversation is not None:
        # Get the user details for the selected conversation
        cursor.execute("SELECT username FROM users WHERE id = ?", (st.session_state.selected_conversation,))
        conversation_user = cursor.fetchone()
        
        if conversation_user:
            st.subheader(f"Conversation with {conversation_user[0]}")
            
            # Get messages for this conversation
            cursor.execute("""
                SELECT m.id, m.sender_id, m.content, m.is_read, m.created_at, u.username
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE (m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?)
                ORDER BY m.created_at
            """, (st.session_state.user_id, st.session_state.selected_conversation, 
                  st.session_state.selected_conversation, st.session_state.user_id))
            messages = cursor.fetchall()
            
            # Mark unread messages as read
            cursor.execute("""
                UPDATE messages
                SET is_read = 1
                WHERE sender_id = ? AND receiver_id = ? AND is_read = 0
            """, (st.session_state.selected_conversation, st.session_state.user_id))
            conn.commit()
            
            # Display messages
            message_container = st.container()
            
            with message_container:
                if not messages:
                    st.info("No messages yet. Start the conversation!")
                else:
                    for msg in messages:
                        msg_id, sender_id, content, is_read, created_at, sender_name = msg
                        
                        # Style the message based on sender
                        if sender_id == st.session_state.user_id:
                            # Message from current user
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.markdown(f"""
                                <div style="background-color: #E1F5FE; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                                    <p>{content}</p>
                                    <small>{created_at}</small>
                                </div>
                                """, unsafe_allow_html=True)
                            with col2:
                                st.write("")
                        else:
                            # Message from the other user
                            col1, col2 = st.columns([1, 4])
                            with col1:
                                st.write("")
                            with col2:
                                st.markdown(f"""
                                <div style="background-color: #F5F5F5; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                                    <p>{content}</p>
                                    <small>{created_at}</small>
                                </div>
                                """, unsafe_allow_html=True)
            
            # Reply form
            with st.form("reply_form", clear_on_submit=True):
                reply_text = st.text_area("Reply", height=100)
                send_reply = st.form_submit_button("Send")
                
                if send_reply and reply_text:
                    try:
                        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute("""
                            INSERT INTO messages (sender_id, receiver_id, content, is_read, created_at)
                            VALUES (?, ?, ?, ?, ?)
                        """, (st.session_state.user_id, st.session_state.selected_conversation, reply_text, 0, now))
                        conn.commit()
                        
                        st.success("Message sent!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error sending message: {e}")
        else:
            st.error("User not found.")
            st.session_state.selected_conversation = None
            st.rerun()
    
    else:
        # No conversation selected
        st.info("Select a conversation from the sidebar or start a new message.")
    
    conn.close()

if __name__ == "__main__":
    app()

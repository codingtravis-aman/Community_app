import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px

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
    st.title("Community Events")
    
    if not st.session_state.authenticated:
        st.warning("Please login to view events.")
        st.stop()
    
    # Initialize session state for event details view
    if 'view_event_details' not in st.session_state:
        st.session_state.view_event_details = None
    
    # Sidebar for calendar view
    st.sidebar.subheader("Calendar View")
    
    # Get the current date and calculate week/month bounds
    today = datetime.now().date()
    
    view_option = st.sidebar.radio(
        "View",
        ["Day", "Week", "Month", "All Upcoming"]
    )
    
    if view_option == "Day":
        selected_date = st.sidebar.date_input("Select Date", today)
        date_filter = selected_date.strftime('%Y-%m-%d')
        
        events_query = """
            SELECT e.id, e.title, e.event_date, e.event_time, e.location, u.username
            FROM events e
            JOIN users u ON e.user_id = u.id
            WHERE e.event_date = ?
            ORDER BY e.event_date ASC, e.event_time ASC
        """
        params = (date_filter,)
        
    elif view_option == "Week":
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        selected_start = st.sidebar.date_input("Start of Week", start_of_week)
        selected_end = selected_start + timedelta(days=6)
        
        events_query = """
            SELECT e.id, e.title, e.event_date, e.event_time, e.location, u.username
            FROM events e
            JOIN users u ON e.user_id = u.id
            WHERE e.event_date BETWEEN ? AND ?
            ORDER BY e.event_date ASC, e.event_time ASC
        """
        params = (selected_start.strftime('%Y-%m-%d'), selected_end.strftime('%Y-%m-%d'))
        
    elif view_option == "Month":
        # Calculate first and last day of current month
        current_month = today.replace(day=1)
        next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)
        last_day = next_month - timedelta(days=1)
        
        # Month selector
        months = ["January", "February", "March", "April", "May", "June", 
                 "July", "August", "September", "October", "November", "December"]
        selected_month = st.sidebar.selectbox("Month", months, index=today.month-1)
        selected_year = st.sidebar.number_input("Year", min_value=2020, max_value=2030, value=today.year)
        
        # Calculate start and end dates of selected month
        month_index = months.index(selected_month) + 1
        start_date = datetime(selected_year, month_index, 1).date()
        if month_index == 12:
            end_date = datetime(selected_year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(selected_year, month_index + 1, 1).date() - timedelta(days=1)
        
        events_query = """
            SELECT e.id, e.title, e.event_date, e.event_time, e.location, u.username
            FROM events e
            JOIN users u ON e.user_id = u.id
            WHERE e.event_date BETWEEN ? AND ?
            ORDER BY e.event_date ASC, e.event_time ASC
        """
        params = (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        
    else:  # All Upcoming
        events_query = """
            SELECT e.id, e.title, e.event_date, e.event_time, e.location, u.username
            FROM events e
            JOIN users u ON e.user_id = u.id
            WHERE e.event_date >= ?
            ORDER BY e.event_date ASC, e.event_time ASC
        """
        params = (today.strftime('%Y-%m-%d'),)
    
    # Main content - Tabs for browsing and creating events
    tab1, tab2 = st.tabs(["Browse Events", "Create Event"])
    
    with tab1:
        # If we're viewing event details
        if st.session_state.view_event_details is not None:
            event_id = st.session_state.view_event_details
            conn = sqlite3.connect('community.db')
            cursor = conn.cursor()
            
            # Get event details
            cursor.execute("""
                SELECT e.title, e.description, e.event_date, e.event_time, e.location, 
                       u.username, e.user_id
                FROM events e
                JOIN users u ON e.user_id = u.id
                WHERE e.id = ?
            """, (event_id,))
            event = cursor.fetchone()
            
            if event:
                title, description, event_date, event_time, location, creator, creator_id = event
                
                st.subheader(title)
                st.write(f"**Date:** {event_date}")
                st.write(f"**Time:** {event_time}")
                st.write(f"**Location:** {location}")
                st.write(f"**Organizer:** {creator}")
                
                st.markdown("---")
                st.subheader("Event Description")
                st.write(description)
                
                st.markdown("---")
                
                # Get current RSVP status for this user
                cursor.execute("""
                    SELECT status FROM rsvps 
                    WHERE event_id = ? AND user_id = ?
                """, (event_id, st.session_state.user_id))
                rsvp_status = cursor.fetchone()
                
                current_status = rsvp_status[0] if rsvp_status else "Not Responded"
                
                # RSVP section
                st.subheader("RSVP")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    attending = st.button("Attending", 
                                         type="primary" if current_status == "attending" else "secondary")
                with col2:
                    maybe = st.button("Maybe", 
                                     type="primary" if current_status == "maybe" else "secondary")
                with col3:
                    not_attending = st.button("Not Attending", 
                                             type="primary" if current_status == "not_attending" else "secondary")
                
                if attending or maybe or not_attending:
                    if attending:
                        new_status = "attending"
                    elif maybe:
                        new_status = "maybe"
                    else:
                        new_status = "not_attending"
                    
                    # Update or insert RSVP
                    try:
                        if rsvp_status:
                            cursor.execute("""
                                UPDATE rsvps 
                                SET status = ? 
                                WHERE event_id = ? AND user_id = ?
                            """, (new_status, event_id, st.session_state.user_id))
                        else:
                            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            cursor.execute("""
                                INSERT INTO rsvps (event_id, user_id, status, created_at)
                                VALUES (?, ?, ?, ?)
                            """, (event_id, st.session_state.user_id, new_status, now))
                        
                        conn.commit()
                        st.success(f"You have RSVP'd as {new_status.replace('_', ' ')}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating RSVP: {e}")
                
                # Attendee list
                st.markdown("---")
                st.subheader("Attendees")
                
                cursor.execute("""
                    SELECT u.username, r.status
                    FROM rsvps r
                    JOIN users u ON r.user_id = u.id
                    WHERE r.event_id = ?
                    ORDER BY r.status, u.username
                """, (event_id,))
                attendees = cursor.fetchall()
                
                if attendees:
                    # Group attendees by status
                    attending_list = [a[0] for a in attendees if a[1] == "attending"]
                    maybe_list = [a[0] for a in attendees if a[1] == "maybe"]
                    not_attending_list = [a[0] for a in attendees if a[1] == "not_attending"]
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**Attending:**")
                        for user in attending_list:
                            st.write(f"- {user}")
                    
                    with col2:
                        st.write("**Maybe:**")
                        for user in maybe_list:
                            st.write(f"- {user}")
                    
                    with col3:
                        st.write("**Not Attending:**")
                        for user in not_attending_list:
                            st.write(f"- {user}")
                else:
                    st.info("No RSVPs yet. Be the first to RSVP!")
                
                # Delete button (only for creator or admin)
                if st.session_state.user_id == creator_id or st.session_state.role == "admin":
                    st.markdown("---")
                    if st.button("Delete Event", type="secondary"):
                        try:
                            # Delete RSVPs first to maintain referential integrity
                            cursor.execute("DELETE FROM rsvps WHERE event_id = ?", (event_id,))
                            # Then delete the event
                            cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
                            conn.commit()
                            st.success("Event deleted successfully!")
                            st.session_state.view_event_details = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting event: {e}")
                
                # Back button
                if st.button("Back to Events List"):
                    st.session_state.view_event_details = None
                    st.rerun()
            
            else:
                st.error("Event not found.")
                st.session_state.view_event_details = None
                st.rerun()
            
            conn.close()
            
        else:
            # Display events based on filter
            conn = sqlite3.connect('community.db')
            cursor = conn.cursor()
            
            cursor.execute(events_query, params)
            events = cursor.fetchall()
            
            if not events:
                st.info("No events found for the selected period.")
            else:
                # Create a simple calendar view
                events_df = pd.DataFrame(events, columns=["id", "title", "date", "time", "location", "organizer"])
                
                if view_option in ["Week", "Month"]:
                    # Group events by date
                    unique_dates = sorted(events_df["date"].unique())
                    
                    for date in unique_dates:
                        st.subheader(f"Events on {date}")
                        
                        day_events = events_df[events_df["date"] == date]
                        
                        for _, event in day_events.iterrows():
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.write(f"**{event['title']}**")
                                st.write(f"Time: {event['time']} | Location: {event['location']}")
                            
                            with col2:
                                if st.button("View Details", key=f"view_{event['id']}"):
                                    st.session_state.view_event_details = event['id']
                                    st.rerun()
                        
                        st.markdown("---")
                else:
                    # Day or All view - simpler list
                    for _, event in events_df.iterrows():
                        cols = st.columns([2, 2, 1])
                        
                        with cols[0]:
                            st.write(f"**{event['title']}**")
                            st.write(f"Organizer: {event['organizer']}")
                        
                        with cols[1]:
                            if view_option == "All Upcoming":
                                st.write(f"Date: {event['date']}")
                            st.write(f"Time: {event['time']}")
                            st.write(f"Location: {event['location']}")
                        
                        with cols[2]:
                            if st.button("View Details", key=f"view_{event['id']}"):
                                st.session_state.view_event_details = event['id']
                                st.rerun()
                        
                        st.markdown("---")
            
            conn.close()
    
    with tab2:
        st.subheader("Create a New Event")
        
        with st.form("create_event_form", clear_on_submit=True):
            event_title = st.text_input("Event Title")
            event_description = st.text_area("Event Description", height=150)
            
            col1, col2 = st.columns(2)
            
            with col1:
                event_date = st.date_input("Event Date", min_value=today)
            
            with col2:
                event_time = st.time_input("Event Time")
            
            event_location = st.text_input("Location")
            
            submit_event = st.form_submit_button("Create Event")
            
            if submit_event:
                if event_title and event_description and event_location:
                    try:
                        conn = sqlite3.connect('community.db')
                        cursor = conn.cursor()
                        
                        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        event_date_str = event_date.strftime('%Y-%m-%d')
                        event_time_str = event_time.strftime('%H:%M:%S')
                        
                        cursor.execute("""
                            INSERT INTO events (user_id, title, description, event_date, event_time, 
                                              location, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (st.session_state.user_id, event_title, event_description, 
                              event_date_str, event_time_str, event_location, now))
                        
                        conn.commit()
                        
                        # Auto-RSVP the creator as attending
                        event_id = cursor.lastrowid
                        cursor.execute("""
                            INSERT INTO rsvps (event_id, user_id, status, created_at)
                            VALUES (?, ?, ?, ?)
                        """, (event_id, st.session_state.user_id, "attending", now))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success("Event created successfully!")
                    except Exception as e:
                        st.error(f"Error creating event: {e}")
                else:
                    st.warning("Please fill in all required fields.")

if __name__ == "__main__":
    app()

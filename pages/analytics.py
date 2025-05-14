import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
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
    st.title("Community Analytics")
    
    if not st.session_state.authenticated:
        st.warning("Please login to view analytics.")
        st.stop()
    
    # Only admins can access analytics
    if not is_admin(st.session_state.user_id):
        st.error("You don't have permission to access this page.")
        st.stop()
    
    # Database connection
    conn = sqlite3.connect('community.db')
    
    # Time period selector
    time_period = st.selectbox(
        "Select Time Period",
        ["Last 7 days", "Last 30 days", "Last 3 months", "Last year", "All time"]
    )
    
    # Calculate start date based on selected time period
    today = datetime.now().date()
    if time_period == "Last 7 days":
        start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    elif time_period == "Last 30 days":
        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    elif time_period == "Last 3 months":
        start_date = (today - timedelta(days=90)).strftime('%Y-%m-%d')
    elif time_period == "Last year":
        start_date = (today - timedelta(days=365)).strftime('%Y-%m-%d')
    else:  # All time
        start_date = "2000-01-01"  # Far past date to include everything
    
    # Create tabs for different analytics categories
    tab1, tab2, tab3, tab4 = st.tabs(["User Activity", "Content", "Events", "Resource Usage"])
    
    with tab1:
        st.subheader("User Activity Analytics")
        
        # Calculate key metrics
        cursor = conn.cursor()
        
        # Total number of users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # New users in selected period
        cursor.execute("SELECT COUNT(*) FROM users WHERE date(created_at) >= ?", (start_date,))
        new_users = cursor.fetchone()[0]
        
        # Active users (users who logged in during the selected period)
        cursor.execute("SELECT COUNT(DISTINCT id) FROM users WHERE date(last_login) >= ?", (start_date,))
        active_users = cursor.fetchone()[0]
        
        # Display metrics in columns
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Users", total_users)
        col2.metric("New Users", new_users)
        col3.metric("Active Users", active_users)
        
        # User growth over time
        cursor.execute("""
            SELECT date(created_at) as date, COUNT(*) as count
            FROM users
            WHERE date(created_at) >= ?
            GROUP BY date(created_at)
            ORDER BY date(created_at)
        """, (start_date,))
        
        user_growth_data = cursor.fetchall()
        
        if user_growth_data:
            growth_df = pd.DataFrame(user_growth_data, columns=['date', 'new_users'])
            growth_df['date'] = pd.to_datetime(growth_df['date'])
            growth_df['cumulative_users'] = growth_df['new_users'].cumsum()
            
            fig = px.line(growth_df, x='date', y='cumulative_users', 
                         title='Cumulative User Growth')
            st.plotly_chart(fig, use_container_width=True)
            
            # Daily new user registrations
            fig2 = px.bar(growth_df, x='date', y='new_users',
                         title='Daily New User Registrations')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info(f"No user registration data available for the selected period ({time_period}).")
        
        # User activity by time of day
        cursor.execute("""
            SELECT strftime('%H', last_login) as hour, COUNT(*) as count
            FROM users
            WHERE date(last_login) >= ?
            GROUP BY hour
            ORDER BY hour
        """, (start_date,))
        
        activity_by_hour = cursor.fetchall()
        
        if activity_by_hour:
            hour_df = pd.DataFrame(activity_by_hour, columns=['hour', 'logins'])
            hour_df['hour'] = hour_df['hour'].astype(int)
            
            fig3 = px.bar(hour_df, x='hour', y='logins',
                         title='User Activity by Hour of Day',
                         labels={'hour': 'Hour (24-hour format)', 'logins': 'Number of Logins'})
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info(f"No login activity data available for the selected period ({time_period}).")
    
    with tab2:
        st.subheader("Content Analytics")
        
        # Discussion stats
        cursor.execute("SELECT COUNT(*) FROM discussions")
        total_discussions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM discussions WHERE date(created_at) >= ?", (start_date,))
        new_discussions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comments WHERE date(created_at) >= ?", (start_date,))
        new_comments = cursor.fetchone()[0]
        
        # Display metrics in columns
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Discussions", total_discussions)
        col2.metric("New Discussions", new_discussions)
        col3.metric("New Comments", new_comments)
        
        # Discussions by category
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM discussions
            WHERE date(created_at) >= ?
            GROUP BY category
            ORDER BY count DESC
        """, (start_date,))
        
        discussions_by_category = cursor.fetchall()
        
        if discussions_by_category:
            category_df = pd.DataFrame(discussions_by_category, columns=['category', 'count'])
            
            fig = px.pie(category_df, values='count', names='category',
                        title='Discussions by Category')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No discussion data available for the selected period ({time_period}).")
        
        # Discussion activity over time
        cursor.execute("""
            SELECT date(created_at) as date, COUNT(*) as count
            FROM discussions
            WHERE date(created_at) >= ?
            GROUP BY date(created_at)
            ORDER BY date(created_at)
        """, (start_date,))
        
        discussion_activity = cursor.fetchall()
        
        if discussion_activity:
            disc_df = pd.DataFrame(discussion_activity, columns=['date', 'discussions'])
            disc_df['date'] = pd.to_datetime(disc_df['date'])
            
            # Also get comment activity
            cursor.execute("""
                SELECT date(created_at) as date, COUNT(*) as count
                FROM comments
                WHERE date(created_at) >= ?
                GROUP BY date(created_at)
                ORDER BY date(created_at)
            """, (start_date,))
            
            comment_activity = cursor.fetchall()
            comment_df = pd.DataFrame(comment_activity, columns=['date', 'comments'])
            comment_df['date'] = pd.to_datetime(comment_df['date'])
            
            # Merge datasets
            activity_df = pd.merge(disc_df, comment_df, on='date', how='outer').fillna(0)
            
            # Create a figure with two traces
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=activity_df['date'], y=activity_df['discussions'],
                                     mode='lines+markers', name='Discussions'))
            fig2.add_trace(go.Scatter(x=activity_df['date'], y=activity_df['comments'],
                                     mode='lines+markers', name='Comments'))
            
            fig2.update_layout(title='Discussion and Comment Activity Over Time',
                              xaxis_title='Date',
                              yaxis_title='Count',
                              legend_title='Activity Type')
            
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info(f"No discussion activity data available for the selected period ({time_period}).")
        
        # Top contributors (users with most discussions/comments)
        cursor.execute("""
            SELECT u.username, COUNT(d.id) as discussion_count
            FROM users u
            JOIN discussions d ON u.id = d.user_id
            WHERE date(d.created_at) >= ?
            GROUP BY u.id
            ORDER BY discussion_count DESC
            LIMIT 10
        """, (start_date,))
        
        top_discussion_creators = cursor.fetchall()
        
        if top_discussion_creators:
            st.subheader("Top Discussion Contributors")
            top_disc_df = pd.DataFrame(top_discussion_creators, columns=['username', 'discussions'])
            
            fig3 = px.bar(top_disc_df, x='username', y='discussions',
                         title='Top 10 Discussion Contributors')
            st.plotly_chart(fig3, use_container_width=True)
        
    with tab3:
        st.subheader("Event Analytics")
        
        # Event stats
        cursor.execute("SELECT COUNT(*) FROM events")
        total_events = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM events WHERE date(created_at) >= ?", (start_date,))
        new_events = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM events 
            WHERE date(event_date) >= ? AND date(event_date) <= ?
        """, (datetime.now().strftime('%Y-%m-%d'), (today + timedelta(days=30)).strftime('%Y-%m-%d')))
        upcoming_events = cursor.fetchone()[0]
        
        # Display metrics in columns
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Events", total_events)
        col2.metric("New Events", new_events)
        col3.metric("Upcoming Events", upcoming_events)
        
        # RSVP statistics
        cursor.execute("""
            SELECT e.title, 
                  SUM(CASE WHEN r.status = 'attending' THEN 1 ELSE 0 END) as attending,
                  SUM(CASE WHEN r.status = 'maybe' THEN 1 ELSE 0 END) as maybe,
                  SUM(CASE WHEN r.status = 'not_attending' THEN 1 ELSE 0 END) as not_attending
            FROM events e
            LEFT JOIN rsvps r ON e.id = r.event_id
            WHERE date(e.event_date) >= ?
            GROUP BY e.id
            ORDER BY e.event_date ASC
            LIMIT 10
        """, (start_date,))
        
        event_rsvps = cursor.fetchall()
        
        if event_rsvps:
            st.subheader("Event RSVP Statistics")
            rsvp_df = pd.DataFrame(event_rsvps, columns=['event', 'attending', 'maybe', 'not_attending'])
            
            # Melt the dataframe for easy plotting
            rsvp_melted = pd.melt(rsvp_df, id_vars=['event'], value_vars=['attending', 'maybe', 'not_attending'],
                                 var_name='status', value_name='count')
            
            fig = px.bar(rsvp_melted, x='event', y='count', color='status', barmode='group',
                        title='RSVP Status by Event')
            fig.update_layout(xaxis={'categoryorder':'total descending'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No event RSVP data available for the selected period ({time_period}).")
        
        # Events by day of week
        cursor.execute("""
            SELECT strftime('%w', event_date) as day_of_week, COUNT(*) as count
            FROM events
            WHERE date(created_at) >= ?
            GROUP BY day_of_week
            ORDER BY day_of_week
        """, (start_date,))
        
        events_by_day = cursor.fetchall()
        
        if events_by_day:
            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            day_df = pd.DataFrame(events_by_day, columns=['day_of_week', 'count'])
            day_df['day_name'] = day_df['day_of_week'].astype(int).apply(lambda x: days[x])
            
            fig2 = px.bar(day_df, x='day_name', y='count',
                         title='Events by Day of Week',
                         category_orders={"day_name": days})
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info(f"No event schedule data available for the selected period ({time_period}).")
    
    with tab4:
        st.subheader("Resource Usage Analytics")
        
        # Resource stats
        cursor.execute("SELECT COUNT(*) FROM resources")
        total_resources = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM resources WHERE date(created_at) >= ?", (start_date,))
        new_resources = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT resource_type, COUNT(*) as count
            FROM resources
            GROUP BY resource_type
        """)
        resource_types = cursor.fetchall()
        type_counts = {r[0]: r[1] for r in resource_types}
        
        # Display metrics in columns
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Resources", total_resources)
        col2.metric("New Resources", new_resources)
        col3.metric("Resource Types", len(type_counts))
        
        # Resources by type
        if resource_types:
            type_df = pd.DataFrame(resource_types, columns=['type', 'count'])
            
            fig = px.pie(type_df, values='count', names='type',
                        title='Resources by Type')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No resource type data available.")
        
        # Resource contributions by user
        cursor.execute("""
            SELECT u.username, COUNT(r.id) as resource_count
            FROM users u
            JOIN resources r ON u.id = r.user_id
            WHERE date(r.created_at) >= ?
            GROUP BY u.id
            ORDER BY resource_count DESC
            LIMIT 10
        """, (start_date,))
        
        top_resource_contributors = cursor.fetchall()
        
        if top_resource_contributors:
            contrib_df = pd.DataFrame(top_resource_contributors, columns=['username', 'resources'])
            
            fig2 = px.bar(contrib_df, x='username', y='resources',
                         title='Top Resource Contributors')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info(f"No resource contribution data available for the selected period ({time_period}).")
        
        # Resource addition over time
        cursor.execute("""
            SELECT date(created_at) as date, COUNT(*) as count
            FROM resources
            WHERE date(created_at) >= ?
            GROUP BY date(created_at)
            ORDER BY date(created_at)
        """, (start_date,))
        
        resource_additions = cursor.fetchall()
        
        if resource_additions:
            resource_df = pd.DataFrame(resource_additions, columns=['date', 'additions'])
            resource_df['date'] = pd.to_datetime(resource_df['date'])
            resource_df['cumulative'] = resource_df['additions'].cumsum()
            
            fig3 = px.line(resource_df, x='date', y='cumulative',
                          title='Cumulative Resource Growth')
            st.plotly_chart(fig3, use_container_width=True)
            
            fig4 = px.bar(resource_df, x='date', y='additions',
                         title='Daily Resource Additions')
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info(f"No resource addition data available for the selected period ({time_period}).")
    
    conn.close()

if __name__ == "__main__":
    app()

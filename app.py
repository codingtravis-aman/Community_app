import streamlit as st
import sqlite3
import os
import pandas as pd
from datetime import datetime
from utils.auth import authenticate, create_user, is_admin
from utils.database import initialize_database
from utils.responsive import apply_responsive_styles, create_responsive_grid, responsive_text, create_responsive_card

# Load secrets if available
try:
    app_settings = st.secrets["app_settings"]
    general_settings = st.secrets["general"]
    app_name = general_settings["app_name"]
    app_version = app_settings["version"]
    app_developer = app_settings["developer"]
    build_date = app_settings["build_date"]
except:
    # Default values if secrets are not available
    app_name = "Community Hub"
    app_version = "1.0.0"
    app_developer = "Aman Jha"
    build_date = "2025-05-12"

# Page configuration
st.set_page_config(
    page_title=app_name,
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply responsive styles and UI enhancements
apply_responsive_styles()

# Apply custom styles for improved UI
st.markdown("""
<style>
    /* Global styles for improved UI */
    h1, h2, h3, h4 {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 600;
        color: #2c3e50;
    }
    
    h1 {
        margin-bottom: 1.5rem;
    }
    
    /* Button styles */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15) !important;
    }
    
    /* Card styling */
    .ui-card {
        border-radius: 10px;
        padding: 1.5rem;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        border-top: 4px solid #4361EE;
    }
    
    /* Input field styling */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        border-radius: 8px !important;
        border: 1px solid #e0e0e0 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
        border-color: #4361EE !important;
        box-shadow: 0 0 0 2px rgba(67, 97, 238, 0.2) !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #eaeaea;
        padding-top: 1rem;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.5rem;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        margin-bottom: 0.3rem;
        padding: 0.4rem 0;
        border-radius: 5px;
        transition: background-color 0.2s;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background-color: rgba(67, 97, 238, 0.05);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1rem;
        border-radius: 10px 10px 0 0;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding: 1rem 0;
    }
    
    /* Expanders styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        border-radius: 5px;
    }
    .streamlit-expanderContent {
        border-radius: 0 0 5px 5px;
    }
    
    /* Specific component styling */
    .stAlert {
        border-radius: 10px !important;
    }
    
    /* Fix React error with inline JS handlers */
    .mobile-nav-buttons button {
        border: none;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
initialize_database()

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None

# Session state for splash screen
if 'show_splash' not in st.session_state:
    st.session_state.show_splash = True

# Splash Screen with developer credit
if st.session_state.show_splash and not st.session_state.authenticated:
    st.markdown(f"""
    <style>
        .splash-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            text-align: center;
            padding: 2rem;
            background: linear-gradient(135deg, #4361EE 0%, #3A0CA3 100%);
            color: white;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            position: relative;
            overflow: hidden;
        }}
        /* Decorative background elements */
        .splash-container::before {{
            content: '';
            position: absolute;
            top: -50px;
            left: -50px;
            width: 200px;
            height: 200px;
            border-radius: 50%;
            background: rgba(255,255,255,0.05);
            z-index: 0;
        }}
        .splash-container::after {{
            content: '';
            position: absolute;
            bottom: -50px;
            right: -50px;
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: rgba(255,255,255,0.05);
            z-index: 0;
        }}
        .splash-content {{
            position: relative;
            z-index: 1;
            width: 100%;
            max-width: 800px;
        }}
        .splash-title {{
            font-size: 3.8rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            letter-spacing: -0.5px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .splash-version {{
            font-size: 0.85rem;
            margin-top: 0.5rem;
            opacity: 0.7;
            background: rgba(255,255,255,0.1);
            padding: 5px 10px;
            border-radius: 30px;
            display: inline-block;
            backdrop-filter: blur(5px);
        }}
        .splash-subtitle {{
            font-size: 1.7rem;
            margin: 1.5rem 0;
            opacity: 0.9;
            font-weight: 300;
        }}
        .splash-features {{
            font-size: 1.1rem;
            max-width: 600px;
            margin: 0 auto 2rem auto;
            line-height: 1.6;
            opacity: 0.8;
        }}
        .developer-credit {{
            margin-top: 3.5rem;
            font-size: 1rem;
            opacity: 0.8;
            padding: 1rem;
            border-top: 1px solid rgba(255,255,255,0.1);
            width: 80%;
        }}
        .social-links {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 12px;
        }}
        .social-links a {{
            color: white;
            text-decoration: none;
            transition: all 0.3s;
            padding: 5px 10px;
            border-radius: 5px;
            background: rgba(255,255,255,0.1);
        }}
        .social-links a:hover {{
            background: rgba(255,255,255,0.2);
            transform: translateY(-2px);
        }}
        .enter-button {{
            margin-top: 25px;
            padding: 12px 32px;
            background-color: white;
            color: #4361EE;
            border: none;
            border-radius: 30px;
            cursor: pointer;
            font-weight: 600;
            font-size: 1.1rem;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .enter-button:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}
        
        /* Responsive adjustments */
        @media (max-width: 768px) {{
            .splash-title {{
                font-size: 2.8rem;
            }}
            .splash-subtitle {{
                font-size: 1.3rem;
            }}
        }}
        @media (max-width: 480px) {{
            .splash-title {{
                font-size: 2.2rem;
            }}
            .splash-subtitle {{
                font-size: 1.1rem;
            }}
            .splash-features {{
                font-size: 0.95rem;
            }}
        }}
    </style>
    <div class="splash-container">
        <div class="splash-content">
            <div class="splash-title">Welcome to {app_name}</div>
            <div class="splash-version">Version {app_version} | Build: {build_date}</div>
            <div class="splash-subtitle">Connect, Share, and Grow Together</div>
            <div class="splash-features">
                A comprehensive platform with discussion boards, events, resources, and more. 
                Join our community to connect with like-minded individuals and expand your network.
            </div>
            <button class="enter-button" onclick="document.querySelector('.splash-container').style.display='none';">
                Enter App
            </button>
            <div class="developer-credit">
                <p>Designed & Developed by {app_developer}</p>
                <div class="social-links">
                    <a href="https://amancreates.netlify.app" target="_blank">Portfolio</a>
                    <a href="https://www.linkedin.com/in/aman-jha-0bb578211" target="_blank">LinkedIn</a>
                    <a href="https://www.instagram.com/codingtravis_aman" target="_blank">@codingtravis_</a>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Enter App"):
        st.session_state.show_splash = False
        st.rerun()

# Authentication with enhanced UI design
if not st.session_state.authenticated and not st.session_state.show_splash:
    # Use responsive text with better typography
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600; color: #2c3e50;">
            Welcome to Community Hub
        </h1>
        <p style="font-size: 1.1rem; color: #666; max-width: 600px; margin: 0 auto; line-height: 1.5;">
            Join our community to connect, share ideas, and grow together.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add enhanced UI styles
    st.markdown("""
    <style>
        /* Auth container styling */
        .auth-container {
            max-width: 900px;
            margin: 0 auto;
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
            overflow: hidden;
            border: 1px solid #f0f0f0;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            background-color: #f8f9fa;
            padding: 10px 10px 0 10px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            border-radius: 10px 10px 0 0;
            font-weight: 500;
            letter-spacing: 0.3px;
            background-color: #f0f2f5;
            margin-right: 4px;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: white;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.05);
            position: relative;
            top: 1px;
        }
        .stTabs [data-baseweb="tab-panel"] {
            padding: 2rem 1rem;
            background: white;
        }
        
        /* Input field styling */
        .stTextInput, .stPasswordInput {
            margin-bottom: 15px;
        }
        .stTextInput > div > div > input, .stPasswordInput > div > div > input {
            font-size: 16px !important;
            padding: 12px 15px !important;
            border-radius: 8px !important;
            border: 1px solid #e0e0e0 !important;
            background-color: #f9f9f9 !important;
            transition: all 0.2s ease !important;
        }
        .stTextInput > div > div > input:focus, .stPasswordInput > div > div > input:focus {
            background-color: white !important;
            border-color: #4361EE !important;
            box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.15) !important;
        }
        
        /* Form sections */
        .form-header {
            font-weight: 600;
            margin-bottom: 1.5rem;
            color: #2c3e50;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            position: relative;
        }
        .form-header:after {
            content: '';
            position: absolute;
            bottom: -8px;
            left: 0;
            height: 3px;
            width: 40px;
            background: #4361EE;
            border-radius: 3px;
        }
        
        /* Button styling */
        .stButton > button {
            height: 48px !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.5px !important;
            border-radius: 8px !important;
            border: none !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1) !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1) !important;
        }
        .stButton > button[data-baseweb="button"] {
            background-color: #4361EE !important;
        }
        
        /* Responsive layout */
        @media (max-width: 768px) {
            .stTabs [data-baseweb="tab-list"] {
                padding: 5px 5px 0 5px;
            }
            .stTabs [data-baseweb="tab-panel"] {
                padding: 1.5rem 0.5rem;
            }
            .main .block-container {
                padding: 1rem 0.5rem !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create better tabs with enhanced UI
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        # Center content with better proportions
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="form-header">Sign In</div>', unsafe_allow_html=True)
            
            login_username = st.text_input("Username", key="login_username", 
                                          placeholder="Enter your username")
            login_password = st.text_input("Password", type="password", key="login_password",
                                          placeholder="Enter your password")
            
            # Full-width button with better styling
            if st.button("Sign In", key="login_btn", use_container_width=True, type="primary"):
                if login_username and login_password:
                    user = authenticate(login_username, login_password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user_id = user[0]
                        st.session_state.username = user[1]
                        st.session_state.role = user[3]
                        st.success(f"Welcome back, {user[1]}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                else:
                    st.warning("Please enter both username and password.")
                    
            # Add helpful text below the login form
            st.markdown("""
            <div style="text-align: center; margin-top: 1.5rem; color: #666; font-size: 0.9rem;">
                Don't have an account? Switch to the Register tab to create one.
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        # Center content with better proportions
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="form-header">Create Account</div>', unsafe_allow_html=True)
            
            new_username = st.text_input("Username", key="new_username", 
                                       placeholder="Choose a username")
            new_email = st.text_input("Email", key="new_email", 
                                    placeholder="Enter your email")
            new_password = st.text_input("Password", type="password", key="new_password", 
                                       placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password", 
                                           placeholder="Confirm your password")
            
            # Add terms and conditions checkbox
            agree_terms = st.checkbox("I agree to the Terms and Conditions", key="agree_terms")
            
            # Full-width button with better styling
            register_btn = st.button("Create Account", key="register_btn", use_container_width=True, 
                               type="primary", disabled=not agree_terms)
            
            if register_btn:
                if new_username and new_email and new_password and confirm_password:
                    if new_password == confirm_password:
                        if create_user(new_username, new_email, new_password):
                            st.success("Registration successful! Please login.")
                            # Automatically switch to login tab
                            st.session_state.active_tab = "Login"
                            st.rerun()
                        else:
                            st.error("Username or email already exists.")
                    else:
                        st.error("Passwords do not match.")
                else:
                    st.warning("Please fill out all fields.")
                    
            # Add password policy guidance
            st.markdown("""
            <div style="margin-top: 1rem; padding: 0.75rem; background-color: #f8f9fa; border-radius: 8px; font-size: 0.85rem; color: #666;">
                <div style="font-weight: 500; margin-bottom: 0.5rem;">Password Requirements:</div>
                <ul style="margin: 0; padding-left: 1.5rem;">
                    <li>At least 8 characters long</li>
                    <li>Include at least one uppercase letter</li>
                    <li>Include at least one number</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

else:
    # Mobile detection for responsive navigation 
    st.markdown("""
    <style>
        /* Mobile-friendly sidebar */
        @media (max-width: 640px) {
            section[data-testid="stSidebar"] {
                width: 80% !important;
                min-width: unset !important;
            }
            /* Mobile quick navigation */
            .mobile-nav-buttons {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
                margin-bottom: 1rem;
            }
            .mobile-nav-buttons button {
                flex: 1 0 auto;
                min-width: 80px;
                padding: 0.5rem;
                font-size: 0.8rem !important;
                height: auto !important;
                white-space: nowrap;
            }
            /* Hide non-essential sidebar elements on small screens */
            .sidebar-optional {
                display: none !important;
            }
        }
        
        /* Hide mobile navigation on larger screens */
        .mobile-nav-buttons {
            display: none;
        }
        @media (max-width: 640px) {
            .mobile-nav-buttons {
                display: flex;
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Enhanced sidebar UI for authenticated users
    st.sidebar.markdown(f"""
    <div style="padding: 1rem 0.5rem; margin-bottom: 1rem; border-radius: 10px; background: linear-gradient(135deg, #4361EE 0%, #3A0CA3 100%);">
        <div style="color: white; font-size: 0.9rem; opacity: 0.8;">Welcome back</div>
        <div style="color: white; font-size: 1.3rem; font-weight: 600; margin-top: 0.3rem;">{st.session_state.username}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced navigation with better styling
    st.sidebar.markdown("""
    <style>
        /* Style for navigation */
        [data-testid="stRadio"] > div {
            padding: 0.5rem;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        [data-testid="stRadio"] label {
            padding: 0.5rem 0.8rem !important;
            margin-bottom: 0.3rem;
            border-radius: 6px;
            transition: all 0.2s;
            line-height: 1.4;
        }
        [data-testid="stRadio"] label:hover {
            background-color: rgba(67, 97, 238, 0.05);
        }
        [data-testid="stRadio"] label div:first-child {
            height: 20px;
            width: 20px;
        }
        [data-testid="stRadio"] label div:first-child div {
            height: 12px;
            width: 12px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Add section title
    st.sidebar.markdown('<div style="margin: 1rem 0 0.5rem 0.5rem; font-size: 0.85rem; font-weight: 600; color: #666;">MAIN MENU</div>', 
                       unsafe_allow_html=True)
    
    # Navigation with icons using Unicode symbols
    navigation_options = {
        "Home": "🏠 Home",
        "Profile": "👤 Profile",
        "Discussions": "💬 Discussions",
        "Events": "📅 Events",
        "Resources": "📚 Resources", 
        "Messages": "✉️ Messages",
        "Announcements": "📣 Announcements"
    }
    
    navigation = st.sidebar.radio(
        "Navigation",  # Add a proper label for accessibility
        list(navigation_options.keys()),
        format_func=lambda x: navigation_options[x],
        label_visibility="collapsed"  # Hide the label but keep it for accessibility
    )
    
    # Mobile quick navigation (only visible on small screens)
    if not 'current_mobile_nav' in st.session_state:
        st.session_state.current_mobile_nav = navigation
        
    # Create mobile navigation buttons using Streamlit components instead of HTML
    st.markdown("""
    <style>
        /* Mobile navigation styling */
        .mobile-nav-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 8px;
            margin-bottom: 20px;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 10px;
        }
        .mobile-nav-grid .stButton button {
            padding: 4px !important;
            font-size: 12px !important;
            height: auto !important;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 2px;
        }
        .mobile-nav-grid .stButton button p {
            margin: 0;
        }
        .nav-icon {
            font-size: 1.2rem;
        }
        @media (min-width: 768px) {
            .mobile-nav-container {
                display: none;
            }
        }
    </style>
    
    <div class="mobile-nav-container">
        <div class="mobile-nav-title" style="text-align: center; margin-bottom: 5px; font-size: 0.8rem; color: #666;">
            Quick Navigation
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Only show on mobile
    mobile_col1, mobile_col2, mobile_col3, mobile_col4, mobile_col5 = st.columns(5)
    
    with mobile_col1:
        if st.button("🏠\nHome", key="mobile_home"):
            st.session_state.current_mobile_nav = "Home"
            st.rerun()
    
    with mobile_col2:
        if st.button("👤\nProfile", key="mobile_profile"):
            st.session_state.current_mobile_nav = "Profile"
            st.rerun()
    
    with mobile_col3:
        if st.button("💬\nDiscuss", key="mobile_discuss"):
            st.session_state.current_mobile_nav = "Discussions"
            st.rerun()
    
    with mobile_col4:
        if st.button("📅\nEvents", key="mobile_events"):
            st.session_state.current_mobile_nav = "Events"
            st.rerun()
    
    with mobile_col5:
        if st.button("📚\nShare", key="mobile_resources"):
            st.session_state.current_mobile_nav = "Resources"
            st.rerun()
    
    # Admin section with enhanced styling (only visible to admins)
    if is_admin(st.session_state.user_id):
        st.sidebar.markdown("""
        <div style="margin: 1.5rem 0 0.5rem 0; height: 1px; background: linear-gradient(to right, rgba(0,0,0,0.05), rgba(0,0,0,0.1), rgba(0,0,0,0.05));"></div>
        """, unsafe_allow_html=True)
        
        # Add admin section title
        st.sidebar.markdown("""
        <div style="margin: 1rem 0 0.5rem 0.5rem; font-size: 0.85rem; font-weight: 600; color: #FF5A5F;">
            ADMIN CONTROLS
        </div>
        """, unsafe_allow_html=True)
        
        # Admin navigation with icons
        admin_options = {
            "User Management": "👥 User Management",
            "Analytics": "📊 Analytics",
            "Site Settings": "⚙️ Site Settings"
        }
        
        admin_nav = st.sidebar.radio(
            "",  # Empty label
            list(admin_options.keys()),
            format_func=lambda x: admin_options[x],
            key="admin_radio"
        )
        
        # Add mobile-friendly admin quick actions using Streamlit components
        if is_admin(st.session_state.user_id):
            # Only show on mobile
            st.markdown("""
            <style>
                .admin-actions {
                    margin-top: 10px;
                    background: rgba(67, 97, 238, 0.05);
                    border-radius: 10px;
                    padding: 10px;
                }
                .admin-title {
                    font-size: 0.85rem;
                    margin-bottom: 5px;
                    color: #4361EE;
                    font-weight: 600;
                }
                @media (min-width: 768px) {
                    .admin-mobile-only {
                        display: none;
                    }
                }
            </style>
            <div class="admin-mobile-only">
                <div class="admin-actions">
                    <div class="admin-title">Admin Actions</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Add admin buttons
            admin_col1, admin_col2, admin_col3 = st.columns(3)
            
            with admin_col1:
                if st.button("👥\nUsers", key="admin_users"):
                    st.session_state.admin_nav = "User Management"
                    st.rerun()
            
            with admin_col2:
                if st.button("📊\nAnalytics", key="admin_analytics"):
                    st.session_state.admin_nav = "Analytics"
                    st.rerun()
            
            with admin_col3:
                if st.button("⚙️\nSettings", key="admin_settings"):
                    st.session_state.admin_nav = "Site Settings"
                    st.rerun()
    
    # Enhanced logout section
    st.sidebar.markdown("""
    <div style="margin: 1.5rem 0 0.5rem 0; height: 1px; background: linear-gradient(to right, rgba(0,0,0,0.05), rgba(0,0,0,0.1), rgba(0,0,0,0.05));"></div>
    """, unsafe_allow_html=True)
    
    # Logout button with better styling
    st.sidebar.markdown("""
    <style>
        .logout-button {
            margin-top: 1rem;
        }
        .logout-button button {
            background-color: #f8f9fa !important;
            color: #666 !important;
            border: 1px solid #e0e0e0 !important;
            width: 100%;
        }
        .logout-button button:hover {
            background-color: #f0f0f0 !important;
            border-color: #d0d0d0 !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Add app information before logout
    st.sidebar.markdown(f"""
    <div style="padding: 0.5rem; margin-bottom: 1rem; font-size: 0.8rem; color: #888; text-align: center;">
        {app_name} v{app_version}<br>
        Built by {app_developer}
    </div>
    """, unsafe_allow_html=True)
    
    # Logout button with icon
    with st.sidebar:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚪 Logout", key="logout_btn"):
                st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()
    
    # Content based on navigation selection
    if navigation == "Home":
        st.title("Community Hub Dashboard")
        
        # Display recent activities
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Recent Discussions")
            conn = sqlite3.connect('community.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.title, u.username, d.created_at 
                FROM discussions d 
                JOIN users u ON d.user_id = u.id 
                ORDER BY d.created_at DESC LIMIT 5
            """)
            discussions = cursor.fetchall()
            
            if discussions:
                for disc in discussions:
                    st.write(f"**{disc[0]}** by {disc[1]} on {disc[2][:10]}")
            else:
                st.info("No discussions yet. Be the first to start one!")
                
        with col2:
            st.subheader("Upcoming Events")
            conn = sqlite3.connect('community.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT title, event_date, location 
                FROM events 
                WHERE event_date >= ? 
                ORDER BY event_date ASC LIMIT 5
            """, (datetime.now().strftime('%Y-%m-%d'),))
            events = cursor.fetchall()
            
            if events:
                for event in events:
                    st.write(f"**{event[0]}** on {event[1]} at {event[2]}")
            else:
                st.info("No upcoming events scheduled.")
        
        # Recent announcements
        st.subheader("Latest Announcements")
        conn = sqlite3.connect('community.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT title, content, created_at 
            FROM announcements 
            ORDER BY created_at DESC LIMIT 3
        """)
        announcements = cursor.fetchall()
        
        if announcements:
            for announce in announcements:
                with st.expander(f"{announce[0]} - {announce[2][:10]}"):
                    st.write(announce[1])
        else:
            st.info("No announcements have been posted yet.")
            
        conn.close()

# Footer with mobile responsiveness
st.markdown("---")
st.markdown(f"""
<style>
    /* Footer Styles */
    .footer-container {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.5rem;
        padding: 0.5rem 0;
    }}
    .footer-copyright {{
        margin-right: 1rem;
    }}
    .footer-links {{
        display: flex;
        gap: 0.5rem;
    }}
    /* Mobile adjustments */
    @media (max-width: 640px) {{
        .footer-container {{
            flex-direction: column;
            align-items: center;
            text-align: center;
        }}
        .footer-copyright {{
            margin-right: 0;
            margin-bottom: 0.5rem;
            font-size: 0.8rem;
        }}
        .footer-version {{
            display: block;
            font-size: 0.7rem;
            margin-top: 0.2rem;
        }}
        .footer-links {{
            flex-wrap: wrap;
            justify-content: center;
            font-size: 0.8rem;
        }}
    }}
</style>
<div class="footer-container">
    <div class="footer-copyright">
        © 2023 {app_name}. All rights reserved.
        <span class="footer-version">v{app_version} (Build: {build_date})</span>
    </div>
    <div class="footer-links">
        Developed by <a href="https://amancreates.netlify.app" target="_blank">{app_developer}</a> | 
        <a href="https://www.linkedin.com/in/aman-jha-0bb578211" target="_blank">LinkedIn</a> | 
        <a href="https://www.instagram.com/codingtravis_aman" target="_blank">@codingtravis_</a>
    </div>
</div>
""", unsafe_allow_html=True)

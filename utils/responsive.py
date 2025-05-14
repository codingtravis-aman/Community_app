import streamlit as st

def get_device_type():
    """
    Detect the user's device type based on viewport width.
    Returns: 'mobile', 'tablet', or 'desktop'
    """
    # This requires JavaScript to detect screen width
    # We'll set a default and use CSS media queries for most of the responsive work
    return "desktop"

def apply_responsive_styles():
    """
    Apply responsive CSS styles for different device types.
    This improves the mobile experience significantly.
    """
    responsive_css = """
    <style>
        /* Base styles for all devices */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        
        /* Mobile styles (max-width: 640px) */
        @media (max-width: 640px) {
            .main .block-container {
                padding-left: 0.5rem;
                padding-right: 0.5rem;
                padding-top: 0.5rem;
            }
            h1 {
                font-size: 1.8rem !important;
            }
            h2 {
                font-size: 1.4rem !important;
            }
            h3 {
                font-size: 1.2rem !important;
            }
            .stButton > button {
                width: 100%;
            }
            .mobile-hidden {
                display: none !important;
            }
            .mobile-smaller {
                font-size: 0.8rem !important;
            }
            /* Make cards stack on mobile */
            div[data-testid="column"] {
                width: 100% !important;
                margin-bottom: 1rem;
            }
            /* Sidebar adjustments */
            section[data-testid="stSidebar"] {
                width: 80% !important;
                min-width: unset !important;
            }
            /* Reduce padding in forms */
            div[data-testid="stVerticalBlock"] > div {
                padding-top: 0.25rem !important;
                padding-bottom: 0.25rem !important;
            }
        }
        
        /* Tablet styles (max-width: 1024px) */
        @media (min-width: 641px) and (max-width: 1024px) {
            .tablet-smaller {
                font-size: 0.9rem !important;
            }
            /* Adjust column layout for tablets */
            div[data-testid="column"]:nth-of-type(2n) {
                margin-right: 0 !important;
            }
        }

        /* Card component for responsive layout */
        .card {
            border-radius: 0.5rem;
            padding: 1rem;
            margin-bottom: 1rem;
            background-color: #f8f9fa;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        }
        
        /* Responsive grid system */
        .grid-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
        }
        
        /* Responsive table */
        .responsive-table {
            width: 100%;
            overflow-x: auto;
        }
        
        /* Bottom navigation for mobile */
        .mobile-bottom-nav {
            display: none;
        }
        
        @media (max-width: 640px) {
            .mobile-bottom-nav {
                display: flex;
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                background: #ffffff;
                box-shadow: 0 -2px 5px rgba(0,0,0,0.1);
                z-index: 1000;
                justify-content: space-around;
                padding: 0.5rem 0;
            }
            .mobile-bottom-nav a {
                text-align: center;
                padding: 0.5rem;
                color: #555;
                text-decoration: none;
                font-size: 0.7rem;
            }
            .mobile-bottom-nav a.active {
                color: #1E88E5;
            }
            .mobile-bottom-nav-icon {
                font-size: 1.2rem;
                margin-bottom: 0.2rem;
            }
            
            /* Add padding to bottom of page to account for nav bar */
            body {
                padding-bottom: 4rem;
            }
        }
    </style>
    """
    st.markdown(responsive_css, unsafe_allow_html=True)

def create_responsive_grid(columns=3, content_list=None, style="card"):
    """
    Create a responsive grid layout that adjusts based on screen size.
    
    Parameters:
    columns (int): Number of columns on desktop
    content_list (list): List of items to display in the grid
    style (str): 'card' or 'simple'
    
    Returns:
    List of columns that can be used to insert content
    """
    if content_list:
        # Use the grid CSS for automatic responsiveness
        grid_html = '<div class="grid-container">'
        for item in content_list:
            if style == "card":
                grid_html += f'<div class="card">{item}</div>'
            else:
                grid_html += f'<div>{item}</div>'
        grid_html += '</div>'
        
        st.markdown(grid_html, unsafe_allow_html=True)
        return None
    else:
        # Return columns for manual content insertion
        return st.columns(columns)

def responsive_text(text, size="normal", align="left"):
    """
    Display text that adjusts size based on device.
    """
    css_class = ""
    if size == "small":
        css_class = "mobile-smaller tablet-smaller"
    elif size == "large":
        css_class = "mobile-normal tablet-normal"
    
    text_html = f'<div class="{css_class}" style="text-align: {align}">{text}</div>'
    st.markdown(text_html, unsafe_allow_html=True)

def add_mobile_bottom_nav(pages):
    """
    Add a mobile-only bottom navigation bar.
    
    Parameters:
    pages (dict): Dictionary of page names and their icons
    """
    current_page = st.session_state.get('page', 'Home')
    
    nav_html = '<div class="mobile-bottom-nav">'
    for page_name, icon in pages.items():
        active_class = "active" if page_name == current_page else ""
        nav_html += f'''
        <a href="#" onclick="changePage('{page_name}')" class="{active_class}">
            <div class="mobile-bottom-nav-icon">{icon}</div>
            <div>{page_name}</div>
        </a>
        '''
    nav_html += '</div>'
    
    # Add JavaScript for navigation
    nav_html += '''
    <script>
        function changePage(pageName) {
            // In a real implementation, we'd use a more sophisticated approach
            // For now, we'll just store the page name and reload
            localStorage.setItem('currentPage', pageName);
            window.location.reload();
        }
    </script>
    '''
    
    st.markdown(nav_html, unsafe_allow_html=True)

def mobile_optimized_container():
    """
    Create a container that's optimized for mobile viewing.
    """
    # This is a simple wrapper for now, but could be extended with more features
    return st.container()

def create_responsive_card(title, content, footer=None, color="#1E88E5"):
    """
    Create a card component that's responsive on different devices.
    """
    card_html = f'''
    <div style="border-radius: 5px; border-left: 5px solid {color}; padding: 1rem; 
               margin-bottom: 1rem; background-color: white; box-shadow: 0 1px 3px rgba(0,0,0,0.12);">
        <h3 style="margin-top: 0; color: {color};">{title}</h3>
        <div>{content}</div>
        {f'<div style="margin-top: 0.5rem; font-size: 0.8rem; color: #666;">{footer}</div>' if footer else ''}
    </div>
    '''
    st.markdown(card_html, unsafe_allow_html=True)
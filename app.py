import streamlit as st
import importlib
import database
import ui_components
importlib.reload(ui_components)

# Ensure DB tables exist before any page renders
database.init_db()

def load_css(file_name: str):
    """Loads a custom CSS file."""
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def main():
    # Set page configuration
    st.set_page_config(
        page_title="MedSim AI",
        page_icon="🩺",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Load custom CSS
    load_css("assets/style.css")

    # Initialize Session State Variables
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'auth_login'
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None  # 'instructor' or 'student'
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None

    # Render top navigation if the user is logged in
    if st.session_state.current_page not in ['auth_login', 'auth_register']:
        ui_components.render_top_nav()

    # Router
    page = st.session_state.current_page
    if page == 'auth_login':
        ui_components.render_login()
    elif page == 'auth_register':
        ui_components.render_register()
    elif page == 'dashboard':
        ui_components.render_dashboard(st.session_state.user_role)
    elif page == 'create_sim':
        ui_components.render_create_simulation()
    elif page == 'review_sim':
        ui_components.render_review_simulation()
    elif page == 'play_sim':
        ui_components.render_simulation_player()
    elif page == 'results':
        ui_components.render_results()
    elif page == 'assistant':
        ui_components.render_assistant()
    elif page == 'my_scenarios':
        ui_components.render_my_scenarios()
    else:
        st.error("Page not found.")

if __name__ == "__main__":
    main()

import streamlit as st
import os
from components.auth import login_page, logout
from config.database import init_connection

# --- Inject custom CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css(os.path.join("assets", "style.css"))  # Make sure assets/style.css exists

# --- Page config ---
st.set_page_config(
    page_title="Scholarship Management System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DB Connect ---
init_connection()

# --- Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.user_name = None

# --- Main ---
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        with st.sidebar:
            st.markdown(
                f"<div style='padding:1em 0'><span style='font-size:1.2em;'>✅ Logged in as <b>{st.session_state.username}</b></span></div>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div style='color:#3C82F5;font-weight:bold;'>Role: {st.session_state.user_role}</div>",
                unsafe_allow_html=True
            )
            if st.button("🚪 Logout", use_container_width=True):
                logout()
                st.rerun()
            st.divider()
            st.markdown("### 📍 Navigation")
            if st.session_state.user_role == "Student":
                if st.button("🎓 Student Dashboard", use_container_width=True):
                    st.switch_page("pages/student_portal.py")
            elif st.session_state.user_role == "Provider":
                if st.button("🏢 Provider Dashboard", use_container_width=True):
                    st.switch_page("pages/provider_portal.py")
            elif st.session_state.user_role == "Admin":
                if st.button("👨‍💼 Admin Dashboard", use_container_width=True):
                    st.switch_page("pages/admin_portal.py")

        st.markdown("<h1 style='font-family:Poppins,sans-serif;color:#3C82F5;'>🎓 Scholarship Management System</h1>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

        # Section with cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("👥 Students - Browse and apply for scholarships")
        with col2:
            st.success("🏢 Providers - Create and manage scholarships")
        with col3:
            st.warning("👨‍💼 Admins - Oversee the entire system")

        st.markdown("---")

        # Quick access buttons
        if st.session_state.user_role == "Student":
            col1, col2, col3 = st.columns(3)
            with col2:
                if st.button("🔍 Browse Scholarships", use_container_width=True, type="primary"):
                    st.switch_page("pages/student_portal.py")
        elif st.session_state.user_role == "Provider":
            col1, col2, col3 = st.columns(3)
            with col2:
                if st.button("➕ Manage Scholarships", use_container_width=True, type="primary"):
                    st.switch_page("pages/provider_portal.py")
        elif st.session_state.user_role == "Admin":
            col1, col2, col3 = st.columns(3)
            with col2:
                if st.button("📊 View Dashboard", use_container_width=True, type="primary"):
                    st.switch_page("pages/admin_portal.py")

        st.markdown("---")
        st.markdown(
            f"<div style='text-align:center;font-size:1.5em;font-family:Poppins;color:#22223B;'>Welcome back, <b>{st.session_state.user_name}</b>! 👋</div>",
            unsafe_allow_html=True
        )

        if st.session_state.user_role == "Student":
            st.info("💡 Start browsing available scholarships and submit your applications!")
        elif st.session_state.user_role == "Provider":
            st.info("💡 Create new scholarships and manage applications from students.")
        elif st.session_state.user_role == "Admin":
            st.info("💡 Review pending providers and manage the scholarship system.")

if __name__ == "__main__":
    main()

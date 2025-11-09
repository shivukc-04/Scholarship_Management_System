import streamlit as st
from config.database import execute_query

def login_page():
    """Display login/registration page"""
    st.title("🎓 Scholarship Management System")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
    
    with tab1:
        login_form()
    
    with tab2:
        register_form()

def login_form():
    """Login form"""
    st.subheader("Login to Your Account")
    
    role = st.selectbox("Select Role", ["Student", "Provider", "Admin"])
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("🔓 Login", use_container_width=True):
        if username and password:
            user = authenticate_user(username, password, role)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_role = role
                st.session_state.user_id = user['id']
                st.session_state.username = username
                st.session_state.user_name = user.get('name', username)
                st.success(f"✅ Welcome back, {username}!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
        else:
            st.warning("⚠️ Please fill in all fields")

def register_form():
    """Registration form"""
    st.subheader("Create New Account")
    
    role = st.selectbox("Register as", ["Student", "Provider"], key="reg_role")
    
    if role == "Student":
        register_student()
    else:
        register_provider()

def register_student():
    """Student registration form"""
    with st.form("student_register"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username*")
            password = st.text_input("Password*", type="password")
            name = st.text_input("Full Name*")
            email = st.text_input("Email*")
        
        with col2:
            dob = st.date_input("Date of Birth*")
            college = st.text_input("College Name*")
            year = st.number_input("Year of Study*", min_value=1, max_value=5, value=1)
            gpa = st.number_input("GPA (0.00-4.00)*", min_value=0.0, max_value=10.0, value=7.5, step=0.01, format="%.2f")
        
        submit = st.form_submit_button("📝 Register", use_container_width=True)
        
        if submit:
            if all([username, password, name, email, college]):
                query = """
                INSERT INTO Student (username, passh, Name, Email, dob, College, Yearof_study, GPA)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                result = execute_query(query, (username, password, name, email, dob, college, year, gpa))
                if result:
                    st.success("✅ Registration successful! Please login.")
                    st.balloons()
                else:
                    st.error("❌ Registration failed. Username or email may already exist.")
            else:
                st.warning("⚠️ Please fill in all required fields marked with *")

def register_provider():
    """Provider registration form - NOW WITH USERNAME"""
    with st.form("provider_register"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username*")  
            password = st.text_input("Password*", type="password")
            org_name = st.text_input("Organization Name*")
            provider_name = st.text_input("Contact Person Name*")
            email = st.text_input("Email*")
        
        with col2:
            website = st.text_input("Website")
            phone = st.text_input("Phone*")
            address = st.text_area("Address*")
        
        submit = st.form_submit_button("📝 Register", use_container_width=True)
        
        if submit:
            # Check all required fields including username
            if all([username, password, org_name, provider_name, email, phone, address]):
                query = """
                INSERT INTO Provider (username, OrganizationName, ProviderName, Email, passh, website, Phone, Address)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                result = execute_query(query, (username, org_name, provider_name, email, password, website, phone, address))
                if result:
                    st.success("✅ Registration successful! Please wait for admin approval.")
                    st.info("ℹ️ Your account status is 'Inactive'. An admin will review and activate your account.")
                    st.balloons()
                else:
                    st.error("❌ Registration failed. Username or email may already exist.")
            else:
                st.warning("⚠️ Please fill in all required fields marked with *")

def authenticate_user(username, password, role):
    """Authenticate user based on role (plain text password comparison)"""
    table_map = {
        "Student": ("Student", "StudentID", "Name"),
        "Provider": ("Provider", "ProviderID", "ProviderName"),
        "Admin": ("Admin", "AdminID", "Name")
    }
    
    table, id_field, name_field = table_map[role]
    
    # Special check for Provider - must be Active
    if role == "Provider":
        query = f"SELECT {id_field} as id, passh, {name_field} as name, statusof_provider FROM {table} WHERE username = %s"
    else:
        query = f"SELECT {id_field} as id, passh, {name_field} as name FROM {table} WHERE username = %s"
    
    result = execute_query(query, (username,), fetch=True)
    
    if result and len(result) > 0:
        user = result[0]
        
        # Check if provider is active
        if role == "Provider" and user.get('statusof_provider') != 'Active':
            st.error("❌ Your provider account is not yet approved by admin.")
            return None
        
        # Compare passwords directly (plain text)
        if password == user['passh']:
            return user
    
    return None

def logout():
    """Logout user"""
    st.session_state.logged_in = True
    st.session_state.user_role = None
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.user_name = None

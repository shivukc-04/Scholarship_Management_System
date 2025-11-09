import mysql.connector
from mysql.connector import Error
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

def init_connection():
    """Initialize database connection and store in session state"""
    if 'db_connection' not in st.session_state:
        try:
            connection = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME'),
                port=int(os.getenv('DB_PORT', 3306)),
                autocommit=False
            )
            if connection.is_connected():
                st.session_state.db_connection = connection
                return connection
        except Error as e:
            st.error(f"Database connection failed: {e}")
            return None
    return st.session_state.db_connection

def get_connection():
    """Get active database connection"""
    if 'db_connection' not in st.session_state or not st.session_state.db_connection.is_connected():
        return init_connection()
    return st.session_state.db_connection

def execute_query(query, params=None, fetch=False):
    """Execute a query and return results"""
    connection = get_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetch:
            result = cursor.fetchall()
            cursor.close()
            return result
        else:
            connection.commit()
            cursor.close()
            return True
    except Error as e:
        st.error(f"Query execution failed: {e}")
        connection.rollback()
        return None

def call_procedure(proc_name, params=None):
    """Call a stored procedure"""
    connection = get_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.callproc(proc_name, params or ())
        
        results = []
        for result in cursor.stored_results():
            results.extend(result.fetchall())
        
        cursor.close()
        connection.commit()
        return results
    except Error as e:
        st.error(f"Procedure call failed: {e}")
        connection.rollback()
        return None

def execute_function(func_name, params):
    """Execute a stored function"""
    connection = get_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        placeholders = ', '.join(['%s'] * len(params))
        query = f"SELECT {func_name}({placeholders}) as result"
        cursor.execute(query, params)
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None
    except Error as e:
        st.error(f"Function execution failed: {e}")
        return None

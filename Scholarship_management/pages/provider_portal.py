import streamlit as st
import os
from utils.queries import (
    create_scholarship,
    get_provider_scholarships,
    get_scholarship_applications,
    update_scholarship,
    get_provider_stats,
    get_total_allocated_amount
)
import pandas as pd
from datetime import datetime, date

# --- Custom CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css(os.path.join("assets", "style.css"))

# --- Auth check ---
if not st.session_state.get('logged_in') or st.session_state.get('user_role') != 'Provider':
    st.error("⛔ Access Denied: Providers only")
    st.stop()

# --- Header ---
st.markdown("<h1 style='font-family:Poppins,sans-serif;color:#3C82F5;'>🏢 Provider Dashboard</h1>", unsafe_allow_html=True)
st.markdown(f"<div style='font-size:1.1em;color:#22223B;'>Welcome, <b>{st.session_state.user_name}</b>!</div>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["➕ Create Scholarship", "📊 My Scholarships", "📈 Analytics"])

# TAB 1: Create Scholarship
with tab1:
    st.subheader("➕ Create New Scholarship")
    with st.form("create_scholarship"):
        title = st.text_input("Scholarship Title*")
        description = st.text_area("Description*", height=150)

        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("Scholarship Amount (₹)*", min_value=100, value=1000, step=100)
            max_students = st.number_input("Maximum Students*", min_value=1, value=10, step=1)
        with col2:
            deadline = st.date_input("Application Deadline*", min_value=date.today())
            min_gpa = st.number_input("Minimum GPA Required*", min_value=0.0, max_value=10.0, value=7.5, step=0.1, format="%.2f")

        submit = st.form_submit_button("🚀 Create Scholarship", use_container_width=True, type="primary")

        if submit:
            if all([title, description, amount, max_students, deadline, min_gpa]):
                result = create_scholarship(
                    st.session_state.user_id,
                    title,
                    description,
                    amount,
                    max_students,
                    deadline,
                    min_gpa
                )
                if result:
                    st.success("✅ Scholarship created successfully!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Failed to create scholarship.")
            else:
                st.warning("⚠️ Please fill in all required fields.")

# TAB 2: My Scholarships
with tab2:
    st.subheader("📊 My Scholarships")
    scholarships = get_provider_scholarships(st.session_state.user_id)

    if scholarships:
        # Metrics
        total_scholarships = len(scholarships)
        total_amount = sum(float(s['Amount']) for s in scholarships)
        total_applications = sum(s['TotalApplications'] or 0 for s in scholarships)
        total_awarded = sum(s['AwardedCount'] or 0 for s in scholarships)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📚 Total Scholarships", total_scholarships)
        col2.metric("💰 Total Amount", f"₹{total_amount:,.2f}")
        col3.metric("📝 Applications", total_applications)
        col4.metric("🏆 Awarded", total_awarded)
        st.markdown("---")

        # Scholarship cards
        for scholarship in scholarships:
            with st.expander(f"{scholarship['Title']} - ₹{float(scholarship['Amount']):,.2f}", expanded=False):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Description:** {scholarship['Description']}")
                    st.markdown(f"**Min GPA:** {float(scholarship['min_GPA']):.2f}")
                    st.markdown(f"**Deadline:** {scholarship['Deadline'].strftime('%Y-%m-%d')}")
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Max Students", scholarship['MaxStudents'])
                    with col_b:
                        st.metric("Applications", scholarship['TotalApplications'] or 0)
                    with col_c:
                        st.metric("Awarded", scholarship['AwardedCount'] or 0)

                    # Progress bar for awarded spots
                    if scholarship['MaxStudents'] > 0:
                        awarded_count = scholarship['AwardedCount'] or 0
                        max_students = scholarship['MaxStudents']
                        progress = float(awarded_count) / float(max_students)
                        st.progress(progress)
                        remaining = max_students - awarded_count
                        st.caption(f"{remaining} spots remaining")

                with col2:
                    if scholarship['status'] == 'Open':
                        st.success(f"✅ {scholarship['status']}")
                    elif scholarship['status'] == 'Closed':
                        st.error(f"🔒 {scholarship['status']}")
                    else:
                        st.warning(f"⏳ {scholarship['status']}")

                    # Edit button
                    if st.button("✏️ Edit", key=f"edit_{scholarship['ScholarshipID']}", use_container_width=True):
                        st.session_state[f"editing_{scholarship['ScholarshipID']}"] = True
                        st.rerun()

                # Edit form
                if st.session_state.get(f"editing_{scholarship['ScholarshipID']}", False):
                    st.markdown("---")
                    st.markdown("### Edit Scholarship")
                    with st.form(f"edit_form_{scholarship['ScholarshipID']}"):
                        edit_title = st.text_input("Title", value=scholarship['Title'])
                        edit_description = st.text_area("Description", value=scholarship['Description'])

                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            edit_amount = st.number_input("Amount", value=float(scholarship['Amount']))
                            edit_max = st.number_input("Max Students", value=scholarship['MaxStudents'])
                        with col_e2:
                            edit_deadline = st.date_input("Deadline", value=scholarship['Deadline'])
                            edit_gpa = st.number_input("Min GPA", value=float(scholarship['min_GPA']), step=0.1, format="%.2f")

                        edit_status = st.selectbox("Status", ["Open", "Closed", "Under Review"],
                                                  index=["Open", "Closed", "Under Review"].index(scholarship['status']))

                        col_s1, col_s2 = st.columns(2)
                        with col_s1:
                            save_btn = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
                        with col_s2:
                            cancel_btn = st.form_submit_button("❌ Cancel", use_container_width=True)

                        if save_btn:
                            result = update_scholarship(
                                scholarship['ScholarshipID'],
                                edit_title,
                                edit_description,
                                edit_amount,
                                edit_max,
                                edit_deadline,
                                edit_gpa,
                                edit_status
                            )
                            if result:
                                st.success("✅ Scholarship updated!")
                                del st.session_state[f"editing_{scholarship['ScholarshipID']}"]
                                st.rerun()
                            else:
                                st.error("❌ Update failed.")

                        if cancel_btn:
                            del st.session_state[f"editing_{scholarship['ScholarshipID']}"]
                            st.rerun()

                # Show applications
                st.markdown("---")
                st.markdown("### 📝 Applications")
                applications = get_scholarship_applications(scholarship['ScholarshipID'])
                if applications:
                    df = pd.DataFrame(applications)
                    df['GPA'] = df['GPA'].astype(float)
                    df = df[['StudentName', 'StudentEmail', 'College', 'GPA', 'Yearof_study', 'DateApplied', 'Status']]
                    df.columns = ['Name', 'Email', 'College', 'GPA', 'Year', 'Applied Date', 'Status']
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No applications yet.")
    else:
        st.info("📭 You haven't created any scholarships yet. Create one above!")

# TAB 3: Analytics
with tab3:
    st.subheader("📈 Performance Analytics")
    stats = get_provider_stats(st.session_state.user_id)
    total_allocated = get_total_allocated_amount(st.session_state.user_id)
    total_allocated_float = float(total_allocated) if total_allocated else 0.0
    st.metric("💰 Total Amount Allocated", f"₹{total_allocated_float:,.2f}")
    st.markdown("---")
    if stats:
        df = pd.DataFrame(stats)
        df['Amount'] = df['Amount'].astype(float)
        df['TotalAmountGranted'] = df['TotalAmountGranted'].astype(float)
        st.markdown("### Scholarship Performance")
        display_df = df[['Title', 'Amount', 'TotalApplications', 'StudentsAwarded', 'TotalAmountGranted']].copy()
        display_df.columns = ['Scholarship', 'Amount', 'Applications', 'Awarded', 'Total Granted']
        display_df['Amount'] = display_df['Amount'].apply(lambda x: f"₹{x:,.2f}")
        display_df['Total Granted'] = display_df['Total Granted'].apply(lambda x: f"₹{x:,.2f}" if pd.notna(x) else "₹0.00")
        st.dataframe(display_df, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Applications by Scholarship")
            chart_data = df[['Title', 'TotalApplications']].set_index('Title')
            st.bar_chart(chart_data)
        with col2:
            st.markdown("### Awards by Scholarship")
            chart_data = df[['Title', 'StudentsAwarded']].set_index('Title')
            st.bar_chart(chart_data)
    else:
        st.info("📭 No data available yet. Create scholarships to see analytics!")

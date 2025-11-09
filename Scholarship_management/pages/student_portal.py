import streamlit as st
import os
from utils.queries import (
    get_available_scholarships, 
    apply_for_scholarship, 
    get_student_applications,
    get_student_profile,
    update_student_profile,
    upload_document,
    get_application_documents
)
import pandas as pd
from datetime import datetime, date

# --- Custom CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css(os.path.join("assets", "style.css"))  # Ensure assets/style.css exists

# --- Auth check ---
if not st.session_state.get('logged_in') or st.session_state.get('user_role') != 'Student':
    st.error("⛔ Access Denied: Students only")
    st.stop()

# --- Header ---
st.markdown("<h1 style='font-family:Poppins,sans-serif;color:#3C82F5;'>🎓 Student Dashboard</h1>", unsafe_allow_html=True)
st.markdown(f"<div style='font-size:1.1em;color:#22223B;'>Welcome, <b>{st.session_state.user_name}</b>!</div>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["📚 Browse Scholarships", "📝 My Applications", "👤 Profile"])

# TAB 1: Browse Scholarships
with tab1:
    st.subheader("📚 Available Scholarships")
    scholarships = get_available_scholarships(st.session_state.user_id)
    if scholarships:
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_eligibility = st.selectbox("Filter by Eligibility", ["All", "Eligible Only", "Not Eligible"])
        with col2:
            min_amount = st.number_input("Minimum Amount per Student (₹)", min_value=0, value=0, step=100)
        with col3:
            max_gpa = st.number_input("Max Required GPA", min_value=0.0, max_value=10.0, value=7.5, step=0.1)
        filtered_scholarships = scholarships
        if filter_eligibility == "Eligible Only":
            filtered_scholarships = [s for s in filtered_scholarships if s['EligibilityStatus'] == 'Eligible']
        elif filter_eligibility == "Not Eligible":
            filtered_scholarships = [s for s in filtered_scholarships if s['EligibilityStatus'] == 'Not Eligible']
        filtered_scholarships = [
            s for s in filtered_scholarships 
            if (float(s['Amount']) / s['MaxStudents']) >= min_amount and float(s['min_GPA']) <= max_gpa
        ]
        st.markdown(f"<div style='background:#eaf4fd;padding:0.7em 1em;border-radius:8px;font-weight:500;'>📊 Showing <b>{len(filtered_scholarships)}</b> scholarships</div>", unsafe_allow_html=True)
        for scholarship in filtered_scholarships:
            amount_per_student = float(scholarship['Amount']) / scholarship['MaxStudents']
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### {scholarship['Title']}")
                    st.markdown(f"**Organization:** {scholarship['OrganizationName']}")
                    if scholarship.get('website'):
                        st.markdown(f"🌐 [Website]({scholarship['website']})")
                    st.markdown(f"**Description:** {scholarship['Description']}")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("💰 Amount per Student", f"₹{amount_per_student:,.2f}")
                    with col_b:
                        st.metric("📅 Deadline", scholarship['Deadline'].strftime('%Y-%m-%d'))
                    st.markdown(f"**Minimum GPA Required:** {float(scholarship['min_GPA']):.2f}")
                with col2:
                    if scholarship['EligibilityStatus'] == 'Eligible':
                        st.success("✅ Eligible")
                    else:
                        st.error("❌ Not Eligible")
                    st.caption(f"Your GPA: {float(scholarship['StudentGPA']):.2f}")
                    st.caption(f"Required: {float(scholarship['min_GPA']):.2f}")
                    if scholarship['AlreadyApplied'] > 0:
                        st.info("✓ Applied")
                    elif scholarship['EligibilityStatus'] == 'Eligible':
                        if st.button(f"📝 Apply Now", key=f"apply_{scholarship['ScholarshipID']}", use_container_width=True, type="primary"):
                            st.session_state[f"show_apply_form_{scholarship['ScholarshipID']}"] = True
                            st.rerun()
                    else:
                        st.button("🚫 Ineligible", disabled=True, use_container_width=True)
                if st.session_state.get(f"show_apply_form_{scholarship['ScholarshipID']}", False):
                    st.markdown("---")
                    st.markdown("### 📝 Application Form")
                    st.info("Please upload all required documents to complete your application.")
                    with st.form(f"application_form_{scholarship['ScholarshipID']}"):
                        st.markdown("#### Required Documents")
                        transcript = st.file_uploader("📄 Transcript*", type=['pdf', 'jpg', 'jpeg', 'png'], key=f"transcript_{scholarship['ScholarshipID']}")
                        photo = st.file_uploader("📷 Passport Size Photo*", type=['jpg', 'jpeg', 'png'], key=f"photo_{scholarship['ScholarshipID']}")
                        income_cert = st.file_uploader("📋 Income/Caste Certificate*", type=['pdf', 'jpg', 'jpeg', 'png'], key=f"income_{scholarship['ScholarshipID']}")
                        aadhar = st.file_uploader("🪪 Aadhar Card*", type=['pdf', 'jpg', 'jpeg', 'png'], key=f"aadhar_{scholarship['ScholarshipID']}")
                        st.markdown("---")
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            submit_btn = st.form_submit_button("✅ Submit Application", use_container_width=True, type="primary")
                        with col_btn2:
                            cancel_btn = st.form_submit_button("❌ Cancel", use_container_width=True)
                        if submit_btn:
                            if all([transcript, photo, income_cert, aadhar]):
                                result = apply_for_scholarship(st.session_state.user_id, scholarship['ScholarshipID'])
                                if result:
                                    from config.database import execute_query
                                    query = """
                                    SELECT ApplicationID FROM Application 
                                    WHERE StudentID = %s AND ScholarshipID = %s 
                                    ORDER BY ApplicationID DESC LIMIT 1
                                    """
                                    app_result = execute_query(query, (st.session_state.user_id, scholarship['ScholarshipID']), fetch=True)
                                    if app_result:
                                        application_id = app_result[0]['ApplicationID']
                                        doc_success = True
                                        docs = [
                                            (transcript, "Transcript"),
                                            (photo, "passportsize-photo"),
                                            (income_cert, "income-caste certificate"),
                                            (aadhar, "adhar card")
                                        ]
                                        for file, doc_type in docs:
                                            file_data = file.read()
                                            if not upload_document(application_id, doc_type, file_data):
                                                doc_success = False
                                                break
                                        if doc_success:
                                            st.success("✅ Application and documents submitted successfully!")
                                            st.balloons()
                                            del st.session_state[f"show_apply_form_{scholarship['ScholarshipID']}"]
                                            st.rerun()
                                        else:
                                            st.error("⚠️ Application submitted but some documents failed to upload. Please upload them from 'My Applications' tab.")
                                            del st.session_state[f"show_apply_form_{scholarship['ScholarshipID']}"]
                                            st.rerun()
                                    else:
                                        st.error("❌ Application submission failed. You may have already applied.")
                            else:
                                st.warning("⚠️ Please upload all required documents marked with *")
                        if cancel_btn:
                            del st.session_state[f"show_apply_form_{scholarship['ScholarshipID']}"]
                            st.rerun()
                    st.divider()
    else:
        st.info("📭 No scholarships available at the moment.")

# TAB 2: My Applications
with tab2:
    st.subheader("📝 My Applications")
    applications = get_student_applications(st.session_state.user_id)
    if applications:
        total_apps = len(applications)
        pending = sum(1 for a in applications if a['Status'] == 'Pending')
        approved = sum(1 for a in applications if a['Status'] == 'Approved')
        awarded = sum(1 for a in applications if a['Status'] == 'Awarded')
        rejected = sum(1 for a in applications if a['Status'] == 'Rejected')
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total", total_apps)
        col2.metric("⏳ Pending", pending)
        col3.metric("✅ Approved", approved)
        col4.metric("🏆 Awarded", awarded)
        col5.metric("❌ Rejected", rejected)
        st.markdown("---")
        for app in applications:
            with st.expander(f"{app['ScholarshipTitle']} - {app['OrganizationName']}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Application ID:** {app['ApplicationID']}")
                    st.markdown(f"**Applied On:** {app['DateApplied'].strftime('%Y-%m-%d')}")
                    st.markdown(f"**Deadline:** {app['Deadline'].strftime('%Y-%m-%d')}")
                with col2:
                    if app['Status'] == 'Pending':
                        st.warning(f"⏳ Status: **{app['Status']}**")
                    elif app['Status'] == 'Approved':
                        st.success(f"✅ Status: **{app['Status']}**")
                    elif app['Status'] == 'Awarded':
                        st.success(f"🏆 Status: **{app['Status']}**")
                        if app['Award_date']:
                            st.markdown(f"**Award Date:** {app['Award_date'].strftime('%Y-%m-%d')}")
                        if app['Amount_Granted']:
                            st.markdown(f"**Amount Granted:** ₹{float(app['Amount_Granted']):,.2f}")
                    else:
                        st.error(f"❌ Status: **{app['Status']}**")
                st.markdown("---")
                st.markdown("### 📄 Uploaded Documents")
                docs = get_application_documents(app['ApplicationID'])
                if docs:
                    for doc in docs:
                        col_d1, col_d2, col_d3 = st.columns([2, 1, 1])
                        with col_d1:
                            st.text(f"📄 {doc['DocTypeID']}")
                        with col_d2:
                            st.text(f"Size: {doc['FileSize'] / 1024:.2f} KB")
                        with col_d3:
                            st.text(f"✓ Uploaded")
                else:
                    st.info("📭 No documents uploaded yet.")
                    if app['Status'] == 'Pending':
                        if st.button(f"📤 Upload Documents", key=f"upload_docs_{app['ApplicationID']}", use_container_width=True):
                            st.session_state[f"show_doc_upload_{app['ApplicationID']}"] = True
                            st.rerun()
                        if st.session_state.get(f"show_doc_upload_{app['ApplicationID']}", False):
                            with st.form(f"doc_upload_form_{app['ApplicationID']}"):
                                st.markdown("#### Upload Missing Documents")
                                transcript = st.file_uploader("📄 Transcript", type=['pdf', 'jpg', 'jpeg', 'png'], key=f"up_transcript_{app['ApplicationID']}")
                                photo = st.file_uploader("📷 Passport Size Photo", type=['jpg', 'jpeg', 'png'], key=f"up_photo_{app['ApplicationID']}")
                                income_cert = st.file_uploader("📋 Income/Caste Certificate", type=['pdf', 'jpg', 'jpeg', 'png'], key=f"up_income_{app['ApplicationID']}")
                                aadhar = st.file_uploader("🪪 Aadhar Card", type=['pdf', 'jpg', 'jpeg', 'png'], key=f"up_aadhar_{app['ApplicationID']}")
                                col_u1, col_u2 = st.columns(2)
                                with col_u1:
                                    upload_btn = st.form_submit_button("✅ Upload", use_container_width=True, type="primary")
                                with col_u2:
                                    cancel_upload_btn = st.form_submit_button("❌ Cancel", use_container_width=True)
                                if upload_btn:
                                    docs_to_upload = [
                                        (transcript, "Transcript"),
                                        (photo, "passportsize-photo"),
                                        (income_cert, "income-caste certificate"),
                                        (aadhar, "adhar card")
                                    ]
                                    uploaded_count = 0
                                    for file, doc_type in docs_to_upload:
                                        if file:
                                            file_data = file.read()
                                            if upload_document(app['ApplicationID'], doc_type, file_data):
                                                uploaded_count += 1
                                    if uploaded_count > 0:
                                        st.success(f"✅ {uploaded_count} document(s) uploaded successfully!")
                                        del st.session_state[f"show_doc_upload_{app['ApplicationID']}"]
                                        st.rerun()
                                    else:
                                        st.warning("⚠️ No documents selected to upload.")
                                if cancel_upload_btn:
                                    del st.session_state[f"show_doc_upload_{app['ApplicationID']}"]
                                    st.rerun()
    else:
        st.info("📭 You haven't applied to any scholarships yet.")

# TAB 3: Profile
with tab3:
    st.subheader("👤 My Profile")
    profile = get_student_profile(st.session_state.user_id)
    if profile:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Name:** {profile['Name']}")
            st.markdown(f"**Username:** {profile['username']}")
            st.markdown(f"**Email:** {profile['Email']}")
            st.markdown(f"**Date of Birth:** {profile['dob'].strftime('%Y-%m-%d')}")
        with col2:
            st.markdown(f"**College:** {profile['College']}")
            st.markdown(f"**Year of Study:** {profile['Yearof_study']}")
            st.markdown(f"**GPA:** {float(profile['GPA']):.2f}")
        st.markdown("---")
        st.markdown("### Update Profile")
        with st.form("update_profile"):
            college = st.text_input("College", value=profile['College'])
            year = st.number_input("Year of Study", min_value=1, max_value=5, value=profile['Yearof_study'])
            gpa = st.number_input("GPA", min_value=0.0, max_value=10.0, value=float(profile['GPA']), step=0.01, format="%.2f")
            submit = st.form_submit_button("💾 Update Profile", use_container_width=True)
            if submit:
                result = update_student_profile(st.session_state.user_id, college, year, gpa)
                if result:
                    st.success("✅ Profile updated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Profile update failed.")

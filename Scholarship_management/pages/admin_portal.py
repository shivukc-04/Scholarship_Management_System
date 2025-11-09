import streamlit as st
import os
from utils.queries import (
    get_pending_providers,
    approve_provider,
    reject_provider,
    get_all_applications,
    update_application_status,
    get_system_statistics,
    get_application_age,
    get_all_providers_with_scholarships,
    get_provider_scholarship_details
)
import pandas as pd

# --- Inject custom CSS for premium look ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css(os.path.join("assets", "style.css"))  # Make sure assets/style.css exists

# --- Check authentication ---
if not st.session_state.get('logged_in') or st.session_state.get('user_role') != 'Admin':
    st.error("⛔ Access Denied: Admins only")
    st.stop()

# --- Premium Header ---
st.markdown("<h1 style='font-family:Poppins,sans-serif;color:#3C82F5;'>👨‍💼 Admin Dashboard</h1>", unsafe_allow_html=True)
st.markdown(f"<div style='font-size:1.1em;color:#22223B;'>Welcome, <b>{st.session_state.user_name}</b>!</div>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# --- Stats Section ---
stats = get_system_statistics()
if stats:
    st.markdown("## ⚡ System Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Students", stats['TotalStudents'])
    col2.metric("🏢 Active Providers", stats['ActiveProviders'])
    col3.metric("📚 Open Scholarships", stats['OpenScholarships'])
    col4.metric("📝 Applications", stats['TotalApplications'])
    col5, col6, col7, col8 = st.columns(4)
    col5.metric("⏳ Pending", stats['PendingApplications'])
    col6.metric("🏆 Awarded", stats['AwardedApplications'])
    col7.metric("💰 Total Awarded", f"₹{float(stats['TotalAmountAwarded']):,.2f}" if stats['TotalAmountAwarded'] else "₹0.00")
    col8.metric("📊 Approval Rate", f"{(stats['AwardedApplications']/stats['TotalApplications']*100):.1f}%" if stats['TotalApplications'] > 0 else "0%")
st.markdown("---")

# --- Tabbed Layout ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🏢 Approve Providers",
    "📝 Review Applications",
    "🏢 Provider Overview",
    "👥 System Overview"
])

# Approve Providers Tab
with tab1:
    st.subheader("🏢 Provider Approval Queue")
    pending_providers = get_pending_providers()
    if pending_providers:
        st.markdown(f"<div style='background:#eaf4fd;padding:0.7em 1em;border-radius:8px;font-weight:500;'>📊 <b>{len(pending_providers)}</b> providers awaiting approval</div>", unsafe_allow_html=True)
        for provider in pending_providers:
            with st.expander(f"{provider['OrganizationName']} - {provider['ProviderName']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Organization:** {provider['OrganizationName']}")
                    st.markdown(f"**Contact Person:** {provider['ProviderName']}")
                    st.markdown(f"**Email:** {provider['Email']}")
                    st.markdown(f"**Phone:** {provider['Phone']}")
                    st.markdown(f"**Address:** {provider['Address']}")
                    if provider.get('website'):
                        st.markdown(f"**Website:** [{provider['website']}]({provider['website']})")
                with col2:
                    st.markdown("### Actions")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ Approve", key=f"approve_{provider['ProviderID']}", use_container_width=True, type="primary"):
                            result = approve_provider(provider['ProviderID'])
                            if result:
                                st.success("✅ Provider approved!")
                                st.rerun()
                            else:
                                st.error("❌ Approval failed.")
                    with col_b:
                        if st.button("❌ Reject", key=f"reject_{provider['ProviderID']}", use_container_width=True):
                            result = reject_provider(provider['ProviderID'])
                            if result:
                                st.success("✅ Provider rejected and removed.")
                                st.rerun()
                            else:
                                st.error("❌ Rejection failed.")
    else:
        st.success("✅ No pending provider approvals!")

# Review Applications Tab
with tab2:
    st.subheader("📝 Application Review")
    applications = get_all_applications()
    if applications:
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Approved", "Rejected", "Awarded"])
        with col2:
            search_student = st.text_input("Search Student Name")
        with col3:
            search_scholarship = st.text_input("Search Scholarship")
        filtered_apps = applications
        if status_filter != "All":
            filtered_apps = [a for a in filtered_apps if a['Status'] == status_filter]
        if search_student:
            filtered_apps = [a for a in filtered_apps if search_student.lower() in a['StudentName'].lower()]
        if search_scholarship:
            filtered_apps = [a for a in filtered_apps if search_scholarship.lower() in a['ScholarshipTitle'].lower()]
        st.markdown(f"<div style='background:#eaf4fd;padding:0.7em 1em;border-radius:8px;font-weight:500;'>📊 Showing <b>{len(filtered_apps)}</b> applications</div>", unsafe_allow_html=True)
        for app in filtered_apps:
            with st.expander(f"{app['StudentName']} → {app['ScholarshipTitle']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Student:** {app['StudentName']}")
                    st.markdown(f"**Email:** {app['StudentEmail']}")
                    st.markdown(f"**GPA:** {float(app['GPA']):.2f}")
                    st.markdown(f"**Scholarship:** {app['ScholarshipTitle']}")
                    st.markdown(f"**Provider:** {app['OrganizationName']}")
                    st.markdown(f"**Amount:** ₹{float(app['ScholarshipAmount']):,.2f}")
                    st.markdown(f"**Applied On:** {app['DateApplied'].strftime('%Y-%m-%d')}")
                    age = get_application_age(app['ApplicationID'])
                    if age is not None:
                        st.markdown(f"**Application Age:** {age} days")
                with col2:
                    # Status badges
                    if app['Status'] == 'Pending':
                        st.warning(f"⏳ Status: {app['Status']}")
                    elif app['Status'] == 'Approved':
                        st.success(f"✅ Status: {app['Status']}")
                    elif app['Status'] == 'Awarded':
                        st.success(f"🏆 Status: {app['Status']}")
                        if app['Amount_Granted']:
                            st.markdown(f"**Granted:** ₹{float(app['Amount_Granted']):,.2f}")
                    else:
                        st.error(f"❌ Status: {app['Status']}")
                    st.markdown("---")
                    st.markdown("### Update Status")
                    new_status = st.selectbox(
                        "Change Status",
                        ["Pending", "Approved", "Rejected", "Awarded"],
                        key=f"status_{app['ApplicationID']}"
                    )
                    amount_granted = None
                    if new_status == "Awarded":
                        amount_granted = st.number_input(
                            "Amount to Grant",
                            min_value=0.0,
                            value=float(app['ScholarshipAmount']),
                            step=100.0,
                            key=f"amount_{app['ApplicationID']}"
                        )
                    if st.button("💾 Update", key=f"update_{app['ApplicationID']}", use_container_width=True, type="primary"):
                        result = update_application_status(
                            app['ApplicationID'],
                            new_status,
                            st.session_state.user_id,
                            amount_granted
                        )
                        if result:
                            st.success("✅ Application updated!")
                            st.rerun()
                        else:
                            st.error("❌ Update failed. Check if scholarship award limit has been reached.")
    else:
        st.info("📭 No applications in the system yet.")

# Provider Overview Tab
with tab3:
    st.subheader("🏢 Provider & Scholarship Overview")
    providers = get_all_providers_with_scholarships()
    if providers:
        total_providers = len(providers)
        active_providers = sum(1 for p in providers if p['statusof_provider'] == 'Active')
        inactive_providers = sum(1 for p in providers if p['statusof_provider'] == 'Inactive')
        total_scholarships = sum(p['TotalScholarships'] for p in providers)
        total_scholarship_amount = sum(float(p['TotalScholarshipAmount']) for p in providers)
        total_granted = sum(float(p['TotalAmountGranted']) for p in providers)
        col1, col2, col3 = st.columns(3)
        col1.metric("🏢 Total Providers", total_providers)
        col2.metric("✅ Active", active_providers)
        col3.metric("⏳ Inactive", inactive_providers)
        col4, col5, col6 = st.columns(3)
        col4.metric("📚 Scholarships", total_scholarships)
        col5.metric("💰 Scholarship Amount", f"₹{total_scholarship_amount:,.2f}")
        col6.metric("🏆 Total Granted", f"₹{total_granted:,.2f}")
        st.markdown("---")
        provider_status_filter = st.selectbox("Filter by Provider Status", ["All", "Active", "Inactive"])
        filtered_providers = providers
        if provider_status_filter != "All":
            filtered_providers = [p for p in filtered_providers if p['statusof_provider'] == provider_status_filter]
        st.markdown(f"<div style='background:#eaf4fd;padding:0.7em 1em;border-radius:8px;font-weight:500;'>📊 Showing <b>{len(filtered_providers)}</b> providers</div>", unsafe_allow_html=True)
        for provider in filtered_providers:
            status_badge = "✅ Active" if provider['statusof_provider'] == 'Active' else "⏳ Inactive"
            with st.expander(f"{provider['OrganizationName']} - {status_badge}", expanded=False):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Organization:** {provider['OrganizationName']}")
                    st.markdown(f"**Contact Person:** {provider['ProviderName']}")
                    st.markdown(f"**Username:** {provider['username']}")
                    st.markdown(f"**Email:** {provider['Email']}")
                    st.markdown(f"**Phone:** {provider['Phone']}")
                    st.markdown(f"**Status:** {provider['statusof_provider']}")
                with col2:
                    st.metric("📚 Scholarships", provider['TotalScholarships'])
                    st.metric("💰 Total Amount", f"₹{float(provider['TotalScholarshipAmount']):,.2f}")
                    st.metric("📝 Applications", provider['TotalApplications'])
                    st.metric("🏆 Awarded", provider['TotalAwarded'] or 0)
                    st.metric("💵 Amount Granted", f"₹{float(provider['TotalAmountGranted']):,.2f}")
                if provider['TotalScholarships'] > 0:
                    st.markdown("---")
                    st.markdown("### 📚 Scholarships by This Provider")
                    scholarships = get_provider_scholarship_details(provider['ProviderID'])
                    if scholarships:
                        for sch in scholarships:
                            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                            with col_s1:
                                st.markdown(f"**{sch['Title']}**")
                                st.caption(f"Status: {sch['status']}")
                            with col_s2:
                                st.caption("Amount")
                                st.markdown(f"₹{float(sch['Amount']):,.2f}")
                            with col_s3:
                                st.caption("Applications")
                                st.markdown(f"{sch['TotalApplications']}")
                            with col_s4:
                                st.caption("Awarded")
                                st.markdown(f"{sch['StudentsAwarded'] or 0} / {sch['MaxStudents']}")
                            st.markdown("---")
    else:
        st.info("📭 No providers registered yet.")

# System Overview Tab
with tab4:
    st.subheader("📊 System Overview")
    applications = get_all_applications()
    if applications:
        df = pd.DataFrame(applications)
        df['GPA'] = df['GPA'].astype(float)
        df['ScholarshipAmount'] = df['ScholarshipAmount'].astype(float)
        if 'Amount_Granted' in df.columns:
            df['Amount_Granted'] = df['Amount_Granted'].apply(lambda x: float(x) if pd.notna(x) else 0.0)
        st.markdown("### Application Status Distribution")
        status_counts = df['Status'].value_counts()
        st.bar_chart(status_counts)
        st.markdown("### Recent Applications")
        recent_df = df.sort_values('DateApplied', ascending=False).head(10)
        display_df = recent_df[['StudentName', 'ScholarshipTitle', 'OrganizationName', 'DateApplied', 'Status']]
        display_df.columns = ['Student', 'Scholarship', 'Provider', 'Date', 'Status']
        st.dataframe(display_df, use_container_width=True)
        st.markdown("### Most Popular Scholarships")
        top_scholarships = df['ScholarshipTitle'].value_counts().head(5)
        st.bar_chart(top_scholarships)
    else:
        st.info("📭 No data available yet.")

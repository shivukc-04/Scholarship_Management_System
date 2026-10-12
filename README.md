#  Scholarship Management System

A comprehensive, role-based web portal designed to automate the entire scholarship lifecycle—from student applications and document uploads to provider management, automated eligibility checks, and administrative award distribution. Built using **Python (Streamlit)** and **MySQL** with robust business logic enforced directly at the database layer via triggers, procedures, and functions.

---

##  Key Features & User Portals

### Student Portal
* **Account Registration & Login:** Secure authentication for student profiles.
* **Smart Scholarship Discovery:** Browse open scholarships and filter by GPA, amount, and eligibility criteria.
* **Application Tracking:** Monitor application statuses in real-time (`Pending`, `Approved`, `Rejected`, `Awarded`).
* **Document Management:** Upload required academic transcripts, identity proofs, and income/caste certificates.
* **Profile Management:** Keep academic details, college info, and GPA up to date.

### Provider Portal
* **Organization Registration:** Register and submit organizational details for admin approval.
* **Scholarship Creation & Management:** Post new scholarships, define maximum seat caps, deadlines, and minimum GPA requirements.
* **Metrics & Analytics:** Track total applicants, successful awardees, and total funds committed using interactive charts.

### Admin Portal
* **Provider Approval Workflow:** Review, approve, or reject new provider signups before they can post scholarships.
* **Application Review:** Oversee system-wide applications, update statuses, and grant scholarship awards.
* **Capacity Safeguards:** Prevent over-awarding beyond scholarship limits.
* **System Analytics:** View high-level metrics, system statistics, and comprehensive visual dashboards.

---

## Tech Stack

* **Frontend & UI:** Streamlit (Python interactive web framework), Plotly (Data visualization), Pillow (Image processing)
* **Backend & Logic:** Python, Pandas, Python-Dotenv
* **Database & Automation:** MySQL, `mysql-connector-python`, Custom SQL Triggers, Stored Procedures, and Functions

---

## Database Architecture & Automated Business Rules

The system leverages advanced MySQL features to maintain data integrity and automate core business rules inside `file1.sql`:
* **GPA Eligibility Triggers:** Automatically prevent students from submitting applications if their GPA falls below the required threshold.
* **Capacity Constraints:** Database triggers ensure that the number of awarded students never exceeds the scholarship's maximum capacity.
* **Stored Procedures & Functions:** Encapsulate complex computations such as provider statistics summaries and pre-eligibility checks.

---

## Project Structure

```text
Scholarship-Management-System/
│
├── Scholarship_management/
│   ├── app.py                 # Main entry point & session router
│   ├── requirements.txt       # Project dependencies
│   ├── config/
│   │   └── database.py        # MySQL connection & query executor
│   ├── components/
│   │   └── auth.py            # Authentication & registration logic
│   ├── pages/
│   │   ├── student_portal.py  # Student dashboard & application flows
│   │   ├── provider_portal.py # Provider scholarship & applicant management
│   │   └── admin_portal.py    # Admin review, approval, and metrics dashboard
│   └── utils/
│       └── queries.py         # Core database queries & data operations
│
└── file1.sql                  # Complete MySQL schema, triggers, and procedures

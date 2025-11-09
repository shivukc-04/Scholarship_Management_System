from config.database import execute_query, call_procedure, execute_function
import pandas as pd

# ==================== STUDENT QUERIES ====================

def get_available_scholarships(student_id):
    """Get all open scholarships with eligibility status"""
    query = """
    SELECT 
        S.ScholarshipID,
        S.Title,
        S.Description,
        S.Amount,
        S.Deadline,
        S.min_GPA,
        S.MaxStudents,
        P.OrganizationName,
        P.website,
        (SELECT COUNT(*) FROM Application WHERE ScholarshipID = S.ScholarshipID AND Status = 'Awarded') as AwardedCount,
        (SELECT GPA FROM Student WHERE StudentID = %s) as StudentGPA,
        CASE 
            WHEN (SELECT GPA FROM Student WHERE StudentID = %s) >= S.min_GPA THEN 'Eligible'
            ELSE 'Not Eligible'
        END as EligibilityStatus,
        (SELECT COUNT(*) FROM Application WHERE StudentID = %s AND ScholarshipID = S.ScholarshipID) as AlreadyApplied
    FROM Scholarship S
    JOIN Provider P ON S.ProviderID = P.ProviderID
    WHERE S.status = 'Open' 
      AND S.Deadline >= CURDATE()
      AND P.statusof_provider = 'Active'
    ORDER BY S.Deadline ASC
    """
    return execute_query(query, (student_id, student_id, student_id), fetch=True)

def check_eligibility(student_gpa, scholarship_id):
    """Check if student is eligible for scholarship (calls stored procedure)"""
    return call_procedure('sp_CheckPreEligibility', (student_gpa, scholarship_id))

def apply_for_scholarship(student_id, scholarship_id):
    """Apply for a scholarship"""
    query = """
    INSERT INTO Application (StudentID, ScholarshipID, DateApplied, Status)
    VALUES (%s, %s, CURDATE(), 'Pending')
    """
    return execute_query(query, (student_id, scholarship_id))

def get_student_applications(student_id):
    """Get all applications for a student"""
    query = """
    SELECT 
        A.ApplicationID,
        A.DateApplied,
        A.Status,
        A.Award_date,
        A.Amount_Granted,
        S.Title as ScholarshipTitle,
        S.Amount as ScholarshipAmount,
        S.Deadline,
        P.OrganizationName
    FROM Application A
    JOIN Scholarship S ON A.ScholarshipID = S.ScholarshipID
    JOIN Provider P ON S.ProviderID = P.ProviderID
    WHERE A.StudentID = %s
    ORDER BY A.DateApplied DESC
    """
    return execute_query(query, (student_id,), fetch=True)

def get_student_profile(student_id):
    """Get student profile information"""
    query = """
    SELECT StudentID, username, Name, Email, dob, College, Yearof_study, GPA
    FROM Student
    WHERE StudentID = %s
    """
    result = execute_query(query, (student_id,), fetch=True)
    return result[0] if result else None

def update_student_profile(student_id, college, year, gpa):
    """Update student profile"""
    query = """
    UPDATE Student
    SET College = %s, Yearof_study = %s, GPA = %s
    WHERE StudentID = %s
    """
    return execute_query(query, (college, year, gpa, student_id))

def upload_document(application_id, doc_type, file_data):
    """Upload document for an application"""
    query = """
    INSERT INTO Document (ApplicationID, DocTypeID, file_data)
    VALUES (%s, %s, %s)
    """
    return execute_query(query, (application_id, doc_type, file_data))

def get_application_documents(application_id):
    """Get all documents for an application"""
    query = """
    SELECT DocumentID, DocTypeID, LENGTH(file_data) as FileSize
    FROM Document
    WHERE ApplicationID = %s
    """
    return execute_query(query, (application_id,), fetch=True)

# ==================== PROVIDER QUERIES ====================

def create_scholarship(provider_id, title, description, amount, max_students, deadline, min_gpa):
    """Create a new scholarship"""
    query = """
    INSERT INTO Scholarship (ProviderID, Title, Description, Amount, MaxStudents, Deadline, min_GPA, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Open')
    """
    return execute_query(query, (provider_id, title, description, amount, max_students, deadline, min_gpa))

def get_provider_scholarships(provider_id):
    """Get all scholarships for a provider"""
    query = """
    SELECT 
        S.ScholarshipID,
        S.Title,
        S.Description,
        S.Amount,
        S.MaxStudents,
        S.Deadline,
        S.min_GPA,
        S.status,
        COUNT(A.ApplicationID) as TotalApplications,
        SUM(CASE WHEN A.Status = 'Pending' THEN 1 ELSE 0 END) as PendingApplications,
        SUM(CASE WHEN A.Status = 'Awarded' THEN 1 ELSE 0 END) as AwardedCount
    FROM Scholarship S
    LEFT JOIN Application A ON S.ScholarshipID = A.ScholarshipID
    WHERE S.ProviderID = %s
    GROUP BY S.ScholarshipID
    ORDER BY S.Deadline DESC
    """
    return execute_query(query, (provider_id,), fetch=True)

def get_scholarship_applications(scholarship_id):
    """Get all applications for a specific scholarship - FIXED with StudentEmail"""
    query = """
    SELECT 
        A.ApplicationID,
        A.StudentID,
        A.DateApplied,
        A.Status,
        ST.Name as StudentName,
        ST.Email as StudentEmail,
        ST.College,
        ST.GPA,
        ST.Yearof_study
    FROM Application A
    JOIN Student ST ON A.StudentID = ST.StudentID
    WHERE A.ScholarshipID = %s
    ORDER BY A.DateApplied DESC
    """
    return execute_query(query, (scholarship_id,), fetch=True)

def update_scholarship(scholarship_id, title, description, amount, max_students, deadline, min_gpa, status):
    """Update scholarship details"""
    query = """
    UPDATE Scholarship
    SET Title = %s, Description = %s, Amount = %s, MaxStudents = %s, 
        Deadline = %s, min_GPA = %s, status = %s
    WHERE ScholarshipID = %s
    """
    return execute_query(query, (title, description, amount, max_students, deadline, min_gpa, status, scholarship_id))

def get_provider_stats(provider_id):
    """Get provider statistics"""
    results = call_procedure('sp_GetProviderStats', (provider_id,))
    return results if results else []

def get_total_allocated_amount(provider_id):
    """Get total amount allocated by provider (calls function)"""
    return execute_function('fn_GetTotalAllocatedAmount', (provider_id,))

# ==================== ADMIN QUERIES ====================

def get_pending_providers():
    """Get all providers pending approval"""
    query = """
    SELECT ProviderID, OrganizationName, ProviderName, Email, Phone, Address, website
    FROM Provider
    WHERE statusof_provider = 'Inactive'
    ORDER BY ProviderID DESC
    """
    return execute_query(query, fetch=True)

def approve_provider(provider_id):
    """Approve a provider"""
    query = """
    UPDATE Provider
    SET statusof_provider = 'Active'
    WHERE ProviderID = %s
    """
    return execute_query(query, (provider_id,))

def reject_provider(provider_id):
    """Reject/Deactivate a provider"""
    query = """
    DELETE FROM Provider WHERE ProviderID = %s
    """
    return execute_query(query, (provider_id,))

def get_all_applications():
    """Get all applications in the system"""
    query = """
    SELECT 
        A.ApplicationID,
        A.DateApplied,
        A.Status,
        A.Amount_Granted,
        ST.Name as StudentName,
        ST.Email as StudentEmail,
        ST.GPA,
        S.Title as ScholarshipTitle,
        S.Amount as ScholarshipAmount,
        P.OrganizationName
    FROM Application A
    JOIN Student ST ON A.StudentID = ST.StudentID
    JOIN Scholarship S ON A.ScholarshipID = S.ScholarshipID
    JOIN Provider P ON S.ProviderID = P.ProviderID
    ORDER BY A.DateApplied DESC
    """
    return execute_query(query, fetch=True)

def update_application_status(application_id, status, admin_id, amount_granted=None):
    """Update application status"""
    if status == 'Awarded' and amount_granted:
        query = """
        UPDATE Application
        SET Status = %s, ReviewBy = %s, Award_date = CURDATE(), Amount_Granted = %s
        WHERE ApplicationID = %s
        """
        return execute_query(query, (status, admin_id, amount_granted, application_id))
    else:
        query = """
        UPDATE Application
        SET Status = %s, ReviewBy = %s
        WHERE ApplicationID = %s
        """
        return execute_query(query, (status, admin_id, application_id))

def get_system_statistics():
    """Get system-wide statistics"""
    query = """
    SELECT 
        (SELECT COUNT(*) FROM Student) as TotalStudents,
        (SELECT COUNT(*) FROM Provider WHERE statusof_provider = 'Active') as ActiveProviders,
        (SELECT COUNT(*) FROM Scholarship WHERE status = 'Open') as OpenScholarships,
        (SELECT COUNT(*) FROM Application) as TotalApplications,
        (SELECT COUNT(*) FROM Application WHERE Status = 'Pending') as PendingApplications,
        (SELECT COUNT(*) FROM Application WHERE Status = 'Awarded') as AwardedApplications,
        (SELECT COALESCE(SUM(Amount_Granted), 0) FROM Application WHERE Status = 'Awarded') as TotalAmountAwarded
    """
    result = execute_query(query, fetch=True)
    return result[0] if result else None

def get_application_age(application_id):
    """Get application age in days (calls function)"""
    return execute_function('fn_GetApplicationAge', (application_id,))

# ==================== ADMIN QUERIES (continued) ====================

def get_all_providers_with_scholarships():
    """Get all providers with their scholarship details"""
    query = """
    SELECT 
        P.ProviderID,
        P.username,
        P.OrganizationName,
        P.ProviderName,
        P.Email,
        P.Phone,
        P.statusof_provider,
        COUNT(DISTINCT S.ScholarshipID) as TotalScholarships,
        COALESCE(SUM(S.Amount), 0) as TotalScholarshipAmount,
        COUNT(DISTINCT A.ApplicationID) as TotalApplications,
        SUM(CASE WHEN A.Status = 'Awarded' THEN 1 ELSE 0 END) as TotalAwarded,
        COALESCE(SUM(A.Amount_Granted), 0) as TotalAmountGranted
    FROM Provider P
    LEFT JOIN Scholarship S ON P.ProviderID = S.ProviderID
    LEFT JOIN Application A ON S.ScholarshipID = A.ScholarshipID
    GROUP BY P.ProviderID, P.username, P.OrganizationName, P.ProviderName, P.Email, P.Phone, P.statusof_provider
    ORDER BY P.statusof_provider DESC, P.OrganizationName ASC
    """
    return execute_query(query, fetch=True)

def get_provider_scholarship_details(provider_id):
    """Get detailed scholarship list for a specific provider"""
    query = """
    SELECT 
        S.ScholarshipID,
        S.Title,
        S.Description,
        S.Amount,
        S.MaxStudents,
        S.Deadline,
        S.min_GPA,
        S.status,
        COUNT(A.ApplicationID) as TotalApplications,
        SUM(CASE WHEN A.Status = 'Awarded' THEN 1 ELSE 0 END) as StudentsAwarded,
        COALESCE(SUM(A.Amount_Granted), 0) as AmountGranted
    FROM Scholarship S
    LEFT JOIN Application A ON S.ScholarshipID = A.ScholarshipID
    WHERE S.ProviderID = %s
    GROUP BY S.ScholarshipID
    ORDER BY S.Deadline DESC
    """
    return execute_query(query, (provider_id,), fetch=True)

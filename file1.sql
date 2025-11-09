CREATE DATABASE IF NOT EXISTS sc;
USE sc;


CREATE TABLE Provider (
    username VARCHAR(50) UNIQUE NOT NULL,
    ProviderID INT AUTO_INCREMENT PRIMARY KEY,
    OrganizationName VARCHAR(100) NOT NULL,
    ProviderName VARCHAR(100) NOT NULL,
    Email VARCHAR(100) NOT NULL,
    passh VARCHAR(255) NOT NULL,
    website VARCHAR(150),
    statusof_provider ENUM('Active','Inactive') DEFAULT 'Inactive',
    Phone VARCHAR(15),
    Address VARCHAR(255),
    INDEX idx_status (statusof_provider)
);

CREATE TABLE Student (
    StudentID INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    passh VARCHAR(255) NOT NULL,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    dob DATE NOT NULL,
    College VARCHAR(150),
    Yearof_study INT,
    GPA DECIMAL(3,2) NOT NULL
);

CREATE TABLE Admin (
    AdminID INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    passh VARCHAR(255) NOT NULL,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    Role ENUM('SuperAdmin','Reviewer','Staff') DEFAULT 'Staff'
);

CREATE TABLE Scholarship (
    ScholarshipID INT AUTO_INCREMENT PRIMARY KEY,
    ProviderID INT NOT NULL,
    Title VARCHAR(150) NOT NULL,
    Description TEXT,
    Amount DECIMAL(10,2) NOT NULL,
    MaxStudents INT NOT NULL,
    Deadline DATE,
    status ENUM('Open','Closed','Under Review') DEFAULT 'Open',
    min_GPA DECIMAL(3,2) DEFAULT 0.00,
    FOREIGN KEY (ProviderID) REFERENCES Provider(ProviderID) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_deadline (Deadline)
);

CREATE TABLE Application (
    ApplicationID INT AUTO_INCREMENT PRIMARY KEY,
    StudentID INT NOT NULL,
    ScholarshipID INT NOT NULL,
    DateApplied DATE DEFAULT (CURRENT_DATE),
    Status ENUM('Pending','Approved','Rejected','Awarded') DEFAULT 'Pending',
    ReviewBy INT NULL,
    Award_date DATE DEFAULT NULL,
    Amount_Granted DECIMAL(10,2) DEFAULT NULL,
    UNIQUE KEY (StudentID, ScholarshipID),
    FOREIGN KEY (StudentID) REFERENCES Student(StudentID) ON DELETE CASCADE,
    FOREIGN KEY (ScholarshipID) REFERENCES Scholarship(ScholarshipID) ON DELETE CASCADE,
    FOREIGN KEY (ReviewBy) REFERENCES Admin(AdminID) On Delete Set Null,
    INDEX idx_status (Status),
    INDEX idx_date (DateApplied)
);

CREATE TABLE Document (
    DocumentID INT AUTO_INCREMENT PRIMARY KEY,
    ApplicationID INT NOT NULL,
    DocTypeID ENUM('Transcript','passportsize-photo','income-caste certificate','adhar card') NOT NULL,
    file_data MEDIUMBLOB NOT NULL,
    FOREIGN KEY (ApplicationID) REFERENCES Application(ApplicationID) ON DELETE CASCADE
);


DELIMITER $$

-- Trigger 1: Check GPA before an application is INSERTED
CREATE TRIGGER trg_CheckGPAOnApply
BEFORE INSERT ON Application
FOR EACH ROW
BEGIN
    DECLARE student_gpa DECIMAL(3,2);
    DECLARE required_gpa DECIMAL(3,2);

    SELECT GPA INTO student_gpa 
    FROM Student 
    WHERE StudentID = NEW.StudentID;
    
    SELECT min_GPA INTO required_gpa 
    FROM Scholarship 
    WHERE ScholarshipID = NEW.ScholarshipID;
    
    IF student_gpa < required_gpa THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Application rejected: Your GPA is below the minimum requirement for this scholarship.';
    END IF;
END$$

-- Trigger 2: Prevents awarding more students than the scholarship's limit
CREATE TRIGGER trg_PreventAwardLimitExceed
BEFORE UPDATE ON Application
FOR EACH ROW
BEGIN
    DECLARE max_students INT;
    DECLARE awarded_count INT;
    
    IF NEW.Status = 'Awarded' AND OLD.Status <> 'Awarded' THEN
        
        SELECT MaxStudents INTO max_students 
        FROM Scholarship 
        WHERE ScholarshipID = NEW.ScholarshipID;

        SELECT COUNT(*) INTO awarded_count 
        FROM Application 
        WHERE ScholarshipID = NEW.ScholarshipID AND Status = 'Awarded';
            
        IF awarded_count >= max_students THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Error: Cannot award this scholarship. The maximum student limit has been reached.';
        END IF;
    END IF;
END$$

DELIMITER ;


-- =======================================================
-- 4. FUNCTIONS
-- =======================================================
DELIMITER $$

-- Function 1: Get the age of a pending application in days
CREATE FUNCTION fn_GetApplicationAge(
    p_application_id INT
)
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE submission_date DATE;
    
    SELECT DateApplied INTO submission_date
    FROM Application
    WHERE ApplicationID = p_application_id;
    
    RETURN DATEDIFF(CURDATE(), submission_date);
END$$

-- Function 2: Get the total amount of money awarded by a specific provider
CREATE FUNCTION fn_GetTotalAllocatedAmount(
    p_provider_id INT
)
RETURNS DECIMAL(12,2)
READS SQL DATA
BEGIN
    DECLARE total_awarded DECIMAL(12,2);
    
    SELECT SUM(A.Amount_Granted) INTO total_awarded
    FROM Application A
    JOIN Scholarship S ON A.ScholarshipID = S.ScholarshipID
    WHERE S.ProviderID = p_provider_id AND A.Status = 'Awarded';
    
    RETURN IFNULL(total_awarded, 0.00);
END$$

DELIMITER ;


-- =======================================================
-- 5. STORED PROCEDURES
-- =======================================================
DELIMITER $$

-- Procedure 1: For the pre-application pop-up to check GPA
CREATE PROCEDURE sp_CheckPreEligibility(
    IN p_student_gpa DECIMAL(3,2),
    IN p_scholarship_id INT
)
BEGIN
    DECLARE required_gpa DECIMAL(3,2);
    
    SELECT min_GPA INTO required_gpa
    FROM Scholarship
    WHERE ScholarshipID = p_scholarship_id;
    
    IF p_student_gpa >= required_gpa THEN
        SELECT 0 AS status_code, 'Eligible! Your GPA meets the minimum requirement.' AS message;
    ELSE
        SELECT 1 AS status_code, CONCAT('Ineligible: Your GPA is ', p_student_gpa, ', but the minimum is ', required_gpa, '.') AS message;
    END IF;
    
END$$

DELIMITER ;

-- =======================================================
-- STORED PROCEDURES FOR PROVIDER ANALYTICS
-- =======================================================

DELIMITER $$

-- Get provider's scholarship performance
CREATE PROCEDURE sp_GetProviderStats(
    IN p_provider_id INT
)
BEGIN
    SELECT 
        S.ScholarshipID,
        S.Title,
        S.Amount,
        S.MaxStudents,
        COUNT(A.ApplicationID) as TotalApplications,
        SUM(CASE WHEN A.Status = 'Awarded' THEN 1 ELSE 0 END) as StudentsAwarded,
        COALESCE(SUM(A.Amount_Granted), 0) as TotalAmountGranted
    FROM Scholarship S
    LEFT JOIN Application A ON S.ScholarshipID = A.ScholarshipID
    WHERE S.ProviderID = p_provider_id
    GROUP BY S.ScholarshipID, S.Title, S.Amount, S.MaxStudents;
END$$

DELIMITER ;

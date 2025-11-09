create database sc;
use sc;

create table provider (
    ProviderID int auto_increment primary key,
    username varchar(50) unique not null,
    ProviderName varchar(100) not null,
    OrganizationName varchar(100) not null,
    Email varchar(100) not null,
    passh varchar(255) not null,
    website varchar(150),
    statusof_provider enum('Active','Inactive') default 'Inactive',
    Phone varchar(15),
    Address varchar(255),
    index idx_status (statusof_provider)
);



create table student (
    StudentID int auto_increment primary key,
    username varchar(50) unique not null,
    passh varchar(255) not null,
    Name varchar(100) not null,
    Email varchar(100) unique not null,
    dob date not null,
    College varchar(150),
    Yearof_study int,
    GPA decimal(3,2) not null
);



create table admin (
    AdminID int auto_increment primary key,
    username varchar(50) unique not null,
    passh varchar(255) not null,
    Name varchar(100) not null,
    Email varchar(100) unique not null,
    Role enum('SuperAdmin','Reviewer','Staff') default 'Staff'
);




create table scholarship (
    ScholarshipID int auto_increment primary key,
    ProviderID int not null,
    Title varchar(150) not null,
    Description text,
    Amount decimal(10,2) not null,
    MaxStudents int not null,
    Deadline date,
    status enum('Open','Closed','Under Review') default 'Open',
    min_GPA decimal(3,2) default 0.00,
    foreign key (ProviderID) references provider(ProviderID) on delete cascade,
    index idx_status (status),
    index idx_deadline (Deadline)
);




create table application (
    ApplicationID int auto_increment primary key,
    StudentID int not null,
    ScholarshipID int not null,
    DateApplied date default (current_date),
    Status enum('Pending','Approved','Rejected','Awarded') default 'Pending',
    ReviewBy int null,
    Award_date date default null,
    Amount_Granted decimal(10,2) default null,
    unique key (StudentID, ScholarshipID),
    foreign key (StudentID) references student(StudentID) on delete cascade,
    foreign key (ScholarshipID) references scholarship(ScholarshipID) on delete cascade,
    foreign key (ReviewBy) references admin(AdminID) on delete set null,
    index idx_status (Status),
    index idx_date (DateApplied)
);




create table document (
    DocumentID int auto_increment primary key,
    ApplicationID int not null,
    DocTypeID enum('Transcript','passportsize-photo','income-caste certificate','adhar card') not null,
    file_data mediumblob not null,
    foreign key (ApplicationID) references application(ApplicationID) on delete cascade
);




delimiter $$

-- trg 1: prevent application if gpa doesn't meet scholarship criteria


create trigger trg_CheckGPAOnApply
before insert on application
for each row
begin
    declare student_gpa decimal(3,2);
    declare required_gpa decimal(3,2);

    select GPA into student_gpa 
    from student 
    where StudentID = new.StudentID;

    select min_GPA into required_gpa 
    from scholarship 
    where ScholarshipID = new.ScholarshipID;

    if student_gpa < required_gpa then
        signal sqlstate '45000'
        set message_text = 'Application rejected: Your GPA is below the minimum requirement for this scholarship.';
    end if;
end$$



-- trg 2: stop awarding if max student limit is already reached
create trigger trg_PreventAwardLimitExceed
before update on application
for each row
begin
    declare max_students int;
    declare awarded_count int;

    if new.Status = 'Awarded' and old.Status <> 'Awarded' then
        select MaxStudents into max_students 
        from scholarship 
        where ScholarshipID = new.ScholarshipID;

        select count(*) into awarded_count 
        from application 
        where ScholarshipID = new.ScholarshipID 
        and Status = 'Awarded';

        if awarded_count >= max_students then
            signal sqlstate '45000'
            set message_text = 'Error: Scholarship limit reached. No more students can be awarded.';
        end if;
    end if;
end$$

delimiter ;


FUNCTIONS: 

delimiter $$

-- fn: retn the no of days since an appn was sub

create function fn_GetApplicationAge(p_application_id int)
returns int
reads sql data
begin
    declare submission_date date;

    select DateApplied into submission_date
    from application
    where ApplicationID = p_application_id;

    return datediff(curdate(), submission_date);
end$$



-- fn: cal total amt granted by a specific pro
create function fn_GetTotalAllocatedAmount(p_provider_id int)
returns decimal(12,2)
reads sql data
begin
    declare total_awarded decimal(12,2);

    select sum(A.Amount_Granted) into total_awarded
    from application A
    join scholarship S on A.ScholarshipID = S.ScholarshipID
    where S.ProviderID = p_provider_id 
    and A.Status = 'Awarded';

    return ifnull(total_awarded, 0.00);
end$$

delimiter ;

-- PROCEDURESS:


delimiter $$

-- procedure: used to check eligibility before applying (for popup)
create procedure sp_CheckPreEligibility(
    in p_student_gpa decimal(3,2),
    in p_scholarship_id int
)
begin
    declare required_gpa decimal(3,2);

    select min_GPA into required_gpa
    from scholarship
    where ScholarshipID = p_scholarship_id;

    if p_student_gpa >= required_gpa then
        select 0 as status_code, 
               'Eligible! Your GPA meets the minimum requirement.' as message;
    else
        select 1 as status_code, 
               concat('Ineligible: Your GPA is ', p_student_gpa, 
                      ', but the minimum required is ', required_gpa, '.') as message;
    end if;
end$$

delimiter ;

-- procedure: provider for stats

delimiter $$

create procedure sp_GetProviderStats(in p_provider_id int)
begin
    select 
        S.ScholarshipID,
        S.Title,
        S.Amount,
        S.MaxStudents,
        count(A.ApplicationID) as TotalApplications,
        sum(case when A.Status = 'Awarded' then 1 else 0 end) as StudentsAwarded,
        coalesce(sum(A.Amount_Granted), 0) as TotalAmountGranted
    from scholarship S
    left join application A on S.ScholarshipID = A.ScholarshipID
    where S.ProviderID = p_provider_id
    group by S.ScholarshipID, S.Title, S.Amount, S.MaxStudents;
end$$

delimiter ;

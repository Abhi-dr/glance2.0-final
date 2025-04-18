from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import MinValueValidator


# ======================================================= STUDENT ===========================================

class Student(User):
    gender_choices = (
        ("Male", "Male"),
        ("Female", "Female"),
        ("Prefer not to say", "Prefer not to say")
    )
    phone_number = models.CharField(max_length=12)
    
    gender = models.CharField(
        max_length=17, choices=gender_choices, blank=True, null=True)
    
    alumni_status_choices = (
        ("Current Student", "Current Student"),
        ("Alumni", "Alumni")
    )
    
    alumni_status = models.CharField(
        max_length=20, choices=alumni_status_choices, default="Current Student")
        
    passout_year = models.CharField(max_length=4, blank=True, null=True)

    # Updated course field to store multiple courses as comma-separated values
    course = models.CharField(max_length=500, blank=True, null=True, help_text="Comma-separated list of courses")
    
    year = models.CharField(max_length=15, blank=True, null=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    tenth = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    twelfth = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    backlog = models.IntegerField(blank=True, null=True)

    resume = models.FileField(upload_to='student_resumes/', blank=True, null=True)
    
    tenth_marksheet = models.FileField(upload_to='student_marksheets/', blank=True, null=True)
    twelfth_marksheet = models.FileField(upload_to='student_marksheets/', blank=True, null=True)
    college_profile_print = models.FileField(upload_to='student_marksheets/', blank=True, null=True)
    
    linkedin_id = models.URLField(blank=True, null=True)
    github_id = models.URLField(blank=True, null=True)
    instagram_id = models.URLField(blank=True, null=True)
    twitter_id = models.URLField(blank=True, null=True)
    
    no_of_companies_left = models.IntegerField(default=100, validators=[
            MinValueValidator(0)
        ])
    
    # Flag to bypass eligibility criteria for special cases
    bypass_eligibility = models.BooleanField(default=False, help_text="If enabled, bypasses all eligibility restrictions like CGPA, 10th, 12th marks")
    
    profile_pic = models.ImageField(
        upload_to="student_profile/", default="/student_profile/default.jpg")
    
    class Meta:
        verbose_name_plural = "Students"
        verbose_name = "Student"

    def get_profile_score(self):
        """
        Calculate profile score with proper error handling
        """
        try:
            score = 0
            
            # Documents
            if hasattr(self, 'tenth_marksheet') and self.tenth_marksheet:
                score += 10
            if hasattr(self, 'twelfth_marksheet') and self.twelfth_marksheet:
                score += 10
            if hasattr(self, 'college_profile_print') and self.college_profile_print:
                score += 10
            if hasattr(self, 'resume') and self.resume:
                score += 10
            
            # Social media
            if hasattr(self, 'linkedin_id') and self.linkedin_id:
                score += 5
            if hasattr(self, 'github_id') and self.github_id:
                score += 5
            if hasattr(self, 'instagram_id') and self.instagram_id:
                score += 5
            if hasattr(self, 'twitter_id') and self.twitter_id:
                score += 5
                
            # Profile picture (safely check)
            try:
                if hasattr(self, 'profile_pic') and self.profile_pic and not str(self.profile_pic).endswith('default.jpg'):
                    score += 15
            except Exception:
                # If any error with profile pic, just skip this score
                pass
            
            # Basic info
            if hasattr(self, 'phone_number') and self.phone_number:
                score += 5
            if hasattr(self, 'gender') and self.gender:
                score += 5
            if hasattr(self, 'course') and self.course:
                score += 5
            if hasattr(self, 'year') and self.year:
                score += 5
            
            # Academic info
            if hasattr(self, 'cgpa') and self.cgpa:
                score += 5
            if hasattr(self, 'backlog') and self.backlog is not None:
                score += 5
            if hasattr(self, 'tenth') and self.tenth:
                score += 5
            if hasattr(self, 'twelfth') and self.twelfth:
                score += 5
            
            # Alumni information
            if hasattr(self, 'alumni_status') and hasattr(self, 'passout_year') and self.alumni_status == "Alumni" and self.passout_year:
                score += 10
            
            return score
            
        except Exception as e:
            # If anything goes wrong, return a default value
            return 0

# ============================================ ADMINISTRATOR =========================================

class Administrator(User):
    gender_choices = (
        ("Male", "Male"),
        ("Female", "Female"),
        ("Prefer not to say", "Prefer not to say")
    )
    phone_number = models.CharField(max_length=12)
    
    gender = models.CharField(
        max_length=17, choices=gender_choices, blank=True, null=True)

    
    profile_pic = models.ImageField(
        upload_to="student_profile/", default="/student_profile/default.jpg")
    
    class Meta:
        verbose_name_plural = "Administrators"
        verbose_name = "Administrator"
        
    def save(self, *args, **kwargs):
        # Ensure administrator users have staff permission
        self.is_staff = True
        super().save(*args, **kwargs)


# ======================================================= COMPANY ===========================================

class Company(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=100)
    website = models.URLField(blank=True, null=True)
    size = models.CharField(max_length=50)
    social_media_links = models.URLField(blank=True)
    benefits_perks = models.TextField(blank=True)
    mail_id = models.EmailField(blank=True, null=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Companies"
        verbose_name = "Company"
    
    def __str__(self):
        return self.name
    
# ======================================================= JOB ===========================================

class Job(models.Model):
    
    interview_date_choice = (
        ("17th April, 2025", "17th April, 2025"),
        ("18th April, 2025", "18th April, 2025"),
        ("19th April, 2025", "19th April, 2025"),

    )
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=100)
    description = models.TextField()
    interview_date = models.CharField(max_length=100, choices=interview_date_choice, default="17th April, 2025")
    deadline = models.DateField()
    interview_mode = models.CharField(max_length=100, blank=True)
    
    # Criteria
    tenth_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    twelfth_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    cgpa_criteria = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    is_backlog_allowed = models.BooleanField(default=True)
    
    no_of_openings = models.IntegerField()
    job_type = models.CharField(max_length=30)
    salary_range = models.CharField(max_length=100, blank=True)
    location_flexibility = models.CharField(max_length=100, blank=True)
    training_period = models.CharField(max_length=100, blank=True)
    bond_timing = models.CharField(max_length=100, blank=True)
    
    role = models.CharField(max_length=100)
    
    # SLug for the better urls
    slug = models.SlugField(max_length=100, unique=True, null=True, blank=True)
    
    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Generate unique slug based on title and company name
        if not self.slug:
            base_slug = slugify(f"{self.company.name}-{self.title}")
            slug = base_slug
            counter = 1
            while Job.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
        
    # def is_student_eligible(self, student):
    #     return (
    #         student.tenth >= self.tenth_percentage and
    #         student.twelfth >= self.twelfth_percentage and
    #         student.cgpa >= self.cgpa_criteria
    #     )            

# ============================================ APPLICATION =========================================

class Application(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    application_date = models.DateTimeField(auto_now_add=True)
    status_choices = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=20, choices=status_choices, default='pending')
    
    def __str__(self):
        return f"{self.student.first_name} applied for {self.job.title}"
    
    class Meta:
        verbose_name_plural = "Applications"
        verbose_name = "Application"
        
        
    def get_color_based_on_status(self):
        if self.status == 'pending':
            return 'warning'
        elif self.status == 'accepted':
            return 'success'
        else:
            return 'danger'
    
    
    
    # def get_all_applications_count_of_particular_job
        

# =========================================== ALUMNI REGISTRATIOSN =================================

class AlumniRegistration(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=12)
    company = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    passout_year = models.IntegerField()
    linkedin_id = models.URLField(blank=True)
    profile_pic = models.ImageField(upload_to='alumni_profile/', blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Alumni Registrations"
        verbose_name = "Alumni Registration"

# ========================================== NOTIFICATIONS =========================================
    
class Notification(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    timeStamp = models.DateTimeField(auto_now_add=True, blank=True)
    
    def __str__(self):
        return self.title

# ================================================ VOLUNTEER ==========================================

class Volunteer(User):
    gender_choices = (
        ("Male", "Male"),
        ("Female", "Female"),
        ("Prefer not to say", "Prefer not to say")
    )
    phone_number = models.CharField(max_length=12)
    
    gender = models.CharField(
        max_length=17, choices=gender_choices, blank=True, null=True)
    
    profile_pic = models.ImageField(
        upload_to="volunteer_profile/", default="/student_profile/default.jpg")
    
    class Meta:
        verbose_name_plural = "Volunteers"
        verbose_name = "Volunteer"

# ========================================== ATTENDANCE =========================================

class Attendance(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name="attendance")
    is_present = models.BooleanField(default=False)
    marked_by = models.ForeignKey(Volunteer, on_delete=models.SET_NULL, null=True, blank=True)
    marked_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.application.student.first_name} - {self.application.job.title} - {'Present' if self.is_present else 'Absent'}"
    
    class Meta:
        verbose_name_plural = "Attendances"
        verbose_name = "Attendance"


from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import MinValueValidator


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
        ("25th April, 2024", "25th April, 2024"),
        ("24th April, 2024", "24th April, 2024"),
    )
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=100)
    description = models.TextField()
    interview_date = models.CharField(max_length=100, choices=interview_date_choice, default="25th April, 2024")
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

    
    course = models.CharField(max_length=100, blank=True, null=True)
    
    year = models.CharField(max_length=15, blank=True, null=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    tenth = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    twelfth = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    backlog = models.IntegerField(blank=True, null=True)

    resume = models.FileField(upload_to='student_resumes/', blank=True, null=True)
    
    tenth_marksheet = models.ImageField(upload_to='student_marksheets/', blank=True, null=True)
    twelfth_marksheet = models.ImageField(upload_to='student_marksheets/', blank=True, null=True)
    college_profile_print = models.ImageField(upload_to='student_marksheets/', blank=True, null=True)
    
    linkedin_id = models.URLField(blank=True, null=True)
    github_id = models.URLField(blank=True, null=True)
    
    no_of_companies_left = models.IntegerField(default=2, validators=[
            MinValueValidator(0)
        ])
    
    profile_pic = models.ImageField(
        upload_to="student_profile/", blank=True, null=True, default="/student_profile/default.jpg")
    
    class Meta:
        verbose_name_plural = "Students"
        verbose_name = "Student"

    def get_profile_score(self):
        score = 0
        
        if self.tenth_marksheet:
            score += 10
        if self.twelfth_marksheet:
            score += 10
        if self.college_profile_print:
            score += 10
        if self.resume:
            score += 10
        
        if self.linkedin_id:
            score += 5
        if self.github_id:
            score += 5
        if self.profile_pic:
            score += 10
        
        if self.phone_number:
            score += 5
        if self.gender:
            score += 5
        if self.course:
            score += 5
        if self.year:
            score += 5
        
        if self.cgpa:
            score += 5
        if self.backlog:
            score += 5
        if self.tenth:
            score += 5
        if self.twelfth:
            score += 5
        
        # return score in percentage
        return score

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
        upload_to="student_profile/", blank=True, null=True, default="/student_profile/default.jpg")
    
    class Meta:
        verbose_name_plural = "Administrators"
        verbose_name = "Administrator"

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


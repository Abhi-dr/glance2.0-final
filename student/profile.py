from django.shortcuts import render, redirect
from accounts.models import Student
from django.contrib.auth.decorators import login_required
from django.contrib import messages


# ================================== STUDENT PROFILE ===========================================

@login_required(login_url='login')
def my_profile(request):
    
    try:
        student = Student.objects.get(id=request.user.id)
    except Student.DoesNotExist:
        # Redirect to edit_profile to create the Student record
        messages.info(request, "Please complete your profile first.")
        return redirect('edit_profile')
    
    parameters = {
        "student": student
    }
    
    return render(request, 'student/profile/my_profile.html', parameters)

# ================================== EDIT PROFILE ===========================================

@login_required(login_url='login')
def edit_profile(request):
    try:
        student = Student.objects.get(id=request.user.id)
    except Student.DoesNotExist:
        # Create a new Student record for this user if it doesn't exist
        student = Student(
            id=request.user.id,
            username=request.user.username,
            email=request.user.email,
            first_name=request.user.first_name,
            last_name=request.user.last_name
        )
        # Copy any other fields from User to Student if needed
        student.save()
        messages.info(request, "Your student profile has been created. Please complete your profile information.")
    
    if request.method == "POST":
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        gender = request.POST["gender"]
        
        # Update student object - basic details
        student.first_name = first_name
        student.last_name = last_name
        student.gender = gender
        
        # Educational details - handle single course selection
        course = request.POST.get('course', '')  # Get single course
        tenth = request.POST.get('tenth', '')
        twelfth = request.POST.get('twelfth', '')
        cgpa = request.POST.get('cgpa', '')
        backlog = request.POST.get('backlog', '')
        year = request.POST.get('year', '')
        
        # Alumni details
        alumni_status = request.POST.get('alumni_status', 'Current Student')
        passout_year = request.POST.get('passout_year', '')
        
        # Update student object with alumni details
        student.alumni_status = alumni_status
        if alumni_status == 'Alumni' and passout_year:
            student.passout_year = passout_year
        elif alumni_status == 'Current Student':
            student.passout_year = None
        
        # Update educational details - only if they haven't been set before
        if course and not student.course:
            # Store as a single value, but in a comma-separated format for future filtering
            student.course = course  # Store single course
            messages.success(request, f"Course has been set to {course} and cannot be changed later.")
        elif not student.course and not course:
            messages.warning(request, "No course was selected. Please select a course.")
            return redirect('edit_profile')
            
        if year and not student.year:
            student.year = year
            messages.success(request, "Year has been set and cannot be changed later.")
            
        if tenth and not student.tenth:
            student.tenth = tenth
            messages.success(request, "Highschool percentage has been set and cannot be changed later.")
            
        if twelfth and not student.twelfth:
            student.twelfth = twelfth
            messages.success(request, "Intermediate percentage has been set and cannot be changed later.")
            
        if cgpa and not student.cgpa:
            student.cgpa = cgpa
            messages.success(request, "CGPA has been set and cannot be changed later.")
            
        if backlog and not student.backlog:
            student.backlog = backlog
            messages.success(request, "Backlog count has been set and cannot be changed later.")
        
        # Social profiles (can always be updated)
        linkedin_id = request.POST.get('linkedin_id', '')
        github_id = request.POST.get('github_id', '')
        instagram_id = request.POST.get('instagram_id', '')
        twitter_id = request.POST.get('twitter_id', '')
        
        # Handle N/A values for social profiles
        student.linkedin_id = None if linkedin_id == 'N/A' else linkedin_id
        student.github_id = None if github_id == 'N/A' else github_id
        student.instagram_id = None if instagram_id == 'N/A' else instagram_id
        student.twitter_id = None if twitter_id == 'N/A' else twitter_id
        
        student.save()
        
        messages.success(request, "Profile updated successfully")
        return redirect('my_profile')
    
    # Generate passout years (current year + 10 years)
    import datetime
    current_year = datetime.datetime.now().year
    passout_years = [str(year) for year in range(current_year-5, current_year+6)]
    
    # Parse existing course for template rendering
    # For backwards compatibility, still attempt to split by comma
    # but take the first value as the selected one if there are multiple
    student_courses = []
    if student.course:
        # Strip whitespace and filter out empty strings
        course_parts = [course.strip() for course in student.course.split(',') if course.strip()]
        if course_parts:
            student_courses = course_parts
    
    parameters = {
        "student": student,
        "passout_years": passout_years,
        "student_courses": student_courses
    }
    
    return render(request, 'student/profile/edit_profile.html', parameters)


# ================================== UPLOAD PROFILE ===========================================

@login_required(login_url='login')
def upload_profile(request):
    if request.method == 'POST':
        if 'profile_pic' not in request.FILES:
            messages.error(request, 'Profile picture is required. Please select a valid image file.')
            return redirect('edit_profile')
        
        try:
            student = Student.objects.get(id=request.user.id)
        except Student.DoesNotExist:
            # Redirect to edit_profile to create the Student record
            messages.info(request, "Please complete your profile first.")
            return redirect('edit_profile')
            
        student.profile_pic = request.FILES['profile_pic']
        student.save()

        messages.success(request, 'Profile Picture Updated Successfully')
        return redirect('my_profile')
        
    return redirect('edit_profile') 
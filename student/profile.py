from django.shortcuts import render, redirect
from accounts.models import Student
from django.contrib.auth.decorators import login_required
from django.contrib import messages


# ================================== STUDENT PROFILE ===========================================

@login_required(login_url='login')
def my_profile(request):
    
    student = Student.objects.get(id=request.user.id)
    
    parameters = {
        "student": student
    }
    
    return render(request, 'student/profile/my_profile.html', parameters)

# ================================== EDIT PROFILE ===========================================

@login_required(login_url='login')
def edit_profile(request):
    
    student = Student.objects.get(id=request.user.id)
    
    if request.method == "POST":
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        gender = request.POST["gender"]
        
        # Update student object - basic details
        student.first_name = first_name
        student.last_name = last_name
        student.gender = gender
        
        # Educational details
        course = request.POST.get('course', '')
        tenth = request.POST.get('tenth', '')
        twelfth = request.POST.get('twelfth', '')
        cgpa = request.POST.get('cgpa', '')
        backlog = request.POST.get('backlog', '')
        year = request.POST.get('year', '')
        
        # Update educational details - only if they haven't been set before
        if course and not student.course:
            student.course = course
            messages.success(request, "Course has been set and cannot be changed later.")
            
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
        student.linkedin_id = linkedin_id
        student.github_id = github_id
        
        student.save()
        
        messages.success(request, "Profile updated successfully")
        return redirect('my_profile')
    
    parameters = {
        "student": student
    }
    
    return render(request, 'student/profile/edit_profile.html', parameters) 


# ================================== UPLOAD PROFILE ===========================================

@login_required(login_url='login')
def upload_profile(request):

    if request.method == 'POST':

        student = Student.objects.get(id=request.user.id)

        student.profile_pic = request.FILES['profile_pic']
        student.save()

        messages.success(request, 'Profile Picture Updated Successfully')

        return redirect('my_profile')
    
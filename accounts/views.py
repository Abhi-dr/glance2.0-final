from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib import messages
from django.http import JsonResponse

from accounts.models import Student, Administrator, Volunteer, Attendance
from django.core.mail import send_mail
from django_ratelimit.decorators import ratelimit
import requests
from django.http import HttpResponse

# Comment out external API email function
"""
def send_email_async(to, subject, text):
    url = 'https://send-mail-api-express.vercel.app/send-email'
    data = {
        'to': to,
        'subject': subject,
        'text': text
    }
    response = requests.post(url, json=data)
    print(response)
    return True
"""

# =============================== LOGIN =========================

@ratelimit(key='post:username', rate='3/m', method=['POST'], block=False)
def login(request):
    if request.user.is_authenticated:
        # Redirect based on user type
        if hasattr(request.user, 'student'):
            student = Student.objects.get(id=request.user.id)
            profile_score = student.get_profile_score()
            if profile_score >= 80: 
                return redirect('student')
            else:
                messages.warning(request, f"Your profile is only {profile_score}% complete. Please complete your profile to continue using the system.")
                return redirect('edit_profile')
        elif hasattr(request.user, 'administrator'):
            return redirect('administration')
        elif hasattr(request.user, 'volunteer'):
            return redirect('volunteer_dashboard')
        else:
            return redirect('home')  # Default fallback

    if getattr(request, 'limited', False):
        messages.error(request, "Too many login attempts for this Username. Please try again after 1 minute.")
        return redirect('login')

    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        username = request.POST.get('email').strip().lower()
        password = request.POST.get('password')

        if Student.objects.filter(username=username).exists():
            user = auth.authenticate(username=username, password=password)

            if user is not None:
                auth.login(request, user)
                
                # Check profile completion after login
                student = Student.objects.get(id=user.id)
                profile_score = student.get_profile_score()
                
                if profile_score < 80:
                    messages.warning(request, f"Your profile is only {profile_score}% complete. Please complete your profile to continue using the system.")
                    return redirect('edit_profile')
                
                return redirect(next_url if next_url else 'student')

            messages.error(request, "Invalid Password")
            return redirect("login")

        elif Administrator.objects.filter(username=username).exists():
            user = auth.authenticate(username=username, password=password)

            if user is not None:
                auth.login(request, user)
                return redirect(next_url if next_url else 'administration')

            messages.error(request, "Invalid Password")
            return redirect("login")
            
        elif Volunteer.objects.filter(username=username).exists():
            user = auth.authenticate(username=username, password=password)

            if user is not None:
                auth.login(request, user)
                return redirect(next_url if next_url else 'volunteer_dashboard')

            messages.error(request, "Invalid Password")
            return redirect("login")

        else:
            messages.error(request, "Invalid Username or Password")
            return redirect("login")

    return render(request, 'accounts/login.html', {'next': next_url})




# ===================================== REGISTER ==============================

def register(request):
    if request.method=="POST":
        username = request.POST.get("email").strip().lower()
        first_name = request.POST.get("first_name").strip().title()
        last_name = request.POST.get("last_name").strip().title()
        phone_number = request.POST.get("mobile_number")
        # profile_pic = request.FILES.get("profile_pic")
        
        # Check if email already exists
        if Student.objects.filter(username=username).exists():
            messages.error(request, "Email Already Registered")
            return redirect("register")
        
        # Check if mobile number already exists
        if Student.objects.filter(phone_number=phone_number).exists():
            messages.error(request, "Mobile Number Already Registered")
            return redirect("register")
        
        # # Validate profile picture
        # if not profile_pic:
        #     messages.error(request, "Profile Photo is Required")
        #     return redirect("register")
        
        password = request.POST.get("password")

        new_user = Student.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            # profile_pic=profile_pic
        )

        new_user.set_password(password)

        new_user.save()
        
        myfile = f"""Dear {first_name},

Congratulations on successfully registering for GLANCE - the Mega Job Fair! 

Your commitment to your professional journey is commendable. Here are some key details:

- Date: 17,18,19 April, 2025
- Opportunity: Connect with recruiters, explore job and internship prospects, and expand your network.
- *Reminder: You can apply to a maximum of two (3) companies. with 1 each day* 

Best of luck! For any queries or assistance, reach out to us at alumniassociation01@gla.ac.in.

Looking forward to seeing you at GLANCE!

Best regards,
Technical Team
Department of Alumni Affairs
GLA University"""
        
        email_subject = ' GLANCE Registration Confirmation - Your Path to Success!'
        email_body = myfile
        email_from = 'GLANCE Job Fair <alumniassociation01@gla.ac.in>'
        email_to = [username]

        # Send the email
        try:
            send_mail(
                email_subject, 
                email_body, 
                email_from, 
                email_to,
                fail_silently=False
            )
        except Exception as e:
            print(f"Error sending email: {e}")
            messages.warning(request, "You will receive a confirmation email soon.")
        
        messages.success(request, "Account created successfully")

        return redirect("login")
    
    return render(request,"accounts/register.html")

# =================================== logout ============================

def logout(request):
     auth.logout(request)
     return redirect("home")

# ====================== check Email availability ====================

def check_username_availability(request):
    username = request.GET.get('username', '')
    data = {'is_available': not Student.objects.filter(username=username).exists()}
    return JsonResponse(data)

# ====================== check Mobile availability ====================

def check_mobile_availability(request):
    mobile = request.GET.get('mobile', '')
    data = {'is_available': not Student.objects.filter(phone_number=mobile).exists()}
    return JsonResponse(data)

# =================================== Terms and Conditions ============

def tnc(request):
    return render(request, "accounts/tnc.html")

# ============================ 404 ===============

def page_not_found_view(request, exception):
    return render(request, '404.html', status=404)

# ============================ 500 ===============

def server_error_view(request):
    return render(request, 'maintenance.html', status=500)

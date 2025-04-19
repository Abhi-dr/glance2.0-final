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
            try:
                admin = Administrator.objects.get(id=request.user.id)
                return redirect('administration')
            except Exception as e:
                print(f"Error accessing administrator: {e}")
                messages.error(request, "Error accessing administrator account. Please contact support.")
                return redirect('home')
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
        
        # Get file uploads - resume is mandatory, others are optional
        profile_pic = request.FILES.get('profile_pic')
        resume = request.FILES.get('resume')
        
        # Resume is required
        if not resume:
            messages.error(request, "Resume is Required")
            return redirect("register")
        
        # Check if email already exists
        if Student.objects.filter(username=username).exists():
            messages.error(request, "Email Already Registered")
            return redirect("register")
        
        # Check if mobile number already exists
        if Student.objects.filter(phone_number=phone_number).exists():
            messages.error(request, "Mobile Number Already Registered")
            return redirect("register")
        
        # Get device info if available
        device_info = request.POST.get('device_info', 'Unknown device')
        print(f"Processing registration from: {device_info}")
            
        # Only validate resume if it was provided (now optional)
        if resume:
            try:
                # Check file size (max 5MB)
                max_size = 5 * 1024 * 1024  # 5MB in bytes
                if resume.size > max_size:
                    messages.error(request, "Resume file is too large. Maximum size is 5MB.")
                    return redirect("register")
                
                # Log file information for debugging
                print(f"Resume file: name={resume.name}, size={resume.size}, content_type={resume.content_type}")
                
                # Enhanced PDF detection with multiple checks for cross-device compatibility
                is_pdf = False
                
                # 1. Check file extension (most reliable across devices)
                if resume.name.lower().endswith('.pdf'):
                    is_pdf = True
                    print("PDF detected by file extension")
                    
                # 2. Check content type (can vary across devices)
                pdf_content_types = [
                    'application/pdf',
                    'application/x-pdf',
                    'application/acrobat',
                    'applications/vnd.pdf',
                    'text/pdf',
                    'text/x-pdf'
                ]
                
                if resume.content_type in pdf_content_types:
                    is_pdf = True
                    print(f"PDF detected by content type: {resume.content_type}")
                
                # 3. Additional check for iOS and older Android devices that may report content type incorrectly
                if 'iPhone' in device_info or 'iPad' in device_info or 'Android 4' in device_info:
                    # For these devices, prioritize file extension over content type
                    if resume.name.lower().endswith('.pdf'):
                        is_pdf = True
                        print("PDF detection override for mobile device")
                
                # Final PDF validation
                if not is_pdf:
                    messages.error(request, "Resume must be a PDF file. Please convert your document to PDF format.")
                    return redirect("register")
            except Exception as e:
                # Log the error but provide a user-friendly message
                print(f"Error validating resume: {str(e)}")
                messages.error(request, "There was a problem with your resume file. Please ensure it's a valid PDF under 5MB.")
                return redirect("register")
        
        # Enhanced profile picture validation with comprehensive device support
        if profile_pic:
            try:
                # Get device info if available
                device_info = request.POST.get('device_info', 'Unknown device')
                print(f"Processing profile picture from: {device_info}")
                
                # Check file size (max 2MB)
                max_size = 2 * 1024 * 1024  # 2MB in bytes
                if profile_pic.size > max_size:
                    messages.error(request, "Profile picture is too large. Maximum size is 2MB.")
                    return redirect("register")
                
                # Log file information for debugging
                print(f"Profile picture: name={profile_pic.name}, size={profile_pic.size}, content_type={profile_pic.content_type}")
                
                # Enhanced image detection with multiple checks for cross-device compatibility
                is_image = False
                
                # 1. Check file extension (most reliable across devices)
                image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic', '.heif']
                if any(profile_pic.name.lower().endswith(ext) for ext in image_extensions):
                    is_image = True
                    print("Image detected by file extension")
                
                # 2. Check content type (can vary across devices)
                if profile_pic.content_type.startswith('image/'):
                    is_image = True
                    print(f"Image detected by content type: {profile_pic.content_type}")
                
                # 3. Additional check for iOS and older Android devices
                if 'iPhone' in device_info or 'iPad' in device_info or 'Android' in device_info:
                    # For these devices, prioritize file extension over content type
                    if any(profile_pic.name.lower().endswith(ext) for ext in image_extensions):
                        is_image = True
                        print("Image detection override for mobile device")
                
                # Final image validation
                if not is_image:
                    messages.error(request, "Profile picture must be an image file (JPEG, PNG, etc.).")
                    return redirect("register")
                    
            except Exception as e:
                # Log the error but provide a user-friendly message
                print(f"Error validating profile picture: {str(e)}")
                messages.error(request, "There was a problem with your profile picture. Please ensure it's a valid image under 2MB.")
                return redirect("register")
        
        password = request.POST.get("password")

        try:
            # Create user with required fields
            new_user = Student.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                resume=resume
            )
            
            # Add optional profile picture if provided
            if profile_pic:
                new_user.profile_pic = profile_pic

            # Set password and save
            new_user.set_password(password)
            new_user.save()
        except Exception as e:
            # Log the error for debugging
            print(f"Error creating user: {str(e)}")
            # Provide a user-friendly error message
            messages.error(request, "There was a problem creating your account. Please try again.")
            return redirect("register")
        
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

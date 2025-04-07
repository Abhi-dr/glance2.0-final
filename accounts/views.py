from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib import messages
from django.http import JsonResponse

from accounts.models import Student
from django.core.mail import send_mail

import requests

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


# =============================== LOGIN =========================

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email').strip().lower()
        password = request.POST.get('password')
        
        # if email.split("@")[-1] != "gla.ac.in":
        #     messages.error(request, "Please use a valid GLA Mail ID")
        #     return redirect("login")

        if Student.objects.filter(username=email).exists():
            user = auth.authenticate(username=email, password=password)

            if user is not None:
                auth.login(request, user)
                # send_email_async(
                #     to=email,
                #     subject='GLA University - Login Alert',
                #     text='You have successfully logged in to your account.'
                # )
                return redirect('student')
            
        else:
            # Check if user is staff
            user = auth.authenticate(username=email, password=password)
            if user is not None and user.is_staff:
                auth.login(request, user)
                # Redirect staff to administration dashboard
                return redirect('administration')

    return render(request, 'accounts/login.html')

# ===================================== REGISTER ==============================

def register(request):
    if request.method=="POST":
        username = request.POST.get("email").strip().lower()
        first_name = request.POST.get("first_name").strip().title()
        last_name = request.POST.get("last_name").strip().title()
        phone_number = request.POST.get("mobile_number")
        # tenth = request.POST.get("tenth").replace("%", "").strip()
        # twelfth = request.POST.get("twelfth").replace("%", "").strip()
        # cgpa = request.POST.get("cgpa").replace("%", "").strip()
        # gender = request.POST.get("gender")
        # backlog = request.POST.get("backlog")
        # year = request.POST.get("year")
        # course = request.POST.get("course")
        
        # if username.split("@")[-1] != "gla.ac.in":
        #     messages.error(request, "Please use a valid GLA Mail ID")
        #     return redirect("login")
        
        password = request.POST.get("password")

        new_user = Student.objects.create(
            username=username,
            first_name=first_name,
            last_name = last_name,
            phone_number = phone_number
        )

        new_user.set_password(password)

        new_user.save()
        
        myfile = f"""Dear {first_name},

Congratulations on successfully registering for GLANCE - the Mega Job Fair! 

Your commitment to your professional journey is commendable. Here are some key details:

- Date: April 24th & 25th April, 2024
- Opportunity: Connect with recruiters, explore job and internship prospects, and expand your network.
- *Reminder: You can apply to a maximum of two (2) companies.*

Best of luck! For any queries or assistance, reach out to us at alumniassociation@gla.ac.in.

Looking forward to seeing you at GLANCE!

Best regards,
Technical Team
Department of Alumni Affairs
GLA University"""
        
        email_subject = ' GLANCE Registration Confirmation - Your Path to Success!'
        email_body = myfile
        email_from = 'GLANCE Job Fair'
        email_to = [username]

        # Send the email
        # send_mail(email_subject, email_body, email_from, email_to)  
        
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

# =================================== Terms and Conditions ============

def tnc(request):
    return render(request, "accounts/tnc.html")

# ============================ 404 ===============

def page_not_found_view(request, exception):
    return render(request, '404.html', status=404)

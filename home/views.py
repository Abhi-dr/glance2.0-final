from django.shortcuts import render, redirect
from .models import Contact, Company_Carousel
from django.contrib import messages

def home(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")
        
        Contact.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
    
        messages.success(request, "Your message has been sent successfully.")
        return redirect("home")
    
    return render(request, 'home/index.html')


# ========================================== ALUMNI REGISTRATIONS =========================================

def alumni_registration(request):
    return render(request, 'home/alumni_registration.html')

# ========================================== TERMS AND CONDITIONS PAGE =========================================

def terms(request):
    return render(request, 'home/terms.html')

def companies(request):
    day = request.GET.get('day', '1')  # Default to day 1 if not specified
    return render(request, 'home/companies.html', {'day': day})
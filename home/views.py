from django.shortcuts import render, redirect
from .models import Contact, Company_Carousel
from django.contrib import messages

def home(request):
    
    images = Company_Carousel.objects.all()
    
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
    
    parameters = {
        'images': images
    }
    
    return render(request, 'home/index.html', parameters)

# ========================================== ALUMNI REGISTRATIONS =========================================

def alumni_registration(request):
    return render(request, 'home/alumni_registration.html')

# ========================================== TERMS AND CONDITIONS PAGE =========================================

def terms(request):
    return render(request, 'home/terms.html')
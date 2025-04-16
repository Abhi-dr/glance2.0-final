from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
import requests
import json
import logging

logger = logging.getLogger(__name__)

def whatsapp_test(request):
    """
    View for testing WhatsApp messaging functionality
    """
    if request.method == 'POST':
        phone = request.POST.get('phone', '')
        message_text = request.POST.get('message', '')
        
        # Basic validation
        if not phone or not message_text:
            messages.error(request, "Both phone number and message are required")
            return render(request, 'administration/whatsapp_test.html')
        
        # Log the test request
        logger.info(f"WhatsApp test message requested for: {phone}")
        
        try:
            # Here you would include your actual WhatsApp API integration
            # For testing purposes, we're just simulating a successful response
            
            # Example API call (commented out)
            """
            api_url = "https://your-whatsapp-api-endpoint.com/send"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer YOUR_API_KEY'
            }
            payload = {
                'phone': phone,
                'message': message_text
            }
            response = requests.post(api_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    messages.success(request, "Test message sent successfully!")
                else:
                    messages.error(request, f"Failed to send message: {result.get('message')}")
            else:
                messages.error(request, f"API Error: {response.status_code}")
            """
            
            # Simulate successful sending for testing
            messages.success(request, "Test message simulated successfully! (No actual message was sent)")
            
        except Exception as e:
            logger.error(f"WhatsApp test error: {str(e)}")
            messages.error(request, f"Error while sending test message: {str(e)}")
    
    return render(request, 'administration/whatsapp_test.html')

def api_test(request):
    """
    View for testing the WhatsApp API connection
    Returns JSON response
    """
    try:
        # Here you would test your actual WhatsApp API connection
        # For testing purposes, we're just simulating a successful response
        
        # Example API connection test (commented out)
        """
        api_url = "https://your-whatsapp-api-endpoint.com/status"
        headers = {
            'Authorization': 'Bearer YOUR_API_KEY'
        }
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            return JsonResponse({
                'success': True,
                'message': 'API connection successful',
                'status': result
            })
        else:
            return JsonResponse({
                'success': False,
                'message': f'API returned status code: {response.status_code}'
            })
        """
        
        # Simulate successful API connection for testing
        return JsonResponse({
            'success': True,
            'message': 'API connection simulated successfully',
            'status': 'online'
        })
        
    except Exception as e:
        logger.error(f"WhatsApp API test error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error while testing API connection: {str(e)}'
        }) 
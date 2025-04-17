import re
from django.conf import settings
from django.shortcuts import render

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Compile a list of URL patterns that should be excluded from maintenance mode
        self.exempt_urls = getattr(settings, 'MAINTENANCE_EXEMPT_URLS', [])
        self.exempt_ips = getattr(settings, 'MAINTENANCE_EXEMPT_IPS', [])
        self.maintenance_mode = getattr(settings, 'MAINTENANCE_MODE', False)

    def __call__(self, request):
        # Skip maintenance mode for exempt URLs or IPs
        path = request.path_info.lstrip('/')
        
        # Check if maintenance mode is enabled
        if self.maintenance_mode:
            # Check if the current URL is exempt
            if any(re.match(url, path) for url in self.exempt_urls):
                return self.get_response(request)
                
            # Check if the current IP is exempt
            client_ip = self.get_client_ip(request)
            if client_ip in self.exempt_ips:
                return self.get_response(request)
                
            # If we're not exempt, show the maintenance page
            context = {'title': 'Site Maintenance'}
            return render(request, 'maintenance.html', context, status=503)
        
        # Maintenance mode is not active, continue with normal request
        return self.get_response(request)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip 
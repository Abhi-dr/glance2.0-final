# from django.shortcuts import render
# from django.conf import settings
# import re

# # Commenting out the entire MaintenanceModeMiddleware class
# class MaintenanceModeMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response
        
#     def __call__(self, request):
#         # Check if maintenance mode is enabled
#         maintenance_mode = getattr(settings, 'MAINTENANCE_MODE', False)
        
#         # Get exempt URLs (paths that should still work during maintenance)
#         exempt_urls = getattr(settings, 'MAINTENANCE_EXEMPT_URLS', [])
#         exempt_ips = getattr(settings, 'MAINTENANCE_EXEMPT_IPS', [])
        
#         # Check if the current path matches any exempt URLs
#         path = request.path_info.lstrip('/')
#         is_exempt = any(re.compile(url).match(path) for url in exempt_urls)
        
#         # Check if user's IP is in exempt IPs list
#         user_ip = self.get_client_ip(request)
#         ip_exempt = user_ip in exempt_ips
        
#         # Check if user is admin (optional override)
#         is_admin = request.user.is_authenticated and request.user.is_staff
#         admin_override = getattr(settings, 'MAINTENANCE_ADMIN_OVERRIDE', True)
        
#         # If in maintenance mode and not exempt, serve the maintenance page
#         if maintenance_mode and not is_exempt and not ip_exempt and not (admin_override and is_admin):
#             context = {
#                 'completion_time': getattr(settings, 'MAINTENANCE_COMPLETION_TIME', None)
#             }
#             return render(request, 'maintenance.html', context, status=503)
        
#         # Otherwise, continue with the regular request
#         return self.get_response(request)
    
#     def get_client_ip(self, request):
#         """Get the client's IP address from the request."""
#         x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#         if x_forwarded_for:
#             # Take the first IP in case of multiple proxies
#             ip = x_forwarded_for.split(',')[0].strip()
#         else:
#             ip = request.META.get('REMOTE_ADDR')
#         return ip

from accounts.models import Student
from datetime import datetime, timedelta



def user_context_processor(request):
    
    # Skip for admin panel URLs
    if request.path.startswith('/mClk3W)$t=/'):
        return {} 
    
    user_type = None
    user_object = None

    if request.user.is_authenticated:
        try:
            if hasattr(request.user, 'student'):
                user_type = 'student'
                user_object = request.user.student
            elif hasattr(request.user, 'administrator'):
                user_type = 'administrator'
                user_object = request.user.administrator
        except Exception:
            # Handle any exceptions gracefully
            pass

    return {
        'user_type': user_type,
        'user': user_object,
    }

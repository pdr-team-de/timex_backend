from django.shortcuts import redirect

class RoleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if request.user.user_type == 'TEMP_WORKER':
                if not request.path.startswith('/tracking/'):
                    return redirect('time-tracking')
        return self.get_response(request)
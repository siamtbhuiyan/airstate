from django.http import HttpResponseRedirect
from django.urls import reverse

def login_required(function):
    def wrap(request, *args, **kwargs):
        if request.session.has_key('username'):
            return function(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse("login")) 
    return wrap
from django.http import HttpResponseRedirect
from django.urls import reverse

def login_required(function):
    def wrap(request, *args, **kwargs):
        if request.session.has_key('username'):
            return function(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse("login")) 
    return wrap

def get_aqi(pm25):
    pm_ranges = [
        (0.0, 12.0),
        (12.1, 35.4),
        (35.5, 55.4),
        (55.5, 150.4),
        (150.5, 250.4),
        (250.5, 350.4),
        (350.5, 500.4)
    ]
    aqi_ranges = [
        (0, 50),
        (51, 100),
        (101, 150),
        (151, 200),
        (201, 300),
        (301, 400),
        (401, 500)
    ]
    aqi_status = ["Good", "Moderate", "Unhealthy for Sensitive Groups", "Unhealthy", "Very unhealthy", "Hazardous", "Hazardous"]
    aqi_colors = ["green", "yellow", "orange", "red", "purple", "maroon", "maroon"]
    c_p = round(pm25, 1)
    for i, pm_range in enumerate(pm_ranges):
        if pm_range[0] <= c_p <= pm_range[1]:
            bp_high = pm_range[1]
            bp_low = pm_range[0]
            index = i

    i_high = aqi_ranges[index][1]
    i_low = aqi_ranges[index][0]   

    aqi_value = round(((i_high - i_low)/(bp_high - bp_low)) * (c_p - bp_low) + i_low)
    return (aqi_value, aqi_status[index], aqi_colors[index])
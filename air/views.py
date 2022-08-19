from django.shortcuts import render
from django.db import connection
from django.http import HttpResponseRedirect
from django.urls import reverse

from air.functions import get_aqi, login_required

@login_required
def index(request):
    username = ""
    if request.session.has_key('username'):
        username = request.session['username']
    with connection.cursor() as cursor:
        cursor.execute("SELECT date(time), pm25 FROM tblAirQuality WHERE division='Dhaka' ORDER BY time DESC")
        current = cursor.fetchone()
        cursor.execute("SELECT DISTINCT division FROM tblAirQuality")
        divisionData = cursor.fetchall()
    currentDivision = "Dhaka"
    aqi = get_aqi(current[1])
    divisions = []
    for d in divisionData:
        divisions.append(d[0])
    print(get_aqi(220.1))
    if request.method == "POST":
        currentDivision = request.POST["division"]
        with connection.cursor() as cursor:
            cursor.execute("SELECT date(time), pm25 FROM tblAirQuality WHERE division=%s ORDER BY time DESC", [currentDivision])
            current = cursor.fetchone()
        aqi = get_aqi(current[1])
    return render(request, "air/index.html", {
        "username": username,
        "currentDate": current[0],
        "divisions": divisions,
        "currentDivision": currentDivision,
        "aqi_value": aqi[0],
        "aqi_status": aqi[1],
        "aqi_color": aqi[2]
    })

def register(request):
    message = ""
    if request.method == "POST":
        if request.POST["username"] == "":
            message = "Please provide Username"
        elif request.POST["password"] == "":
            message = "Please provide Password"
        elif request.POST["confirmation"] == "":
            message = "Please provide Confirmation"
        elif request.POST["password"] != request.POST["confirmation"]:
            message = "Confirmation must match Password"
        else:
            with connection.cursor() as cursor:
                cursor.execute("SELECT username FROM tblUser WHERE username=%s", [request.POST["username"]])
                user = cursor.fetchone()
            if user != None:
                message = "Username already exists"
            else:
                with connection.cursor() as cursor:
                    cursor.execute("INSERT INTO tblUser (username, password) VALUES(%s, %s)", [request.POST["username"], request.POST["password"]])
                request.session["username"] = request.POST["username"]
                return HttpResponseRedirect(reverse("index")) 
    return render(request, "air/register.html", {
        "message": message
    })

def login(request):
    message = ""
    if request.method == "POST":
        if request.POST["username"] == "":
            message = "Please provide Username"
        elif request.POST["password"] == "":
            message = "Please provide Password"
        else:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM tblUser WHERE username=%s", [request.POST["username"]])
                user = cursor.fetchone()
            if user == None:
                message = "User doesn't exist"
            else:
                if user[2] != request.POST["password"]:
                    message = "Incorrect Password"
                else:
                    request.session["username"] = request.POST["username"]
                    return HttpResponseRedirect(reverse("index")) 
    return render(request, "air/login.html", {
        "message": message
    })

@login_required
def logout(request):
    request.session.flush()
    return HttpResponseRedirect(reverse("index")) 

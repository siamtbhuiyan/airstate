from django.shortcuts import render
from django.db import connection
from django.http import HttpResponseRedirect
from django.urls import reverse

from air.functions import login_required

@login_required
def index(request):
    username = ""
    if request.session.has_key('username'):
        username = request.session['username']
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tblAirQuality")
        data = cursor.fetchall()
    return render(request, "air/index.html", {
        "username": username,
        "data": data
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

from django.shortcuts import render
from django.db import connection
from django.http import HttpResponseRedirect
from django.urls import reverse

from air.functions import get_aqi, login_required

import pandas as pd
from plotly.offline import plot
import plotly.express as px

@login_required
def index(request):
    username = ""
    if request.session.has_key('username'):
        username = request.session['username']
    with connection.cursor() as cursor:
        cursor.execute("SELECT DATE(time), pm25 FROM tblAirQuality WHERE division='Dhaka' ORDER BY time DESC")
        current = cursor.fetchone()
        cursor.execute("SELECT DISTINCT division FROM tblAirQuality")
        divisionData = cursor.fetchall()
        cursor.execute("SELECT DISTINCT strftime('%Y', time) FROM tblAirQuality")
        yearData = cursor.fetchall()
        cursor.execute("SELECT DISTINCT season FROM tblAirQuality")
        seasonData = cursor.fetchall()
    currentDivision = "Dhaka"
    aqi = get_aqi(current[1])
    divisions = []
    years = []
    seasons = []
    times = ["Yearly", "Seasonal"]
    for d in divisionData:
        divisions.append(d[0])
    for s in seasonData:
        seasons.append(s[0])
    for y in yearData:
        years.append(y[0])
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
        "seasons": seasons,
        "years": years,
        "currentDivision": currentDivision,
        "times": times,
        "box_basis": ["By Station", "Monthly"],
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

@login_required
def data_sources(request):
    username = ""
    if request.session.has_key('username'):
        username = request.session['username']
    if request.method == "POST":
        with connection.cursor() as cursor:
            cursor.execute("SELECT pm25, DATE(time), organization FROM tblAirQuality WHERE season=%s AND DATE(time) LIKE %s", [request.POST["season"], str(request.POST["year"] + "%")])
            data = cursor.fetchall()

        cleaned_data = [
            {
                "Daily": d[1],
                "Daily Avg PM2.5": d[0],
                "Organization": d[2] 
            } for d in data
        ]

        figure = px.line(cleaned_data, x="Daily", y="Daily Avg PM2.5", title=f"{request.POST['season']} {request.POST['year']}", color="Organization")
        line_chart = plot(figure, output_type="div")

        return render(request, "air/data-sources.html", {
            "username": username,
            "line_chart": line_chart
        })

@login_required
def time_based(request):
    username = ""
    if request.session.has_key('username'):
        username = request.session['username']
    if request.method == "POST":
        line_chart = []
        if request.POST["time"] == "Yearly":
            with connection.cursor() as cursor:
                cursor.execute("SELECT avg(pm25), strftime('%Y', time) FROM tblAirQuality WHERE division = 'Dhaka' GROUP BY strftime('%Y', time)")
                dhaka = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), strftime('%Y', time) FROM tblAirQuality WHERE division = 'Rangpur' GROUP BY strftime('%Y', time)")
                rangpur = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), strftime('%Y', time) FROM tblAirQuality WHERE division = 'Barishal' GROUP BY strftime('%Y', time)")
                barishal = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), strftime('%Y', time) FROM tblAirQuality WHERE division = 'Sylhet' GROUP BY strftime('%Y', time)")
                sylhet = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), strftime('%Y', time) FROM tblAirQuality WHERE division = 'Khulna' GROUP BY strftime('%Y', time)")
                khulna = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), strftime('%Y', time) FROM tblAirQuality WHERE division = 'Rajshahi' GROUP BY strftime('%Y', time)")
                rajshahi = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), strftime('%Y', time) FROM tblAirQuality WHERE division = 'Chittagong' GROUP BY strftime('%Y', time)")
                chittagong = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), strftime('%Y', time) FROM tblAirQuality WHERE division = 'Mymensingh' GROUP BY strftime('%Y', time)")
                mymensingh = cursor.fetchall()
            cleaned_dhaka = [
                {
                    "pm2.5": d[0],
                    "year": d[1], 
                    "division": "Dhaka"
                } for d in dhaka
            ]
            cleaned_rangpur = [
                {
                    "pm2.5": d[0],
                    "year": d[1], 
                    "division": "Rangpur"
                } for d in rangpur
            ]
            cleaned_sylhet = [
                {
                    "pm2.5": d[0],
                    "year": d[1], 
                    "division": "Sylhet"
                } for d in sylhet
            ]
            cleaned_rajshahi = [
                {
                    "pm2.5": d[0],
                    "year": d[1], 
                    "division": "Rajshahi"
                } for d in rajshahi
            ]
            cleaned_barishal = [
                {
                    "pm2.5": d[0],
                    "year": d[1], 
                    "division": "Barishal"
                } for d in barishal
            ]
            cleaned_chittagong = [
                {
                    "pm2.5": d[0],
                    "year": d[1], 
                    "division": "Chittagong"
                } for d in chittagong
            ]
            cleaned_mymensingh = [
                {
                    "pm2.5": d[0],
                    "year": d[1], 
                    "division": "Mymensingh"
                } for d in mymensingh
            ]
            cleaned_khulna = [
                {
                    "pm2.5": d[0],
                    "year": d[1], 
                    "division": "Khulna"
                } for d in khulna
            ]
            data = cleaned_dhaka + cleaned_rangpur + cleaned_sylhet + cleaned_barishal + cleaned_mymensingh + cleaned_chittagong + cleaned_khulna + cleaned_rajshahi
            figure = px.line(data, x="year", y="pm2.5", color="division")
            line_chart = plot(figure, output_type="div")
        elif request.POST["time"] == "Seasonal":
            with connection.cursor() as cursor:
                cursor.execute("SELECT avg(pm25), season FROM tblAirQuality WHERE division = 'Dhaka' GROUP BY season")
                dhaka = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), season FROM tblAirQuality WHERE division = 'Rangpur' GROUP BY season")
                rangpur = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), season FROM tblAirQuality WHERE division = 'Barishal' GROUP BY season")
                barishal = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), season FROM tblAirQuality WHERE division = 'Sylhet' GROUP BY season")
                sylhet = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), season FROM tblAirQuality WHERE division = 'Khulna' GROUP BY season")
                khulna = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), season FROM tblAirQuality WHERE division = 'Rajshahi' GROUP BY season")
                rajshahi = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), season FROM tblAirQuality WHERE division = 'Chittagong' GROUP BY season")
                chittagong = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), season FROM tblAirQuality WHERE division = 'Mymensingh' GROUP BY season")
                mymensingh = cursor.fetchall()
            cleaned_dhaka = [
                {
                    "pm2.5": d[0],
                    "season": d[1], 
                    "division": "Dhaka"
                } for d in dhaka
            ]
            print(cleaned_dhaka)
            cleaned_rangpur = [
                {
                    "pm2.5": d[0],
                    "season": d[1], 
                    "division": "Rangpur"
                } for d in rangpur
            ]
            cleaned_sylhet = [
                {
                    "pm2.5": d[0],
                    "season": d[1], 
                    "division": "Sylhet"
                } for d in sylhet
            ]
            cleaned_rajshahi = [
                {
                    "pm2.5": d[0],
                    "season": d[1], 
                    "division": "Rajshahi"
                } for d in rajshahi
            ]
            cleaned_barishal = [
                {
                    "pm2.5": d[0],
                    "season": d[1], 
                    "division": "Barishal"
                } for d in barishal
            ]
            cleaned_chittagong = [
                {
                    "pm2.5": d[0],
                    "season": d[1], 
                    "division": "Chittagong"
                } for d in chittagong
            ]
            cleaned_mymensingh = [
                {
                    "pm2.5": d[0],
                    "season": d[1], 
                    "division": "Mymensingh"
                } for d in mymensingh
            ]
            cleaned_khulna = [
                {
                    "pm2.5": d[0],
                    "season": d[1], 
                    "division": "Khulna"
                } for d in khulna
            ]
            data = cleaned_dhaka + cleaned_rangpur + cleaned_sylhet + cleaned_barishal + cleaned_mymensingh + cleaned_chittagong + cleaned_khulna + cleaned_rajshahi
            figure = px.line(data, x="season", y="pm2.5", color="division")
            line_chart = plot(figure, output_type="div")
        return render(request, "air/time-based.html", {
            "username": username,
            "line_chart": line_chart
        })

@login_required
def box_plot(request):
    username = ""
    if request.session.has_key('username'):
        username = request.session['username']
    if request.method == "POST":
        if request.POST["time"] == "By Station":
            with connection.cursor() as cursor:
                cursor.execute("SELECT pm25, station FROM tblAirQuality")
                data = cursor.fetchall()
            cleaned_data = [
                {
                    "PM2.5": d[0],
                    "Station": d[1], 
                } for d in data
            ]
            figure = px.box(cleaned_data, x="Station", y="PM2.5")
            box = plot(figure, output_type="div")
        elif request.POST["time"] == "Monthly":
            with connection.cursor() as cursor:
                cursor.execute("SELECT pm25, strftime('%m', time) FROM tblAirQuality")
                data = cursor.fetchall()
            cleaned_data = [
                {
                    "PM2.5": d[0],
                    "Month": d[1], 
                } for d in data
            ]
            figure = px.box(cleaned_data, x="Month", y="PM2.5")
            box = plot(figure, output_type="div")
    return render(request, "air/box-plot.html", {
            "username": username,
            "box": box
        })

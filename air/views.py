from django.shortcuts import render
from django.db import connection
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse

from air.functions import get_aqi, login_required

import pandas as pd
from plotly.offline import plot
import plotly.express as px

from json import load

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import csv

import datetime


@login_required
def index(request):
    username = ""
    if request.session.has_key('username'):
        username = request.session['username']
    with connection.cursor() as cursor:
        cursor.execute("SELECT isAdmin FROM tblUser WHERE username=%s", [username])
        admin_data = cursor.fetchone()
    isAdmin = False
    if admin_data[0] == 1:
        isAdmin = True
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
    times = ["Yearly", "Monthly", "Seasonal"]
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
        "box_basis": ["By Station", "Monthly", "Yearly"],
        "season_basis": ["Monthly", "Yearly"],
        "aqi_value": aqi[0],
        "aqi_status": aqi[1],
        "aqi_color": aqi[2],
        "pm25": current[1],
        "isAdmin": isAdmin
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

        figure = px.line(cleaned_data, x="Daily", y="Daily Avg PM2.5", title=f"Compare Multiple Data Sources from {request.POST['season']} {request.POST['year']}", color="Organization")
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
            figure = px.line(data, x="year", y="pm2.5", color="division", title="Division-Wise Yearly AQI")
            line_chart = plot(figure, output_type="div")
        elif request.POST["time"] == "Monthly":
            with connection.cursor() as cursor:
                cursor.execute("SELECT avg(pm25), strftime('%m', time) FROM tblAirQuality WHERE division = 'Dhaka' GROUP BY strftime('%m', time)")
                dhaka = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), strftime('%m', time) FROM tblAirQuality WHERE division = 'Rangpur' GROUP BY strftime('%m', time)")
                rangpur = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), strftime('%m', time) FROM tblAirQuality WHERE division = 'Barishal' GROUP BY strftime('%m', time)")
                barishal = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), strftime('%m', time) FROM tblAirQuality WHERE division = 'Sylhet' GROUP BY strftime('%m', time)")
                sylhet = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), strftime('%m', time) FROM tblAirQuality WHERE division = 'Khulna' GROUP BY strftime('%m', time)")
                khulna = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), strftime('%m', time) FROM tblAirQuality WHERE division = 'Rajshahi' GROUP BY strftime('%m', time)")
                rajshahi = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), strftime('%m', time) FROM tblAirQuality WHERE division = 'Chittagong' GROUP BY strftime('%m', time)")
                chittagong = cursor.fetchall()
                cursor.execute("SELECT avg(pm25), strftime('%m', time) FROM tblAirQuality WHERE division = 'Mymensingh' GROUP BY strftime('%m', time)")
                mymensingh = cursor.fetchall()
            cleaned_dhaka = [
                {
                    "pm2.5": d[0],
                    "Month": d[1], 
                    "division": "Dhaka"
                } for d in dhaka
            ]
            cleaned_rangpur = [
                {
                    "pm2.5": d[0],
                    "Month": d[1], 
                    "division": "Rangpur"
                } for d in rangpur
            ]
            cleaned_sylhet = [
                {
                    "pm2.5": d[0],
                    "Month": d[1], 
                    "division": "Sylhet"
                } for d in sylhet
            ]
            cleaned_rajshahi = [
                {
                    "pm2.5": d[0],
                    "Month": d[1], 
                    "division": "Rajshahi"
                } for d in rajshahi
            ]
            cleaned_barishal = [
                {
                    "pm2.5": d[0],
                    "Month": d[1], 
                    "division": "Barishal"
                } for d in barishal
            ]
            cleaned_chittagong = [
                {
                    "pm2.5": d[0],
                    "Month": d[1], 
                    "division": "Chittagong"
                } for d in chittagong
            ]
            cleaned_mymensingh = [
                {
                    "pm2.5": d[0],
                    "Month": d[1], 
                    "division": "Mymensingh"
                } for d in mymensingh
            ]
            cleaned_khulna = [
                {
                    "pm2.5": d[0],
                    "Month": d[1], 
                    "division": "Khulna"
                } for d in khulna
            ]
            data = cleaned_dhaka + cleaned_rangpur + cleaned_sylhet + cleaned_barishal + cleaned_mymensingh + cleaned_chittagong + cleaned_khulna + cleaned_rajshahi
            figure = px.line(data, x="Month", y="pm2.5", color="division", title="Division-Wise Monthly AQI")
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
            figure = px.line(data, x="season", y="pm2.5", color="division", title="Division-Wise Seasonal AQI")
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
            figure = px.box(cleaned_data, x="Station", y="PM2.5", title="Box plot AQI Data Visualization By Station")
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
            figure = px.box(cleaned_data, x="Month", y="PM2.5", title="Box plot Monthly AQI Data Visualization")
            box = plot(figure, output_type="div")
        elif request.POST["time"] == "Yearly":
            with connection.cursor() as cursor:
                cursor.execute("SELECT pm25, strftime('%Y', time) FROM tblAirQuality")
                data = cursor.fetchall()
            cleaned_data = [
                {
                    "PM2.5": d[0],
                    "Year": d[1], 
                } for d in data
            ]
            figure = px.box(cleaned_data, x="Year", y="PM2.5", title="Box plot Yearly AQI Data Visualization")
            box = plot(figure, output_type="div")    
        return render(request, "air/box-plot.html", {
                "username": username,
                "box": box
            })

@login_required
def season_wise(request):
    username = ""
    if request.session.has_key('username'):
        username = request.session['username']
    if request.method == "POST":
        if request.POST["time"] == "Monthly":
            with connection.cursor() as cursor:
                cursor.execute("SELECT AVG(pm25), season FROM tblAirQuality WHERE season='Summer' GROUP BY strftime('%m', time)")
                summer_data = cursor.fetchall()
                cursor.execute("SELECT AVG(pm25), season FROM tblAirQuality WHERE season='Winter' GROUP BY strftime('%m', time)")
                winter_data = cursor.fetchall()
                cursor.execute("SELECT AVG(pm25), season FROM tblAirQuality WHERE season='Spring' GROUP BY strftime('%m', time)")
                spring_data = cursor.fetchall()
                cursor.execute("SELECT AVG(pm25), season FROM tblAirQuality WHERE season='Autumn' GROUP BY strftime('%m', time)")
                autumn_data = cursor.fetchall()
            cleaned_summer_data = [
                {
                    "PM2.5": d[0],
                    "Season": d[1], 
                } for d in summer_data
            ]
            cleaned_winter_data = [
                {
                    "PM2.5": d[0],
                    "Season": d[1], 
                } for d in winter_data
            ]
            cleaned_spring_data = [
                {
                    "PM2.5": d[0],
                    "Season": d[1], 
                } for d in spring_data
            ]
            cleaned_autumn_data = [
                {
                    "PM2.5": d[0],
                    "Season": d[1], 
                } for d in autumn_data
            ]
            cleaned_data = cleaned_autumn_data + cleaned_spring_data + cleaned_winter_data + cleaned_summer_data
            figure = px.box(cleaned_data, x="Season", y="PM2.5", color="Season", title="Season-Wise Monthly AQI")
            box = plot(figure, output_type="div")    
        elif request.POST["time"] == "Yearly":
            with connection.cursor() as cursor:
                cursor.execute("SELECT AVG(pm25), season FROM tblAirQuality WHERE season='Summer' GROUP BY strftime('%Y', time)")
                summer_data = cursor.fetchall()
                cursor.execute("SELECT AVG(pm25), season FROM tblAirQuality WHERE season='Winter' GROUP BY strftime('%Y', time)")
                winter_data = cursor.fetchall()
                cursor.execute("SELECT AVG(pm25), season FROM tblAirQuality WHERE season='Spring' GROUP BY strftime('%Y', time)")
                spring_data = cursor.fetchall()
                cursor.execute("SELECT AVG(pm25), season FROM tblAirQuality WHERE season='Autumn' GROUP BY strftime('%Y', time)")
                autumn_data = cursor.fetchall()
            cleaned_summer_data = [
                {
                    "PM2.5": d[0],
                    "Season": d[1], 
                } for d in summer_data
            ]
            cleaned_winter_data = [
                {
                    "PM2.5": d[0],
                    "Season": d[1], 
                } for d in winter_data
            ]
            cleaned_spring_data = [
                {
                    "PM2.5": d[0],
                    "Season": d[1], 
                } for d in spring_data
            ]
            cleaned_autumn_data = [
                {
                    "PM2.5": d[0],
                    "Season": d[1], 
                } for d in autumn_data
            ]
            cleaned_data = cleaned_autumn_data + cleaned_spring_data + cleaned_winter_data + cleaned_summer_data
            figure = px.box(cleaned_data, x="Season", y="PM2.5", color="Season", title="Season-Wise Yearly AQI")
            box = plot(figure, output_type="div")  
        return render(request, "air/season-wise.html", {
                    "username": username,
                    "box": box
                })

def yearly_average(request):
    if request.session.has_key('username'):
        username = request.session['username']
    with connection.cursor() as cursor:
        cursor.execute("SELECT AVG(pm25), strftime('%Y', time) season FROM tblAirQuality GROUP BY strftime('%Y', time)")
        data = cursor.fetchall()
    cleaned_data = [
            {
                "PM2.5": d[0],
                "Year": d[1], 
            } for d in data
        ]
    figure = px.bar(cleaned_data, x="Year", y="PM2.5", title="Yearly Average AQI")
    bar = plot(figure, output_type="div")  
    return render(request, "air/yearly.html", {
            "username": username,
            "bar": bar
        })
        

@login_required
def daily_based(request):
    username = ""
    if request.session.has_key('username'):
        username = request.session['username']
    with connection.cursor() as cursor:
        cursor.execute("SELECT pm25, DATE(time) FROM tblAirQuality WHERE division='Dhaka' ORDER BY time DESC")
        dhaka = cursor.fetchone()
        cursor.execute("SELECT pm25, DATE(time) FROM tblAirQuality WHERE division='Rangpur' ORDER BY time DESC")
        rangpur = cursor.fetchone()
        cursor.execute("SELECT pm25, DATE(time) FROM tblAirQuality WHERE division='Barishal' ORDER BY time DESC")
        barishal = cursor.fetchone()
        cursor.execute("SELECT pm25, DATE(time) FROM tblAirQuality WHERE division='Sylhet' ORDER BY time DESC")
        sylhet = cursor.fetchone()
        cursor.execute("SELECT pm25, DATE(time) FROM tblAirQuality WHERE division='Khulna' ORDER BY time DESC")
        khulna = cursor.fetchone()
        cursor.execute("SELECT pm25, DATE(time) FROM tblAirQuality WHERE division='Rajshahi' ORDER BY time DESC")
        rajshahi = cursor.fetchone()
        cursor.execute("SELECT pm25, DATE(time) FROM tblAirQuality WHERE division='Chittagong' ORDER BY time DESC")
        chittagong = cursor.fetchone()
        cursor.execute("SELECT pm25, DATE(time) FROM tblAirQuality WHERE division='Mymensingh' ORDER BY time DESC")
        mymensingh = cursor.fetchone()
        cleaned_dhaka = {
                "pm2.5": dhaka[0],
                "date": dhaka[1], 
                "division": "Dhaka"
        }
        cleaned_rangpur = {
                "pm2.5": rangpur[0],
                "date": rangpur[1], 
                "division": "rangpur"
        }
        cleaned_barishal = {
                "pm2.5": barishal[0],
                "date": barishal[1], 
                "division": "barishal"
        }
        cleaned_sylhet = {
                "pm2.5": sylhet[0],
                "date": sylhet[1], 
                "division": "sylhet"
        }
        cleaned_khulna = {
                "pm2.5": khulna[0],
                "date": khulna[1], 
                "division": "khulna"
        }
        cleaned_rajshahi = {
                "pm2.5": rajshahi[0],
                "date": rajshahi[1], 
                "division": "rajshahi"
        }
        cleaned_chittagong = {
                "pm2.5": chittagong[0],
                "date": chittagong[1], 
                "division": "chittagong"
        }
        cleaned_mymensingh = {
                "pm2.5": mymensingh[0],
                "date": mymensingh[1], 
                "division": "mymensingh"
        }
        data = []
        data.append(cleaned_dhaka)
        data.append(cleaned_rangpur)
        data.append(cleaned_sylhet)
        data.append(cleaned_barishal)
        data.append(cleaned_mymensingh)
        data.append(cleaned_chittagong)
        data.append(cleaned_khulna)
        data.append(cleaned_rajshahi)
        figure = px.line(data, x="division", y="pm2.5", title="Division-Wise Daily AQI")
        line_chart = plot(figure, output_type="div")
    return render(request, "air/daily-based.html", {
            "username": username,
            "line_chart": line_chart
        })

def bd_map(request):
    username = ""
    if request.session.has_key('username'):
        username = request.session['username']
    divisions = load(open('bangladesh_geojson_8_divisions.json','r'))	
    with connection.cursor() as cursor:
        cursor.execute("SELECT pm25, DATE(time) FROM tblAirQuality WHERE division='Dhaka' ORDER BY time DESC")
        dhaka = cursor.fetchone()
        cursor.execute("SELECT pm25, DATE(time) FROM tblAirQuality WHERE division='Rangpur' ORDER BY time DESC")
        rangpur = cursor.fetchone()
        cursor.execute("SELECT pm25, DATE(time) FROM tblAirQuality WHERE division='Barishal' ORDER BY time DESC")
        barishal = cursor.fetchone()
        cursor.execute("SELECT pm25, DATE(time) FROM tblAirQuality WHERE division='Sylhet' ORDER BY time DESC")
        sylhet = cursor.fetchone()
        cursor.execute("SELECT pm25, DATE(time) FROM tblAirQuality WHERE division='Khulna' ORDER BY time DESC")
        khulna = cursor.fetchone()
        cursor.execute("SELECT pm25, DATE(time) FROM tblAirQuality WHERE division='Rajshahi' ORDER BY time DESC")
        rajshahi = cursor.fetchone()
        cursor.execute("SELECT pm25, DATE(time) FROM tblAirQuality WHERE division='Chittagong' ORDER BY time DESC")
        chittagong = cursor.fetchone()
        cursor.execute("SELECT pm25, DATE(time) FROM tblAirQuality WHERE division='Mymensingh' ORDER BY time DESC")
        mymensingh = cursor.fetchone()

        data = [
            {
                "id": 0,
                "name": "Barishal",
                "AQI": get_aqi(barishal[0])[0],
                "aqi_status": get_aqi(barishal[0])[1],
                "aqi_color": get_aqi(barishal[0])[2]
            },
            {

                "id": 1,
                "name": "Chittagong",
                "AQI": get_aqi(chittagong[0])[0],
                "aqi_status": get_aqi(chittagong[0])[1],
                "aqi_color": get_aqi(chittagong[0])[2]
            },
            {

                "id": 2,
                "name": "Dhaka",
                "AQI": get_aqi(dhaka[0])[0],
                "aqi_status": get_aqi(dhaka[0])[1],
                "aqi_color": get_aqi(dhaka[0])[2]
            },
            {

                "id": 3,
                "name": "Khulna",
                "AQI": get_aqi(khulna[0])[0],
                "aqi_status": get_aqi(khulna[0])[1],
                "aqi_color": get_aqi(khulna[0])[2]
            },
            {

                "id": 4,
                "name": "Mymensingh",
                "AQI": get_aqi(mymensingh[0])[0],
                "aqi_status": get_aqi(mymensingh[0])[1],
                "aqi_color": get_aqi(mymensingh[0])[2]
            },
            {

                "id": 5,
                "name": "Rajshahi",
                "AQI": get_aqi(rajshahi[0])[0],
                "aqi_status": get_aqi(rajshahi[0])[1],
                "aqi_color": get_aqi(rajshahi[0])[2]
            },
            {

                "id": 6,
                "name": "Rangpur",
                "AQI": get_aqi(rangpur[0])[0],
                "aqi_status": get_aqi(rangpur[0])[1],
                "aqi_color": get_aqi(rangpur[0])[2]
            },
            {

                "id": 7,
                "name": "Sylhet",
                "AQI": get_aqi(sylhet[0])[0],
                "aqi_status": get_aqi(sylhet[0])[1],
                "aqi_color": get_aqi(sylhet[0])[2]
            }
        ]
        clrs = []
        for i in range(len(data)):
            if data[i]["AQI"] <= 50:
                clrs.append('rgb(0, 255, 0)')
            elif 51 < data[i]["AQI"] <= 100:
                clrs.append('rgb(255, 255, 0)')
            elif 101 < data[i]["AQI"] <= 150:
                clrs.append('rgb(255, 165, 0)')
            elif 151 < data[i]["AQI"] <= 200:
                clrs.append('rgb(255, 0, 0)')
            elif 201 < data[i]["AQI"] <= 300:
                clrs.append('rgb(128, 0, 128)')
            elif 301 < data[i]["AQI"] <= 500:
                clrs.append('rgb(128, 0, 0)')
        figure = px.choropleth_mapbox(data, geojson=divisions, locations='id', color='name', mapbox_style="carto-positron", center= { 'lat' : 23.6850, 'lon' : 90.3563}, zoom=5, opacity=0.6, title='Division Wise AQI Visualization with Colorcoding', hover_name='name', hover_data=['AQI'], color_discrete_sequence=clrs)
        division_map = plot(figure, output_type="div")
    return render(request, "air/bd-map.html", {
            "username": username,
            "division_map": division_map
        })

@login_required
def add(request):
    username = ""
    message = ""
    if request.session.has_key('username'):
        username = request.session['username']
    with connection.cursor() as cursor:
        cursor.execute("SELECT isAdmin FROM tblUser WHERE username=%s", [username])
        admin_data = cursor.fetchone()
    isAdmin = False
    if admin_data[0] == 1:
        isAdmin = True
    if request.method == "POST":
        if 'time' in request.POST:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO tblAirQuality (time, pm25, averageTemp, rainPercipitation, windSpeed, visibility, cloudCover, relativeHumidity, station, division, organization, season) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [request.POST["time"], request.POST["pm25"], request.POST["temp"], request.POST["rain"], request.POST["wind"], request.POST["visibility"], request.POST["cloud"], request.POST["relative"], request.POST["station"], request.POST["division"], request.POST["organization"], request.POST["season"]])
            message = "Data Inserted Successfully"
        elif 'csv' in request.FILES:
            current_csv = request.FILES['csv']
            path = default_storage.save(f'{current_csv.name}', ContentFile(current_csv.read()))
            file = pd.read_csv(f'uploads/{path}')
            file['time'] = pd.to_datetime(file['time']).dt.date
            data = file.values.tolist()
            for d in data:
                with connection.cursor() as cursor:
                    cursor.execute("INSERT INTO tblAirQuality (time, pm25, averageTemp, rainPercipitation, windSpeed, visibility, cloudCover, relativeHumidity, station, division, organization, season) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", d)
                message = "Data Imported Successfully"
    return render(request, "air/add.html", {
            "username": username,
            "isAdmin": isAdmin,
            "message": message
        })

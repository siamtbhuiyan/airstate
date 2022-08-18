from django.shortcuts import render
from django.db import connection

def index(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM tblAirQuality")
        data = cursor.fetchall()
    print(data)
    return render(request, "air/index.html", {
        "data": data
    })
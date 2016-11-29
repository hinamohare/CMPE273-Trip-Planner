import urllib2

from flask import Flask, render_template
from flask import jsonify, request, session # import objects from the flask module
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from sqlalchemy import event
from sqlalchemy import DDL
import requests
from flask import Response

#***************************** lyft authorization and cost api*******************************
class LyftApi :

    @staticmethod
    def getAccessToken():
        """get Lyft access token for using lyft api"""

        client_secrete ="WRU95RMFGN9kRV9VOIXhzBEaBcqwTzHV"
        client_Id = "9M08-8z29d9G"
        url = "https://api.lyft.com/oauth/token"
        payload = {"grant_type": "client_credentials", "scope": "public"}
        data = json.dumps(payload)

        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, data=data, auth=(client_Id,client_secrete ), headers= headers)
        response = resp.content
        response_json = json.loads(response)
        access_token = response_json["access_token"]
        return access_token

    def __init__(self):
        pass

    @staticmethod
    def getLyftCost( start_lat,start_lng,end_lat, end_lng):

        """   input: start_lat, start_lng, end_lat, end_lng
                return:  name(Lyft), ride type (Lyft_line), cost(USD), time(minute), distance(miles)"""

        lyft_cost_url = "https://api.lyft.com/v1/cost?start_lat="+start_lat+"&start_lng="+start_lng+"&end_lat="+end_lat+"&end_lng="+end_lng
        access_token = LyftApi.getAccessToken()
        mytoken = "bearer "+access_token
        cost_resp = requests.get(lyft_cost_url, headers={'Authorization': mytoken})
        cost_data = cost_resp.content
        cost_json = json.loads(cost_data)
        ride_data = cost_json["cost_estimates"][1] # cheapest ride is Lyft_line
        ride_type = ride_data["ride_type"] # ride type
        ride_time = round(ride_data["estimated_duration_seconds"]/60.0, 2) # time in minutes
        ride_cost = round(ride_data["estimated_cost_cents_max"]/100.0, 2) # max cost in USD
        ride_distance = ride_data["estimated_distance_miles"] # distance in mile
        lyft_cost_info = {"Service_provider": "Lyft",
                          "car_type" : ride_type,
        "costs_by_cheapest_car_type": ride_cost,
        "total_duration": ride_time,
        "total_distance": ride_distance}
        return lyft_cost_info


#print LyftApi.getLyftCost("37.7772","-122.4233","37.7972","-122.4533")
list = [1,2,3,4,5]
i = 0
while (i<(len(list)-1)):
    print list[i]
    print list[i+1]
    i=i+1





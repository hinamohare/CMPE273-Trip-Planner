# coding=utf-8
import urllib2
import itertools

from flask import Flask, render_template
from flask import jsonify, request, session # import objects from the flask module
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_
from datetime import datetime
import json
from sqlalchemy import event
from sqlalchemy import DDL
import requests
from flask import Response
from lyft import LyftApi
from uber import UberApi
from model import *
from address import AddressParser, Address
app = Flask(__name__) #define app using Flask


#************************************  database config information    ********************************#
app.config['SQLALCHEMY_DATABASE_URI']  = 'mysql+pymysql://root:root@127.0.0.1:3306/address'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

#**********************************   database model  ************************************************#
#db = SQLAlchemy(app)

class LocationDetails(db.Model):
    __tablename__ = 'LocationDetails'
    location_id = db.Column('location_id', db.Integer, primary_key=True)
    name = db.Column('name', db.String(100))
    address = db.Column('address', db.String(1000))
    city = db.Column('city', db.String(100))
    state = db.Column('state', db.String(50))
    zip = db.Column('zip', db.String(10))
    createdOn = db.Column('createdOn', db.DateTime, default=db.func.now())
    updatedOn = db.Column('updatedOn', db.DateTime, default=db.func.now())
    lat = db.Column('lat', db.FLOAT)
    lng = db.Column('lng', db.FLOAT)

    def __init__(self, name, address,city, state, zip, createdOn, updatedOn, lat, lng):
        self.name = name
        self.address = address
        self.city = city
        self.state = state
        self.zip = zip
        self.createdOn = createdOn
        self.updatedOn = updatedOn
        self.lat = lat
        self.lng = lng

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.location_id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip': self.zip,
            'coordinate': {'lat': self.lat,'lng': self.lng}
        }

#********************************************* functions ****************************************#
start_point = {} # holds starting point name, lat and lng
end_point = {} # holds end point name, lat and lng
optimized_route =[] # list of optimized route in the form of {"address":" ", "lat":" ", "lng" : " " }
Locations = {"start":start_point, "end": end_point, "intermediate_locations" : optimized_route}
final_result = {}
providers = [] #list of service provider data (uber, lyft)
provider =  {                                     # dict containing information of each service data
            "name" : "",
            "total_costs_by_cheapest_car_type" : 0,
            "currency_code": "USD",
            "total_duration" : 0,
            "duration_unit": "minute",
            "total_distance" : 0,
            "distance_unit": "mile"}



def get_lat_lng(req_url):
    """
    obtain the geological latitude and longitude using google api
    :param req_url:  google api with address of a location to get its latitude and longitude
    :return:  {"lat": lat, "lng": lng} Dictionary containing latitude and longitude of the location
    """
    result = {} # stores the latitude and longitude
    response = urllib2.urlopen(req_url) # call the google api using url provided
    json_response = response.read()
    jsonList = json.loads(json_response)

    # extract the latitude and longitude from the response
    lat = jsonList["results"][0]["geometry"]["location"]["lat"]
    lng = jsonList["results"][0]["geometry"]["location"]["lng"]
    result["lat"] = lat
    result["lng"] = lng
    return result



def get_details(List):
    """
     get the latitude and longitude of the intermedate locations without optimum routes
    :param List: List of intermediate locations of the travel
    :return: list of dictionary containing the address, lattitude and longitude of the intermediate locations
    """
    original_location_order = []
    for i in List:
        location = i.replace(" ","+")
        geo_location = get_location_db(location, "intermediate")
        lat = geo_location.lat
        lng = geo_location.lng
        original_location_order.append({"address" : i, "lat": lat, "lng" : lng, "location_id":geo_location})

    return original_location_order  
    
def get_best_route(locations_list,origin_address, destination_address):
    global optimized_route
    del optimized_route[:]
    src = origin_address

    print "\n get_best_route optimized_route :", len(optimized_route)
    i = 0
    while i < (len(locations_list) - 1):
        print "\n get_best_route for :", i
        min = 99999
        nxt = locations_list[0]
        for loc in locations_list:
            dst = get_distance(src, loc)
            if dst < min:
                min = dst
                nxt = loc
        optimized_route.append(nxt)
        locations_list.remove(nxt)
        src = nxt

    optimized_route.append(locations_list[0])  #append the remaining intermediate location
    for loc in optimized_route:
        print "\n\n optimized route : ", loc
    
def get_distance(origin_address, destination_address):
    originLat = str(origin_address["lat"])
    originLng = str(origin_address["lng"])
    destLat = str(destination_address["lat"])
    destLng = str(destination_address["lng"])
    
    url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins="+originLat+","+originLng+"&destinations="+destLat+","+destLng+"&key=AIzaSyAmsECtTD88DUJDFgf_iq-YFLYHkRyLBi8"
    response = urllib2.urlopen(url)  # call the google api using url provided
    json_response = response.read()
    jsonList = json.loads(json_response)
    
    dist = jsonList["rows"][0]["elements"][0]["distance"]["text"]
    d = dist.split()
    s = float(d[0])
    return s


def get_Lyft_details_direct():
    """
    When there are no middle/intermediate points on the route, calculates cost, distance and duration for trip for lyft
    :return: lyft_data = {"name": name, "car_type": car_type, "total_costs_by_cheapest_car_type": total_cost, "currency_code": "USD",
                        "total_duration": total_duration, "duration_unit": "minute", "total_distance": total_distance, "distance_unit": "mile"}
    """
    lat1 = start_point["lat"]
    lng1 = start_point["lng"]
    lat2 = end_point["lat"]
    lng2 = end_point["lng"]
    drive_data = LyftApi.getLyftCost(lat1,lng1,lat2,lng2)
    total_cost = drive_data["costs_by_cheapest_car_type"]
    total_distance = drive_data["distance"]
    total_duration = drive_data["duration"]

    # construct the response
    name = drive_data["service_provider"]
    car_type = drive_data["car_type"]
    lyft_data = {
        "name": name,
        "car_type": car_type,
        "total_costs_by_cheapest_car_type": total_cost,
        "currency_code": "USD",
        "total_duration": total_duration,
        "duration_unit": "minute",
        "total_distance": total_distance,
        "distance_unit": "mile"
    }
    return lyft_data


def get_Lyft_details():
    """
    calculates cost, distance and duration for entire trip for lyft
    :return: lyft_data = {"name": name, "car_type": car_type, "total_costs_by_cheapest_car_type": total_cost, "currency_code": "USD",
                        "total_duration": total_duration, "duration_unit": "minute", "total_distance": total_distance, "distance_unit": "mile"}
     the lyft ride details for the entire travel
    """
    
    if no_inter_points == 0:
        result_data =  get_Lyft_details_direct()
        return result_data
    
    #calculate the lyft data from the starting point to the first location in the optimum route list
    lat1 = start_point["lat"]
    lng1 = start_point["lng"]
    lat2 = optimized_route[0]["lat"]
    lng2 = optimized_route[0]["lng"]
    drive_data = LyftApi.getLyftCost(lat1,lng1,lat2,lng2)
    if drive_data["car_type"] == "Not available":
        lyft_data = {
        "name": drive_data["service_provider"],
        "car_type": drive_data["car_type"],
        "total_costs_by_cheapest_car_type": 0,
        "currency_code": "USD",
        "total_duration": 0,
        "duration_unit": "minute",
        "total_distance": 0,
        "distance_unit": "mile"
        }
        return lyft_data
        
    total_cost = drive_data["costs_by_cheapest_car_type"]
    total_distance = drive_data["distance"]
    total_duration = drive_data["duration"]

    # calculate the lyft data for the intermediate optimum route locations
    i = 0
    while i < (len(optimized_route) - 1):
        lat1 = optimized_route[i]["lat"]
        lng1 = optimized_route[i]["lng"]
        lat2 = optimized_route[i+1]["lat"]
        lng2 = optimized_route[i+1]["lng"]
        drive_data = LyftApi.getLyftCost(lat1, lng1, lat2, lng2)
        if drive_data["car_type"] == "Not available":
            lyft_data = {
            "name": drive_data["service_provider"],
            "car_type": drive_data["car_type"],
            "total_costs_by_cheapest_car_type": 0,
            "currency_code": "USD",
            "total_duration": 0,
            "duration_unit": "minute",
            "total_distance": 0,
            "distance_unit": "mile"
            }
            return lyft_data
        total_cost = total_cost+ drive_data["costs_by_cheapest_car_type"]
        total_distance = total_distance + drive_data["distance"]
        total_duration = total_distance + drive_data["duration"]
        i += 1
    # calculate the lyft data for the last intermediate optimum route locations to the end location in the travel plan
    lat1 = optimized_route[i]["lat"]
    lng1 = optimized_route[i]["lng"]
    lat2 = end_point["lat"]
    lng2 = end_point["lng"]
    drive_data = LyftApi.getLyftCost(lat1, lng1, lat2, lng2)
    total_cost = total_cost + drive_data["costs_by_cheapest_car_type"]
    total_distance = total_distance + drive_data["distance"]
    total_duration = total_duration + drive_data["duration"]

    # construct the response
    name = drive_data["service_provider"]
    car_type = drive_data["car_type"]
    lyft_data = {
        "name": name,
        "car_type": car_type,
        "total_costs_by_cheapest_car_type": total_cost,
        "currency_code": "USD",
        "total_duration": total_duration,
        "duration_unit": "minute",
        "total_distance": total_distance,
        "distance_unit": "mile"
    }
    return lyft_data

def get_Uber_details_direct():
    """
    When there are no middle/intermediate points on the route, calculates cost, distance and duration for trip for uber
    :return: uber_data = {"name": name, "car_type": car_type, "total_costs_by_cheapest_car_type": total_cost, "currency_code": "USD",
                        "total_duration": total_duration, "duration_unit": "minute", "total_distance": total_distance, "distance_unit": "mile"}
    """
    
    #calculate the uber data from the starting point to the first location in the optimum route list
    lat1 = start_point["lat"]
    lng1 = start_point["lng"]
    lat2 = end_point["lat"]
    lng2 = end_point["lng"]
    drive_data = UberApi.getUberCost(lat1,lng1,lat2,lng2)
    total_cost = drive_data["costs_by_cheapest_car_type"]
    total_distance = drive_data["distance"]
    total_duration = drive_data["duration"]

    # construct the response
    name = drive_data["service_provider"]
    car_type = drive_data["car_type"]
    uber_data = {
        "name": name,
        "car_type": car_type,
        "total_costs_by_cheapest_car_type": total_cost,
        "currency_code": "USD",
        "total_duration": total_duration,
        "duration_unit": "minute",
        "total_distance": total_distance,
        "distance_unit": "mile"
    }
    return uber_data

def get_Uber_details():
    """
    calculates cost, distance and duration for entire trip for uber
    :return: uber_data = {"name": name, "car_type": car_type, "total_costs_by_cheapest_car_type": total_cost, "currency_code": "USD",
                        "total_duration": total_duration, "duration_unit": "minute", "total_distance": total_distance, "distance_unit": "mile"}
     the uber ride details for the entire travel
    """
    if no_inter_points == 0:
        result_data =  get_Uber_details_direct()
        return result_data
    
    #calculate the uber data from the starting point to the first location in the optimum route list
    lat1 = start_point["lat"]
    lng1 = start_point["lng"]
    lat2 = optimized_route[0]["lat"]
    lng2 = optimized_route[0]["lng"]
    drive_data = UberApi.getUberCost(lat1,lng1,lat2,lng2)
    total_cost = drive_data["costs_by_cheapest_car_type"]
    total_distance = drive_data["distance"]
    total_duration = drive_data["duration"]

    # calculate the uber data for the intermediate optimum route locations
    i = 0
    while i < (len(optimized_route) - 1):
        lat1 = optimized_route[i]["lat"]
        lng1 = optimized_route[i]["lng"]
        lat2 = optimized_route[i+1]["lat"]
        lng2 = optimized_route[i+1]["lng"]
        drive_data = UberApi.getUberCost(lat1, lng1, lat2, lng2)
        total_cost = total_cost+ drive_data["costs_by_cheapest_car_type"]
        total_distance = total_distance + drive_data["distance"]
        total_duration = total_distance + drive_data["duration"]
        i += 1
    # calculate the uber data for the last intermediate optimum route locations to the end location in the travel plan
    lat1 = optimized_route[i]["lat"]
    lng1 = optimized_route[i]["lng"]
    lat2 = end_point["lat"]
    lng2 = end_point["lng"]
    drive_data = UberApi.getUberCost(lat1, lng1, lat2, lng2)
    total_cost = total_cost + drive_data["costs_by_cheapest_car_type"]
    total_distance = total_distance + drive_data["distance"]
    total_duration = total_duration + drive_data["duration"]

    # construct the response
    name = drive_data["service_provider"]
    car_type = drive_data["car_type"]
    uber_data = {
        "name": name,
        "car_type": car_type,
        "total_costs_by_cheapest_car_type": total_cost,
        "currency_code": "USD",
        "total_duration": total_duration,
        "duration_unit": "minute",
        "total_distance": total_distance,
        "distance_unit": "mile"
    }
    return uber_data
#***************************************code for user interface*************************************#
@app.route('/test1')
def test1():
    return render_template('test1.html')

@app.route('/')
def index():
    """
    returns the index page which consists a form for locations input
    :return: index page
    """
    return render_template('index.html')
    
def get_best_routeDj(locations_list,origin_address, destination_address):
    print "\n\n\n get_best_routeDj 1"
    global optimized_route
    del optimized_route[:]
    interLocsLen = len(locations_list)
    if interLocsLen == 1:
        optimized_route.append(locations_list[0])
        return
        
    print "\n\n\n get_best_routeDj 2"
    
    distancesMatrix =  [[99999 for _ in range(interLocsLen)] for _ in range(interLocsLen)]
    
    distFrmStart = []   
    indx = 0
    while indx < interLocsLen:
        distFrmStart.append(get_distance(origin_address, locations_list[indx]))
        indx = indx + 1
    
    #print "\n\n\n get_best_routeDj 3"
    
    distToEnd = []
    indx = 0
    while indx < interLocsLen:
        distToEnd.append(get_distance(locations_list[indx], destination_address))
        indx = indx + 1
    
    #print "\n\n\n get_best_routeDj 4"
    
    index1 = 0    
    index2 = 0
    while index1 < interLocsLen:
        while index2 < interLocsLen:
            #print " intered with ", index1, index2
            if index1 == index2:
                distancesMatrix[index1][index2] = 99999
            else:
                dst = get_distance(locations_list[index1], locations_list[index2])
                #print "\n Cost1 is ", dst
                distancesMatrix[index1][index2] = dst
            index2 = index2 + 1
        index1= index1 + 1
        index2 = 0
        
    paths = []
    locs = []
    minCost = 99999
    for indx in range(0, interLocsLen):
        locs.append(indx)
    for L in range(0, interLocsLen+1):
        for subset in itertools.permutations(locs, L):
            if len(subset) == interLocsLen:
                #print "\n Full path found : ", subset
                
                curCost = 0
                for i in range(0,interLocsLen-1):
                    srcIndx = subset[i]
                    destIndx = subset[i+1]
                    #print "\n Cost is ", srcIndx, destIndx, distancesMatrix[srcIndx][destIndx]
                    curCost = curCost + distancesMatrix[srcIndx][destIndx]
                    
                curCost = curCost + distFrmStart[subset[0]]
                curCost = curCost + distToEnd[subset[interLocsLen-1]]                
                print "\n Path and Cost are = ", subset, curCost
                if curCost < minCost:
                    print "\n found minimum cost adding", subset, len(paths)
                    minCost =  curCost
                    paths.append(subset)
    print "\n\n Minimum cost is ", minCost
    bestPth = paths[len(paths)-1]
    print "\n Best path is ", bestPth
    for i in range(0,interLocsLen):
        optimized_route.append(locations_list[bestPth[i]])
    print "\n Best final path is ", optimized_route

@app.route('/result',methods = ['POST'])    
def getPrice():
    """
    returns the optimum route solution for the input locations based on cost provided by Lyft and Uber
    :return: json_result
    """
    global start_point
    global end_point
    global no_inter_points
    input_json = request.get_json(force=True)
    #print "\n Input json \n", input_json

    startlocation = request.json["startlocation"] # starting point of the travel
    location = startlocation.replace(" ","+")
    adrs = get_location_db(location, "start")
    #print "\n\n\n new func    ", adrs.lat, adrs.lng
    start_point["lat"] = adrs.lat
    start_point["lng"] = adrs.lng
    start_point["address"]= startlocation
    
    endlocation = request.json["endlocation"] # end point of the travel
    location = endlocation.replace(" ", "+")
    result = get_location_db(location, "end")
    end_point["address"] = endlocation
    end_point["lat"] = result.lat
    end_point["lng"] = result.lng
    #print "\n End point \n", end_point
    
    dist = get_distance(start_point,end_point)
    print "\n\n The distnce is ", dist
    
    original_list = request.json["intermidiatelocation"] # list containing the intermediate locations
    #print "intermidiatelocation \n", original_list

    no_inter_points = len(original_list)
    #print "\n\n no_inter_points = ", no_inter_points
    if no_inter_points>0 :
        intermediate_address_lat_lng = get_details(original_list) # get the latitude and longitude of the intermediate locations
        #print(intermediate_address_lat_lng)
        #get_optimum_route(intermediate_address_lat_lng, startlocation, endlocation) # get the optimized route using google api
        get_best_routeDj(intermediate_address_lat_lng, start_point, end_point)
        print "\n\n optimized_route = ", optimized_route
        
    del providers[:]
    lyft_data = get_Lyft_details() # get the cost, duration and distance for entire trip with lyft
    providers.append(lyft_data)  # append the result to the list of service providers


    uber_data = get_Uber_details() # get the cost, duration and distance for entire trip with uber
    providers.append(uber_data) # append the result to the list of service providers
    best_route = []
    if no_inter_points>0 :
        for L in optimized_route:
            midPoint = {}
            midPoint["lat"] = L["lat"]
            midPoint["lng"] = L["lng"]
            midPoint["address"]= L["address"]
            best_route.append(midPoint)

    # construct the final response
    final_result["start"] = start_point
    final_result["end"] = end_point
    final_result["best_route_by_costs"]= best_route
    final_result["providers"] = providers

    optimal_locs = []
    for interLoc in optimized_route:
        locan = interLoc["address"].replace(" ","+")
        result = get_location_db(locan, "end")
        optimal_locs.append(result.location_id)
    
    best_route_str = str(optimal_locs).strip('[]')
    #print "\n\n\n\n\n best route   ", best_route_str   
    #insert the trip details into the database
    trip = TripDetails(adrs.location_id,result.location_id,best_route_str,uber_data["total_costs_by_cheapest_car_type"],uber_data["total_duration"],uber_data["total_distance"],lyft_data["total_costs_by_cheapest_car_type"],lyft_data["total_duration"],lyft_data["total_distance"])
    db.session.add(trip)
    db.session.commit()
    record = TripDetails.query.filter_by(trip_id=trip.trip_id).first_or_404()
    
    json_result = json.dumps(final_result)
    print "\n\n\n final answer : ",json_result
    return json_result

# ****************************************Get location from db function*********************************************#
def get_location_db(location, name):
    """
    Search the location in db. If found return. else get its lat and long from google and store in db.
    :param location: actual location
    :name :name of the location
    :return: the geological information of the location
    """
    ap = AddressParser()
    loc_address = ap.parse_address(location)
    street = ""
    if loc_address.house_number is not None:
                    street += loc_address.house_number
    if loc_address.street_prefix is not None:
                    street += loc_address.street_prefix
    if loc_address.street is not None:
                    street += loc_address.street
    if loc_address.street_suffix is not None:
                    street += loc_address.street_suffix
                    
    loc_city = ""
    if loc_address.city is not None:
                    loc_city = loc_address.city   
    loc_state = ""
    if loc_address.state is not None:
                    loc_state = loc_address.state
    loc_zip = ""
    if loc_address.zip is not None:
                    loc_zip = loc_address.zip
                    
    if LocationDetails.query.filter(LocationDetails.address==street,LocationDetails.city==loc_city,LocationDetails.state==loc_state,LocationDetails.zip==loc_zip).count() > 0:
        #print "\n\n\n Address found", location
        record = LocationDetails.query.filter(LocationDetails.address==street,LocationDetails.city==loc_city,LocationDetails.state==loc_state,LocationDetails.zip==loc_zip).first_or_404()
        return record
    
    #print "\n\n\n Address NOT found", location
        
    # get the geolocation of the address
    geo_location = get_lat_lng("http://maps.google.com/maps/api/geocode/json?address="+location+"&sensor=false")
    lat = geo_location["lat"]
    lng = geo_location["lng"]
    createdOn = datetime.now()
    updatedOn = datetime.now()
    
    #insert the address details into the database
    record = LocationDetails(name,street,loc_city,loc_state,loc_zip,createdOn, updatedOn, lat, lng)
    db.session.add(record)
    db.session.commit()
    
    record = LocationDetails.query.filter(LocationDetails.address==street,LocationDetails.city==loc_city,LocationDetails.state==loc_state,LocationDetails.zip==loc_zip).first_or_404()
    return record

# ****************************************CRUST API*********************************************#
# ***************************************    GET ***********************************************#

@app.route('/v1/locations/<int:location_id>', methods=['GET'])
def retrieve_record(location_id):
    """
    :param location_id: id of the location whose geological address information is needed
    :return: the geological information of the location
    """
    record = LocationDetails.query.get(location_id)
    record = LocationDetails.query.filter_by(location_id=location_id).first_or_404()
    return jsonify(result=[record.serialize])


# *****************************************  POST **********************************************#
@app.route('/v1/locations/', methods=['POST'])
def post_location():
    """
    accepts the locations form and store it to database
    :return: geological information collected using the googel api
    """
    input_json = request.get_json(force=True)
    name = request.json['name']
    address = request.json['address']
    city = request.json['city']
    state = request.json['state']
    zip = request.json['zip']
    createdOn = datetime.now()
    updatedOn = datetime.now()
    # build url to get the latitude and longitude for the address provided by the user
    url = ("http://maps.google.com/maps/api/geocode/json?address="+name+",+"+address+",+"+city+",+"+state+",+"+zip+"&sensor=false")
    req_url = url.replace(" ","+")
    # get the geolocation of the address
    geo_location = get_lat_lng(req_url)
    lat = geo_location["lat"]
    lng = geo_location["lng"]
    #insert the address details into the database
    record = LocationDetails(name,address,city,state,zip,createdOn, updatedOn, lat, lng)
    db.session.add(record)
    db.session.commit()
    record = LocationDetails.query.filter_by(name=name).first_or_404()
    #return the address details to the user in json form
    return jsonify(result=[record.serialize]), 201

#**********************************************  PUT ***********************************************#

@app.route('/v1/locations/<int:location_id>', methods = ['PUT'])
def put(location_id):
    """
    PUT API that will update the location for the particular location_id
    :param location_id:
    :return: http 202 response
    """
    input_json = request.get_json(force = True)
    name = request.json['name'] # get the updated name of the location
    record = LocationDetails.query.filter_by(location_id = location_id).first_or_404()
    record.name = name
    db.session.commit()
    return "",202

#******************************************* DELETE  ***********************************************#

@app.route('/v1/locations/<int:location_id>', methods =['DELETE'])
def delete(location_id):
    """
    DELETE API that will delete the location for the particular location_id
    :param location_id:
    :return: http 204 reponse
    """
    record = LocationDetails.query.filter_by(location_id = location_id).delete()
    #db.session.delete(session)
    db.session.commit()
    return "",204
    
#************************************Trip Planner APIs - POST**************************************#   
@app.route('/v1/trips/', methods=['POST'])
def post_trip():
    input_json = request.get_json(force=True)
    start = request.json["start"]
    end = request.json["end"]
    others = request.json["others"]

    startLoc = LocationDetails.query.filter_by(location_id=start).first_or_404()
    startLoc.address += startLoc.city
    startLoc.address += startLoc.state
    startLoc.address += startLoc.zip
    endLoc = LocationDetails.query.filter_by(location_id=end).first_or_404()
    endLoc.address += endLoc.city
    endLoc.address += endLoc.state
    endLoc.address += endLoc.zip
    
    original_locs = []
    for interLoc in others:
        geo_location = LocationDetails.query.filter_by(location_id=interLoc).first_or_404()
        lat = geo_location.lat
        lng = geo_location.lng
        adrs = geo_location.address + geo_location.city + geo_location.state + geo_location.zip
        original_locs.append({"address" : adrs, "lat": lat, "lng" : lng, "location_id" : interLoc})
        
    #get_optimum_route(original_locs, startlocation, endlocation) # get the optimized route using google api
    get_best_routeDj(original_locs, startLoc, endLoc)
    
    optimal_locs = []
    for interLoc in optimized_route:
        locan = interLoc["address"].replace(" ","+")
        result = get_location_db(locan, "end")
        optimal_locs.append(result.location_id)
    
    best_route_str = str(optimal_locs).strip('[]')
    
    lyft_data = get_Lyft_details()
    uber_data = get_Uber_details() 
    
    #insert the trip details into the database
    trip = TripDetails(start,end,best_route_str,uber_data["total_costs_by_cheapest_car_type"],uber_data["total_duration"],uber_data["total_distance"],lyft_data["total_costs_by_cheapest_car_type"],lyft_data["total_duration"],lyft_data["total_distance"])
    db.session.add(trip)
    db.session.commit()
    record = TripDetails.query.filter_by(trip_id=trip.trip_id).first_or_404()
    #return the trip details to the user in json form
    return jsonify(result=[record.serialize]), 201

@app.route('/reviews', methods=['POST'])
def post_review():
    print "\n post_review : got request"
    trip_id = request.form['trip_id']
    rating = request.form["rating"]
    review = request.form["review"]
    print "\n post_review : ",trip_id, rating, review
    #insert the trip review into the database
    tripReview = TripReviews(trip_id,rating,review)
    rs = db.session.add(tripReview)
    db.session.flush()
    rs = db.session.commit()
    record = TripReviews.query.filter_by(review_id=tripReview.review_id).first_or_404()
    trip = TripDetails.query.filter_by(trip_id=record.trip_id).first_or_404()
    start = LocationDetails.query.filter_by(location_id=trip.start_location).first_or_404()
    end = LocationDetails.query.filter_by(location_id=trip.end_location).first_or_404()
    data = {
    "review_id":tripReview.review_id,
    "trip_id": record.trip_id,
    "start":start.address.replace("+"," "),
    "end":end.address.replace("+"," "),
    "rating":record.rating,
    "review":record.review}
    return render_template('reviewPosted.html', record=data)
    #return the review details to the user in json form
    
    
@app.route('/reviewsJson/', methods=['POST'])
def post_review_json():
    print "got request"
    input_json = request.get_json(force=True)
    trip_id = request.json["trip_id"]
    rating = request.json["rating"]
    review = request.json["review"]
  
    #insert the trip review into the database
    tripReview = TripReviews(trip_id,rating,review)
    rs = db.session.add(tripReview)
    db.session.flush()
    rs = db.session.commit()
    record = TripReviews.query.filter_by(review_id=tripReview.review_id).first_or_404()
    return jsonify(result=[record.serialize]), 201
    
    
@app.route('/bestreviewsjson/', methods=['GET'])
def get_best_reviews_json():
    record = TripReviews.query.filter_by(rating=5)
    return jsonify(json_list=[i.serialize for i in record.all()])

@app.route('/bestreviews/', methods=['GET'])
def get_best_reviews():
    records = TripReviews.query.filter_by(rating=5)
    trips = []
    for record in records:
        trip = TripDetails.query.filter_by(trip_id=record.trip_id).first_or_404()
        start = LocationDetails.query.filter_by(location_id=trip.start_location).first_or_404()
        print "\n id = ", start.location_id
        end = LocationDetails.query.filter_by(location_id=trip.end_location).first_or_404()
        data = {
        "trip_id": record.trip_id,
        "start":start.address.replace("+"," "),
        "end":end.address.replace("+"," "),
        "rating":record.rating,
        "review":record.review}
        trips.append(data)
    return render_template('bestReviews.html', records=trips)
    
@app.route('/postreviews')
def postreviews():
    return render_template('reviews.html')

#************************************Combination Route**************************************#
@app.route('/waiting')
def waiting():
    """
    returns the index page which consists a form for locations input
    :return: index page
    """
    return render_template('combinationUI.html')
    
@app.route('/combinationPrice',methods = ['POST'])
def getCombinationPrice():
    """
    returns the optimum route solution for the input locations based on cost provided by Lyft and Uber
    :return: json_result
    """
    global start_point
    global end_point
    global no_inter_points

    #startlocation = request.json["startlocation"] # starting point of the travel
    startlocation = request.form['start'] # starting point of the travel
    location = startlocation.replace(" ","+")
    adrs = get_location_db(location, "start")
    print "\n\n\n Start point :  ", adrs.lat, adrs.lng
    start_point["lat"] = adrs.lat
    start_point["lng"] = adrs.lng
    start_point["address"]= startlocation
    
    endlocation = request.form['end'] # end point of the travel
    location = endlocation.replace(" ", "+")
    result = get_location_db(location, "end")
    end_point["address"] = endlocation
    end_point["lat"] = result.lat
    end_point["lng"] = result.lng
    print "\n End point : ", end_point
    
   
    #original_list = request.json["intermidiatelocation"] # list containing the intermediate locations
    original_list = []
    original_list.append(request.form['inter1'])
    original_list.append(request.form['inter2'])
    print "intermidiatelocation \n", original_list

    no_inter_points = len(original_list)
    print "\n\n no_inter_points = ", no_inter_points
    if no_inter_points>0 :
        intermediate_address_lat_lng = get_details(original_list) # get the latitude and longitude of the intermediate locations
        bestRt = get_best_price(intermediate_address_lat_lng, start_point, end_point)
        print "\n\n optimized_route2 = ", bestRt
        for i in bestRt:
            i["end"].pop('location_id', None)
            i["start"].pop('location_id', None)
        json_result = json.dumps(bestRt)
        print "\n\n\n final answer : ",json_result
        #return json_result
        return render_template('combinationResp.html', result=bestRt)
    else:
        emptyLocs = []
        bestRt = get_best_price(emptyLocs, start_point, end_point)
        print "\n\n optimized_route1 = ", bestRt
        bestRt[0]["end"].pop('location_id', None)
        bestRt[0]["start"].pop('location_id', None)
        json_result = json.dumps(bestRt)
        print "\n\n\n final answer1 : ",json_result
        print "\n\n getCombinationPrice ended"
        #return json_result
        return render_template('combinationResp.html', result=bestRt)

@app.route('/combinationPriceJson',methods = ['POST'])
def getCombinationPriceJson():
    """
    returns the optimum route solution for the input locations based on cost provided by Lyft and Uber
    :return: json_result
    """
    global start_point
    global end_point
    global no_inter_points

    startlocation = request.json["startlocation"] # starting point of the travel
    location = startlocation.replace(" ","+")
    adrs = get_location_db(location, "start")
    #print "\n\n\n new func    ", adrs.lat, adrs.lng
    start_point["lat"] = adrs.lat
    start_point["lng"] = adrs.lng
    start_point["address"]= startlocation
    
    endlocation = request.json["endlocation"] # end point of the travel
    location = endlocation.replace(" ", "+")
    result = get_location_db(location, "end")
    end_point["address"] = endlocation
    end_point["lat"] = result.lat
    end_point["lng"] = result.lng
    #print "\n End point \n", end_point
    
    dist = get_distance(start_point,end_point)   
    original_list = request.json["intermidiatelocation"] # list containing the intermediate locations
    
    no_inter_points = len(original_list)
    if no_inter_points>0 :
        intermediate_address_lat_lng = get_details(original_list) # get the latitude and longitude of the intermediate locations
        bestRt = get_best_price(intermediate_address_lat_lng, start_point, end_point)
        print "\n\n optimized_route2 = ", bestRt
        for i in bestRt:
            i["end"].pop('location_id', None)
            i["start"].pop('location_id', None)
        json_result = json.dumps(bestRt)
        print "\n\n\n final answer : ",json_result
        return json_result
       
    else:
        emptyLocs = []
        bestRt = get_best_price(emptyLocs, start_point, end_point)
        print "\n\n optimized_route1 = ", bestRt
        bestRt[0]["end"].pop('location_id', None)
        bestRt[0]["start"].pop('location_id', None)
        json_result = json.dumps(bestRt)
        print "\n\n\n final answer1 : ",json_result
        return json_result
        
        
def get_price_2dest(start_point, end_point):
    print "\n get_price_2dest 1"
    lat1 = start_point["lat"]
    lng1 = start_point["lng"]
    lat2 = end_point["lat"]
    lng2 = end_point["lng"]
    lyft_data = LyftApi.getLyftCost(lat1,lng1,lat2,lng2)
    uber_data = UberApi.getUberCost(lat1,lng1,lat2,lng2)
    if lyft_data["costs_by_cheapest_car_type"] < uber_data["costs_by_cheapest_car_type"]:
        part = {"start": start_point,
                "end": end_point,
                "service_provider": "Lyft",
                "car_type": lyft_data["car_type"] ,
                "costs_by_cheapest_car_type": lyft_data["costs_by_cheapest_car_type"],
                "duration": lyft_data["duration"],
                  "distance": lyft_data["distance"]}
    else:
        part = {"start": start_point,
                "end": end_point,
                "service_provider": "Uber",
                "car_type": uber_data["car_type"] ,
                "costs_by_cheapest_car_type": uber_data["costs_by_cheapest_car_type"],
                "duration": uber_data["duration"],
                  "distance": uber_data["distance"]}
    return part


def get_best_price(locations_list,origin_address, destination_address):
    print "\n\n\n get_best_price 1"
    optimized_price_route = []
    interLocsLen = len(locations_list)
    if interLocsLen == 0:
        print "\n get_best_price : No intermediate"
        part1 = get_price_2dest(origin_address, destination_address)
        optimized_price_route.append(part1)
        return optimized_price_route
    if interLocsLen == 1:
        print "\n get_best_price : Only 1 intermediate"
        part1 = get_price_2dest(origin_address, locations_list[0])
        part2 = get_price_2dest(locations_list[0], destination_address)
        optimized_price_route.append(part1)
        optimized_price_route.append(part2)
        return optimized_price_route
        
    print "\n\n\n get_best_price 2"
    
    priceMatrix =  [[99999 for _ in range(interLocsLen)] for _ in range(interLocsLen)]
    
    priceFrmStart = []   
    indx = 0
    while indx < interLocsLen:
        priceFrmStart.append(get_price_2dest(origin_address, locations_list[indx]))
        indx = indx + 1   
    print "\n\n\n get_best_price : priceFrmStart : ", priceFrmStart
    
    priceToEnd = []
    indx = 0
    while indx < interLocsLen:
        priceToEnd.append(get_price_2dest(locations_list[indx], destination_address))
        indx = indx + 1
    print "\n\n\n get_best_price : priceToEnd : ", priceToEnd
    
    index1 = 0    
    index2 = 0
    while index1 < interLocsLen:
        while index2 < interLocsLen:
            #print " intered with ", index1, index2
            if index1 == index2:
                priceMatrix[index1][index2] = 99999
            else:
                dst = get_price_2dest(locations_list[index1], locations_list[index2])
                #print "\n Cost1 is ", dst
                priceMatrix[index1][index2] = dst
            index2 = index2 + 1
        index1= index1 + 1
        index2 = 0
        
    paths = []
    locs = []
    minCost = 99999
    for indx in range(0, interLocsLen):
        locs.append(indx)
    for L in range(0, interLocsLen+1):
        for subset in itertools.permutations(locs, L):
            if len(subset) == interLocsLen:
                print "\n Full path found : ", subset                
                curCost = 0
                curRt = []
                curRt.append(priceFrmStart[subset[0]])
                for i in range(0,interLocsLen-1):
                    srcIndx = subset[i]
                    destIndx = subset[i+1]
                    bestPriceRt = priceMatrix[srcIndx][destIndx]
                    print "\n Cost is ", srcIndx, destIndx, bestPriceRt["costs_by_cheapest_car_type"]
                    curCost = curCost + bestPriceRt["costs_by_cheapest_car_type"]
                    curRt.append(bestPriceRt)

                curRt.append(priceToEnd[subset[interLocsLen-1]])
                bestStartRt = priceFrmStart[subset[0]]
                bestEndRt = priceToEnd[subset[interLocsLen-1]]                
                curCost = curCost + bestPriceRt["costs_by_cheapest_car_type"]
                curCost = curCost + bestEndRt["costs_by_cheapest_car_type"]                
                print "\n Path and Cost are = ", subset, curCost
                if curCost < minCost:
                    print "\n found minimum cost adding", subset, len(paths)
                    minCost =  curCost
                    paths.append(curRt)
    print "\n\n Minimum cost is ", minCost
    bestPth = paths[len(paths)-1]
    print "\n Best path is ", bestPth
    return bestPth    

#************************************run the main program**************************************#

if __name__ == "__main__" :
    db.create_all()
    event.listen(LocationDetails.__table__,"after_create",DDL("ALTER TABLE %(table)s AUTO_INCREMENT = 1001;"))
    app.run( host='0.0.0.0',port = 5000, debug = True) # run app in debug mode

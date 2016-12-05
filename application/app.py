# coding=utf-8
import urllib2

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
    name = db.Column('name', db.String(50))
    address = db.Column('address', db.String(250))
    city = db.Column('city', db.String(30))
    state = db.Column('state', db.String(30))
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


def get_optimum_route(locations_list,origin_address, destination_address):
    """
    obtain the ordered list of the optimum route for the intermediate locations using google api
    :param locations_list: list of intermediate locations
    :param origin_address: starting point address of travel
    :param destination_address: end point address of travel
    :return: update the global list optimized_route containing dictionary of
            intermediate location's address, lattitude and longitude organized in optimum way
    """

    # building the url for getting optimum path
    origin = origin_address.replace(" ","+")
    destination = destination_address.replace(" ","+")
    addresses = ""
    for L in locations_list :
        addresses = addresses + "|"+ L["address"].replace(" ","+")
    url = "https://maps.googleapis.com/maps/api/directions/json?origin="+origin+"&destination="+destination+"&waypoints=optimize:true"+ addresses+"&key=AIzaSyBq3bKwekCVVP7k_K2788yvA1NwUMwM3ms"
    response = urllib2.urlopen(url)  # call the google api using url provided
    json_response = response.read()
    jsonList = json.loads(json_response)

    # google returns the optimized route depending upon the distance
    waypoint_order = jsonList["routes"][0]["waypoint_order"]

    global optimized_route
    for index in waypoint_order :
        optimized_route.append(locations_list[index])
    return

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


@app.route('/')
def index():
    """
    returns the index page which consists a form for locations input
    :return: index page
    """
    return render_template('index.html')

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
        get_best_route(intermediate_address_lat_lng, start_point, end_point)
        print "\n\n optimized_route = ", optimized_route
        
    lyft_data = get_Lyft_details() # get the cost, duration and distance for entire trip with lyft
    providers.append(lyft_data)  # append the result to the list of service providers


    uber_data = get_Uber_details() # get the cost, duration and distance for entire trip with uber
    providers.append(uber_data) # append the result to the list of service providers
    best_route = []
    if no_inter_points>0 :
        for L in optimized_route:
            best_route.append(L["address"])

    # construct the final response
    final_result["start"] = start_point["address"]
    final_result["end"] = end_point["address"]
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
        
    get_optimum_route(original_locs, startlocation, endlocation) # get the optimized route using google api
          
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

#************************************run the main program**************************************#

if __name__ == "__main__" :
    db.create_all()
    event.listen(LocationDetails.__table__,"after_create",DDL("ALTER TABLE %(table)s AUTO_INCREMENT = 1001;"))
    app.run( host='0.0.0.0',port = 5000, debug = True) # run app in debug mode

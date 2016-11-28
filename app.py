# coding=utf-8
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

app = Flask(__name__) #define app using Flask


#************************************  database config information    ********************************#
#app.config['SQLALCHEMY_DATABASE_URI']  = 'mysql+pymysql://root:hina@mysqlserver:3306/expensedb'
app.config['SQLALCHEMY_DATABASE_URI']  = 'mysql+pymysql://hina:hina@127.0.0.1:3306/address'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

#**********************************   database model  ************************************************#
db = SQLAlchemy(app)

class LocationDetails(db.Model):
    __tablename__ = 'LocationDetails'
    location_id = db.Column('location_id', db.Integer, primary_key=True)
    name = db.Column('name', db.String(50))
    address = db.Column('address', db.String(50))
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
start_point = {}
end_point = {}
optimized_route =[]
Locations = {"start":start_point, "end": end_point, "intermediate_locations" : optimized_route}
final_result = {}
providers = []
provider =  {
            "name" : "",
            "total_costs_by_cheapest_car_type" : 0,
            "currency_code": "USD",
            "total_duration" : 0,
            "duration_unit": "minute",
            "total_distance" : 0,
            "distance_unit": "mile"}


# obtain the geological latitude and longitude using google api
def get_lat_lng(req_url):
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


# get the latitude and longitude of the intermedate locations without optimum routes
def get_details(List):
    original_location_order = []
    for i in List:
        location = i.replace(" ","+")
        request_url = ("http://maps.google.com/maps/api/geocode/json?address="+location+"&sensor=false")
        geo_location = get_lat_lng(request_url)
        lat = geo_location["lat"]
        lng = geo_location["lng"]
        original_location_order.append({"address" : i, "lat": lat, "lng" : lng})

    return original_location_order


# obtain the ordered list of the optimum route for the intermediate locations using google api
def get_optimum_route(locations_list,origin_address, destination_address):

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

def get_Lyft_details():
    global provider
    global providers
    provider["name"] = "Lyft"
    cost = 0;

    for i in optimized_route:

    return

def get_Uber_details():
    return
#***************************************code for user interface*************************************#


@app.route('/')
def index():
    # return the index page which consists a form for locations input
   return render_template('index.html')

@app.route('/result',methods = ['POST'])
def getPrice():
    global start_point
    global end_point
    input_json = request.get_json(force=True)

    startlocation = request.json["startlocation"] # starting point of the travel
    location = startlocation.replace(" ","+")
    result = get_lat_lng("http://maps.google.com/maps/api/geocode/json?address="+location+"&sensor=false")
    start_point["address"]= startlocation
    start_point["lat"] = result["lat"]
    start_point["lng"] = result["lng"]
    print (start_point)

    endlocation = request.json["endlocation"] # end point of the travel
    location = endlocation.replace(" ", "+")
    result = get_lat_lng("http://maps.google.com/maps/api/geocode/json?address=" + location + "&sensor=false")
    end_point["address"] = endlocation
    end_point["lat"] = result["lat"]
    end_point["lng"] = result["lng"]
    print(end_point)

    original_list = request.json["intermidiatelocation"] # list containing the intermediate locations
    print (original_list)

    intermediate_address_lat_lng = get_details(original_list) # get the latitude and longitude of the intermediate locations
    print(intermediate_address_lat_lng)

    get_optimum_route(intermediate_address_lat_lng, startlocation, endlocation) # get the optimized route
    print (optimized_route)

    get_Lyft_details()
    get_Uber_details()
    return "success"




# ****************************************CRUST API*********************************************#
# ***************************************    GET ***********************************************#

@app.route('/v1/locations/<int:location_id>', methods=['GET'])
def retrieve_record(location_id):
    record = LocationDetails.query.get(location_id)
    record = LocationDetails.query.filter_by(location_id=location_id).first_or_404()
    return jsonify(result=[record.serialize])


# *****************************************  POST **********************************************#
@app.route('/v1/locations/', methods=['POST'])
def post_location():
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
#         PUT API that will update the location for the particular location_id
@app.route('/v1/locations/<int:location_id>', methods = ['PUT'])
def put(location_id):
	input_json = request.get_json(force = True)
	name = request.json['name']
	record = LocationDetails.query.filter_by(location_id = location_id).first_or_404()
	record.name = name
	db.session.commit()
	return "",202

#******************************************* DELETE  ***********************************************#
#       DELETE API that will delete the location for the particular location_id

@app.route('/v1/locations/<int:location_id>', methods =['DELETE'])
def delete(location_id):
    record = LocationDetails.query.filter_by(location_id = location_id).delete()
    #db.session.delete(session)
    db.session.commit()
    return "",204


#************************************run the main program**************************************#

if __name__ == "__main__" :
    db.create_all()
    event.listen(LocationDetails.__table__,"after_create",DDL("ALTER TABLE %(table)s AUTO_INCREMENT = 1001;"))
    app.run( host='0.0.0.0',port = 5000, debug = True) # run app in debug mode
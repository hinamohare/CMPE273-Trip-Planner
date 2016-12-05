from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import *
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
 
# Database Configurations
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']  = 'mysql+pymysql://root:root@127.0.0.1:3306/address'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)

class TripDetails(db.Model):
    __tablename__ = 'TripDetails'
    trip_id = db.Column('trip_id', db.Integer, primary_key=True)
    start_location = db.Column('start_location', db.Integer)
    end_location = db.Column('end_location', db.Integer)
    best_route = db.Column('best_route', db.String(250))
    uber_cost = db.Column('uber_cost', db.Float)
    uber_duration = db.Column('uber_duration', db.Float)
    uber_distance = db.Column('uber_distance', db.Float)
    lyft_cost = db.Column('lyft_cost', db.Float)
    lyft_duration = db.Column('lyft_duration', db.Float)
    lyft_distance = db.Column('lyft_distance', db.Float)
    
    def __init__(self, start_location, end_location, best_route, uber_cost, uber_duration, uber_distance, lyft_cost, lyft_duration, lyft_distance):
        self.start_location = start_location
        self.end_location = end_location
        self.best_route = best_route
        self.uber_cost = uber_cost
        self.uber_duration = uber_duration
        self.uber_distance = uber_distance
        self.lyft_cost = lyft_cost
        self.lyft_duration = lyft_duration
        self.lyft_distance = lyft_distance
        
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.trip_id,
            'start': self.start_location,
            'end': self.end_location,
            'best_route_by_costs': self.best_route,
            'providers': [{'name' : 'Uber', 'total_costs_by_cheapest_car_type' : self.uber_cost, 'currency_code': 'USD',
            'total_duration' : self.uber_duration, 'duration_unit': 'minute',
            'total_distance' : self.uber_distance, 'distance_unit': 'mile'},{'name' : 'Lyft', 'total_costs_by_cheapest_car_type' : self.lyft_cost, 'currency_code': 'USD',
            'total_duration' : self.lyft_duration, 'duration_unit': 'minute',
            'total_distance' : self.lyft_distance, 'distance_unit': 'mile'}]
        }
        
class TripReviews(db.Model):
    __tablename__ = 'Tripreviews'
    review_id = db.Column('review_id', db.Integer, primary_key=True)
    trip_id = db.Column('trip_id', db.Integer)
    rating = db.Column('rating', db.Integer)
    review = db.Column('review', db.String(250))

    def __init__(self, tripId, rating, review):
        self.trip_id = tripId
        self.rating = rating
        self.review = review
        
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'review_id':self.review_id,
            'trip_id': self.trip_id,
            'rating': self.rating,
            'review': self.review
        }
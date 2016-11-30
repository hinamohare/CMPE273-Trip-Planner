import json
import requests
#***************************** uber authorization and cost api*******************************#
class UberApi:
    def __init__(self):
        pass

    @staticmethod
    def getUberCost(start_lat, start_lng, end_lat, end_lng):
        """
                :param start_lat: latitude of the starting point (string)
                :param start_lng: longitude of the  staring point (string)
                :param end_lat: latitude of the end point (string)
                :param end_lng: latitude of the end point (string)
                :return: {name : "Uber", ride type : "UberX", "costs_by_cheapest_car_type": ride_cost (USD),
                                  "duration": ride_time (minute),
                                  "distance": ride_distance(miles)}
                """
        url = "https://api.uber.com/v1.2/estimates/price?start_latitude="+str(start_lat)+"&start_longitude="+str(start_lng)+"&end_latitude="+str(end_lat)+"&end_longitude="+str(end_lng)
        header = {'Authorization': "Token 4p4BDMuysqRv1n1RLDryBeMXxGk27HLL2wEuliPf"}
        response = requests.get(url, headers= header)
        data = response.content
        json_data = json.loads(data)
        ride_data = json_data["prices"][1]
        ride_type = ride_data["localized_display_name"]  # ride type
        ride_time = ride_data["duration"] / 60  # time in minutes
        ride_cost = ride_data["high_estimate"]   # max cost in USD
        ride_distance = ride_data["distance"]  # distance in mile
        Uber_cost_info = {"service_provider": "Uber",
                                  "car_type": ride_type,
                                  "costs_by_cheapest_car_type": ride_cost,
                                  "duration": ride_time,
                                  "distance": ride_distance}


        return Uber_cost_info


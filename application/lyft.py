import json
import requests

#***************************** lyft authorization and cost api*******************************#
class LyftApi:
    def __init__(self):
        pass

    @staticmethod
    def getAccessToken():
        #get Lyft access token for using lyft api
        client_secrete = "WRU95RMFGN9kRV9VOIXhzBEaBcqwTzHV"
        client_Id = "9M08-8z29d9G"
        url = "https://api.lyft.com/oauth/token"
        payload = {"grant_type": "client_credentials", "scope": "public"}
        data = json.dumps(payload)

        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, data=data, auth=(client_Id, client_secrete), headers=headers)
        response = resp.content
        response_json = json.loads(response)
        access_token = response_json["access_token"]
        return access_token

    @staticmethod
    def getLyftCost(start_lat, start_lng, end_lat, end_lng):
        """
        This function calculates the different ride parameters for the travel
        :param start_lat: latitude of the starting point (string)
        :param start_lng: longitude of the  staring point (string)
        :param end_lat: latitude of the end point (string)
        :param end_lng: latitude of the end point (string)
        :return: {name : "Lyft", ride type : "Lyft_line", "costs_by_cheapest_car_type": ride_cost (USD),
                          "duration": ride_time (minute),
                          "distance": ride_distance(miles)}
        """

        lyft_cost_url = "https://api.lyft.com/v1/cost?start_lat=" + str(start_lat) + "&start_lng=" + str(start_lng) + "&end_lat=" + str(end_lat) + "&end_lng=" + str(end_lng)
        access_token = LyftApi.getAccessToken()
        mytoken = "bearer " + access_token
        cost_resp = requests.get(lyft_cost_url, headers={'Authorization': mytoken})
        cost_data = cost_resp.content
        cost_json = json.loads(cost_data)
        if "cost_estimates" in cost_json:
            indx = len(cost_json["cost_estimates"])
            ride_data = cost_json["cost_estimates"][indx-1]  # cheapest ride among Lyft, Lyft Plus and Lyft Line is Lyft
            ride_type = ride_data["ride_type"]  # ride type
            ride_time = ride_data["estimated_duration_seconds"] / 60  # time in minutes
            ride_cost = ride_data["estimated_cost_cents_max"] / 100  # max cost in USD
            ride_distance = ride_data["estimated_distance_miles"]  # distance in mile
        else:
            ride_type = "Not available"
            ride_cost = 9998
            ride_time = 0
            ride_distance = 0

        lyft_cost_info = {"service_provider": "Lyft",
                          "car_type": ride_type,
                          "costs_by_cheapest_car_type": ride_cost,
                          "duration": ride_time,
                          "distance": ride_distance}
                              
        return lyft_cost_info
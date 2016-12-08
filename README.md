# CMPE273-Trip-Planner
Team - WildCraft
Team members -
Harshada Bhide-Apte
Heena Mohare
Natasha Dsouza
veereshkamble

Trip Planner - This application shows the best distance path and best cost path for given locations alongwith cooresponding Uber and Lyft estimates.

Algorithms(deviation of dijkstra) - We have implemented our own algorithms for calculating shortest distance path and shortest cost path. Both the algorithms are slight deviations of the dijkstra algorithm modified to cover all the intermediate points. We calculate a matrix for all the locatons and evalutate all the permutations possible.

def get_best_routeDj() - This function calculates the best route with minimumdistance to be travelled. Then Lyft and Uber costs are estimated for the entire route. This algorithm assumes user will use only one service (either Lyft or Uber) for the entire journey.
Node = Location
Weight = distance(node1, node2)

get_best_price() - This function calculates the cost for Uber and Lyft between every 2 locations and considers the least of the two. It then evaluates all the possible permutations to get the least expensive route-service combination.
Node = Location
Weight = Minimum(UberCost(node1, node2), LyftCost(node1, node2))

Database -  When a particular location is entered by the user for the first time, its latitude and longitude are retrived using Google API. Then that information is stored in the app db. Each time user enters a location, its co-ordinates are first checked in app db, if not found then only retrived using API. The application also stores the generated trip routes and reviews posted by users.

APIs used - Google API is used for getting latitude and longitude of the location. Lyft and Uber APIs are used to get corresponding cost estimates.

Home screen (minimum distance) - http://localhost:5000/result
On this screen user can enter Starting location, end location and intermediate locations. The UI has the restriction to enter only 5 intermediate locations but server can actually handle 'n' number of intermediate locations. The application displays the best route with minimum distance and the estimated costs for Uber and Lyft for that route. It has links which take to Uber and Lyft websites to make bookings.

Least cost screen - http://localhost:5000/waiting
If user has waiting time of more than 15 minutes then they can use different services between locations. On the waiting screen user can enter starting location, end location and 2 intermediate locations. The application provides a combination of services (Lyft, Uber) to travel from one location to another. The UI can accept only 2 intermediate locations but the server can actually process 'n' number of intermediate locations.

Best Reviews screen - http://localhost:5000/bestreviews/
This screen provides the list of all the routes generated on this application for which the user gave "5" rating.

Post Review screen - http://localhost:5000/postreviews
On this screen user can enter the trip id and post rating (1-5 stars) and review for that trip.

Steps to run the code:
- Start the database:
    - Create database with name "address"
    - Change UID and Password for your db at app.py (line 23)
    - Change UID and Password for your db at model.py (line 11)
- Start the Server: 
    - Run app.py file on your preferred IDE/ Command Prompt
- Start Client:
    -  On your browser "http://localhost:5000/"

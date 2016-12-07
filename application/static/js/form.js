$(document).ready(function(){
        // click on button submit
        $("#submit").on('click', function(){
			
			var inputdata = getpayloaddata();
			
			//console.log(inputdata);
            $.ajax({
                url: '/result', // url where to submit the request
                type : "post", // type of action post || get
				contentType:'application/json',
                datatype : 'json', // data type
                data : inputdata, // post data || get data
                success : function(result) {
                console.log()
                var obj = JSON.parse(result);
                //alert(obj.start)

                console.log("Start point is "+obj.start)
                //document.getElementById('result').innerHTML = result;
              var tbl=$("<table/>").attr("id","mytable");

             // var result2 = $("<div/>").attr("id","heading");
              var st="<h3>"+obj.start+"</h3>";
              var en="<h3>"+obj.end+"</h3>";
              var addLs="<h3>"+obj.best_route_by_costs+"</h3>";

                $("#heading").append(st+en);
                $("#addL").append(addLs);
                $("#results").append(tbl);

                    for(var i=0;i<obj.providers.length;i++)
                        {
                             var tr="<tr>";
                              var td1="<td>"+obj.providers[i]["car_type"]+"</td>";
                              var td2="<td>"+obj.providers[i]["name"]+"</td>";
                              var td3="<td>"+obj.providers[i]["total_distance"]+"</td>";
                              var td4="<td>"+obj.providers[i]["total_duration"]+"</td>";
                              var td5="<td>"+obj.providers[i]["duration_unit"]+"</td>";
                              var td6="<td>"+obj.providers[i]["distance_unit"]+"</td>";
                              var td7="<td>"+obj.providers[i]["total_costs_by_cheapest_car_type"]+"</td>";
                              var td8="<td>"+obj.providers[i]["currency_code"]+"</td></tr>";

                            $("#mytable").append(tr+td1+td2+td3+td4+td5+td6+td7+td8);

                        }
                    // you can see the result from the console
                    // tab of the developer tools
                  //  console.log(result);
                },
                error: function(xhr, resp, text) {
                    console.log(xhr, resp, text);
                }
            })
        });
		
		
		function getpayloaddata()
		{
			var startPoint = $('#start').val();
			var endPoint = $('#end').val();
			
			var locObject = new Object();
			locObject.startlocation = startPoint;
			locObject.endlocation = endPoint;
			
			var arrOfIntermediateLoc = [];
			var interLoc = $('.otherlocation');
			if(interLoc)
			{
				$.each(interLoc,function(index, value){
					
					var loc = $(value).val()
					arrOfIntermediateLoc.push(loc);
				});
				locObject.intermidiatelocation = arrOfIntermediateLoc;
			}
			var jsonstring = JSON.stringify(locObject);
			return jsonstring;
			
		}
		
		function getOtherLocation(){
			
			var formdata = document.getElementById('form');
			var start = formdata.getElementById('start').value;
			var end = formdata.getElementById('end').value;
			var otherlocations = formdata.getElementByClassName('otherlocation');
			var others = [];
			var locations = {};
			for(var i=0; i < otherlocation.length; i++){
				others.push(otherlocation[i].value); 
			}
			locations["start"] = start;
			locations["end"] = end;
			locations["others"] = others;
			return locations
			
		}
    });

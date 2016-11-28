$(document).ready(function(){
        // click on button submit
        $("#submit").on('click', function(){
			
			var inputdata = getpayloaddata();
			
			console.log(inputdata);
            $.ajax({
                url: '/result', // url where to submit the request
                type : "post", // type of action post || get
				contentType:'application/json',
                datatype : 'json', // data type
                data : inputdata, // post data || get data
                success : function(result) {
                    // you can see the result from the console
                    // tab of the developer tools
                    console.log(result);
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
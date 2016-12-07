$( document ).ajaxStart(function() {
  //$( "#loading" ).show();
});
$(document).ready(function(){
        var dialog = $( "#modal" ).dialog({
        autoOpen: false,
        height: 50,
        width: 100,
        modal: true
        });

                $("#frmAddress").validate();
        // click on button submit
        $("#submit").on('click', function(){

        if ($('#frmAddress').valid()) {
        } else {
            //alert("form is invalid");
            return false;
        }
			var inputdata = getpayloaddata();

            $.ajax({
                url: '/result', // url where to submit the request
                type : "post", // type of action post || get
				contentType:'application/json',
                datatype : 'json', // data type
                data : inputdata, // post data || get data

                beforeSend:function(){

                    $("#modal").parent().find(".ui-dialog-titlebar").hide();
                    dialog.dialog( "open" );},

                success : function(result) {


					showoutput(result);
                },
                error: function(xhr, resp, text) {
                    console.log(xhr, resp, text);
                },
                complete:function()
                {
                    dialog.dialog( "close" );

                }
            })
        });
		$('#btnAddMoreAddress').on('click',function(){
			
			 if (counter == limit)  {

              alert("You have reached the limit of adding " + counter + " Location");

         }

         else {
			var divName ='';
			var txtId = 'loc' + counter;
			var trId = 'trloc' + counter;
              var newtr = "<tr id='" +trId+"'><td>Location " + (counter) + " </td>:<td><input required type='text' class = 'otherlocation' id = '"+txtId+"' size='50' name='others' placeholder='Enter location' autocomplete='off'><span class='remloc'>[ Remove ]</span></td></tr>";
              $('#tblAddress tr:last').after(newtr);
			  var loc = document.getElementById(txtId);
			  var locautoComplete = new google.maps.places.Autocomplete(loc);

              counter++;
		 }
             $('.remloc').on('click', function(){

            var self = this;
            $(self).parent().parent('tr').remove();
            });
		});
		
		function showoutput(result)
		{
		var objOutput = $.parseJSON(result);
		var startdata = objOutput.start;
		var enddata =objOutput.end;
		var providerdata = objOutput.providers;
		if(providerdata && providerdata.length >0)
        {
            for(var idx=0;idx<providerdata.length;idx++)
            {
                setprovidermetrics(providerdata[idx]);
            }
        }
		var bestroutedata =objOutput.best_route_by_costs;


		var itemhtml ='';
           itemhtml += '<li  class="startaddress">'+startdata.address+'  ↓  </li>';
        if(bestroutedata && bestroutedata.length >0)
        {

        for(var idx=0;idx<bestroutedata.length;idx++)
        {
        var itemaddress = bestroutedata[idx].address;
         itemhtml+='<li>'+itemaddress +'  ↓  </li>'
        console.log(itemaddress);}
        }

        itemhtml += '<li  class="endaddress">'+enddata.address+'</li>'

        $('#addresslist').empty();
        $('#addresslist').append(itemhtml);


		}
		function setprovidermetrics(data)
		{
		    var provider = data.name;
		    var containerid = '';
		    if(provider ==='Lyft')
		    {
		    containerid ="#lyftresultcontainer";
		    }

		    if(provider ==='Uber')
		    {
		    containerid ="#uberresultcontainer";
		    }

            var pricedata = data.total_costs_by_cheapest_car_type +' '+data.currency_code;
            $($(containerid + ' .price')[0]).text(pricedata);
             var timedata = Math.round(data.total_duration * 100) / 100 +' '+ data.distance_unit;
            $($(containerid +' .time')[0]).text(timedata);
            var distancedata =  Math.round( data.total_distance* 100) / 100+' '+data.distance_unit;
            $($(containerid +' .distance')[0]).text(distancedata);

            $($(containerid + ' .ridetype')[0]).text(data.car_type);


		}
		$('#btnClear').on('click',function(){
			$('#addresslist').empty();
			
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
	
	function addInput(divName){

         if (counter == limit)  {

              alert("You have reached the limit of adding " + counter + " Location");

         }

         else {

              var newdiv = document.createElement('div');
			  var txtId = 'loc' + counter
              newdiv.innerHTML = "<b>Location " + (counter) + " :<b> <input type='text' class = 'otherlocation' id = '"+txtId+"' size='50' name='others' placeholder='Enter location' autocomplete='off'><br><Br>";
              document.getElementById(divName).appendChild(newdiv);
			  var loc = document.getElementById(txtId);
			  var locautoComplete = new google.maps.places.Autocomplete(loc);

              counter++;

         }

    }
	
	
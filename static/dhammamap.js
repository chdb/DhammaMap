;(function() {
/*jshint laxcomma:true */
"use strict";
	var $form = $('#formdiv form');
	if ($form.length>0) // if  $('#form form') element exists, IE there's a <form> element in the DOM with a parent with id='form'
	{	
		var xhr;
		var $flashes = $('#flashes');
		var $formdiv = $('#formdiv');		// put "formdiv" as the id on the div that will be blocked, and which contains the form.
		var beforeFn = function() 
			{ //console.log('before');
				//$flashes.empty();
				$formdiv.block ({ message: '<img src="../static/snakes-chasing.gif">' 
												, css	   :  { width  :'6%'				
																		, padding:'4px 0 0 0' 
																	  , border :'0'/*
																	  , backgroundColor: '#FFDDFF'
																	 , cursor:'wait'
																	 }						
												, overlayCSS:{ backgroundColor: '#FFFFFF'
																		 , opacity		  : 0.0
																		 , cursor		  : 'wait'*/ 
																		 }  						
												});  
				if ($flashes.children().length) 
					$flashes.slideUp (1000); 
			};
		var showMsgs = function (resp)
			{ //$flashes.empty();
				$formdiv.unblock();
				if (resp.msgs)
				{ $flashes.html (resp.msgs);
					//console.log('flashes: ' + $flashes.html());
					$flashes.slideDown (1000);
				}
				
			};
		var successFn = function (resp)
			{
				if (resp.mode === 'good')
					window.location = 'secure';
				else if (resp.mode === 'wait')
				{	console.log('wait and try again');
					setTimeout	( function(){ ajaxCall(); //try again
																	}
											, resp.delay
											);
				}
				else	showMsgs(resp); 
			  //window.console.log('done waiting');
			
				/*
				switch (resp.mode)
				{	case 'good' 	:		window.location = 'secure';
						break;
					case 'wait' :		
						break;
					case 'locked' :		wait(resp);
						break;
					case 'lock' :		wait(resp);
						break;
					case '429':		//console.log('aborting');
													//console.log(resp.msgs)
													showMsgs(resp);
													//alert(resp.msgs);
													setTimeout	( function(){ xhr.abort(); console.log('aborted');}
																			, resp.delay
																			);
				}*/			 
			};
		var ajaxCall = function ()
			{	xhr = $.ajax( { type		: "POST"
											, url 		: $form.attr('action') //+ '/ajax' //url = remove '_no_js' from end of action's value
											, data		: $form.serialize() //encode all the inputs from the form
											, dataType: 'json'
											, beforeSend: beforeFn
											, success	: successFn
											} );

			};
		
		$(document).ready( function() 
			{	//window.console.log('loaded');
				$form.submit( function(ev) // make an ajax call instead of the default submit action 
					{	console.log('submit');
						ajaxCall();
						ev.preventDefault();	
					});
			});
	}
})();


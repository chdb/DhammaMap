
;(function() {
/*jshint laxcomma:true */
"use strict";
	var $form = $('#formdiv form');
	if ($form.length>0) // if  $('#form form') element exists, IE there's a <form> element in the DOM with a parent with id='form'
	{	
		var xhr;
		var blocked = false;
		var $flashes = $('#flashes');
		var $formdiv = $('#formdiv');		// put "formdiv" as the id on the div that will be blocked, and which contains the form
		var beforeFn = function() 
			{ 	if ($flashes.children().length) 
					$flashes.slideUp( 1000)
							.animate( { paddingLeft: 0 }
									, 2000
									);  
				if (! blocked) 
				{	$formdiv.block(	{ message: '<i class="fa fa-circle-o-notch fa-spin fa-5x"></i>'
									, css	 : 	{ width  : 'inherit'		
												, border : '10px solid darkgreen'
												, borderRadius: '45%'
												} 			 
									} );
					blocked = true;
				}
			};
		var showMsgs = function (resp)
			{ 	if (resp.msgs)
				{ 	$flashes.html (resp.msgs);
					$flashes.animate  ( { padding: '20px 20px 20px 40px' }
									  , 2000
									  )
							.slideDown( 1000
							          , function() { $formdiv.unblock();
										  			 blocked = false; }
 									  );  
				}
				else
					$formdiv.unblock();
			};
		var successFn = function (resp)
			{	if      (resp.mode ==='good')
					window.location = 'secure';			// redirect
				else if (resp.mode ==='wait')
					setTimeout (ajaxCall, resp.delay);	// try again
				else
					showMsgs (resp); 	
			};
		var ajaxCall = function ()
			{	xhr = $.ajax( { type	  : 'POST'
							  , url 	  : $form.attr('action') //+ '/ajax' //url = remove '_no_js' from end of action's value
							  , data	  : $form.serialize() //+'&'+ $.param({'ipx': ipx }) //encode all the inputs from the form
							  , dataType  : 'json'
							  , beforeSend: beforeFn
							  , success	  : successFn
							  } );
			};
		
		$(document).ready( function() 
			{	$form.submit( function(ev) // make an ajax call instead of the default submit action 
					{	ev.preventDefault();	
						ajaxCall();
					});
			});
	}
})();

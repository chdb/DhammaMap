

;(function() { //keep everything from global namespace
/*jshint laxcomma:true */
"use strict";

/* This script does 3 things
1) clientSide RateLimiting by using UIBlock and wait-cursor to emulate slow server response (in concert with serverSide Ratelimiting)
2) animated flash messages 
3) uses ajax for the Ratelimiting and for repeat attempts
*/
	var $form = $('#formdiv form');
	// if ($form.length>0) // if  $('#form form') element exists, IE there's a <form> element in the DOM with a parent with id='form'
	// {
	var xhr;
	var blocked = false;
	var forgot	= false;
	var $flashes = $('#flashes');
	var $formdiv = $('#formdiv');		// put "formdiv" as the id on the div that will be blocked, and which contains the form
	var	$forgot  = $('#forgot');
	
	function initFlashes ()
	{	$flashes.hide()
				.height('auto')
				.css( { fontSize:'25%'
					  , padding: 0 } );
		logTS('up done'); 
	}		
	function beforeFn () 
	{ 	if ($flashes.children().length) 
		{	logTS('start up');
			$flashes.stop()
					.animate( { height : 0
							  , fontSize : '50%'
							  , paddingLeft: 0
							  , paddingRight: 0
							  , paddingTop: 0
							  , paddingBottom: 0
							  }
							, 200
							, initFlashes
							);
		}
		if (! blocked) 
		{	$formdiv.block(	{ message: '<i class="fa fa-circle-o-notch fa-spin fa-3x"></i>'
							, css	 : 	{ width  : 'inherit'		
										, border : '4px solid darkgreen'
										, borderRadius: '45%'
										} 			 
							} );
			blocked = true;
		}
	}
	function logTS (s)
	{	var d = new Date();
		console.log (d.toLocaleString() + ': ' + s);
	}
	function showMsgs (msgs)
	{ 	if (msgs.length)
		{ 	$flashes.html (msgs);
			$flashes.stop()
					.show()
					.animate( { height : 20
							 // , padding: '20px 20px 120px 40px'
							  , fontSize : '1em'
							  , paddingLeft  : 50
							  , paddingRight : 20
							  , paddingTop	 : 15
							  , paddingBottom: 15
							  }
							, 200
							, function() {	$flashes.height('auto'); 
												$formdiv.unblock();
												blocked = false; 
												logTS('down done');
											 }
							);
		}
		else $formdiv.unblock();
	}
	function errorFn (resp)
	{	xhr.abort()
		var $err = $($.parseHTML(resp.responseText));
		showMsgs ($err);
	}
	function successFn (resp)
	{	if (resp.nextUrl)	// redirect
			window.location = resp.nextUrl;			
		else if (resp.delay)// try again
		{	logTS('wait: ' + resp.delay);
			setTimeout (ajaxCall, resp.delay);	
		}else  				// stop
			showMsgs (resp.msgs); 	
	}
	function ajaxCall ()
	{	xhr = $.ajax( { type	  	  :'POST'
						  , url 	  	  : $form.attr('action') //+ '/ajax' //url = remove '_no_js' from end of action's value
						  , data	  	  : $form.serialize() //+'&'+ $.param({'ipx': ipx }) //encode all the inputs from the form
						  , dataType  :'json'
						  , beforeSend: beforeFn
						  , success	  : successFn
						  , error	  : errorFn
						  } );
	}

	$(document).ready( function() 
	{	var bAjax = true;
		//var formAction = $form.attr('action');
		//alert("formAction = "+ formAction);
		//$form.prop('action', formAction);
		initFlashes();
		$form.submit( function(ev) // make an ajax call instead of the default submit action 
			{	if (bAjax)
				{	ev.preventDefault();
					//var formAction = $form.attr('action');
					//alert("formAction = "+ formAction);
					ajaxCall();
				}
				else //because (most) browsers implement policy that back button preserves state
				{	bAjax = true; 
					//$("input").attr('required','');
					//$("input[novalidate]").removeAttr('novalidate');
				}
			});
		$forgot.click( function() 
			 { //	$("input[required]").removeAttr('required');
			    // $("input[pattern]").removeAttr('pattern');
			   // ,select[required]
				//,textarea[required
				
				//$('input').attr('novalidate','')
				bAjax = false;
				
				
				//$form.prop('action', '/forgot/rq');
				// $form.submit();
				//$form.prop('target', '_blank');	
				//forgot = true;
				// $forgot.attr('href', function() 
					// {	return this.href + '/' + $email.val();
					// });
					
				// alert(this.href);
				//var $email = $form.find('[name="email"]');
				//alert($email.val());
				// $formdiv.after( '<form id="f22" action="/forgot/rq" method="POST">'
							  // +		'<input type=hidden name=email value='+$email.val()+'/>'
							  // + '</form>'
							  // );
				// var v = $('#f22');
				// v.submit();
				
				// $('<input />').attr('type', 'hidden')
					// .attr('name', param.name)
					// .attr('value', param.value)
					// .appendTo('#commentForm');
									
			});
			
	}	);
//}
})();

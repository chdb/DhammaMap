;(function() {
/*jshint laxcomma:true */
"use strict";

var $form = $('#form form');
if ($form.length>0) // if  $('#form form') element exists, IE there's a <form> element in the DOM with a parent with id='form'
{
	var $flashes = $('#flashes');
	var $formdiv = $('#form');		// put "form" as the id on the div that will be blocked, and which contains the form.
	var beforeFn = function() 
	{ 	$flashes.slideUp (1000, function() {$flashes.empty();});  
	};
	var successFn = function (resp)
	{	if (resp.ok) 
		{	if (url in resp)
				window.location = resp.url; 
		}
		else 
		{	$formdiv.block ({ message  : '<img src="../static/snakes-chasing.gif">' 
							, css	   : { width :'10%'				/*
										 , border:'3px solid #FFFFFF'
										 , cursor:'wait'
										 , backgroundColor: '#FFFFFF'
										 }						
							, overlayCSS:{ backgroundColor: '#FFFFFF'
										 , opacity		  : 0.0
										 , cursor		  : 'wait'*/ 
										 }  						
							}); 
			setTimeout	( function() {  $formdiv.unblock();
										$flashes.append (resp.msgs);
										$flashes.slideDown (1000);
									 }
						, resp.timeout
						);
		}
	};
	
	$(document).ready( function() 
		{	$form.submit( function(ev) 
			{	ev.preventDefault();
				$.ajax( { type		: "POST"
						, url 		: $form.attr('action').replace('/s/','/a/')
						, data		: $(this).serialize()
						, dataType	: 'json'
						, beforeSend: beforeFn
						, success	: successFn
						} );
			});
		});
};	
})();

//
// Mailgun Address Validation Plugin
//
// Attaching to a form:
//
//    $('jquery_selector').mailgun_validator({
//        api_key: 'api-key',
//        in_progress: in_progress_callback, // called when request is made to validator
//        success: success_callback,         // called when validator has returned
//        error: validation_error,           // called when an error reaching the validator has occured
//    });
//
//
// Sample JSON in success callback:
//
//  {
//      "is_valid": true,
//      "parts": {
//          "local_part": "john.smith@example.com",
//          "domain": "example.com",
//          "display_name": ""
//      },
//      "address": "john.smith@example.com",
//      "did_you_mean": null
//  }
//
// More API details: https://api.mailgun.net/v2/address
//


$.fn.mailgun_validator = function(options) {
    return this.each(function() {
        $(this).focusout(function() {
            run_validator($(this).val(), options);
        });
    });
};


function run_validator(address_text, options) {
    // don't run validator without input
    if (!address_text) {
        return;
    }

    // length check
    if (address_text.length > 512) {
        error_message = 'Stream exceeds maxiumum allowable length of 512.';
        if (options && options.error) {
            options.error(error_message);
        }
        else {
            console.log(error_message);
        }
        return;
    }

    // validator is in progress
    if (options && options.in_progress) {
        options.in_progress();
    }

    // require api key
    if (options && options.api_key == undefined) {
        console.log('Please pass in api_key to mailgun_validator.')
    }

    var success = false;

    // make ajax call to get validation results
    $.ajax({
        type: "GET",
        url: 'https://api.mailgun.net/v2/address/validate?callback=?',
        data: { address: address_text, api_key: options.api_key },
        dataType: "jsonp",
        crossDomain: true,
        success: function(data, status_text) {
            success = true;
            if (options && options.success) {
                options.success(data);
            }
        },
        error: function(request, status_text, error) {
            success = true;
            error_message = 'Error occurred, unable to validate address.';

            if (options && options.error) {
                options.error(error_message);
            }
            else {
                console.log(error_message);
            }
        }
    });

    // timeout incase of some kind of internal server error
    setTimeout(function() {
        error_message = 'Error occurred, unable to validate address.';
        if (!success) {
            if (options && options.error) {
                options.error(error_message);
            }
            else {
                console.log(error_message);
            }
        }
    }, 30000);

}

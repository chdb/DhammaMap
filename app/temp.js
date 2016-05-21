% endblock %}


	bc.find('.submit').click(function (e) {
    e.preventDefault();
    if ($(this).hasClass('lock'))
        return;
    $.blockUI();
    $(this).addClass('lock');
    bc.submit();
});

var validator;
validator = bc.validate({
    ignore: '',
    rules: {
        UserName: {
            required: true
        }
    },
    messages: {
        UserName: 'must have',
    },
    submitHandler: function (form) {
        $.ajax({
            url: '/yyyy/xxxx',
            type: 'POST',
            data: postdata,
            complete: function () {
                bc.find('.submit').removeClass('lock');
            },
            success: function (data) {
                if (data.status == 'OK') {
                    $.blockUI({ message: 'OK' });
                    ......
                }
                else {
                    switch (data.status) {
                        case 'xxx':
                        ......
                    }
                    $.unblockUI();
                }
            },
            error: function () {
                $.unblockUI();
                alert('xxx');
            }
        });
    }
})
 
$(document).ready(function() {
	$('.form').submit(function(e) {
		e.preventDefault();
		$.ajax({
			 type: "POST",
			 url: '/aLogin',
			 data: $(this).serialize(),
			 success: function(resp)
			 {
					if (resp === 'Login') {
						window.location = '/secure';
					}
					else {
						alert('Invalid Credentials');
					}
			 }
		});
	});
});


$.blockUI (	{ message  : '<img src="your.gif" />' 
			, css	   : { width :'4%'
						 , border:'0px solid #FFFFFF'
						 , cursor:'wait'
						 , backgroundColor: '#FFFFFF'
						 }
			, overlayCSS:{ backgroundColor: '#FFFFFF'
						 , opacity		  : 0.0
						 , cursor		  : 'wait'
						 } 
}); 

for (var i=0; i<data.length; ++i)
{	$('.flashes').append ("<li>" + data[i][0] + "</li>")
}
// same as $.ajax but settings can have a blockUI property
// if settings.blockUI is defined UI will block while ajax in property
// settings.blockUI is the setting object for $.blockUI
// as a shortcut, if settings.blockUI===true, blockUI with only an hourglass 

function ajaxBlockUI(settings) {
    var dfd = new $.Deferred();

    var blockUIsettings;

    if (settings.blockUI)
    {
        blockUIsettings = settings.blockUI;
        delete settings.blockUI;

        if (blockUIsettings === true) {
            blockUIsettings = {
                overlayCSS: {
                    backgroundColor: 'transparent'
                },
                message: ''
            };
        }
    }

    if (blockUIsettings) $.blockUI(blockUIsettings);

    $.ajax(settings)
        .fail(function(jqXHR, textStatus, errorThrown) {
            if (blockUIsettings) $.unblockUI();
            dfd.reject(jqXHR, textStatus, errorThrown);
        }).done(function(data, textStatus, jqXHR) {
            if (blockUIsettings) $.unblockUI();
            dfd.resolve(data, textStatus, jqXHR);
        });

    return dfd.promise();
}

//with this you can now do:

ajaxBlockUI ({ url: url,
				blockUI: true
			}).fail(function (jqXHR, textStatus, errorThrown) {
						console.log('error ' + textStatus);
			}).done(function (data, textStatus, jqXHR) {
						console.log('success ' + JSON.stringify(data));
			});
{% block mediaJS %}
// https://stackoverflow.com/questions/6142025/dynamically-add-field-to-a-form
// https://simpleisbetterthancomplex.com/tutorial/2016/11/22/django-multiple-file-upload-using-ajax.html
// todo: reset uploading text on failure
// todo: can fail to update description and hang on this screen during upload

$(document).ready(function(){

    // submit photos via API calls
    $("form").on('submit', function (e) {
        var photos = new FormData(); //new FormData(document.getElementById("uploadphotosform"));

        photos.append('image', $('#id_file')[0].files[0]);
        console.log($('#id_description')[0].value);
        var inputdesc = $('#id_description')[0].value;

        var albumid = document.getElementById("albumid").value;

        var csrftoken = getCookie('csrftoken');

        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                // use csrf token
                if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                    // Only send the token to relative URLs i.e. locally.
                    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                }
                
                // replace submit button with "uploading..."
                var myAnchor = document.getElementById("sendupload");
                var mySpan = document.createElement("span");
                mySpan.innerHTML = "Uploading...";
                myAnchor.parentNode.replaceChild(mySpan, myAnchor);
            }
        });

        $.ajax({
            type: 'POST',
            data: photos,
            url: '/api/upload/' + albumid,
            dataType: 'json',
            contentType: false,
            processData: false,
            statusCode: {
                201: function (response) {
                    console.log("Uploaded!");
                    var photoid = response.id;

                    var xhr = new XMLHttpRequest();
                    // define success check
                    xhr.onreadystatechange = function() {
                        if (xhr.readyState === 4) {
                            if (xhr.status === 204) {
                                console.log('successful description update');
                                window.location.href = '/album/' + albumid + '/';
                            } else {
                                console.log('failed description update');
                                alert('Failed to add description to photo.  Sorry!');
                                window.location.href = '/album/' + albumid + '/';
                            }
                        }
                    }
                    xhr.open("POST", '/api/update/photo/desc/' + photoid, true);
                    xhr.setRequestHeader("Content-Type", "application/json");
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    var data = JSON.stringify({"description": inputdesc});
                    xhr.send(data);

                    console.log("Desc update sent!");
                }
            },
            // handle error case
            error: function(jqXHR, textStatus, errorThrown) {
                alert('Ooowee.. we could not upload that photo.  Check javascript console for more info if so inclined.');

                //$('#result').html('<p>status code: '+jqXHR.status+'</p><p>errorThrown: ' + errorThrown + '</p><p>jqXHR.responseText:</p><div>'+jqXHR.responseText + '</div>');
                console.log('jqXHR:');
                console.log(jqXHR);
                console.log('textStatus:');
                console.log(textStatus);
                console.log('errorThrown:');
                console.log(errorThrown);
            }
        }).done(function (response) {
            console.log("In done...");
        });

        //stop form submission
        e.preventDefault();
    });
});

// probably wont use this but keeping for now
function DuplicateIn() {

  var formInvalid = false;
  $('#register_form input').each(function() {
    if ($(this).val() === '') {
      formInvalid = true;
    }
  });

  if (formInvalid)
    alert('One or Two fields are empty. Please fill up all fields');
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
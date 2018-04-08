//https://stackoverflow.com/questions/6142025/dynamically-add-field-to-a-form

$(document).ready(function(){
    form_count = Number($("[name=extra_field_count]").val());
    // get extra form count so we know what index to use for the next item.

    $("#add-another").click(function() {
        form_count ++;

        element = $('<input type="file"/>');
        element.attr('name', 'extra_file_' + form_count);
        #("#forms").append(element);

        element = $('<input type="text"/>');
        element.attr('name', 'extra_desc_' + form_count);
        $("#forms").append(element);
        // build element and append it to our forms container

        $("[name=extra_field_count]").val(form_count);
        // increment form count so our view knows to populate
        // that many fields for validation
    })
});

/*
<p>
        <label for="id_file">File:</label><br>
        <input type="file" name="file" required id="id_file" />


      </p>
*/

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
/**
 * @file setup.js
 * @author Joseph Ciurej
 * @date Spring 2014
 *
 * Container Module for Base Setup Logic for CS411 Project Pages
 *
 * @TODO
 */


// Helper Functions //

/**
 * @return gid The group identifier for the current page (only valid for the
 *  groups page).
 */
function getGroupID()
{
	return $( "meta[name=groupid]" ).attr( "content" );
}

// Primary Entry Point //

/**
 * Main function for the 'setup.js' script file.
 */
function main()
{
	// Set Up Libraries //
	{
		// Setup the Editable Fields //
		$.fn.editable.defaults.mode = "popup";
		$( ".editable-field" ).editable();

		// Setup the Deadline List Modules //
		$( ".deadline-notes" ).hide();
		$( ".deadline-entry" ).click( function() {
			$( this ).find( ".deadline-notes" ).slideToggle( "slow" );
		} );

		// Setup the Datetime Picker Modules //
		$( ".datetimepicker-form" ).datetimepicker();
		$( ".timepicker-form" ).datetimepicker( {pickDate: false} );

		// Setup the Select Modules //
		$( "select" ).selectpicker();
		// TODO: Select all members by default in schedule modal select.
	}

	// Set up Autocomplete Fields ///
	{
		var typeahead_options = { hint: true, highlight: true, minlength: 2 };

		var emailFinder = new Bloodhound( {
			datumTokenizer: Bloodhound.tokenizers.obj.whitespace( "value" ),
			queryTokenizer: Bloodhound.tokenizers.whitespace,
			remote: "../get-emails"
		} );
		emailFinder.initialize();
		$( "#new_user_email" ).typeahead( typeahead_options,
			{ name: "emails", displaykey: "value", source: emailFinder.ttAdapter() } );

		// TODO: Only allow this feature if the user can add courses.
		var courseFinder = new Bloodhound( {
			datumTokenizer: Bloodhound.tokenizers.obj.whitespace( "value" ),
			queryTokenizer: Bloodhound.tokenizers.whitespace,
			remote: "../get-courses"
		} );
		courseFinder.initialize();
		$( "#group_name" ).typeahead( typeahead_options,
			{ name: "emails", displaykey: "value", source: courseFinder.ttAdapter() } );

		var deadlineFinder = new Bloodhound( {
			datumTokenizer: Bloodhound.tokenizers.obj.whitespace( "value" ),
			queryTokenizer: Bloodhound.tokenizers.whitespace,
			remote: "../get-deadlines"
		} );
		deadlineFinder.initialize();
		$( "#deadline_name" ).typeahead( typeahead_options,
			{ name: "emails", displaykey: "value", source: deadlineFinder.ttAdapter() } );

		// TODO: Remove this example code.
		/*$( "#group_name" ).typeahead( { hint: true, highlight: true, minlength: 2 },
			{ name: "states", displaykey: "value", source: substringMatcher(states) } );*/
	}

	// Bind AJAX Requests to Fields //
	{
		// Setup the Google Authentication Button //
		$( "#google_auth" ).click( function() {
			$.post("google-auth-request", function(url) {
				window.location.replace(url);
			});
		} );

        $( "#leave_group" ).click( function () {
            var data1 = {};
            data1['group_id'] = getGroupID();
            $.ajax({
                type: 'POST',
                url: '/leave-group',
                data: {'data': JSON.stringify(data1)},
                dataType: 'application/json',
                complete: function(msg) {
                    window.location.reload();
                },
                fail: function(data) {
                    alert("Failed to leave group.");
                }
            });
        });
 
		$( "#delete_group" ).click( function() {
            var data1 = {};
            data1['group_id'] = getGroupID();

            $.ajax({
                type: 'POST',
                url: '/delete-group',
                data: {'data': JSON.stringify(data1)},
                dataType: 'application/json',
                complete: function(msg) {
                    window.location.reload();
                },
                fail: function(data) {
                    alert("Failed to delete group.");
                }
            }); 
		});
        
        $( "#add-member-submit" ).click( function () {
            var data1 = {};
            data1['group_id'] = getGroupID();

            // Input element has no ID tag defined 
            data1['user_email'] = $('[name="user_email"]').val();
            $.ajax({
                type: 'POST',
                url: '/add-member',
                data: {'data': JSON.stringify(data1)},
                dataType: 'application/json',
                complete: function(msg) {
                    $('#add-member-modal').modal('hide');
                },
                fail: function(data) {
                    alert("Failed to add user to group.");
                }
            });
        });
            
                    
        $( "#add-subgroup-submit" ).click( function () {
            var data1 = {};
            data1['group_id'] = getGroupID();

            // Input element has no ID tag defined 
            data1['group_name'] = $('[name="group_name"]').val();
            data1['group_description'] = $('[name="group_description"]').val();
            $.ajax({
                type: 'POST',
                url: '/add-subgroup',
                data: {'data': JSON.stringify(data1)},
                dataType: 'application/json',
                complete: function(msg) {
                    $('#add-subgroup-modal').modal('hide');
                },
                fail: function(data) {
                    alert("Failed to add subgroup.");
                }
            });
        });
        

	    // Setup Group Page Modal Submission Buttons //

		// TODO: Add group page submission button post requests.
	}
}


$( document ).ready( main );


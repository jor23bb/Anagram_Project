(function(window, document, undefined) {

	function format_array_responses(response){
		var text = '';
		for (var key in response){
			if (response[key].length == 0){
				continue;
			}

			text += key + ': '

			for (values in response[key]){
				text += response[key] + ' '

				//Because the delete all function calls this after returning & I didn't want to give it it's own ajax function
				if (!Array.isArray(response[key])){
					return text;
				}
			}
			text += '\n\n'
		}
		return text
	}

	function format_simple_responses(response){
		var text = '';

		for (var key in response){
			text += key + ': ' + response[key] + '\n\n'
		}

		return text
	}

	function post_request(){
		var words = document.getElementById('post-textarea').value.replace(/[^a-z\s]/gi, '').match(/[^\s]+/g);
		
		if (!words){
			document.getElementById('post-textarea').value = '';
			return
		}
		console.log(words);
		var uri = '../../anagrams';

		if (document.getElementById('proper-noun').checked){
			uri += '?proper_nouns=true'
		}

		$.ajax({
			type: 'POST',
			url: uri,
			contentType: 'application/json',
			dataType: 'json',
			data: JSON.stringify({'words': words}),
			success: function(response){
				alert(format_simple_responses(response));
			},
			error: function(response){
				alert(response);
			},
			complete: function(){
				document.getElementById('post-textarea').value = '';
				document.getElementById('proper-noun').checked = false;
			}
		});
	}

//consider having the python version change its response from {anagrams: [word1 word2]} to {originial_word: [word 1, word 2]}
	function get_request(get_all){
		var uri = '../../anagrams';

		if (!get_all){
			var words;
			try{
				words = document.getElementById('get-textarea').value.replace(/[^a-z\s]/gi, '').match(/[^\s]+/g).join('&word=');
			}
			catch(e){
				document.getElementById('get-textarea').value = '';
				document.getElementById('max-num-results-textarea').value = '';
				return
			}

			var limit = document.getElementById('max-num-results-textarea').value.trim();

			uri += '/?word=' + words;
			if (/^\d+$/.test(limit)){
				uri += '&limit=' + limit.toString();
			}
		}

		$.ajax({
			type: 'GET',
			url: uri,
			success: function(response){
				if (get_all){
					open_modal(full_dict_to_text(response));
				} else{
					open_modal(dictionary_to_text(response));
				}
			},
			error: function(response){
				alert(response);
			},
			complete: function(){
				document.getElementById('get-textarea').value = '';
				document.getElementById('max-num-results-textarea').value = '';
			}
		});
	}

	function delete_request(delete_all){
		var uri = '../../';

		if (!delete_all){
			//for when users submit an empty text area / one with only non-alpha characters
			var words;
			try{
				words = document.getElementById('deletion-textarea').value.replace(/[^a-z\s]/gi, '').match(/[^\s]+/g).join('&word=');
			} catch(e){
				document.getElementById('deletion-textarea').value = '';
				document.getElementById('delete-associated-anagrams').checked = false;
				return
			}

			if (document.getElementById('delete-associated-anagrams').checked){
				uri += 'anagrams/?word=' + words
			}
			else{
				uri += 'words/?word=' + words
			}
		}


		$.ajax({
			type: 'DELETE',
			url: uri,
			success: function(response){
				alert(format_array_responses(response));
			},
			error: function(response){
				alert(response);
			},
			complete: function(){
				document.getElementById('deletion-textarea').value = '';
				document.getElementById('delete-associated-anagrams').checked = false;
			}
		});
	}

	function stat_request(){

		var uri = '../../stats';

		$.ajax({
			type: 'GET',
			url: uri,
			success: function(response){
				open_modal(dictionary_to_text(response));
			},
			error: function(response){
				alert(response);
			}
		});
	}

	function open_modal(new_text){
		var modal = document.getElementById('modal-wrapper');
		modal.style.display = 'block';
		document.getElementById('modal-text').innerHTML = new_text;
	}

	$('.close').click(function(){
		document.getElementById('modal-text').innerHTML = '';
		document.getElementById('modal-wrapper').style.display = 'none';
	});

	function dictionary_to_text(d){
		var text = '';
		for (key in d){
			text += '<b>' + key + '</b>' + ': ';
			if (Array.isArray(d[key])){
				text += d[key].join(', ') + '<br>'
			} else {
				text += d[key].toString() + '<br>'
			}
		}	
		return text
	}

	function full_dict_to_text(d){
		var text = '';
		for (key in d){
			text += '<b>' + d[key][0] + '</b>' + ': ' + d[key].slice(1).join(', ') + '<br>'
		}	
		return text
	}


	function add_text_file(){

	}


//Pressing 'enter' in any of the main text areas is the equivalent of pressing the associated submit button
	$('#post-textarea').keyup(function(event) {
		if (event.keyCode === 13){
			post_request();
		}
	});

	$('#get-textarea').keyup(function(event) {
		if (event.keyCode === 13){
			get_request(false);
		}
	});

	$('#deletion-textarea').keyup(function(event) {
		if (event.keyCode === 13){
			delete_request(false);
		}
	});


//Click handlers for the various buttons

	$('#get-submit-button').click(function(){
		get_request(false);
	});

	$('#get-stats-button').click(function(){
		stat_request();
	});

	$('#get-all-button').click(function(){
		get_request(true);
	});

	$('#post-submit-button').click(function(){
		post_request();
	});

	$('#deletion-submit-button').click(function(){
		delete_request(false);
	});

	$('#delete-everything-button').click(function(){
		delete_request(true);
	});

	$('#file-upload-button').click(function(){
		add_text_file();
	});













})(this, this.document);
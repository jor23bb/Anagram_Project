from flask import Flask, jsonify, make_response, abort, flash, request, render_template
import json
import heapq
import os

#NOTE: EVEN IF 'USE PROPER NOUNS' IS ENABLED, PROPER NOUNS ARE STORED AS SEPARATE FROM THEIR LOWERCASE COUNTERPARTS, AKA 'Mike' & 'mike' ARE STORED AS TWO DISTINCT STRINGS. SO CALLING 'DELETE' ON 'mike' WILL NOT DELETE THE OTHER, AND VICE VERSA

anagram_dict = {}
most_anagrams_dict = {}

#EXTRAS

#Stats
total_word_count = 0
min_word_length = 25 #replace later after determining what our maximum allowable word length will be
max_word_length = 0
avg_word_length = float(0)
min_heap_for_median = []
max_heap_for_median = []

#Most Anagrams
#As currently constructed, array will not be sorted. Will have all related anagrams sorted, followed by each other group of anagrams
max_num_anagrams = 0
words_with_most_anagrams = []


#HELPER FUNCTIONS

def sort_word(word):
	return ''.join(sorted(word))

def insertion_bsearch(arr, target): #Returns mid because I call this when inserting. Since I want to maintain a sorted array, keeping track of insertion point here is easier than sorting everytime
	def helper(arr, target, first, last):
		if first >= last:
			return last
		mid = (last + first+1) / 2
		if arr[mid] == target:
			return mid
		if arr[mid] > target:
			return helper(arr, target, first, mid - 1)
		return helper(arr, target, mid + 1, last)
	return helper(arr, target, 0, len(arr) - 1)

#normal bsearch that returns -1 when target isnt found	
def bsearch(arr, target): 
	def helper(arr, target, first, last):
		mid = (last + first) / 2
		if arr[mid] == target:
			return mid
		if mid == last:
			return -1
		if arr[mid] > target:
			return helper(arr, target, first, mid - 1)
		return helper(arr, target, mid + 1, last)
	return helper(arr, target, 0, len(arr) - 1)

def adding_to_median(word_length):
	global total_word_count
	global max_heap_for_median
	global min_heap_for_median

	if total_word_count % 2 == 0:
		heapq.heappush(max_heap_for_median, -1 * word_length)
		if len(min_heap_for_median) == 0:
			return
		if -1 * max_heap_for_median[0] > min_heap_for_median[0]:
			new_min = -1 * heapq.heappop(max_heap_for_median)
			new_max = -1 * heapq.heappop(min_heap_for_median)
			heapq.heappush(max_heap_for_median, new_max)
			heapq.heappush(min_heap_for_median, new_min)
	else:
		new_min = -1 * heapq.heappushpop(max_heap_for_median, -1 * word_length)
		heapq.heappush(min_heap_for_median, new_min)

def get_median_word_length():
	global total_word_count
	global min_heap_for_median
	global max_heap_for_median

	if total_word_count % 2 == 0:
		return (min_heap_for_median[0] + -1*max_heap_for_median[0]) / 2
	return -1*max_heap_for_median[0]

#this is for when adding numbers, not removing them
def calc_new_avg_word_length(new_word_length):
	global avg_word_length
	global total_word_count

	#in this total_word_count has already been updated, which is why 1 isn't added to the denominator
	return avg_word_length + (new_word_length - avg_word_length)/float(total_word_count)

#need to deal with updating the median
def update_stats_post_single_deletion(word):
	global max_heap_for_median
	global min_heap_for_median
	global total_word_count
	global avg_word_length
	global anagram_dict
	global min_word_length
	global max_word_length
	global max_num_anagrams
	global words_with_most_anagrams

	l = len(word)

	#dealing with updating the median
	if l > -1 * max_heap_for_median[0]:
		min_heap_for_median.remove(l)
		heapq.heapify(min_heap_for_median)

		new_min = -1 * heapq.heappop(max_heap_for_median)
		heapq.heappush(min_heap_for_median, new_min)
	else:
		max_heap_for_median.remove(-1*l)
		heapq.heapify(max_heap_for_median)

		if total_word_count % 2 == 0:
			new_max = -1 * heapq.heappop(min_heap_for_median)
			heapq.heappush(max_heap_for_median, new_max)

	avg_word_length = (avg_word_length*total_word_count - l)/(total_word_count - 1)
	total_word_count -= 1

	if not sort_word(word) in anagram_dict:
		if l == min_word_length:
			keys = anagram_dict.keys()
			min_word_length = len(min(keys, key=len))
		if l == max_word_length:
			keys = anagram_dict.keys()
			max_word_length = len(max(keys, key=len))
	else:
		l = len(anagram_dict[sort_word(word)]) + 1
		if l == max_num_anagrams:
			if len(words_with_most_anagrams) == l:
				#need to update both
				pass
			else:
				#remove word + everything remaining in the anagram dict from the 'words with most anagrams'
				pass



def update_stats_post_multiple_deletion(key):
	global min_word_length
	global max_word_length
	global total_word_count
	global avg_word_length
	global max_num_anagrams
	global anagram_dict
	global words_with_most_anagrams

	arr = anagram_dict[key]
	key_len = len(key)
	list_len = len(arr)

	avg_word_length = (avg_word_length*total_word_count - key_len*list_len)/(total_word_count - list_len)
	total_word_count -= list_len

	if list_len == max_num_anagrams:
		if len(words_with_most_anagrams) == list_len:
			#need to update both
			pass
		else:
			#remove everything in arr from 'words with most anagrams'
			pass

	del anagram_dict[key]
	
	if key_len == min_word_length:
		keys = anagram_dict.keys()
		min_word_length = min(keys, key=len)
	if key_len == max_word_length:
		keys = anagram_dict.keys()
		max_word_length = max(keys, key=len)



#FLASK CODE
template_folder = os.path.abspath('HTML')
# static_folder = os.path.abspath('static')
app = Flask(__name__, template_folder = template_folder)

#not sure why this has occasionally been necessary...
app.secret_key = 'secret'


@app.route('/')
def landing_page():
	return render_template('index.html')

@app.route('/anagrams', methods=['GET'])
def get_full_dict():
	global anagram_dict

	return jsonify(anagram_dict), 200

@app.route('/anagrams/to_each_other/', methods=['GET'])
def anagrams_of_each_other():
	words = request.args.getlist('word')
	if len(words) < 2:
		return jsonify({'Error': 'Please input at least 2 words in the valid format. Ex: url/?word="try"&word="again"'})

	letters = sort_word(words[0])
	try:
		arr = anagram_dict[letters]
		for word in words:
			index = bsearch(arr, word)
			if index < 0:
				return jsonify({'Success': 'Based upon what is in our datastore, these are not valid anagrams of each other.'}), 200
		else:
			return jsonify({'Success': 'Yes, these are all valid anagrams of each other.'}), 200
	except KeyError:
		return jsonify({'Error': 'One or more of these so-called "words" does not currently exist in our datastore.'})

@app.route('/anagrams/', methods=['GET'])
def get():
	global anagram_dict

	words = request.args.getlist('word')
	if len(words) < 1:
		return jsonify({'Error': "You either didn't input a word or used an incorrect format. Please use '/anagrams/?word=insert_word_here&word=additional_words'"})

	max_num_results = -1
	if request.args.get('limit'):
		max_num_results = int(request.args.get('limit'))
		if max_num_results == 0:
			return jsonify({'Error': "You asked for 0 results. Congrats, that's dumb."}), 200

	return_dict = {}
	for word in words:
		sorted_word = sort_word(word)
		try:
			arr = anagram_dict[sorted_word]
			index = bsearch(arr, word)
			if index > -1:
				arr = arr[:index] + arr[index + 1:]
			if max_num_results < 0 or max_num_results > len(arr):
				return_dict[word] = arr
			else:
				return_dict[word] = arr[:max_num_results]
		except KeyError:
			pass
	if not any(return_dict):
		return jsonify({'Too Bad': "The word(s) you input don't have any anagrams in our datastore"}), 200
	return jsonify(return_dict), 200


@app.route('/anagrams', methods=['POST'])
def post():

	if not request.get_json() or not request.get_json()['words']:
		abort(400)

	global min_word_length
	global max_word_length
	global total_word_count
	global avg_word_length
	global max_num_anagrams
	global words_with_most_anagrams
	global anagram_dict

	arr = request.get_json()['words']

	use_proper_nouns = False
	if request.args.get('proper_nouns'):
		use_proper_nouns = request.args.get('proper_nouns').lower() == 'true'

	for word in arr:
		if use_proper_nouns:
			sorted_word = sort_word(word.lower())
		else:
			sorted_word = sort_word(word)


		#if its already in there, add it to the array. keep it sorted so that whenever its requested
		#it'll already be sorted. Doing it this way rather than sorting when returning for 2 reasons:
		#1: Operating under the assumption that there will be many 'get' calls to the dictionary, so more efficient long term to just have them all already sorted  
		#2: Given the anatomy of the dictionary (all anagrams are stored together on the sorted letters) it makes it quicker to do lookup when removing the original word from the return list (a word cannot be its own anagram)
		
		if sorted_word in anagram_dict:
			a = anagram_dict[sorted_word]
			index = insertion_bsearch(a, word)
			if a[index] == word:
				# flash(word + ' already exists in our datastore')
				continue
			elif a[index] < word:
				index += 1
			a.insert(index, word)
			anagram_dict[sorted_word] = a
		else:
			anagram_dict[sorted_word] = [word]


		#purely for updating word stats		
		l = len(word)
		if l < min_word_length:
			min_word_length = l
		if l > max_word_length:
			max_word_length = l

		adding_to_median(l)

		total_word_count += 1
		avg_word_length = calc_new_avg_word_length(l)

		#for updating things regarding 'most anagrams'
		curr_arr = anagram_dict[sorted_word]
		length_curr_arr = len(curr_arr)
		if length_curr_arr > max_num_anagrams:
			max_num_anagrams = length_curr_arr
			words_with_most_anagrams = curr_arr
		elif length_curr_arr == max_num_anagrams:
			words_with_most_anagrams = words_with_most_anagrams + curr_arr

	return jsonify({'Success': 'Saved all words to the corpus, sans duplicates'}), 201


@app.route('/words/', methods=['DELETE'])
def single_delete():
	global anagram_dict

	words = request.args.getlist('word')
	if len(words) < 1:
		return jsonify({'Error': "You either didn't input a word or used an incorrect format. Please use '/words/?word=insert_word_here&word=additional_words'"})

	successes = []
	failures = []
	for word in words:
		sorted_word = sort_word(word)
		try:
			arr = anagram_dict[sorted_word]
			index = bsearch(arr, word)
			if index > -1:
				#if it doesn't have any anagrams just delete the entire key from the dictionary
				if len(arr) == 1:
					del anagram_dict[sorted_word]
				else:
					del arr[index]
				update_stats_post_single_deletion(word)
				successes.append(word)
			else:
				failures.append(word)
		except KeyError:
			failures.append(word)
	if len(successes) == 0:
		jsonify({'Error': failures})
	return jsonify({'Success': successes, 'Error': failures}), 200

@app.route('/', methods=['DELETE'])
def complete_deletion():
	global min_word_length
	global max_word_length
	global total_word_count
	global avg_word_length
	global max_num_anagrams
	global words_with_most_anagrams
	global anagram_dict
	global min_heap_for_median
	global max_heap_for_median


	anagram_dict = {}
	total_word_count = 0
	min_word_length = 25
	max_word_length = 0
	avg_word_length = 0
	min_heap_for_median = []
	max_heap_for_median = []

	max_num_anagrams = 0
	words_with_most_anagrams = []

	return jsonify({'Success': 'Successfully deleted everything.'}), 200


@app.route('/anagrams/', methods=['DELETE'])
def delete_all_anagrams():
	global anagram_dict

	words = request.args.getlist('word')
	if len(words) < 1:
		return jsonify({'Error': "You either didn't input a word or used an incorrect format. Please use '/anagrams/?word=insert_word_here&word=additional_words'"})

	successes = []
	for word in words:
		key = sort_word(word)
		if key in anagram_dict:
			if not word in anagram_dict[key]:
				#couldn't find word
				pass
			update_stats_post_multiple_deletion(key)
			successes.append(word)
		else:
			#couldn't find word
			pass
	if len(successes) < 1:
		return jsonify({'Error': 'None of the given words could be found in the corpus'})
	return jsonify({'Success': successes}), 200

#count of words in the corpus and min/max/median/average word length
@app.route('/stats', methods=['GET'])
def datastore_stats():
	global min_word_length
	global max_word_length
	global total_word_count
	global avg_word_length
	global max_num_anagrams
	global words_with_most_anagrams

	if total_word_count == 0:
		return jsonify({'Error': "Everything is 0. There aren't any words here yet!"})

	stats = {
		'Total Words' : total_word_count,
		'Shortest Word Length' : min_word_length,
		'Longest Word Length' : max_word_length,
		'Median Word Length' : get_median_word_length(),
		'Average Word Length' : float("%.2f" % avg_word_length),
		'Max Number of Anagrams for a Single Word' : max_num_anagrams,
		'Words With Most Anagrams' : words_with_most_anagrams
	}

	return jsonify(stats), 200


@app.errorhandler(400)
def not_found(error_code):
    return make_response(jsonify({'Error': "Please format your requests as a JSON object with the key being 'words'"}), 400)

@app.errorhandler(404)
def not_found(error_code):
    return make_response(jsonify({'Error': 'Not Found'}), 404)

if __name__ == '__main__':
    app.run()









# curl -i -H "Content-Type: application/json" -X POST -d '{"words": ["Read", "dear", "dare"]}' http://localhost:5000/anagrams
# curl -i -H "Content-Type: application/json" -X POST -d '{"words": ["life", "file", "flier"]}' http://localhost:5000/anagrams
# curl -i -H "Content-Type: application/json" -X POST -d '{"words": ["battle", "dabble", "babled"]}' http://localhost:5000/anagrams


# curl -i http://localhost:5000/anagrams/read

# curl -i http://localhost:5000/stats

# curl -i -X DELETE http://localhost:5000/words/read

# curl -i -X DELETE http://localhost:5000/anagrams/read

# curl -i -X DELETE http://localhost:5000/

# curl -i http://localhost:5000/anagrams/rade?limit=2
# curl -i "http://localhost:5000/anagrams/to_each_other/?word=read&word=dare"





# curl -i http://localhost:5000/anagrams/?word=word?limit=1











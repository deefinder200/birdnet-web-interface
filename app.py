import analyzer
import requests
import datetime
from urllib.parse import urlparse, unquote
from pydub import AudioSegment
from flask import Flask, request, render_template, jsonify
import os.path

temp_dir = "temp"
if not os.path.exists(temp_dir):
	os.mkdir(temp_dir)

##
# Variables to use when testing
##
use_test_detections = False # Useful when developing the front-end
use_test_single_recording = False
use_test_multiple_recordings = False
##

app = Flask(__name__)

@app.route('/', methods=['GET'])
async def home():
	return render_template('identify.html')

@app.route('/detections', methods=['POST'])
async def getDetections():
	detection_data = []

	if use_test_detections:
		return jsonify({"detection_data": {"recording_1": [{'common_name': 'Mountain Chickadee', 'scientific_name': 'Poecile gambeli', 'start_time': 12.5, 'end_time': 15.5, 'confidence': 0.29550546407699585, 'label': 'Poecile gambeli_Mountain Chickadee'}, {'common_name': 'Boreal Chickadee', 'scientific_name': 'Poecile hudsonicus', 'start_time': 17.5, 'end_time': 20.5, 'confidence': 0.5595659017562866, 'label': 'Poecile hudsonicus_Boreal Chickadee'}]}})

	inaturalist_observation_url = request.form['inaturalist_observation_url']
	detection_data = await getDetectionsFromObservationUrl(inaturalist_observation_url)

	return jsonify({"detection_data": detection_data})

##
# Retrieve detections from an Observation URL
#
# @param Str observation_url		Observation URL to handle
#
# return Dictionary(all detections)
##
async def getDetectionsFromObservationUrl(observation_url):
	if use_test_single_recording:
		# Example Boreal Chickadee
		observation_url = "https://www.inaturalist.org/observations/333479462"

	elif use_test_multiple_recordings:
		# Example Marsh Tit with multiple recordings
		observation_url = "https://www.inaturalist.org/observations/332146765"

	# Extract the part of the URL after the last backslash to get the Observation ID
	last_slash_index = observation_url.rfind('/')
	observation_id = observation_url[last_slash_index + 1:]

	api_url = "https://api.inaturalist.org/v1/observations/" + observation_id

	log("Making request for " + observation_id)
	response = await makeHttpRequest(api_url)
	log("Got response for " + observation_id)

	[filepaths, lat, lon, observed_on_date] = extractVariablesFromAPIResponse(response)

	log("Filepaths: " + str(filepaths))
	log("Latitude: " + str(lat))
	log("Longitude: " + str(lon))
	log("Timestamp: " + str(observed_on_date.timestamp()))

	all_detections = {}
	i = 1
	for filepath in filepaths:
		detections = analyzer.getBirdNetDetections(filepath, lat, lon, observed_on_date.timestamp())
		log("Detections: " + str(detections))
		all_detections["recording_" + str(i)] = detections
		i += 1

	# Clear temp_dir
	for filename in os.listdir(temp_dir):
		file_path = os.path.join(temp_dir, filename)
		os.remove(file_path)

	return all_detections

##
# Extract sound files from Observation's API response
#
# @param Dictionary observation_fields		Observation fields to handl
#
# @return Array[filepaths]
##
def extractSoundFilesFromObservation(observation_fields):
	output_filepaths = []

	i = 1
	sounds = observation_fields["sounds"]
	for sound in sounds:
		log("Sound: " + str(sound))
		sound_url = sound["file_url"]
		log("Sound url: " + sound_url)

		file_extension = getFileExtension(sound_url)

		log("File extension: " + file_extension)

		filepath = os.path.join(temp_dir, "temp" + str(i) + "." + file_extension)
		output_filepath = os.path.join(temp_dir, "temp.wav")
		with open(filepath, mode="wb") as file:
			response = requests.get(sound_url)
			file.write(response.content)

		# Convert m4a to wav
		sound = AudioSegment.from_file(filepath, format=file_extension)
		sound.export(output_filepath, format='wav')

		output_filepaths.append(output_filepath)
		i += 1

	return output_filepaths

##
# Extracts relevant variables from API response
#
# @param Response response		HTTP response to handle
#
# @return Array[filepaths, lat, lon, observed_on_date]
##
def extractVariablesFromAPIResponse(response):
	response_body = response.json()

	results = response_body["results"]
	result = results[0]
	observed_on_details = result["observed_on_details"]
	year = observed_on_details["year"]
	month = observed_on_details["month"]
	day = observed_on_details["day"]

	observed_on_date = datetime.datetime(year=year, month=month, day=day)
	filepaths = extractSoundFilesFromObservation(result)

	lat = None
	lon = None
	geojson = result["geojson"]
	if not geojson is None and "coordinates" in geojson:
		coordinates = geojson["coordinates"]
		lon = coordinates[0]
		lat = coordinates[1]

	return [filepaths, lat, lon, observed_on_date]

##
# Extracts the file extension from a given URL
#
# @param Str url	Url to extract file extension from
#
# return Str
##
def getFileExtension(url):
	parsed_url = urlparse(url)
	path = parsed_url.path

	# Decode the path to handle URL-encoded characters
	path = unquote(path)

	# Find the last period in the path to get the file extension
	ext_start = path.rfind('.')

	if ext_start == -1:
		return ''
	else:
		return path[ext_start+1:]

##
# Print a msg to the log
#
# @param Str msg		Message to print
#
# @return None
##
def log(msg):
	print(str(msg))
	app.logger.info(str(msg))

##
# Make a HTTP request
#
# @param Str uri		Uri to call
# @param Str method		HTTP Method to use
# @param Dict data		Data to pass in the request
#
# @return Response
##
async def makeHttpRequest(uri, method = "get", data = {}):
	headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 OPR/120.0.0.0'}

	# Make request
	if (method == "get"):
		return requests.get(uri, headers=headers)

	return requests.post(uri, headers=headers)

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5000, debug=True)
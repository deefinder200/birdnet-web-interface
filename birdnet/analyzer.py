##
# Birdnet Analyzer
#
# CLI Usage: $ python analyzer.py 43.0 -89.4 1760142984 /data/sound-1-quiet.wav
##
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer
from datetime import datetime
import sys

def getBirdNetDetections(filepath, lat, lon, unix_timestamp):
	date = datetime.fromtimestamp(unix_timestamp)

	analyzer = Analyzer()

	recording = Recording(
		analyzer,
		filepath,
		lat=lat,
		lon=lon,
		date=date, # use date or week_48
		min_conf=0.25,
		overlap=0.5
	)

	recording.analyze()
	return recording.detections

if __name__ == "__main__":
	if len(sys.argv) < 5:
		print("Please provide the following: python analyzer.py {lat} {lon} {unixtime timestamp} {path to file}")
	else:
		lat = sys.argv[1]
		lon = sys.argv[2]
		unix_timestamp = sys.argv[3]
		filepath = sys.argv[4]

		print(getBirdNetDetections(filepath, lat, lon, unix_timestamp))
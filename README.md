# iNaturalist Audio Identifier with Birdnet
Docker container for a web interface to run Birdnet on iNaturalist observations.

# Installation
1. Build docker container
	* $ docker build -t birdnetapi -f birdnet/dockerfile .

2. Run docker container
	* $ docker run -p 4333:5000 -v ./birdnet:/app birdnetapi python3 app.py
	* Access webapp by going to http://localhost:4333

# Helpful commands
* One-liner for updating Docker container
	* $ docker build -t birdnetapi -f birdnet/dockerfile .; echo ""; docker run -p 4333:5000 -v ./birdnet:/app birdnetapi python3 app.py

# Files
* birdnet/app.py: App file that runs the Flask app
* birdnet/analzyer.py: File that runs the BirdNet analyzer
* birdnet/temp/*: Temporary folder where recordings will be stored. They will be deleted after running analyzer.
* birdnet/templates/: Where Flask templates are stored
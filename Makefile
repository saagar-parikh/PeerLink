build:
	pip install -r requirements.txt
	apt-get update -y
	apt-get install -y psmisc
	
	find . -type d -name "__pycache__" -exec rm -rf {} +
	echo "Nothing to be built"
test:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	python3 test.py -v
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
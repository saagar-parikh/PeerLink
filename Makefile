build:
	pip install -r requirements.txt
	echo "Nothing to be built"
test:
	python3 test.py -v
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
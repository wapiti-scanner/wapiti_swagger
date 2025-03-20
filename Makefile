release:
	rm -rf dist build *.egg-info
	python -m build --sdist --wheel
	
test:
	pytest -vv tests/

style:
	pip install -e .
	pylint wapiti_swagger/ tests/
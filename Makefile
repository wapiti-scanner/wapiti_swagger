release:
	rm -rf dist build *.egg-info
	python -m build --sdist --wheel
	

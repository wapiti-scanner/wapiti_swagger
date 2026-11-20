IMAGE_NAME_DEB ?= debian:testing
IMAGE_NAME_RPM ?= fedora:41

# Default target when running `make`
all: format lint test

release:
	@echo "--- Building release artifacts ---"
	rm -rf dist build *.egg-info
	python -m build --sdist --wheel

# Build Debian package (.deb) using Docker
deb: release
	@echo "--- Building Debian package in Docker (${IMAGE_NAME_DEB}) ---"
	@mkdir -p build/deb
	# Copy sdist to the build dir (needed by the container)
	cp dist/*.tar.gz build/deb/

	# Run the build inside a Debian container
	docker run --rm \
		-v $(PWD):/app \
		-w /app/build/deb \
		${IMAGE_NAME_DEB} /bin/bash -c "set -e; \
			apt update && apt install -y build-essential debhelper python3 python3-setuptools python3-dev dh-python pybuild-plugin-pyproject fakeroot; \
			tar -xzf *.tar.gz --strip 1; \
			cp -r /app/packaging/debian ./debian; \
			rm -f ./debian/compat; \
			dpkg-buildpackage -us -uc -b; \
		"
	@echo "--- Debian package generated successfully ---"

# Build RPM package (.rpm) using Docker
rpm: release
	@echo "--- Building RPM package in Docker (${IMAGE_NAME_RPM}) ---"
	rm -rf build/rpm
	mkdir -p build/rpm/BUILD
	mkdir -p build/rpm/RPMS
	mkdir -p build/rpm/SOURCES
	mkdir -p build/rpm/SPECS
	mkdir -p build/rpm/SRPMS
	# Copy source tarball
	cp dist/*.tar.gz build/rpm/SOURCES/
	cp dist/*.whl build/rpm/SOURCES/
	cp packaging/wapiti-swagger.spec build/rpm/SPECS/
	docker run --rm \
		-v $(PWD):/app \
		-w /app \
		${IMAGE_NAME_RPM} /bin/bash -c "set -e; \
		dnf update -y && \
		dnf install -y rpm-build python3-devel pyproject-rpm-macros python3-setuptools python3-wheel && \
		rpmbuild --define '_topdir /app/build/rpm' -ba /app/build/rpm/SPECS/wapiti-swagger.spec"
	@echo "--- RPM package generated in build/rpm/RPMS/ ---"
	
test:
	@echo "--- Running tests with coverage ---"
	pytest -vv tests/

publish: release
	@echo "--- Publishing package to PyPI ---"
	twine upload dist/*

# Format code using black
format:
	@echo "--- Formatting code ---"
	black wapiti_swagger tests

# Lint code using pylint
lint:
	@echo "--- Linting code ---"
	pylint wapiti_swagger tests

# Clean Python build and test artifacts
clean:
	@echo "--- Cleaning build and test artifacts ---"
	rm -rf dist .pytest_cache .coverage
	find . -name __pycache__ -type d -not -path './.git/*' -prune -exec rm -rf {} +

# Clean everything, including packaging artifacts
clean-all: clean
	@echo "--- Cleaning all packaging artifacts ---"
	rm -rf build
	rm -rf *.egg-info

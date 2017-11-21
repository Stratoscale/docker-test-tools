# *** WARNING: Targets are meant to run in a build container - Use skipper make ***

# Get docker api version and set the compose file version accordingly
DOCKER_API_VERSION = $(shell python docker_test_tools/api_version.py)
COMPOSE_FILE_VERSION = $(shell python -c 'print("2.1" if "$(DOCKER_API_VERSION)" >= "1.24" else "2")')
DTT_COMPOSE_PATH=tests/resources/docker-compose-v$(COMPOSE_FILE_VERSION).yml

all: coverage nose2 pytest dist/docker-test-tools-*.tar.gz

flake8:
	flake8 docker_test_tools

pylint:
	mkdir -p build/
	PYLINTHOME=reports/ pylint -r n docker_test_tools

test:
	# Run the unittests and create a junit-xml report
	mkdir -p build/
	nose2 --config=tests/ut/nose2.cfg --verbose --project-directory .

coverage: test
	# Create a coverage report and validate the given threshold
	coverage html --fail-under=84 -d build/coverage

nose2:
	mkdir -p build/

	# Run the example nose2 tests - validate the package works
	DTT_COMPOSE_PATH=$(DTT_COMPOSE_PATH) \
	nose2 --config=tests/integration/nose2.cfg --verbose --project-directory .

pytest:
	mkdir -p build/

	# Run the example pytest tests - validate the package works
	DTT_COMPOSE_PATH=$(DTT_COMPOSE_PATH) \
	pytest -v tests/integration/

dist/docker-test-tools-*.tar.gz:
	# Create the source distribution
	python setup.py sdist

clean:
	# Clean any generated files
	rm -rf build dist docker_test_tools.egg-info .coverage .cache

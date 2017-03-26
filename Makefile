# *** WARNING: Targets are meant to run in a build container - Use skipper make ***

# Local Docker version
DOCKER_VERSION = $(shell docker version --format '{{.Server.Version}}')

ifneq ($(filter $(DOCKER_VERSION),1.6.0 1.7.0 1.8.0 1.9.0 1.10.0 1.11.0),)
# Docker version doesn't supports health checks (<1.12.0)
DTT_COMPOSE_PATH=tests/resources/docker-compose-v2.yml
else
# Docker version supports health checks (>=1.12.0)
DTT_COMPOSE_PATH=tests/resources/docker-compose.yml
endif

all: coverage nose2 pytest dist/docker-test-tools-*.tar.gz

test:
	# Run the unittests and create a junit-xml report
	mkdir -p build/
	nose2 --config=tests/ut/nose2.cfg --verbose --project-directory .

coverage: test
	# Create a coverage report and validate the given threshold
	coverage html --fail-under=90 -d build/coverage

nose2:
	mkdir -p build/

	# Run the example nose2 tests - validate the package works
	CONFIG=tests/nose2/nose2.cfg  DTT_COMPOSE_PATH=$(DTT_COMPOSE_PATH) \
	nose2 --config=tests/nose2/nose2.cfg --verbose --project-directory .

pytest:
	mkdir -p build/

	# Run the example pytest tests - validate the package works
	CONFIG=tests/pytest/pytest.cfg DTT_COMPOSE_PATH=$(DTT_COMPOSE_PATH)  pytest -v tests/pytest/

dist/docker-test-tools-*.tar.gz:
	# Create the source distribution
	python setup.py sdist

clean:
	# Clean any generated files
	rm -rf build dist docker_test_tools.egg-info .coverage .cache
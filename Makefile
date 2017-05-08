# *** WARNING: Targets are meant to run in a build container - Use skipper make ***

# Get local Docker version - use a default value in case of failure
DOCKER_VERSION = $(shell docker version --format '{{.Server.Version}}' || echo 1.10.0)

ifeq "1.12.0" "$(word 1, $(sort 1.12.0 $(DOCKER_VERSION)))"
# Docker version supports health checks (>=1.12.0)
DTT_COMPOSE_PATH=tests/resources/docker-compose.yml
else
# Docker version doesn't supports health checks (<1.12.0)
DTT_COMPOSE_PATH=tests/resources/docker-compose-v2.yml
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
	CONFIG=tests/integration/nose2.cfg DTT_COMPOSE_PATH=$(DTT_COMPOSE_PATH) \
	nose2 --config=tests/integration/nose2.cfg --verbose --project-directory .

pytest:
	mkdir -p build/

	# Run the example pytest tests - validate the package works
	CONFIG=tests/integration/pytest.cfg DTT_COMPOSE_PATH=$(DTT_COMPOSE_PATH)  pytest -v tests/integration/

dist/docker-test-tools-*.tar.gz:
	# Create the source distribution
	python setup.py sdist

clean:
	# Clean any generated files
	rm -rf build dist docker_test_tools.egg-info .coverage .cache

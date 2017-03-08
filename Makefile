# *** WARNING: Targets are meant to run in a build container - Use skipper make ***

all: coverage nose2 pytest dist/docker-test-tools-*.tar.gz

test:
	# Run the unittests and create a junit-xml report
	mkdir -p build/
	nose2 --config=tests/ut/nose2.cfg --verbose --project-directory .

coverage: test
	# Create a coverage report and validate the given threshold
	coverage html --fail-under=90 -d build/coverage

nose2:
	# Run the example nose2 tests - validate the package works
	mkdir -p build/
	CONFIG=tests/nose2_example/nose2.cfg \
	nose2 --config=tests/nose2_example/nose2.cfg --verbose --project-directory .

pytest:
	# Run the example pytest tests - validate the package works
	CONFIG=tests/pytest_example/env.cfg pytest tests/pytest_example/

dist/docker-test-tools-*.tar.gz:
	# Create the source distribution
	python setup.py sdist

clean:
	# Clean any generated files
	rm -rf build dist docker_test_tools.egg-info .coverage .cache
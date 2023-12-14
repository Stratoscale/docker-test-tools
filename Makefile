all: py27 py3

py27:
	# Run the internal make file using python 2.7 container
	skipper --build-container-image=py27-build make

py3:
	# Run the internal make file using python 3.6 container
	skipper --build-container-image=py3-build make

clean:
	# Clean any generated files
	rm -rf build dist docker_test_tools.egg-info .coverage .cache
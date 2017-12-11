all: py27 py36

py27:
	# Run the internal make file using python 2.7 container
	skipper --build-container-image=py27-build make

py36:
	# Run the internal make file using python 3.6 container
	skipper --build-container-image=py36-build make

clean:
	# Clean any generated files
	rm -rf build dist docker_test_tools.egg-info .coverage .cache
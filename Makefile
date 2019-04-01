build:
	python3 setup.py sdist bdist_wheel

clean-build:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info

.PHONY: build

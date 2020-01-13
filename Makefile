.PHONY: setup install remove build clean

setup:
	pip install -r requirements.txt

install:
	pip install --user dist/batchren-0.7.0-py3-none-any.whl

remove:
	pip uninstall batchren

build:
	python3 setup.py sdist bdist_wheel

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info

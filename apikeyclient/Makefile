.DEFAULT_GOAL := build

.PHONY: clean build
clean:
	find . -type d -name __pycache__ -exec rm -r {} \+
	rm -rf build dist

build: clean
	python -m build --sdist --wheel .

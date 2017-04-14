.PHONY: build
build: clean
	python setup.py sdist

.PHONY: clean
clean:
	rm -rf *.egg-info dist

.PHONY: install
install: build
	pip install dist/*.tar.gz

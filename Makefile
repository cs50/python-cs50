.PHONY: build
build: clean
	python setup.py sdist

.PHONY: clean
clean:
	rm -rf *.egg-info dist

.PHONY: install
install: build
	pip install dist/*.tar.gz

.PHONY: push
push:
	git push origin "v$$(python setup.py --version)"

.PHONY: release
release: tag push

.PHONY: tag
tag:
	git tag "v$$(python setup.py --version)"

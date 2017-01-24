BUILD_DIR := build
LIB_DIR := $(BUILD_DIR)/usr/lib
PYTHON2_DIR := $(LIB_DIR)/python2.7/dist-packages/cs50
PYTHON3_DIR := $(LIB_DIR)/python3/dist-packages/cs50
DESCRIPTION := CS50 Library for Python
MAINTAINER := CS50 <sysadmins@cs50.harvard.edu>
NAME := python-cs50
OLD_NAME := lib50-python
VERSION := 1.2.4

.PHONY: bash
bash:
	docker run -i --rm -t -v "$(PWD)":/root cs50/cli

.PHONY: build
build: clean
	mkdir -p "$(PYTHON2_DIR)" "$(PYTHON3_DIR)"
	find "$(PYTHON2_DIR)" "$(PYTHON3_DIR)" -maxdepth 0 -exec cp src/* {} \;
	chmod -R a+rX "$(PYTHON2_DIR)" "$(PYTHON3_DIR)"

.PHONY: clean
clean:
	rm -rf "$(BUILD_DIR)"

.PHONY: deb
deb: build
	fpm \
	-C "$(BUILD_DIR)" \
	-m "$(MAINTAINER)" \
	-n "$(NAME)" \
	-p "$(BUILD_DIR)" \
	-s dir \
	-t deb \
	-v "$(VERSION)" \
	--after-install after-install.sh \
	--conflicts "$(NAME) (<< $(VERSION)), $(OLD_NAME)" \
	--deb-no-default-config-files \
	--depends python \
	--depends python3 \
	--description "$(DESCRIPTION)" \
	--replaces "$(NAME) (<= $(VERSION)), $(OLD_NAME)" \
	--provides "$(NAME)" \
	--provides "$(OLD_NAME)" \
	usr

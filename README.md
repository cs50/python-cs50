# CS50 Library for Python

[![Build Status](https://travis-ci.org/cs50/python-cs50.svg?branch=master)](https://travis-ci.org/cs50/python-cs50)

Supports Python 2 and Python 3.

## Development

Requires [Docker Engine](https://docs.docker.com/engine/installation/).

    make bash
    make deb # builds .deb

## Installation

1. Download the latest release per https://github.com/cs50/python-cs50/releases
1. Extract `python-cs50-*`
1. `cd python-cs50-*`
1. `make install`

## Usage

    import cs50

    ...

    c = cs50.get_char();
    f = cs50.get_float();
    i = cs50.get_int();
    l = cs50.get_long(); # Python 2 only
    s = cs50.get_string();

## TODO

* Add install target to Makefile.
* Conditionally install for Python 2 and/or Python 3.
* Add targets for `pacman`, `rpm`.
* Add tests.

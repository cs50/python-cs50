# CS50 Library for Python

Supports Python 2 and Python 3.

## Development

Requires [Docker Engine](https://docs.docker.com/engine/installation/).

    make bash
    make deb # builds .deb

## Installation

1. Download the latest release per https://github.com/cs50/lib50-python/releases
1. Extract `lib50-python-*`
1. `cd lib50-python-*`
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

* Add comments.
* Conditionally install for Python 2 and/or Python 3.
* Add targets for `pacman`, `rpm`.
* Add tests.

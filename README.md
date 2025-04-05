# CS50 Library for Python

## Installation

```
pip3 install cs50
```

## Usage

```
import cs50

...

f = cs50.get_float();
i = cs50.get_int();
s = cs50.get_string();
```

## Testing

1. In one terminal, execute:

    ```
    cd python-cs50
    docker compose build
    docker compose up
    ```

1. In another terminal, execute:

    ```
    docker exec -it python-cs50 bash -l
    ```

    And then execute, e.g.:

    ```
    python tests/sql.py
    ```

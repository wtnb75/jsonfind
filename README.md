# JSON(python dict) finder

## Install

- pip install jsonfind

## CLI

```
# jsonfind
Usage: jsonfind [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  find-any
  find-by
  find-eq
  find-is
  find-key
  find-regex
  find-subset

# jsonfind find-any --help
Usage: jsonfind find-any [OPTIONS] [OBJ]

Options:
  --verbose / --no-verbose
  --target TEXT                   query(JSON string)  [required]
  --format [jsonpath|jsonpointer]
  --key [eq|is|in1|in2|match|sub|eval|fnmatch|range]
  --value [eq|is|in1|in2|match|sub|eval|fnmatch|range]
  --mode [sub|super|set]
  --help                          Show this message and exit.
```

- jo hello=world a=$(jo b=$(jo c=d))
    - `{"hello":"world","a":{"b":{"c":"d"}}}`
- jo hello=world a=$(jo b=$(jo c=d)) | jsonfind find-eq --target $(jo c=d) --format jsonpointer
    - `["/a/b"]`
- jo hello=world a=$(jo b=$(jo c=d)) | ./bin/jsonfind find-eq --target $(jo c=d) --format jsonpath
    - `["a.b"]`
- jo hello=world a=$(jo b=$(jo c=d)) | ./bin/jsonfind find-by --format jsonpointer --query /a/b
    - `{"c": "d"}`
- jo hello=world a=$(jo b=$(jo c=d)) | ./bin/jsonfind find-by --format jsonpath --query a.b
    - `[{"c": "d"}]`

## Python

```
>>> from jsonfind import JsonFind
>>> obj = {"a":"b","c":{"d":"e"}}
>>> tgt = obj["c"]
>>> JsonFind.to_jsonpointer(JsonFind.find_eq(obj, tgt))
'/c'
>>> JsonFind.to_jsonpath(JsonFind.find_eq(obj, tgt))
'c'
```

# links

- [pypi repository](https://pypi.org/project/jsonfind/)
- [coverage report](https://wtnb75.github.io/jsonfind/)
- [local pypi repository](https://wtnb75.github.io/jsonfind/dist/)

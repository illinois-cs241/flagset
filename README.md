# FlagSet
[![Build Status](https://travis-ci.com/illinois-cs241/flagset.svg?branch=master)](https://travis-ci.com/illinois-cs241/flagset)
[![Coverage Status](https://coveralls.io/repos/github/illinois-cs241/flagset/badge.svg?branch=master)](https://coveralls.io/github/illinois-cs241/flagset?branch=master)
![License](https://img.shields.io/badge/license-NCSA%2FIllinois-blue.svg)
![Python Versions](https://img.shields.io/badge/python-3.5%2B-blue.svg)

A Python module for managing flags across environment variables, commandline arguments, and configuration files

## Dependencies

See `requirements_test.txt` for test dependencies
The package itself doesn't have any dependencies on third-party packages

## Usage

```
pip install git+https://github.com/illinois-cs241/flagset
```

Create a FlagSet object
```
fset = FlagSet(
    {
        "debug": Flag(
            bool,
            default=False,
            cmdline_name=["-d", "--debug"],
            help="enable debug mode",
        ),
        "token": Flag(
            str,
            required=True,
            cmdline_name="--token",
            help="access token",
        ),
        "bind_addr": Flag(
            str,
            default="localhost:8080",
            cmdline_name="--bind-addr",
            env_name="BIND_ADDR",
            help="web app bind address",
        ),
        "mongodb_dsn": Flag(
            str,
            default="mongodb://localhost:27017",
            config_name="some.path.in.the.config",
            help="mongodb",
        ),
    }
)
```

Then parse the given flags and config(args defaults to `sys.argv[1:]` and env defaults to `os.environ`)
```
config = fset.parse(args=[...], env={...}, ...)
```

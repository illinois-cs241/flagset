import os
import sys
import json
import argparse


class _ArgumentParserWithException(argparse.ArgumentParser):
    def error(self, msg):
        raise FlagParseError(msg)

    def print_help(self, file=None):
        raise FlagHelp()


class FlagParseError(Exception):
    pass


class FlagHelp(Exception):
    pass


class JSONFileParser:
    def __init__(self, path):
        with open(path) as f:
            self.obj = json.loads(f.read())

    def get(self, name):
        """
        :param name: name can be in the format of <top level key>.<2nd level key>.[...]
        """

        path = []
        cur = self.obj

        for key in name.split("."):
            path.append(key)

            if key not in cur:
                return None

            cur = cur[key]

        return cur


class Flag:
    def __init__(
        self,
        type=str,
        cmdline_name=None,
        env_name=None,
        config_name=None,
        default=None,
        help=None,
        required=False,
    ):
        """
        :param type: type should be a function from str to desired type of the flag
        """

        assert (
            cmdline_name is not None or env_name is not None or config_name is not None
        ), "expecting at least one flag name"

        assert (
            default is None or not required
        ), "cannot provide default value for required flag"

        self.type = type
        self.cmdline_name = cmdline_name
        self.env_name = env_name
        self.config_name = config_name
        self.default = default
        self.help = help
        self.required = required
        self.positional = isinstance(cmdline_name, str) and not cmdline_name.startswith(
            "-"
        )

    def _parse_env(self, env):
        if self.env_name is not None and self.env_name in env:
            v = env.get(self.env_name, None)
            return self.type(v) if v is not None else None

        return None

    def _bind_argparser(self, parser, dest=None):
        """
        bind the flag to an argparser

        :param dest: destination namespace field
        """

        kwargs = {}

        if dest is not None and not self.positional:
            kwargs["dest"] = dest

        # help message: <help>[. default value '<default>'][. env var '<env>']
        kwargs["help"] = self.help if self.help is not None else ""

        if self.default is not None:
            default_msg = "{}default value '{}'".format(
                ". " if kwargs["help"] != "" else "", self.default
            )

            kwargs["help"] += default_msg

        if self.env_name is not None:
            env_msg = "{}environment variable ${}".format(
                ". " if kwargs["help"] != "" else "", self.env_name
            )

            kwargs["help"] += env_msg

        if self.config_name is not None:
            config_msg = "{}config variable '{}'".format(
                ". " if kwargs["help"] != "" else "", self.config_name
            )

            kwargs["help"] += config_msg

        # allowed usages of boolean flags:
        # 1. --flag [t|true|yes|...|f|false|no|...]
        # 2. --flag
        if self.type is not bool:
            kwargs["type"] = self.type
        else:
            kwargs["type"] = _str2bool
            kwargs["nargs"] = "?"
            kwargs["const"] = True  # if used as --flag, true is stored

        if isinstance(self.cmdline_name, list):
            parser.add_argument(*self.cmdline_name, **kwargs)
        elif isinstance(self.cmdline_name, str):
            parser.add_argument(self.cmdline_name, **kwargs)

    def _name(self):
        """
        get a user friendly name
        """
        if isinstance(self.cmdline_name, list):
            return "flag {}".format("/".join(self.cmdline_name))
        elif isinstance(self.cmdline_name, str):
            return "flag {}".format(self.cmdline_name)
        elif self.env_name is not None:
            return "environment variable ${}".format(self.env_name)
        elif self.config_name is not None:
            return "config variable '{}'".format(self.config_name)

        return None


class FlagSet:
    """
    a flag consists of:
        2. a type
        3. at least one of the following sources:
          a. cmdline_name(first argument to ArgumentParser.add_argument, list or str)
          b. env_name
          c. config_name
        4. optional default value(if not provided, then required)
        5. optional help message
    """

    def __init__(self, init_set={}):
        """
        :params config_parser: should take a string and return dict
        """
        self.flags = init_set

    def add_flag(self, name, *args, **kwargs):
        assert name not in self.flags, "flag '{}' already exists".format(name)
        self.flags[name] = Flag(*args, **kwargs)

    def _parse_cmdline(self, args):
        """
        returns a dict {
            "<canonical name>": None or parsed value
        }
        """

        res = {}

        parser = _ArgumentParserWithException(add_help=False)
        parser.add_argument("--help", "-h", dest="__help", action="help", default=False)

        for canon, flag in self.flags.items():
            res[canon] = None

            if flag.cmdline_name is not None:
                flag._bind_argparser(parser, canon)

        # bind config flag last
        parser.add_argument("__config", nargs="?")

        parsed = vars(parser.parse_args(args))

        for canon, flag in self.flags.items():
            if (
                flag.positional
                and flag.cmdline_name in parsed
                and canon != flag.cmdline_name
            ):
                parsed[canon] = parsed[flag.cmdline_name]
                del parsed[flag.cmdline_name]

        for canon in res:
            if canon in parsed:
                res[canon] = parsed[canon]

        return res, parsed["__config"]

    def _parse_env(self, env):
        return {canon: flag._parse_env(env) for canon, flag in self.flags.items()}

    def _parse_config(self, parser):
        res = {}

        for canon, flag in self.flags.items():
            res[canon] = None

            if flag.config_name is not None:
                res[canon] = parser.get(flag.config_name)

        return res

    def parse(
        self,
        args=sys.argv[1:],
        env=os.environ,
        config_parser=JSONFileParser,
        use_exc=False,
        help_output_file=sys.stderr,
    ):
        try:
            cmdline_args, config_path = self._parse_cmdline(args)
            env_args = self._parse_env(env)

            if config_path is not None:
                config_args = self._parse_config(config_parser(config_path))
            else:
                config_args = {}

            # merge all args
            args = _remove_none(config_args)
            args.update(_remove_none(env_args))
            args.update(_remove_none(cmdline_args))

            # set defaults
            for canon, flag in self.flags.items():
                if canon not in args:
                    if flag.required:
                        raise FlagParseError(
                            "{} is required but not given".format(flag._name())
                        )
                    else:
                        args[canon] = flag.default

            return args

        except FlagParseError as e:
            if use_exc:
                raise e from None
            else:
                self.print_help(help_output_file)
                print("\nerror: {}".format(str(e)), file=help_output_file)
                sys.exit(2)

        except FlagHelp:
            self.print_help(help_output_file)

            if not use_exc:
                sys.exit(0)

    def print_help(self, file=sys.stderr):
        parser = argparse.ArgumentParser()

        for flag in self.flags.values():
            flag._bind_argparser(parser)

        parser.add_argument("config", nargs="?", help="config file")

        parser.print_help(file)

        # show other flags
        if {f for f in self.flags.values() if f.cmdline_name is None}:
            print("\nother arguments:", file=sys.stderr)
            for flag in self.flags.values():
                if flag.cmdline_name is None:
                    if flag.help:
                        print(
                            "  {}: {}".format(flag._name(), flag.help), file=sys.stderr
                        )
                    else:
                        print("  {}".format(flag._name()), file=sys.stderr)


def _str2bool(v):
    if v.lower() in ["t", "true", "y", "yes", "1"]:
        return True
    elif v.lower() in ["f", "false", "n", "no", "0"]:
        return False
    else:
        raise argparse.ArgumentTypeError("expecting boolean value")


def _remove_none(d):
    return {k: v for k, v in d.items() if v is not None}

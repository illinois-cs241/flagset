import unittest

from flagset import Flag, FlagSet, FlagParseError


class TestError(unittest.TestCase):
    def test_parse_error(self):
        fset = FlagSet()
        fset.add_flag("test_int", int, cmdline_name="--test-int")

        with self.assertRaises(FlagParseError):
            fset.parse(["--test-int", "a"], use_exc=True)

    def test_undefined_flag(self):
        fset = FlagSet()

        with self.assertRaises(FlagParseError):
            fset.parse(["--no-such-flag"], use_exc=True)

    def test_require(self):
        fset = FlagSet({"required": Flag(cmdline_name="-r", required=True)})

        with self.assertRaises(FlagParseError):
            fset.parse([], use_exc=True)

    def test_constraint(self):
        with self.assertRaises(AssertionError):
            FlagSet({"required": Flag(cmdline_name="-r", required=True, default="no")})

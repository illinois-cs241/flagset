import unittest

from flagset import Flag, FlagSet


class TestBasic(unittest.TestCase):
    def test_basic(self):
        fset = FlagSet(
            {
                "test_str": Flag(str, cmdline_name="--test-str"),
                "test_bool": Flag(bool, cmdline_name=["--test-bool", "-b"]),
                "test_int": Flag(int, cmdline_name="--test-int"),
                "test_float": Flag(
                    float, cmdline_name="--test-float", env_name="TEST_FLOAT"
                ),
                "test_nothing": Flag(default="hey", cmdline_name="-c"),
            }
        )

        flags = fset.parse(["--test-str", "hi", "--test-bool"], use_exc=True)
        self.assertEqual(flags["test_str"], "hi")
        self.assertTrue(flags["test_bool"])
        self.assertEqual(flags["test_nothing"], "hey")

        flags = fset.parse(["--test-bool", "false"], use_exc=True)
        self.assertFalse(flags["test_bool"])

        flags = fset.parse(["-b"], use_exc=True)
        self.assertTrue(flags["test_bool"])

        flags = fset.parse(["--test-int", "1000", "--test-float", "1.0"], use_exc=True)
        self.assertEqual(flags["test_int"], 1000)
        self.assertEqual(flags["test_float"], 1.0)

        flags = fset.parse([], env={"TEST_FLOAT": "1.1"})
        self.assertEqual(flags["test_float"], 1.1)

    def test_config(self):
        fset = FlagSet()
        fset.add_flag("test_str", str, config_name="well_.this_is.really.a.path")
        fset.add_flag("not_found", str, config_name="does.not.exist")

        flags = fset.parse(["tests/_fixture/config1.json"], use_exc=True)
        self.assertEqual(flags["test_str"], "hey")
        self.assertEqual(flags["not_found"], None)

    def test_precedence(self):
        fset = FlagSet(
            {"flag": Flag(cmdline_name="--flag", env_name="FLAG", config_name="flag")}
        )

        # cmdline flag > env
        flags = fset.parse(
            args=["--flag", "from cmd"], env={"FLAG": "from env"}, use_exc=True
        )
        self.assertEqual(flags["flag"], "from cmd")

        # 　env > config file
        flags = fset.parse(
            args=["tests/_fixture/config2.json"], env={"FLAG": "from env"}, use_exc=True
        )
        self.assertEqual(flags["flag"], "from env")

        # 　cmdline flag > config file
        flags = fset.parse(
            args=["--flag", "from cmd", "tests/_fixture/config2.json"],
            env={"FLAG": "from env"},
            use_exc=True,
        )
        self.assertEqual(flags["flag"], "from cmd")

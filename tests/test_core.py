import os
import unittest

from environment_variable_string_expander import expand, expand_with_mapping, ExpansionError


class TestSimple(unittest.TestCase):
    def test_plain_string(self):
        self.assertEqual(expand_with_mapping("hello", {}), "hello")

    def test_empty_string(self):
        self.assertEqual(expand_with_mapping("", {}), "")

    def test_dollar_alone_at_end(self):
        self.assertEqual(expand_with_mapping("price: $", {}), "price: $")

    def test_double_dollar_at_end(self):
        self.assertEqual(expand_with_mapping("$$", {}), "$$")

    def test_dollar_then_non_name(self):
        # $ followed by lowercase is not a var reference; $ is literal.
        self.assertEqual(expand_with_mapping("cost is $5", {}), "cost is $5")


class TestDollarName(unittest.TestCase):
    def test_simple_var(self):
        self.assertEqual(expand_with_mapping("$FOO", {"FOO": "bar"}), "bar")

    def test_var_in_middle(self):
        self.assertEqual(
            expand_with_mapping("x=$FOO/y", {"FOO": "bar"}), "x=bar/y"
        )

    def test_unset_var_empty(self):
        self.assertEqual(expand_with_mapping("[$MISSING]", {}), "[]")

    def test_adjacent_vars(self):
        self.assertEqual(
            expand_with_mapping("$A$B", {"A": "1", "B": "2"}), "12"
        )

    def test_var_prefix_only(self):
        # Only uppercase/underscore counts as the name.
        self.assertEqual(
            expand_with_mapping("$FOO_bar", {"FOO": "x"}), "bar"
        )


class TestBraces(unittest.TestCase):
    def test_braced_var(self):
        self.assertEqual(expand_with_mapping("${FOO}", {"FOO": "bar"}), "bar")

    def test_braces_disambiguate(self):
        self.assertEqual(
            expand_with_mapping("${FOO}bar", {"FOO": "x"}), "xbar"
        )

    def test_empty_braces_error(self):
        with self.assertRaises(ExpansionError):
            expand_with_mapping("${}", {})

    def test_unclosed_brace_error(self):
        with self.assertRaises(ExpansionError):
            expand_with_mapping("${FOO", {})

    def test_invalid_char_in_braces(self):
        with self.assertRaises(ExpansionError):
            expand_with_mapping("${FOO+bar}", {})


class TestDefaults(unittest.TestCase):
    def test_default_when_unset(self):
        self.assertEqual(
            expand_with_mapping("${MISSING:-default}", {}), "default"
        )

    def test_default_with_plain_dash(self):
        self.assertEqual(expand_with_mapping("${MISSING-default}", {}), "default")

    def test_default_not_used_when_set(self):
        self.assertEqual(
            expand_with_mapping("${FOO:-default}", {"FOO": "x"}), "x"
        )

    def test_default_with_special_chars(self):
        self.assertEqual(
            expand("${MISSING:-/usr/bin}"), "/usr/bin"
        )

    def test_default_empty(self):
        self.assertEqual(expand_with_mapping("${MISSING:-}", {}), "")

    def test_invalid_colon_no_dash(self):
        with self.assertRaises(ExpansionError):
            expand_with_mapping("${FOO:bar}", {})

    def test_unclosed_default(self):
        with self.assertRaises(ExpansionError):
            expand_with_mapping("${FOO:-default", {})


class TestTypes(unittest.TestCase):
    def test_int_value_in_mapping(self):
        self.assertEqual(expand_with_mapping("$N", {"N": 42}), "42")

    def test_float_value_in_mapping(self):
        self.assertEqual(expand_with_mapping("$N", {"N": 3.5}), "3.5")

    def test_non_str_text_raises(self):
        with self.assertRaises(TypeError):
            expand_with_mapping(123, {})

    def test_non_dict_mapping_raises(self):
        with self.assertRaises(TypeError):
            expand_with_mapping("$FOO", ["FOO"])


class TestExpandUsesOsEnviron(unittest.TestCase):
    def test_expand_reads_os_environ(self):
        os.environ["EXPANDER_TEST_VAR"] = "from-environ"
        try:
            self.assertEqual(expand("$EXPANDER_TEST_VAR"), "from-environ")
        finally:
            del os.environ["EXPANDER_TEST_VAR"]

    def test_expand_unset_in_environ(self):
        self.assertNotIn("EXPANDER_DEFINITELY_MISSING", os.environ)
        self.assertEqual(expand("[${EXPANDER_DEFINITELY_MISSING}]"), "[]")


if __name__ == "__main__":
    unittest.main()

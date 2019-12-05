import unittest
from jsonfind import JsonFind, format_list, find_format_list


class TestJsonFind1(unittest.TestCase):
    def test_format_list(self):
        self.assertIn("jsonpointer", format_list)
        self.assertIn("jsonpath", format_list)

    def test_find_format_list(self):
        self.assertIn("jsonpointer", find_format_list)
        self.assertIn("jsonpath", find_format_list)

    def test_JsonFind(self):
        self.assertEquals(["a"], JsonFind.find_is({"a": "b"}, "b"))

    def test_misc(self):
        obj = {"a": "b", "c": {"d": "e"}, "f": [1, 2, 3]}
        self.assertTrue(JsonFind.issubset(
            {"d": "e", "f": "g"}, {"f": "g"}), "fg")
        self.assertFalse(JsonFind.issubset(
            {"d": "e", "f": "g"}, {"f": "h"}), "fh")
        self.assertTrue(JsonFind.issubset([1, 2, 3, 4], [4, 2]), "42")
        self.assertFalse(JsonFind.issubset([1, 2, 3, 4], [4, 5]), "45")
        self.assertEquals(["c"], JsonFind.find_eq(obj, obj["c"]), "eq_c")
        self.assertEquals([["c"]], list(
            JsonFind.filter_eq(obj, obj["c"])), "eq_c1.1")
        self.assertEquals(["a"], JsonFind.find_eq(obj, obj["a"]), "eq_a")
        self.assertEquals(["c"], JsonFind.find_eq(obj, {"d": "e"}), "eq_c")
        self.assertEquals(["a"], JsonFind.find_eq(obj, "b"), "eq_a2")
        self.assertEquals(["c"], JsonFind.find_is(obj, obj["c"]), "is_c1")
        self.assertEquals(["a"], JsonFind.find_is(obj, obj["a"]), "is_a1")
        self.assertIsNone(JsonFind.find_is(obj, {"d": "e"}), "is_c2")
        self.assertEquals(["a"], JsonFind.find_is(obj, "b"), "is_a2")
        self.assertEquals("c", JsonFind.to_jsonpath(
            JsonFind.find_eq(obj, obj["c"])), "eq_c(jsonpath)")
        self.assertEquals("/c", JsonFind.to_jsonpointer(
            JsonFind.find_eq(obj, obj["c"])), "eq_c(jsonptr)")
        one = JsonFind.find_eq(obj, 1)
        self.assertEquals("f[0]", JsonFind.to_jsonpath(one), "one(jsonpath)")
        self.assertEquals("/f/0", JsonFind.to_jsonpointer(one), "one(jsonptr)")

    def test_findkey(self):
        obj = {"a": "b", "c": {"d": "e"}, "f": [1, 2, 3]}
        self.assertEquals(JsonFind.find_key(obj, ["d"]), ["c", "d"])
        self.assertEquals(JsonFind.find_key(obj, ["c", "d"]), ["c", "d"])
        self.assertIsNone(JsonFind.find_key(obj, ["f", "d"]))

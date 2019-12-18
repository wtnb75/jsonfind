"""
>>> obj = {"a":"b","c":{"d":"e"}}
>>> tgt = obj["c"]
>>> JsonFind.to_jsonpointer(JsonFind.find_eq(obj, tgt))
'/c'
>>> JsonFind.to_jsonpath(JsonFind.find_eq(obj, tgt))
'c'
"""
import re
import fnmatch
from logging import getLogger
import jsonpointer
import jsonpath
try:
    import pyjq
except (ModuleNotFoundError, ImportError):
    pyjq = None
try:
    import jsonselect
except (ModuleNotFoundError, ImportError):
    jsonselect = None

log = getLogger(__name__)


def EQ(a, b):
    """
    >>> EQ(1, 2)
    False
    >>> EQ(1, 1)
    True
    >>> EQ("abc", "abc")
    True
    >>> EQ("abc", "def")
    False
    >>> EQ({"a":"b"}, {"a":"b"})
    True
    >>> EQ({"a":"b"}, {"a":"c"})
    False
    """
    return a == b


def IS(a, b):
    """
    >>> IS(1, 2)
    False
    >>> IS(1, 1)
    True
    >>> IS("abc", "abc")
    True
    >>> IS("abc", "def")
    False
    >>> IS({"a":"b"}, {"a":"b"})
    False
    >>> IS({"a":"b"}, {"a":"c"})
    False
    """
    return a is b


def IN1(a, b):
    """
    >>> IN1(1, [1,2,3])
    True
    >>> IN1([1,2,3], 1)
    False
    >>> IN1(1, [2,3])
    False
    >>> IN1("abc", "hello abc world")
    True
    >>> IN1("xyz", "hello abc world")
    False
    """
    try:
        return a in b
    except TypeError:
        return False


def IN2(a, b):
    """
    >>> IN2(1, [1,2,3])
    False
    >>> IN2([1,2,3], 1)
    True
    >>> IN2([2,3], 1)
    False
    >>> IN2("hello abc world", "abc")
    True
    >>> IN2("hello abc world", "xyz")
    False
    """
    try:
        return b in a
    except TypeError:
        return False


def compare_regexp(a, b):
    """
    >>> compare_regexp("abcde", "bcd")
    False
    >>> compare_regexp("abcde", "a[bcd]{3}e")
    True
    >>> compare_regexp("a,bcde", "[abcde,]*")
    True
    >>> compare_regexp("abcde", re.compile("bcd[ef]"))
    False
    >>> compare_regexp({"b":"abcde"}, "bcd[ef]")
    False
    """
    log.debug("compare(regexp) %s %s", a, b)
    if isinstance(a, str):
        if hasattr(b, "fullmatch"):
            return b.fullmatch(a) is not None
        elif isinstance(b, str):
            return re.fullmatch(b, a) is not None
    return EQ(a, b)


def compare_regexp_substr(a, b):
    """
    >>> compare_regexp_substr("abcde", "bcd")
    True
    >>> compare_regexp_substr("abcde", "bcdf")
    False
    >>> compare_regexp_substr("abcde", "bcd[ef]")
    True
    >>> compare_regexp_substr("abcde", re.compile("bcd[ef]"))
    True
    >>> compare_regexp_substr({"b":"abcde"}, "bcd[ef]")
    False
    """
    if isinstance(a, str):
        if hasattr(b, "search"):
            return b.search(a) is not None
        elif isinstance(b, str):
            return re.search(b, a) is not None
    return EQ(a, b)


def compare_fnmatch(a, b):
    """
    >>> compare_fnmatch("world", "worl?")
    True
    >>> compare_fnmatch("world", "word*")
    False
    >>> compare_fnmatch("world", "wor*d")
    True
    >>> compare_fnmatch("world", "?or??")
    True
    >>> compare_fnmatch("world", "?and?")
    False
    >>> compare_fnmatch(1, 2)
    False
    """
    if isinstance(a, str) and isinstance(b, str):
        return fnmatch.fnmatch(a, b)
    return EQ(a, b)


def compare_range(a, b):
    """
    >>> compare_range(1, "-10")
    True
    >>> compare_range(1, "10-")
    False
    >>> compare_range(20, "-10")
    False
    >>> compare_range(1, "10-20")
    False
    >>> compare_range(1.0, "0-1.0")
    True
    >>> compare_range(100, "-")
    True
    >>> compare_range("b", "a-z")
    True
    >>> compare_range("b", "b")
    True
    >>> compare_range("b", "a")
    False
    """
    if "-" not in b:
        return a == type(a)(b)
    bmin, bmax = b.split("-", 1)
    if bmin not in (None, "") and type(a)(bmin) > a:
        return False
    if bmax not in (None, "") and type(a)(bmax) < a:
        return False
    return True


def compare_eval(a, b):
    """
    >>> compare_eval(1, "x%2==1")
    True
    >>> compare_eval(1, "0<x/3 and x/3 <=1.0")
    True
    >>> compare_eval("xyz", "len(x)==3")
    True
    >>> compare_eval("xyz", 'hash(x)!=hash("xyz")')
    False
    >>> compare_eval("xyz", 'x[2]=="z"')
    True
    >>> compare_eval("xyzxyz", 'x[:int(len(x)/2)]==x[int(len(x)/2):]')
    True
    >>> compare_eval("xyzxyz123123", 'x[:int(len(x)/2)]==x[int(len(x)/2):]')
    False
    """
    return eval(b, {}, {"x": a})


def compare_subset(a, b, key_fn=EQ, val_fn=EQ):
    """
    >>> compare_subset({"a":"b", "c":{"d":"e"}}, {"a":"b"})
    True
    >>> compare_subset({"a":"b", "c":{"d":"e"}}, {"a":"c"})
    False
    >>> compare_subset({"a":"b", "c":{"d":"e"}}, {"a":"b", "c":"d"})
    False
    >>> compare_subset({"a":"b", "c":{"d":"e"}}, {})
    True
    >>> compare_subset([1,2,3], [1,3,5,2,4])
    False
    >>> compare_subset([1,2,3], [1,3])
    True
    """
    if isinstance(b, (list, tuple)) and isinstance(a, (list, tuple)):
        for ib in b:
            if not any(compare_subset(ia, ib, key_fn, val_fn) for ia in a):
                return False
        return True
    elif isinstance(b, dict) and isinstance(a, dict):
        for kb, vb in b.items():
            flag = False
            for ka, va in filter(lambda f: key_fn(f[0], kb), a.items()):
                if compare_subset(va, vb, key_fn, val_fn):
                    flag = True
                    break
            if not flag:
                return False
        return True
    return val_fn(a, b)


def compare_superset(a, b, key_fn=EQ, val_fn=EQ):
    """
    >>> compare_superset({"a":"b", "c":{"d":"e"}}, {"a":"b", "c":{"d":"e", "f":"g"}})
    True
    >>> compare_superset({"a":"b", "c":{"d":"e"}}, {"a":"b"})
    False
    >>> compare_superset({"a":"b", "c":{"d":"e"}}, {"a":"b", "c":"d"})
    False
    >>> compare_superset({"a":"b", "c":{"d":"e"}}, {})
    False
    >>> compare_superset({"a":"b"}, {"a":"b"})
    True
    >>> compare_superset({"a":"b"}, {"a":"b", "c":"d"})
    True
    >>> compare_superset([1,2,3], [1,3,5,2,4])
    True
    >>> compare_superset([1,2,3], [1,3])
    False
    """
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        for ia in a:
            if not any(compare_superset(ia, ib, key_fn, val_fn) for ib in b):
                return False
        return True
    elif isinstance(a, dict) and isinstance(b, dict):
        for ka, va in a.items():
            flag = False
            for kb, vb in filter(lambda f: key_fn(ka, f[0]), b.items()):
                if compare_superset(va, vb, key_fn, val_fn):
                    flag = True
                    break
            if not flag:
                return False
        return True
    return val_fn(a, b)


def compare_set(a, b, key_fn=EQ, val_fn=EQ):
    """
    >>> compare_set({"a":"b", "c":"d"}, {"a":"b", "c":"d"})
    True
    >>> compare_set({"a":"b", "c":"d"}, {"a":"b"})
    False
    >>> compare_set({"a":"b"}, {"a":"b", "c":"d"})
    False
    """
    return compare_subset(a, b, key_fn, val_fn) and compare_superset(a, b, key_fn, val_fn)


class JsonFind:

    @classmethod
    def get_children(cls, obj):
        if isinstance(obj, dict):
            return obj.items()
        elif isinstance(obj, (tuple, list)):
            return enumerate(obj)
        return []

    @classmethod
    def get_children_attr(cls, obj):
        """
        >>> class A: hello="world"
        >>> list(filter(lambda f: not f[0].startswith("_"), JsonFind.get_children_attr(A)))
        [('hello', 'world')]
        """
        return obj.__dict__.items()

    @classmethod
    def issubset(cls, obj, target):
        if isinstance(target, dict) and isinstance(obj, dict):
            if obj.items() >= target.items():
                return True
        elif isinstance(target, (list, tuple)) and isinstance(obj, (list, tuple)):
            if all(x in obj for x in target):
                return True
        return False

    @classmethod
    def filter_subset(cls, obj, target):
        if cls.issubset(obj, target):
            yield []
            return
        for k, v in cls.get_children(obj):
            for chld in cls.filter_subset(v, target):
                yield [k, *chld]
        return

    @classmethod
    def filter_eq(cls, obj, target):
        if obj == target:
            yield []
            return
        for k, v in cls.get_children(obj):
            for chld in cls.filter_eq(v, target):
                yield [k, *chld]
        return

    @classmethod
    def filter_is(cls, obj, target):
        if obj is target:
            yield []
            return
        for k, v in cls.get_children(obj):
            for chld in cls.filter_is(v, target):
                yield [k, *chld]
        return

    @classmethod
    def filter_compare(cls, obj, target, key_fn=IS, val_fn=IS):
        if compare_set(obj, target, key_fn, val_fn):
            log.debug("found %s %s", obj, target)
            yield []
            return
        log.debug("not-found %s %s", obj, target)
        for k, v in cls.get_children(obj):
            for chld in cls.filter_compare(v, target, key_fn, val_fn):
                yield [k, *chld]
        return

    @classmethod
    def filter_compare_subset(cls, obj, target, key_fn=IS, val_fn=IS):
        if compare_subset(obj, target, key_fn, val_fn):
            log.debug("found %s %s", obj, target)
            yield []
            return
        log.debug("not-found %s %s", obj, target)
        for k, v in cls.get_children(obj):
            for chld in cls.filter_compare_subset(v, target, key_fn, val_fn):
                yield [k, *chld]
        return

    @classmethod
    def filter_compare_superset(cls, obj, target, key_fn=IS, val_fn=IS):
        if compare_superset(obj, target, key_fn, val_fn):
            log.debug("found %s %s", obj, target)
            yield []
            return
        log.debug("not-found %s %s", obj, target)
        for k, v in cls.get_children(obj):
            for chld in cls.filter_compare_superset(v, target, key_fn, val_fn):
                yield [k, *chld]
        return

    @classmethod
    def filter_attr_eq(cls, obj, target):
        if obj == target:
            yield []
            return
        for k, v in cls.get_children_attr(obj):
            for chld in cls.filter_attr_eq(v, target):
                yield [k, *chld]
        return

    @classmethod
    def filter_attr_is(cls, obj, target):
        if obj is target:
            yield []
            return
        for k, v in cls.get_children_attr(obj):
            for chld in cls.filter_attr_is(v, target):
                yield [k, *chld]
        return

    @classmethod
    def filter_key(cls, obj, target, prev=[]):
        if prev[-len(target):] == target:
            yield []
            return
        for k, v in cls.get_children(obj):
            for chld in cls.filter_key(v, target, [*prev, k]):
                yield [k, *chld]
        return

    @classmethod
    def find_eq(cls, obj, target):
        return next(cls.filter_eq(obj, target), None)

    @classmethod
    def find_is(cls, obj, target):
        return next(cls.filter_is(obj, target), None)

    @classmethod
    def find_attr_eq(cls, obj, target):
        return next(cls.filter_attr_eq(obj, target), None)

    @classmethod
    def find_attr_is(cls, obj, target):
        return next(cls.filter_attr_is(obj, target), None)

    @classmethod
    def find_subset(cls, obj, target):
        return next(cls.filter_subset(obj, target), None)

    @classmethod
    def find_superset(cls, obj, target):
        return next(cls.filter_superset(obj, target), None)

    @classmethod
    def find_key(cls, obj, target, prev=[]):
        return next(cls.filter_key(obj, target, prev), None)

    @classmethod
    def to_jsonpath(cls, val):
        res = ""
        for i in val:
            if isinstance(i, str):
                res += "." + i
            elif isinstance(i, int):
                res += "[{}]".format(i)
            else:
                raise Exception("invalid type: {} ({})".format(i, val))
        return res.lstrip(".")

    @classmethod
    def escape_jsonptr(cls, s):
        if not isinstance(s, str):
            return str(s)
        s = s.replace("~", "~0")
        return s.replace("/", "~1")

    @classmethod
    def to_jsonpointer(cls, val):
        return "/" + "/".join([cls.escape_jsonptr(x) for x in val])

    @classmethod
    def format_to(cls, mode, val):
        fn = getattr(cls, "to_{}".format(mode))
        return fn(val)

    @classmethod
    def find_by(cls, mode, obj, path):
        if mode == "jsonpointer":
            return jsonpointer.resolve_pointer(obj, path)
        elif mode == "jsonpath":
            return jsonpath.jsonpath(obj, path)
        elif pyjq is not None and mode == "jq":
            return pyjq.all(path, obj)
        elif jsonselect is not None and mode == "jsonselect":
            return list(jsonselect.match(path, obj))
        return None


format_list = [x.split("_", 1)[-1]
               for x in filter(lambda f: f.startswith("to_"), dir(JsonFind))]
find_format_list = [*format_list]
if pyjq is not None and "jq" not in find_format_list:
    find_format_list.append("jq")
if jsonselect is not None and "jsonselect" not in find_format_list:
    find_format_list.append("jsonselect")

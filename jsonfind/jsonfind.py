"""
>>> obj = {"a":"b","c":{"d":"e"}}
>>> tgt = obj["c"]
>>> JsonFind.to_jsonpointer(JsonFind.find_eq(obj, tgt))
'/c'
>>> JsonFind.to_jsonpath(JsonFind.find_eq(obj, tgt))
'c'
"""

from logging import getLogger
import jsonpointer
import jsonpath
try:
    import pyjq
except ModuleNotFoundError:
    pyjq = None
try:
    import jsonselect
except ModuleNotFoundError:
    jsonselect = None

log = getLogger(__name__)


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

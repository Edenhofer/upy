from collections import deque, namedtuple
from collections.abc import Mapping, Set
from ctypes import LibraryLoader
from importlib import reload
from numbers import Number
import sys
from types import ModuleType
import typing

ZERO_DEPTH_BASES = [str, bytes, Number, range, bytearray, type]
if hasattr(typing, "_GenericAlias"):
    ZERO_DEPTH_BASES += [typing._GenericAlias]
if hasattr(typing, "_SpecialGenericAlias"):
    ZERO_DEPTH_BASES += [typing._SpecialGenericAlias]
ZERO_DEPTH_BASES = tuple(ZERO_DEPTH_BASES)
ZERO_DEPTH_INSTANCES = (LibraryLoader, )


Timed = namedtuple("Timed", ("time", "number"), rename=True)


def timeit(stmt, setup=lambda: None, number=None):
    import timeit

    if number is None:
        number, _ = timeit.Timer(stmt).autorange()

    setup()
    t = timeit.timeit(stmt, number=number) / number
    return Timed(time=t, number=number)


def getsizeof(obj_0):
    """Returns the size of an object and all of its members in bytes when
    recursively iterating through it.
    """
    _seen_ids = set()

    def inner(obj):
        obj_id = id(obj)
        if obj_id in _seen_ids:
            return 0
        _seen_ids.add(obj_id)
        size = sys.getsizeof(obj)
        if isinstance(obj, ZERO_DEPTH_INSTANCES):
            return size

        if isinstance(obj, ZERO_DEPTH_BASES):
            pass  # bypass remaining control flow and return
        elif isinstance(obj, (tuple, list, Set, frozenset, deque)):
            size += sum(inner(i) for i in obj)
        elif isinstance(obj, Mapping) or hasattr(obj, 'items'):
            size += sum(inner(k) + inner(v) for k, v in getattr(obj, 'items')())
        # Attempt to traverse custom object
        if hasattr(obj, 'nbytes'):
            # Account for `nbytes` only if of correct type
            sz = getattr(obj, "nbytes")
            size += sz if isinstance(sz, int) else 0
        if hasattr(obj, '__dict__'):
            size += inner(vars(obj))
        if hasattr(obj, '__slots__') and getattr(obj, '__slots__') is not None:
            size += sum(
                inner(getattr(obj, s))
                for s in obj.__slots__ if hasattr(obj, s)
            )
        return size

    return inner(obj_0)


def pprint_global_memory(
    globals_, *, exclude=("In", "Out"), exclude_type=(ModuleType, )
):
    import warnings

    all_sizes = {}
    for k in set(globals_.keys()):  # Copy keys for immutability
        el = globals_[k]
        if k in exclude or isinstance(el, exclude_type):
            continue

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                all_sizes[k] = getsizeof(el)
        except (TypeError, ValueError):
            pass

    for k, v in sorted(all_sizes.items(), key=lambda el: el[1]):
        sz = "{0:>9s} B".format(f"{v:#6.4g}")
        print(f"{str(k):>30} :: {sz}", file=sys.stderr)


def rreload(module, _top_lvl=None):
    """Recursively reload modules"""
    _top_lvl = module.__name__ if _top_lvl is None else _top_lvl
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, ModuleType) and attr.__name__.startswith(_top_lvl):
            rreload(attr)
    reload(module)

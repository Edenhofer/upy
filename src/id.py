#!/usr/bin/env python3

import struct
from warnings import warn

import numpy as np


def hashit(obj, n_chars=8, _raw=False, _raise_unknown=False):
    """Get first `n_chars` characters of Blake2B hash of `obj`."""
    from hashlib import blake2b

    try:
        hsh = blake2b(obj)
    except (TypeError, BufferError, ValueError) as e:
        if isinstance(obj, bool):
            hsh = blake2b(bytes(obj))
        elif isinstance(obj, int):
            obj = obj.to_bytes(
                obj.bit_length() // 8 + 1, byteorder="little", signed=True
            )
            hsh = blake2b(obj)
        elif isinstance(obj, float):
            hsh = blake2b(struct.pack("d", obj))
        elif isinstance(obj, str):
            hsh = blake2b(bytes(obj, "utf-8"))
        elif isinstance(obj, (list, tuple, dict)):
            obj = obj.items() if isinstance(obj, dict) else obj
            hsh = blake2b()
            for el in obj:
                hsh.update(hashit(el, _raw=True))
        elif isinstance(obj, slice):
            hsh = blake2b(b"slice")
            hsh.update(hashit((obj.start, obj.stop, obj.step), _raw=True))
        elif obj is None:
            hsh = blake2b(b"None")
        elif isinstance(obj, np.ndarray
                       ) and "ndarray is not C-contiguous" in "".join(e.args):
            hsh = blake2b(obj.reshape(obj.shape, order="C"))
        elif hasattr(obj, "tree_flatten") and callable(obj.tree_flatten):
            hsh = blake2b(bytes(obj.__class__.__name__, "utf-8"))
            hsh.update(hashit(obj.tree_flatten(), _raw=True))
        elif isinstance(e, BufferError) and any(
            "only defined for CPU" in a for a in e.args
        ) and obj.__class__.__name__ == "DeviceArray":
            # Object is of type JAX DeviceArray; avoid the isinstance check to
            # not depend on jax
            hsh = blake2b(np.asarray(obj))
        elif _raise_unknown:
            raise ValueError("unknown object")
        else:
            warn(f"unknown object of type {type(obj)!r}; hashing repr")
            obj = bytes(repr(obj), "utf-8")
            hsh = blake2b(obj)

    if _raw:
        return hsh.digest()
    return hsh.hexdigest()[slice(n_chars)]


def git_reproduce(file_excludes=(":!*.tex", ":!*.bib"), root_dir=None):
    """Get the necessary information from git to fully reproduce the current
    state of all tracked files.
    """
    import os
    from subprocess import check_output, CalledProcessError

    about_git = None

    if root_dir is None:
        try:
            root_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:  # __file__ must not be defined
            root_dir = os.getcwd()

    git_cmd = ("git", "-C", root_dir)
    try:
        check_output(git_cmd + ("rev-parse", "--git-dir"))
        has_git = True
    except (CalledProcessError, FileNotFoundError):
        has_git = False
    if has_git:
        head = check_output(git_cmd + ("rev-parse", "HEAD")).decode().strip()
        br = check_output(git_cmd + ("rev-parse", "--abbrev-ref",
                                     "HEAD")).decode().strip()
        dirt = check_output(
            git_cmd + ("diff-index", "--name-only", "HEAD", "--")
        ).decode().strip()
        dirty = dirt != ""
        patch = check_output(
            git_cmd + ("diff", "--patch", "HEAD", "--") + file_excludes
        ).decode().strip()
        about_git = {"HEAD": head, "branch": br, "dirty": dirty, "patch": patch}

    return about_git


def about(*args, **kwargs):
    """Collect information about the current state of afairs."""
    import os
    import sys
    from datetime import datetime

    about = {"args": args, "date": str(datetime.now())}
    about |= kwargs
    about["environment"] = dict(os.environ)
    about["argv"] = sys.argv
    about["git"] = git_reproduce()
    return about

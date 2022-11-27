"""
Custom types definition for mypy
"""

from typing import Union, Any

Numeric = Union[int, float]

# Numeric iterable type
NumericIter = Union[Numeric, list[Numeric], tuple[Numeric]]

StrDict = dict[str, str]
NestedStrKeyDict = dict[str, dict[str, Any]]

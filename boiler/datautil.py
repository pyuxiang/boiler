#!/usr/bin/env python3
# Justin, 2022-12-20
"""Provides helper functions for data management.
"""

__all__ = ["pprint", "read_log"]

import datetime as dt
import re
from typing import Optional, Type

import numpy as np
import tqdm

# For pprint to accept NaN values
NOVALUE = np.iinfo(np.int64).min

def pprint(
        *values,
        width: int = 7,
        out: Optional[str] = None,
        pbar: Optional[Type[tqdm.tqdm]] = None,
        stdout: bool = True,
):
    """Prints right-aligned columns of fixed width.

    Saved data is enforced to be tab-delimited to save storage space
    (typically not directly printed into console anyway, but post-processed).

    Args:
        out: Optional filepath to save data.
        pbar: tqdm.ProgressBar.
        print: Determines if should write to console.
     
    Note:
        The default column width of 7 is predicated on the fact that
        10 space-separated columns can be comfortably squeezed into a
        80-width terminal (with an extra buffer for newline depending
        on the shell).

        Not released.

        Integrates with tqdm.ProgressBar.

        Conflicts with Python's pprint module, which is implemented
        for pretty-printing of data structures instead of plain tabular data.
    """
    array = [(str(value) if value != NOVALUE else ' ') for value in values]

    # Checks if progress bar is supplied - if so, update that instead
    if pbar:
        line = " ".join(array)
        pbar.set_description(line)

    # Prints line delimited to console
    elif stdout:
        line = " ".join([f"{value: >{width}s}" for value in array])
        print(line)

    # Write to file if filepath provided
    if out:
        line = "\t".join(array) + "\n"
        with open(out, "a") as f:
            f.write(line)

    return


def read_log(filename: str, schema: list, merge: bool = False):
    """Parses a logfile into a dictionary of columns.

    Convenience method to read out logfiles generated by the script.
    This is not filename-aware (i.e. date and schema version is not
    extracted from the filename) since these are not rigorously
    set-in-stone yet.

    Args:
        filename: Filename of log file.
        schema: List of datatypes to parse each column in logfile.
        merge:
            Whether multiple logging runs in the same file should
            be merged into a single list, or as a list-of-lists.

    Note:
        This code assumes tokens in columns do not contain spaces,
        including headers.

    TODO(Justin):
        Consider usage of PEP557 dataclasses for type annotations.
        Change the argument type of filename to include Path-like objects.
        Implement non-merge functionality.

        Not released.
    """

    # Custom datatype
    def convert_time(s):
        """Converts time in HHMMSS format to datetime object.
        
        Note:
            The default date is 1 Jan 1900.
        """
        return dt.datetime.strptime(s, "%H%M%S")

    # Parse schema
    _maps = []
    for dtype in schema:
        # Parse special (hardcoded) types
        if isinstance(dtype, str):
            if dtype == "time":
                _map = convert_time
            else:
                raise ValueError(f"Unrecognized schema value - '{dtype}'")
        # Treat everything else as regular Python datatypes
        elif isinstance(dtype, type):
            _map = dtype
        else:
            raise ValueError(f"Unrecognized schema value - '{dtype}'")
        _maps.append(_map)

    # Read file
    is_header_logged = False
    _headers = []
    _data = []
    with open(filename, "r") as f:
        for row_str in f:
            # Squash all intermediate spaces
            row = re.sub(r"\s+", " ", row_str.strip()).split(" ")
            try:
                # Equivalent to Pandas's 'applymap'
                row = [f(v) for f, v in zip(_maps, row)]
                _data.append(row)
            except:
                # If fails, assume is string header
                if not is_header_logged:
                    _headers = row
                    is_header_logged = True

    if not is_header_logged:
        raise ValueError("Logfile does not contain a header.")
    
    # Merge headers
    _data = list(zip(*_data))
    _items = tuple(zip(_headers, _data))
    return dict(_items)
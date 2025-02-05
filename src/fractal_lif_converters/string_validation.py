"""Naming string validation functions for fractal-lif-converters."""

import re


def validate_well_name_type1(well_name: str) -> tuple[bool, str, str]:
    """Validate well name for type 1 plate layout.

    Well name must be a singe or duble letter followed by a positive integer.
    Valid examples are `A1`, `A2`, `B1`, `AA1`, `AA12` etc.
    """
    match = re.match(r"([A-Z]+)(\d+)", well_name)
    if match is None:
        return False, "", ""
    row = match.group(1)
    col = match.group(2)
    if int(col) <= 0:
        # covers cases like "A0"
        return False, "", ""

    if f"{row}{col}" != well_name:
        # covers cases like "A1.1"
        return False, "", ""
    return True, row, col


def validate_well_name_type2(row_name: str, column_name: str) -> tuple[bool, str, str]:
    """Validate well name for type 2 plate layout.

    Well can be hierarchically structured, for example `A/1`, `A/2`, `B/1`, `AA/1`, etc.
    Where the row must be a single or double letter and the column must be a positive integer.
    """
    if len(row_name) < 1 or len(row_name) > 2:
        return False, "", ""

    if len(column_name) < 1:
        return False, "", ""

    # Re-use type1 validation for row and column
    well_name = f"{row_name}{column_name}"
    return validate_well_name_type1(well_name)


def _validate_position_name(position_name: str, prefix: str) -> tuple[bool, str]:
    match = re.match(rf"{prefix}(\d+)", position_name)
    if match is None:
        return False, ""

    position_number = match.group(1)
    if f"{prefix}{position_number}" != position_name:
        # covers cases like "R1.2"
        return False, ""

    if int(position_number) <= 0:
        # covers cases like "R0"
        return False, ""

    return True, position_name


def validate_position_name_type1(position_name: str) -> tuple[bool, str]:
    """Validate type 1 position name.

    Position name must the letter `R` followed by a positive integer.
    """
    return _validate_position_name(position_name, "R")


def validate_position_name_type2(position_name: str) -> tuple[bool, str]:
    """Validate type 2 position name.

    Position name must `Position` followed by a space and a positive integer.
    """
    return _validate_position_name(position_name, "Position ")

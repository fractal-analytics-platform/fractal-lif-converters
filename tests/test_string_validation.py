from fractal_lif_converters.string_validation import (
    validate_position_name_type1,
    validate_position_name_type2,
    validate_well_name_type1,
    validate_well_name_type2,
)
import pytest


@pytest.mark.parametrize(
    "well_name, expected",
    [
        ("A1", (True, "A", "1")),
        ("A2", (True, "A", "2")),
        ("B1", (True, "B", "1")),
        ("AA1", (True, "AA", "1")),
        ("AA12", (True, "AA", "12")),
        ("A", (False, "", "")),
        ("1", (False, "", "")),
        ("1A", (False, "", "")),
        ("AcqName1", (False, "", "")),
        ("A0", (False, "", "")),
        ("A-1", (False, "", "")),
        ("A1.2", (False, "", "")),
        ("A.A1", (False, "", "")),
    ],
)
def test_validate_well_name_type1(well_name, expected):
    assert validate_well_name_type1(well_name) == expected


@pytest.mark.parametrize(
    "well_name, expected",
    [
        ("A/1", (True, "A", "1")),
        ("A/2", (True, "A", "2")),
        ("B/1", (True, "B", "1")),
        ("AA/1", (True, "AA", "1")),
        ("AA/12", (True, "AA", "12")),
        ("A/", (False, "", "")),
        ("1/", (False, "", "")),
        ("1/A", (False, "", "")),
        ("/A1", (False, "", "")),
        ("AcqName/1", (False, "", "")),
        ("A/0", (False, "", "")),
        ("A/-1", (False, "", "")),
        ("A1/.2", (False, "", "")),
        ("A/.A1", (False, "", "")),
        ("A./A1", (False, "", "")),
        ("A.A/1", (False, "", "")),
    ],
)
def test_validate_well_name_type2(well_name, expected):
    row, col = well_name.split("/")
    assert validate_well_name_type2(row, col) == expected


@pytest.mark.parametrize(
    "position_name, expected",
    [
        ("R1", (True, "R1")),
        ("R2", (True, "R2")),
        ("R12", (True, "R12")),
        ("R", (False, "")),
        ("1", (False, "")),
        ("1R", (False, "")),
        ("AcqName1", (False, "")),
        ("R0", (False, "")),
        ("R-1", (False, "")),
        ("R1.2", (False, "")),
        ("R.R1", (False, "")),
        ("RR1", (False, "")),
    ],
)
def test_validate_position_name_type1(position_name, expected):
    assert validate_position_name_type1(position_name) == expected


@pytest.mark.parametrize(
    "position_name, expected",
    [
        ("Position 1", (True, "Position 1")),
        ("Position 2", (True, "Position 2")),
        ("Position 12", (True, "Position 12")),
        ("Position", (False, "")),
        ("1", (False, "")),
        ("1 Position", (False, "")),
        ("AcqName1", (False, "")),
        ("Position 0", (False, "")),
        ("Position -1", (False, "")),
        ("Position 1.2", (False, "")),
        ("Position .Position 1", (False, "")),
        ("Position.Position 1", (False, "")),
    ],
)
def test_validate_position_name_type2(position_name, expected):
    assert validate_position_name_type2(position_name) == expected

"""The tool calls' checks: every year asked about has a ceremony, and each output is exactly what the data says."""

from contract import Tool

from .checks import YEARS, nominations, records, result
from .data import CEREMONIES, FIRST_YEAR, LAST_YEAR


def verify_input(tool, value):
    # Any title may be asked about: the tool itself says when no film has it.
    if tool is Tool.GET_CEREMONY and value.year not in YEARS:
        return result(
            False, f"{value.year} is not a film year: they run from {FIRST_YEAR} to {LAST_YEAR}", given=value.year
        )
    return result(True, "input is valid")


def verify_output(tool, input_value, output_value, workspace):
    if tool is Tool.GET_CEREMONY:
        return verify_ceremony(input_value, output_value)
    found = records(input_value.title)
    if not found:
        return result(False, f"no film is titled {input_value.title!r}, so the tool must fail, not answer")
    expected = (input_value.title, found)
    given = (
        output_value.title,
        [
            (
                film.year,
                film.ceremony,
                film.title,
                [(row.award.value, row.nominee, row.won) for row in film.nominations],
            )
            for film in output_value.films
        ],
    )
    if given != expected:
        return result(False, f"get_film_awards must give exactly {input_value.title!r}'s records", expected=expected)
    return result(True, "output is valid")


def verify_ceremony(input_value, output_value):
    year = input_value.year
    if year not in YEARS:
        return result(False, f"{year} has no ceremony, so the tool must fail, not answer")
    expected = (year, CEREMONIES[year][0], nominations(year, input_value.awards))
    given = (
        output_value.year,
        output_value.ceremony,
        [(row.award.value, row.film, row.nominee, row.won) for row in output_value.nominations],
    )
    if given != expected:
        return result(False, f"get_ceremony must give exactly {year}'s nominations", expected=expected)
    return result(True, "output is valid")

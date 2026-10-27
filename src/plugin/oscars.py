"""The tools that read the Academy Awards records, from verifier/data.py: the one copy, which the verifier also judges
by. Years and titles follow verifier/checks.py's rules, so a tool and a verdict never disagree on them. No tool applies
a query's conditions: the agent filters the films from what they give."""

from __future__ import annotations

from pathlib import Path

from contract import (
    Award,
    AwardRecord,
    CeremonyInput,
    CeremonyOutput,
    FilmAwardsOutput,
    FilmInput,
    FilmRecord,
    Nomination,
)
from verifier.checks import YEARS, nominations, records
from verifier.data import CEREMONIES, FIRST_YEAR, LAST_YEAR


def get_ceremony(given: CeremonyInput, workspace: Path) -> CeremonyOutput:
    if given.year not in YEARS:
        raise ValueError(
            f"no ceremony: film years run from {FIRST_YEAR} (ceremony {CEREMONIES[FIRST_YEAR][0]}) to {LAST_YEAR} "
            f"(ceremony {CEREMONIES[LAST_YEAR][0]}), and {given.year} is not one"
        )
    return CeremonyOutput(
        year=given.year,
        ceremony=CEREMONIES[given.year][0],
        nominations=[
            Nomination(award=Award(award), film=title, nominee=nominee, won=won)
            for award, title, nominee, won in nominations(given.year, given.awards)
        ],
    )


def get_film_awards(given: FilmInput, workspace: Path) -> FilmAwardsOutput:
    found = records(given.title)
    if not found:
        raise ValueError(
            f"no such film: no film titled {given.title!r} was nominated for an award this plugin covers; "
            "use a title as get_ceremony gives it"
        )
    return FilmAwardsOutput(
        title=given.title,
        films=[
            FilmRecord(
                title=title,
                year=year,
                ceremony=number,
                nominations=[AwardRecord(award=Award(award), nominee=nominee, won=won) for award, nominee, won in kept],
            )
            for year, number, title, kept in found
        ],
    )

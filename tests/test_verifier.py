"""The verifier, called as NanoAgent's sandbox calls it, with contract instances built from JSON: every answer to the
task and every tool output, judged against the data. The steps the task's instructions describe, played through the
tools, earn a valid verdict on every sampled query."""

from __future__ import annotations

import random
from pathlib import Path

import pytest
from slimconfig import build_output, plain_output

import verifier
from contract import TOOLS, Award, CeremonyInput, FilmInput, FilmsOutput, SearchInput, Status, Tool
from plugin.oscars import get_ceremony, get_film_awards

STATUSES = [status.value for status in Status]
AWARDS = [award.value for award in Award]


def query(first_year: int, last_year: int, won=(), not_won=(), nominated_not_won=()) -> dict:
    return {
        "first_year": first_year,
        "last_year": last_year,
        "won": list(won),
        "not_won": list(not_won),
        "nominated_not_won": list(nominated_not_won),
    }


def verify(arguments: dict, answer: dict) -> dict:
    """The verdict on an answer to the task; there is no reference."""
    built = build_output(arguments, SearchInput)
    return verifier.verify_task("find-films", built, build_output(answer, FilmsOutput), None, ".")


def found(*films: tuple[str, int]) -> dict:
    return {"status": "found", "films": [{"title": title, "year": year} for title, year in films]}


EXAMPLE = query(2000, 2024, ["best_picture", "directing"], ["actor"])
RIGHT = [
    ("A Beautiful Mind", 2001),
    ("The Lord of the Rings: The Return of the King", 2003),
    ("Million Dollar Baby", 2004),
    ("The Departed", 2006),
    ("No Country for Old Men", 2007),
    ("Slumdog Millionaire", 2008),
    ("The Hurt Locker", 2009),
    ("Birdman or (The Unexpected Virtue of Ignorance)", 2014),
    ("The Shape of Water", 2017),
    ("Parasite", 2019),
    ("Nomadland", 2020),
    ("Everything Everywhere All at Once", 2022),
    ("Anora", 2024),
]


def test_accepts_the_right_films() -> None:
    verdict = verify(EXAMPLE, found(*RIGHT))
    assert verdict["valid"] is True and verdict["score"] == 1.0, verdict
    # Any order; a title's case, accents, curly quotes and spacing are free.
    assert verify(EXAMPLE, found(*RIGHT[::-1]))["valid"] is True
    loose = [("  a beautiful MIND ", 2001), *RIGHT[1:]]
    assert verify(EXAMPLE, found(*loose))["valid"] is True
    speech = query(2010, 2010, ["actor"])
    assert verify(speech, found(("The King’s Speech", 2010)))["valid"] is True
    tar = query(2022, 2022, [], [], ["actress"])
    tar_films = verifier.films.expected(2022, 2022, [], [], [Award.ACTRESS])[2]
    assert ("Tár", 2022) in tar_films
    assert verify(tar, found(*[("TAR" if title == "Tár" else title, year) for title, year in tar_films]))["valid"]


def test_casting_winner_excluded_by_best_picture_has_no_matches(tmp_path: Path) -> None:
    arguments = query(2025, 2025, ["casting"], ["best_picture"])
    answer = follow_instructions(arguments, tmp_path)
    assert answer == {"status": "no_matches", "films": []}
    verdict = verify(arguments, answer)
    assert verdict["valid"] is True and verdict["score"] == 1.0
    assert "0 films from 2025 to 2025 won casting; did not win best_picture" in verdict["message"]
    for incorrect in (found(), found(("One Battle after Another", 2025))):
        verdict = verify(arguments, incorrect)
        assert verdict["valid"] is False and verdict["score"] == 0.0
        assert "the status is no_matches" in verdict["message"]
    assert verify(query(2025, 2025, ["casting"]), found(("One Battle after Another", 2025)))["valid"] is True


@pytest.mark.parametrize(
    ("films", "missing", "wrong", "score"),
    [
        (RIGHT[1:], 1, 0, 24 / 25),  # A Beautiful Mind left out
        ([*RIGHT, ("Oppenheimer", 2023)], 0, 1, 26 / 27),  # its leading actor won
        ([*RIGHT, ("The King's Speech", 2010)], 0, 1, 26 / 27),
        ([*RIGHT, ("Crash", 2005)], 0, 1, 26 / 27),  # its director was not the winner
        ([*RIGHT, ("Parasite", 2019)], 0, 1, 26 / 27),  # listed twice
        ([*RIGHT[:-1], ("Anora", 2025)], 1, 1, 24 / 26),  # the wrong year
        ([*RIGHT[:-1], ("Anora: The Movie", 2024)], 1, 1, 24 / 26),  # not the title
        ([("Gladiator", 2000)], 13, 1, 0.0),
        ([], 13, 0, 0.0),
    ],
)
def test_refuses_missing_and_wrong_films_with_partial_credit(films, missing: int, wrong: int, score: float) -> None:
    verdict = verify(EXAMPLE, found(*films))
    assert verdict["valid"] is False and verdict["score"] == pytest.approx(score), verdict
    assert (len(verdict["details"]["missing"]), len(verdict["details"]["wrong"])) == (missing, wrong)
    assert len(verdict["details"]["expected"]) == 13 and "13 films from 2000 to 2024" in verdict["message"]


def test_names_the_records_behind_each_missing_and_wrong_film() -> None:
    verdict = verify(EXAMPLE, found(*RIGHT[1:-1], ("Oppenheimer", 2023), ("Parasite", 2019), ("Anora", 2025)))
    details = verdict["details"]
    assert details["missing"] == [
        "A Beautiful Mind (2001): best_picture won, directing won, actor lost",
        "Anora (2024): best_picture won, directing won, actor not nominated",
    ]
    assert sorted(details["wrong"]) == [
        "Anora (2025): no nomination for any award at that year's ceremony",
        "Oppenheimer (2023): best_picture won, directing won, actor won",
        "Parasite (2019): listed more than once",
    ]
    assert verdict["message"].startswith("2 missing: ") and "; 3 wrong: " in verdict["message"]


def test_tells_not_won_apart_from_nominated_but_lost() -> None:
    lost = query(2000, 2024, ["best_picture"], [], ["directing"])
    not_won = query(2000, 2024, ["best_picture"], ["directing"])
    both = [("Gladiator", 2000), ("Chicago", 2002), ("Crash", 2005), ("12 Years a Slave", 2013)]
    both += [("Spotlight", 2015), ("Moonlight", 2016)]
    unnominated = [("Argo", 2012), ("Green Book", 2018), ("CODA", 2021)]
    assert verify(lost, found(*both))["valid"] is True
    assert verify(not_won, found(*both, *unnominated))["valid"] is True
    verdict = verify(lost, found(*both, *unnominated))
    assert verdict["valid"] is False and "Argo (2012): best_picture won, directing not nominated" in verdict["message"]
    assert verify(not_won, found(*both))["details"]["missing"][0].endswith("directing not nominated")


@pytest.mark.parametrize(
    ("arguments", "status"),
    [
        (query(2024, 2000, ["actor"]), "invalid_years"),
        (query(2001, 2000, [], [], []), "invalid_years"),
        (query(1927, 2000, ["actor"]), "out_of_range"),
        (query(2000, 2026, ["actor"]), "out_of_range"),
        (query(-5, 3000, [], ["actor"]), "out_of_range"),
        (query(2000, 2024, [], ["actor"]), "no_condition"),
        (query(2000, 2024), "no_condition"),
        (query(2000, 2025, ["actor"], ["actor"]), "no_matches"),
        (query(2025, 2025, ["casting"], ["best_picture"]), "no_matches"),
    ],
)
def test_accepts_only_the_status_the_query_has(arguments: dict, status: str) -> None:
    verdict = verify(arguments, {"status": status, "films": []})
    assert verdict["valid"] is True and verdict["score"] == 1.0, verdict
    for other in STATUSES:
        if other != status:
            assert verify(arguments, {"status": other, "films": []})["valid"] is False
    # Films go only with found.
    verdict = verify(arguments, {"status": status, "films": [{"title": "Parasite", "year": 2019}]})
    assert verdict["valid"] is False and "empty" in verdict["message"]


def test_a_query_with_films_is_never_another_status() -> None:
    for status in STATUSES[1:]:
        assert verify(EXAMPLE, {"status": status, "films": []})["valid"] is False


def follow_instructions(arguments: dict, tmp_path: Path) -> dict:
    """The answer the task's instructions lead to, through the tools."""
    first, last = arguments["first_year"], arguments["last_year"]
    won, not_won, lost = arguments["won"], arguments["not_won"], arguments["nominated_not_won"]
    if first > last:
        return {"status": "invalid_years", "films": []}
    if first < 1928 or last > 2025:
        return {"status": "out_of_range", "films": []}
    if not won and not lost:
        return {"status": "no_condition", "films": []}
    candidates = []
    for year in range(first, last + 1):
        ceremony = get_ceremony(build_output({"year": year, "awards": [*won, *lost]}, CeremonyInput), tmp_path)
        films: dict[str, dict[str, bool]] = {}
        for row in ceremony.nominations:
            awards = films.setdefault(row.film, {})
            awards[row.award.value] = awards.get(row.award.value, False) or row.won
        for title, awards in films.items():
            if all(awards.get(award) for award in won) and all(award in awards and not awards[award] for award in lost):
                candidates.append((title, year))
    kept = []
    for title, year in candidates:
        if not_won:
            record = get_film_awards(FilmInput(title=title), tmp_path)
            entry = next(film for film in record.films if film.year == year)
            if any(row.won and row.award.value in not_won for row in entry.nominations):
                continue
        kept.append((title, year))
    return found(*kept) if kept else {"status": "no_matches", "films": []}


def test_the_instructions_earn_a_valid_verdict(tmp_path: Path) -> None:
    rng = random.Random(580)
    queries = [
        EXAMPLE,
        query(1928, 2025, ["best_picture", "directing", "actor", "actress"]),
        query(2000, 2024, ["best_picture"], [], ["directing"]),
        query(2000, 2024, ["best_picture"], ["directing"]),
        query(1928, 1935, ["actress"]),  # several films in one nomination
        query(1939, 1966, ["cinematography"], ["best_picture"]),  # black-and-white and color
        query(2025, 2025, ["casting"], ["best_picture", "directing"]),
        query(2024, 2000, ["actor"]),
        query(1900, 2000, ["actor"]),
        query(2000, 2024, [], ["actor"]),
    ]
    major = AWARDS[:8]
    for _ in range(300):
        first = rng.randint(1925, 2026)
        last = first + rng.choice([-1, 0, 1, 5, 10, 30, 60])
        won = rng.sample(rng.choice([major, AWARDS]), rng.choice([0, 1, 1, 1, 2]))
        not_won = rng.sample(rng.choice([major, AWARDS]), rng.choice([0, 1, 2]))
        lost = rng.sample(major, rng.choice([0, 0, 0, 1]))
        queries.append(query(first, last, won, not_won, lost))
    seen, sizes = set(), []
    for arguments in queries:
        answer = follow_instructions(arguments, tmp_path)
        verdict = verify(arguments, answer)
        assert verdict["valid"] is True, (arguments, answer, verdict)
        seen.add(answer["status"])
        sizes.append(len(answer["films"]))
    assert seen == set(STATUSES) and sum(size > 0 for size in sizes) > 100


@pytest.mark.parametrize(
    "answer",
    [
        {},
        {"status": "found"},
        {"films": []},
        {"status": "FOUND", "films": []},
        {"status": "ok", "films": []},
        {"status": "found", "films": ["Parasite"]},
        {"status": "found", "films": [{"title": "Parasite"}]},
        {"status": "found", "films": [{"title": "Parasite", "year": "2019"}]},
        {"status": "found", "films": [{"title": None, "year": 2019}]},
        {"status": "found", "films": [{"title": "Parasite", "year": 2019, "won": ["best_picture"]}]},
        {"status": "found", "films": [], "count": 0},
    ],
)
def test_a_malformed_answer_never_reaches_the_verifier(answer: dict) -> None:
    # NanoAgent builds every answer into its contract class first, and refuses one that does not fit.
    with pytest.raises(ValueError):
        build_output(answer, FilmsOutput)


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {key: value for key, value in EXAMPLE.items() if key != "not_won"},
        {**EXAMPLE, "first_year": "2000"},
        {**EXAMPLE, "last_year": 2024.0},
        {**EXAMPLE, "won": "best_picture"},
        {**EXAMPLE, "won": ["Best Picture"]},  # awards by their value only
        {**EXAMPLE, "not_won": ["best_actor"]},
        {**EXAMPLE, "nominated_not_won": ["honorary_award"]},
        {**EXAMPLE, "lost": ["actor"]},
    ],
)
def test_a_malformed_task_input_is_refused(arguments: dict) -> None:
    build_output(EXAMPLE, SearchInput)
    with pytest.raises(ValueError):
        build_output(arguments, SearchInput)


def check(tool: str, value: dict, output: dict | None = None) -> bool:
    """Whether verify_input (without ``output``) or verify_output (with it) approves a tool call."""
    given, made = TOOLS[Tool(tool)]
    if output is None:
        return verifier.verify_input(tool, build_output(value, given))["valid"]
    return verifier.verify_output(tool, build_output(value, given), build_output(output, made), ".")["valid"]


def test_checks_tool_inputs() -> None:
    for year in [1928, 1999, 2025]:
        assert check("get_ceremony", {"year": year, "awards": ["actor"]}) is True
    for year in [1927, 2026, 0, -2000]:
        assert check("get_ceremony", {"year": year, "awards": ["actor"]}) is False
    for title in ["Parasite", "", "No Such Film"]:
        assert check("get_film_awards", {"title": title}) is True  # the tool says


@pytest.mark.parametrize(
    "value",
    [
        {"year": 2023, "awards": ["best_picture", "actor"]},
        {"year": 2023, "awards": ["actor", "best_picture", "actor"]},
        {"year": 1928, "awards": AWARDS},
        {"year": 1944, "awards": ["cinematography", "production_design"]},
        {"year": 2000, "awards": []},
    ],
)
def test_approves_every_true_get_ceremony_output(value: dict, tmp_path: Path) -> None:
    output = plain_output(get_ceremony(build_output(value, CeremonyInput), tmp_path))
    assert check("get_ceremony", value, output) is True


@pytest.mark.parametrize("title", ["Parasite", "little women", " Amelie ", "Rashomon", "Street Angel", "Hamlet"])
def test_approves_every_true_get_film_awards_output(title: str, tmp_path: Path) -> None:
    output = plain_output(get_film_awards(FilmInput(title=title), tmp_path))
    assert check("get_film_awards", {"title": title}, output) is True


def changed(output: dict, **fields) -> dict:
    return {**output, **fields}


def test_refuses_a_tool_output_that_is_not_the_data(tmp_path: Path) -> None:
    value = {"year": 2023, "awards": ["best_picture", "actor"]}
    ceremony = plain_output(get_ceremony(build_output(value, CeremonyInput), tmp_path))
    rows = ceremony["nominations"]
    assert check("get_ceremony", value, changed(ceremony, ceremony=95)) is False
    assert check("get_ceremony", value, changed(ceremony, year=2024)) is False
    assert check("get_ceremony", value, changed(ceremony, nominations=rows[1:])) is False  # one left out
    assert check("get_ceremony", value, changed(ceremony, nominations=rows[::-1])) is False  # out of order
    flipped = [{**row, "won": not row["won"]} if row["film"] == "Oppenheimer" else row for row in rows]
    assert check("get_ceremony", value, changed(ceremony, nominations=flipped)) is False
    renamed = [{**row, "film": "Barbie 2"} if row["film"] == "Barbie" else row for row in rows]
    assert check("get_ceremony", value, changed(ceremony, nominations=renamed)) is False
    other = plain_output(get_ceremony(CeremonyInput(year=2022, awards=[Award.BEST_PICTURE, Award.ACTOR]), tmp_path))
    assert check("get_ceremony", value, changed(other, year=2023, ceremony=96)) is False  # 2022's passed off as 2023's
    missing = {"year": 2026, "awards": ["actor"]}
    assert check("get_ceremony", missing, changed(ceremony, year=2026, nominations=[])) is False  # must fail
    film = plain_output(get_film_awards(FilmInput(title="Parasite"), tmp_path))
    entry = film["films"][0]
    assert check("get_film_awards", {"title": "Parasite"}, changed(film, title="parasite")) is False
    assert check("get_film_awards", {"title": "Parasite"}, changed(film, films=[])) is False
    lost = [{**entry, "nominations": [{**row, "won": False} for row in entry["nominations"]]}]
    assert check("get_film_awards", {"title": "Parasite"}, changed(film, films=lost)) is False
    shifted = [{**entry, "year": 2020, "ceremony": 93}]
    assert check("get_film_awards", {"title": "Parasite"}, changed(film, films=shifted)) is False
    women = plain_output(get_film_awards(FilmInput(title="Little Women"), tmp_path))
    assert check("get_film_awards", {"title": "Little Women"}, changed(women, films=women["films"][1:])) is False
    assert check("get_film_awards", {"title": "Paracite"}, changed(film, title="Paracite")) is False  # must fail

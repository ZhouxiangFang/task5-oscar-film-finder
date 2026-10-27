"""Checks shared by the verifiers and the tools: the film years the data covers, how titles are compared, a ceremony's
nominations, a film's records, and which films meet a query's conditions. Pure functions of their arguments and
data.py."""

import unicodedata

from contract import Award, Status

from .data import CEREMONIES, FIRST_YEAR, LAST_YEAR

YEARS = range(FIRST_YEAR, LAST_YEAR + 1)
QUOTES = str.maketrans("‘’“”", "''\"\"")
# How many films a verdict's message names; its details name every one.
SHOWN = 5


def result(valid, message, *, score=None, **details):
    return {
        "valid": valid,
        "score": float(valid) if score is None else score,
        "message": message,
        "details": details,
    }


def folded(text):
    """``text`` as titles are compared: accents and curly quotes dropped, case folded, runs of spaces made one."""
    plain = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    return " ".join(plain.translate(QUOTES).casefold().split())


def nominations(year, awards):
    """Film year ``year``'s nominations for ``awards``, award by award in Award's order: (award, title, nominee, won)."""
    wanted = {award.value for award in awards}
    return [row for row in CEREMONIES[year][1] if row[0] in wanted]


def standings():
    """film year -> folded title -> (the title, {award: whether a nomination of the film for it won})."""
    found = {}
    for year, (_, rows) in CEREMONIES.items():
        films = found[year] = {}
        for award, title, _, won in rows:
            _, awards = films.setdefault(folded(title), (title, {}))
            awards[award] = awards.get(award, False) or won
    return found


def film_records():
    """folded title -> each ceremony a film with that title was nominated at, earliest first: (year, ceremony number,
    the title, [(award, nominee, won), ...])."""
    found = {}
    for year, (number, rows) in CEREMONIES.items():
        films = {}
        for award, title, nominee, won in rows:
            films.setdefault(title, []).append((award, nominee, won))
        for title, kept in films.items():
            found.setdefault(folded(title), []).append((year, number, title, kept))
    return found


STANDINGS = standings()
FILMS = film_records()


def records(title):
    """Every ceremony a film titled ``title`` was nominated at, as film_records gives them; [] if none."""
    return FILMS.get(folded(title), [])


def standing(title, year):
    """The film titled ``title`` (compared folded) at film year ``year``'s ceremony: (its title, {award: won}), or None
    when it has no nomination there."""
    return STANDINGS.get(year, {}).get(folded(title))


def meets(awards, won, not_won, nominated_not_won):
    """Whether a film whose nominations at one ceremony are ``awards`` ({award: won}) meets the conditions."""
    return (
        all(awards.get(award) for award in won)
        and not any(awards.get(award) for award in not_won)
        and all(award in awards and not awards[award] for award in nominated_not_won)
    )


def named(won, not_won, nominated_not_won):
    """Every award the conditions (lists of Award) name, by value in Award's order."""
    given = set(won) | set(not_won) | set(nominated_not_won)
    return [award.value for award in Award if award in given]


def record(awards, shown):
    """What a film with nominations ``awards`` did in each award of ``shown``: won, lost, or not nominated."""
    said = {True: "won", False: "lost"}
    return ", ".join(f"{award} {said.get(awards.get(award), 'not nominated')}" for award in shown)


def conditions(won, not_won, nominated_not_won):
    parts = [
        f"{label} {', '.join(awards)}"
        for label, awards in (
            ("won", won),
            ("did not win", not_won),
            ("were nominated for but lost", nominated_not_won),
        )
        if awards
    ]
    return "; ".join(parts)


def expected(first_year, last_year, won, not_won, nominated_not_won):
    """The status a query has, why, and every film that meets its conditions, (title, film year), by year ([] unless
    found). ``won``, ``not_won`` and ``nominated_not_won`` are lists of Award.

    The checks go in this order, the first that holds deciding: the years' order, their range, then whether an award
    must be won or nominated for, without which the conditions name no list (every film ever made won none).
    """
    if first_year > last_year:
        return Status.INVALID_YEARS, f"the first year {first_year} is after the last year {last_year}", []
    if first_year < FIRST_YEAR or last_year > LAST_YEAR:
        span = f"the years {first_year} to {last_year} go outside the data's {FIRST_YEAR} to {LAST_YEAR}"
        return Status.OUT_OF_RANGE, span, []
    if not won and not nominated_not_won:
        return Status.NO_CONDITION, "no award must be won or nominated for, so the conditions name no list", []
    won, not_won, nominated_not_won = (
        [award.value for award in awards] for awards in (won, not_won, nominated_not_won)
    )
    films = [
        (title, year)
        for year in range(first_year, last_year + 1)
        for title, awards in STANDINGS[year].values()
        if meets(awards, won, not_won, nominated_not_won)
    ]
    fact = f"{len(films)} films from {first_year} to {last_year} {conditions(won, not_won, nominated_not_won)}"
    return Status.FOUND if films else Status.NO_MATCHES, fact, films

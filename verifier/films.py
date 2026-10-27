"""The find-films task's check: the status the query has, and for a found list every film that meets the conditions,
each once, and no other. A film is its title (compared folded) and its film year."""

from collections import Counter

from contract import Status

from .checks import SHOWN, expected, folded, named, record, result, standing


def verify_task(arguments, output, reference, workspace):
    """``output``: a contract FilmsOutput, judged against the data itself (the task has no reference tool)."""
    won, not_won, nominated_not_won = arguments.won, arguments.not_won, arguments.nominated_not_won
    status, fact, films = expected(arguments.first_year, arguments.last_year, won, not_won, nominated_not_won)
    if output.status is not status:
        return result(False, f"{fact}, so the status is {status.value}, but the answer says {output.status.value}")
    if status is not Status.FOUND:
        if output.films:
            return result(False, f"films must be empty unless status is found; {fact}")
        return result(True, f"{fact}, as the answer says")
    want = Counter((folded(title), year) for title, year in films)
    given = Counter((folded(film.title), film.year) for film in output.films)
    if want == given:
        return result(True, f"{fact}, as the answer says")
    # Each film under the data's title where it has one, else the answer's.
    titles = {(folded(film.title), film.year): film.title for film in output.films}
    titles.update({(folded(title), year): title for title, year in films})
    shown = named(won, not_won, nominated_not_won)
    missing = [f"{titles[key]} ({key[1]}): {why(key, shown)}" for key in want - given]
    wrong = [
        f"{titles[key]} ({key[1]}): {'listed more than once' if key in want else why(key, shown)}"
        for key in given - want
    ]
    parts = [
        f"{len(found)} {label}: {'; '.join(found[:SHOWN])}{'; ...' if len(found) > SHOWN else ''}"
        for label, found in (("missing", missing), ("wrong", wrong))
        if found
    ]
    # F1 of the answer's films against the right ones: 1 only for exactly the right films, 0 for none of them.
    score = 2 * sum((want & given).values()) / (sum(want.values()) + sum(given.values()))
    return result(
        False,
        f"{'; '.join(parts)}. In all, {fact}",
        score=score,
        expected=[{"title": title, "year": year} for title, year in films],
        missing=missing,
        wrong=wrong,
    )


def why(key, shown):
    """The records behind a film's verdict: what it did in each award the conditions name at that year's ceremony."""
    found = standing(*key)
    return record(found[1], shown) if found else "no nomination for any award at that year's ceremony"

"""The data and the tools: the snapshot is the pinned one and data.py is built from it, every nomination agrees with the
raw table read apart from data.py, winners agree with ones written down by hand, the rules for ties, black-and-white
and color awards, nominations of several films and honorary awards hold, and the tools are true to the data."""

from __future__ import annotations

import csv
import gzip
import io
from collections import Counter
from pathlib import Path

import pytest
from build_data import AWARDS, HONORARY, OSCARS, TARGET, build, render

from contract import Award, CeremonyInput, FilmInput, Status
from plugin.oscars import get_ceremony, get_film_awards
from verifier.checks import STANDINGS, expected, folded, nominations, records
from verifier.data import CEREMONIES, FIRST_YEAR, LAST_YEAR

A = Award

# Best Picture winners written down by hand, by film year.
BEST_PICTURE = {
    1928: "Wings",
    1929: "The Broadway Melody",
    1930: "All Quiet on the Western Front",
    1931: "Cimarron",
    1932: "Grand Hotel",
    1933: "Cavalcade",
    1934: "It Happened One Night",
    1935: "Mutiny on the Bounty",
    1936: "The Great Ziegfeld",
    1937: "The Life of Emile Zola",
    1938: "You Can't Take It with You",
    1939: "Gone with the Wind",
    1940: "Rebecca",
    1941: "How Green Was My Valley",
    1942: "Mrs. Miniver",
    1943: "Casablanca",
    1944: "Going My Way",
    1945: "The Lost Weekend",
    1946: "The Best Years of Our Lives",
    1947: "Gentleman's Agreement",
    1948: "Hamlet",
    1949: "All the King's Men",
    1950: "All about Eve",
    1951: "An American in Paris",
    1952: "The Greatest Show on Earth",
    1953: "From Here to Eternity",
    1954: "On the Waterfront",
    1955: "Marty",
    1956: "Around the World in 80 Days",
    1957: "The Bridge on the River Kwai",
    1958: "Gigi",
    1959: "Ben-Hur",
    1960: "The Apartment",
    1961: "West Side Story",
    1962: "Lawrence of Arabia",
    1963: "Tom Jones",
    1964: "My Fair Lady",
    1965: "The Sound of Music",
    1966: "A Man for All Seasons",
    1967: "In the Heat of the Night",
    1968: "Oliver!",
    1969: "Midnight Cowboy",
    1970: "Patton",
    1971: "The French Connection",
    1972: "The Godfather",
    1973: "The Sting",
    1974: "The Godfather Part II",
    1975: "One Flew over the Cuckoo's Nest",
    1976: "Rocky",
    1977: "Annie Hall",
    1978: "The Deer Hunter",
    1979: "Kramer vs. Kramer",
    1980: "Ordinary People",
    1981: "Chariots of Fire",
    1982: "Gandhi",
    1983: "Terms of Endearment",
    1984: "Amadeus",
    1985: "Out of Africa",
    1986: "Platoon",
    1987: "The Last Emperor",
    1988: "Rain Man",
    1989: "Driving Miss Daisy",
    1990: "Dances with Wolves",
    1991: "The Silence of the Lambs",
    1992: "Unforgiven",
    1993: "Schindler's List",
    1994: "Forrest Gump",
    1995: "Braveheart",
    1996: "The English Patient",
    1997: "Titanic",
    1998: "Shakespeare in Love",
    1999: "American Beauty",
    2000: "Gladiator",
    2001: "A Beautiful Mind",
    2002: "Chicago",
    2003: "The Lord of the Rings: The Return of the King",
    2004: "Million Dollar Baby",
    2005: "Crash",
    2006: "The Departed",
    2007: "No Country for Old Men",
    2008: "Slumdog Millionaire",
    2009: "The Hurt Locker",
    2010: "The King's Speech",
    2011: "The Artist",
    2012: "Argo",
    2013: "12 Years a Slave",
    2014: "Birdman or (The Unexpected Virtue of Ignorance)",
    2015: "Spotlight",
    2016: "Moonlight",
    2017: "The Shape of Water",
    2018: "Green Book",
    2019: "Parasite",
    2020: "Nomadland",
    2021: "CODA",
    2022: "Everything Everywhere All at Once",
    2023: "Oppenheimer",
    2024: "Anora",
    2025: "One Battle after Another",  # Wikipedia's 98th Academy Awards page, read 2026-10-26
}
# The films whose director and leading actor won, written down by hand, 2000 to 2025.
DIRECTING = [
    "Traffic",
    "A Beautiful Mind",
    "The Pianist",
    "The Lord of the Rings: The Return of the King",
    "Million Dollar Baby",
    "Brokeback Mountain",
    "The Departed",
    "No Country for Old Men",
    "Slumdog Millionaire",
    "The Hurt Locker",
    "The King's Speech",
    "The Artist",
    "Life of Pi",
    "Gravity",
    "Birdman or (The Unexpected Virtue of Ignorance)",
    "The Revenant",
    "La La Land",
    "The Shape of Water",
    "Roma",
    "Parasite",
    "Nomadland",
    "The Power of the Dog",
    "Everything Everywhere All at Once",
    "Oppenheimer",
    "Anora",
    "One Battle after Another",
]
ACTOR = [
    "Gladiator",
    "Training Day",
    "The Pianist",
    "Mystic River",
    "Ray",
    "Capote",
    "The Last King of Scotland",
    "There Will Be Blood",
    "Milk",
    "Crazy Heart",
    "The King's Speech",
    "The Artist",
    "Lincoln",
    "Dallas Buyers Club",
    "The Theory of Everything",
    "The Revenant",
    "Manchester by the Sea",
    "Darkest Hour",
    "Bohemian Rhapsody",
    "Joker",
    "The Father",
    "King Richard",
    "The Whale",
    "Oppenheimer",
    "The Brutalist",
    "Sinners",
]


def raw_rows() -> list[dict]:
    text = gzip.decompress((OSCARS / "oscars.csv.gz").read_bytes()).decode("utf-8")
    return list(csv.DictReader(io.StringIO(text), delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\"))


def winners(year: int, award: Award) -> list[str]:
    return [title for title, awards in STANDINGS[year].values() if awards.get(award.value)]


def test_the_snapshot_is_the_pinned_one_and_data_py_is_built_from_it() -> None:
    assert TARGET.read_text(encoding="utf-8") == render(build())


def test_every_film_year_has_one_ceremony_numbered_from_it() -> None:
    assert (FIRST_YEAR, LAST_YEAR) == (1928, 2025)
    assert list(CEREMONIES) == list(range(1928, 2026))
    assert all(number == year - 1927 for year, (number, _) in CEREMONIES.items())
    assert CEREMONIES[2023][0] == 96  # held March 10, 2024


def test_nominations_agree_with_the_raw_table() -> None:
    # Read apart from build_data.py: each row's award from its canonical category, one count per film it names.
    award_of = {category: award for award, categories in AWARDS.items() for category in categories}
    raw = Counter()
    for row in raw_rows():
        award = award_of.get(row["CanonicalCategory"])
        if award and row["Category"] not in HONORARY and row["Film"]:
            for title in row["Film"].split("|"):
                raw[(int(row["Ceremony"]) + 1927, award, title, row["Name"], row["Winner"] == "True")] += 1
    data = Counter((year, *nomination) for year, (_, rows) in CEREMONIES.items() for nomination in rows)
    assert data == raw and sum(data.values()) == 10153


def test_nominations_go_award_by_award() -> None:
    order = [award.value for award in Award]
    for _, rows in CEREMONIES.values():
        positions = [order.index(award) for award, *_ in rows]
        assert positions == sorted(positions)


@pytest.mark.parametrize(("year", "title"), BEST_PICTURE.items())
def test_best_picture_winners_are_the_ones_written_down_by_hand(year: int, title: str) -> None:
    assert [folded(found) for found in winners(year, A.BEST_PICTURE)] == [folded(title)]


def test_directing_and_actor_winners_are_the_ones_written_down_by_hand() -> None:
    for year, director, actor in zip(range(2000, 2026), DIRECTING, ACTOR):
        assert winners(year, A.DIRECTING) == [director], year
        assert winners(year, A.ACTOR) == [actor], year


def test_ties_and_split_awards_give_two_winners() -> None:
    assert sorted(winners(1968, A.ACTRESS)) == ["Funny Girl", "The Lion in Winter"]  # Hepburn and Streisand tied
    assert sorted(winners(1932, A.ACTOR)) == ["Dr. Jekyll and Mr. Hyde", "The Champ"]  # March and Beery tied
    assert sorted(winners(1939, A.CINEMATOGRAPHY)) == [
        "Gone with the Wind",
        "Wuthering Heights",
    ]  # color, black-and-white
    assert sorted(winners(1928, A.DIRECTING)) == ["7th Heaven", "Two Arabian Knights"]  # dramatic, comedy
    assert sorted(winners(2025, A.LIVE_ACTION_SHORT)) == ["The Singers", "Two People Exchanging Saliva"]


def test_a_nomination_of_several_films_counts_for_each() -> None:
    # Janet Gaynor won for three films, and Street Angel was nominated again the next year.
    for title in ["7th Heaven", "Street Angel", "Sunrise"]:
        assert STANDINGS[1928][folded(title)][1]["actress"] is True
    assert [year for year, *_ in records("Street Angel")] == [1928, 1929]


def test_honorary_and_filmless_awards_are_left_out() -> None:
    # Rashomon's 1951 award was honorary; its one competitive nomination came a year later.
    assert [(year, [award for award, _, _ in kept]) for year, _, _, kept in records("Rashomon")] == [
        (1952, ["production_design"])
    ]
    assert winners(1956, A.INTERNATIONAL_FEATURE) == ["La Strada"]  # the first competitive one
    assert all(title for _, (_, rows) in CEREMONIES.items() for _, title, _, _ in rows)


def test_remakes_are_separate_films() -> None:
    assert [year for year, *_ in records("little women")] == [1933, 1949, 1994, 2019]
    assert [year for year, *_ in records("A Star Is Born")] == [1937, 1954, 1976, 2018]


def test_titles_compare_folded() -> None:
    assert folded("  Amélie ") == folded("AMELIE") == "amelie"
    assert folded("Schindler’s  List") == folded("schindler's list")
    assert records("TÁR") == records("Tár") and records("Tar")


# Queries worked out by hand from the winners above.
@pytest.mark.parametrize(
    ("query", "films"),
    [
        (
            (2000, 2024, [A.BEST_PICTURE, A.DIRECTING], [A.ACTOR], []),  # the README's example
            [
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
            ],
        ),
        (
            (1928, 2025, [A.BEST_PICTURE, A.DIRECTING, A.ACTOR, A.ACTRESS], [], []),  # the big five
            [
                ("It Happened One Night", 1934),
                ("One Flew over the Cuckoo's Nest", 1975),
                ("The Silence of the Lambs", 1991),
            ],
        ),
        (
            (2000, 2024, [A.BEST_PICTURE], [A.DIRECTING], []),  # not won: Argo, Green Book and CODA were not nominated
            [
                ("Gladiator", 2000),
                ("Chicago", 2002),
                ("Crash", 2005),
                ("Argo", 2012),
                ("12 Years a Slave", 2013),
                ("Spotlight", 2015),
                ("Moonlight", 2016),
                ("Green Book", 2018),
                ("CODA", 2021),
            ],
        ),
        (
            (2000, 2024, [A.BEST_PICTURE], [], [A.DIRECTING]),  # nominated but lost
            [
                ("Gladiator", 2000),
                ("Chicago", 2002),
                ("Crash", 2005),
                ("12 Years a Slave", 2013),
                ("Spotlight", 2015),
                ("Moonlight", 2016),
            ],
        ),
        ((2023, 2023, [A.DIRECTING], [A.BEST_PICTURE], []), []),
        ((2000, 2025, [A.ACTOR], [A.ACTOR], []), []),  # contradictory conditions name no film
        ((2025, 2025, [A.CASTING], [A.BEST_PICTURE], []), []),
        ((2010, 2010, [A.ACTOR, A.BEST_PICTURE], [], [A.SUPPORTING_ACTOR]), [("The King's Speech", 2010)]),
    ],
)
def test_each_query_has_the_films_worked_out_by_hand(query: tuple, films: list) -> None:
    status, _, found = expected(*query)
    assert (status, found) == (Status.FOUND if films else Status.NO_MATCHES, films)


@pytest.mark.parametrize(
    ("query", "status"),
    [
        ((2024, 2000, [A.ACTOR], [], []), Status.INVALID_YEARS),
        ((2030, 1900, [], [], []), Status.INVALID_YEARS),  # the order first
        ((1927, 2000, [A.ACTOR], [], []), Status.OUT_OF_RANGE),
        ((2000, 2026, [A.ACTOR], [], []), Status.OUT_OF_RANGE),
        ((2026, 2026, [], [], []), Status.OUT_OF_RANGE),  # the range before the conditions
        ((2000, 2024, [], [A.ACTOR], []), Status.NO_CONDITION),
        ((2000, 2024, [], [], []), Status.NO_CONDITION),
        ((1928, 1928, [], [], [A.ACTOR]), Status.FOUND),
        ((2025, 2025, [A.CASTING], [], []), Status.FOUND),
    ],
)
def test_each_query_has_its_status(query: tuple, status: Status) -> None:
    got = expected(*query)
    assert got[0] is status and (got[2] == []) is (status is not Status.FOUND)


def test_gets_a_ceremonys_nominations(tmp_path: Path) -> None:
    found = get_ceremony(CeremonyInput(year=2023, awards=[A.ACTOR, A.BEST_PICTURE, A.ACTOR]), tmp_path)
    assert (found.year, found.ceremony) == (2023, 96)
    assert [row.award for row in found.nominations] == [A.BEST_PICTURE] * 10 + [A.ACTOR] * 5
    assert [(row.film, row.nominee) for row in found.nominations if row.won] == [
        ("Oppenheimer", "Emma Thomas, Charles Roven and Christopher Nolan, Producers"),
        ("Oppenheimer", "Cillian Murphy"),
    ]
    first = get_ceremony(CeremonyInput(year=1928, awards=[A.ACTRESS]), tmp_path)
    assert [(row.film, row.won) for row in first.nominations if row.nominee == "Janet Gaynor"] == [
        ("7th Heaven", True),
        ("Street Angel", True),
        ("Sunrise", True),
    ]
    assert get_ceremony(CeremonyInput(year=2000, awards=[]), tmp_path).nominations == []
    for year in [1927, 2026, 0]:
        with pytest.raises(ValueError, match="no ceremony"):
            get_ceremony(CeremonyInput(year=year, awards=[A.ACTOR]), tmp_path)


def test_gets_a_films_records(tmp_path: Path) -> None:
    found = get_film_awards(FilmInput(title=" parasite "), tmp_path)
    assert found.title == " parasite " and [(film.title, film.year, film.ceremony) for film in found.films] == [
        ("Parasite", 2019, 92)
    ]
    assert [(row.award, row.won) for row in found.films[0].nominations] == [
        (A.BEST_PICTURE, True),
        (A.DIRECTING, True),
        (A.ORIGINAL_SCREENPLAY, True),
        (A.INTERNATIONAL_FEATURE, True),
        (A.FILM_EDITING, False),
        (A.PRODUCTION_DESIGN, False),
    ]
    assert len(nominations(2019, [A.BEST_PICTURE])) == 9
    for title in ["Paracite", "", "The Room"]:
        with pytest.raises(ValueError, match="no such film"):
            get_film_awards(FilmInput(title=title), tmp_path)

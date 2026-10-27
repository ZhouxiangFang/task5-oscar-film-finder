"""Builds verifier/data.py from the frozen Academy Awards snapshot in tests/oscars/.

    uv run python tests/build_data.py

One file, downloaded on SNAPSHOT_DAY and gzipped; it is checked against its SHA-256 (taken before gzip) before anything
is read:

- oscars.csv.gz: oscars.csv of DLu/oscar_data at commit COMMIT,
  https://raw.githubusercontent.com/DLu/oscar_data/<COMMIT>/oscars.csv, a tab-separated table of every nomination of
  the 1st to the 98th Academy Awards, parsed from the Academy's own database, https://awardsdatabase.oscars.org/.
  Its BSD 2-Clause license is tests/oscars/LICENSE.

The rules:

- A ceremony's film year is the Year it honors; a two-year season of the first six ceremonies, such as 1927/28,
  counts as its later year. Every film year from 1928 to 2025 then has exactly one ceremony, numbered the year minus
  1927.
- Each award is the canonical categories AWARDS gives it: present names and earlier ones (the snapshot's
  CanonicalCategory already joins those), the black-and-white and color awards of 1939 to 1966, and the 1st
  ceremony's two directing awards. The honorary foreign language film awards of 1950 to 1955 are not
  international_feature. Every other canonical category (honorary, scientific and technical, and discontinued ones)
  is left out, and IGNORED names each, so a new category in a later snapshot stops the build.
- A nomination naming several films, as some in the first ceremonies did, counts once for each film. A nomination
  naming no film (studio sound departments, two effects engineers of the 1st ceremony) is left out.
- Within a ceremony a title names one film: two IMDb ids under one title, or one id under two titles, stop the build.
  Every award at every ceremony has a winner.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent
OSCARS = HERE / "oscars"
TARGET = HERE.parent / "verifier" / "data.py"
SNAPSHOT_DAY = "2026-10-26"
COMMIT = "c5e9716b7e020e70205d6b95f5a5678526c1b45f"
SHA256 = {"oscars.csv.gz": "3b1d39eedad7303468b83323f51bd1069289a2710ff9873efc4b4298ae1bba78"}
COLUMNS = [
    "Ceremony",
    "Year",
    "Class",
    "CanonicalCategory",
    "Category",
    "Film",
    "FilmId",
    "Name",
    "Nominees",
    "NomineeIds",
    "Winner",
    "Detail",
    "Note",
    "Citation",
]
# award -> the snapshot's canonical categories it joins, in contract.Award's order
AWARDS = {
    "best_picture": ["BEST PICTURE"],
    "directing": ["DIRECTING", "DIRECTING (Comedy Picture)", "DIRECTING (Dramatic Picture)"],
    "actor": ["ACTOR IN A LEADING ROLE"],
    "actress": ["ACTRESS IN A LEADING ROLE"],
    "supporting_actor": ["ACTOR IN A SUPPORTING ROLE"],
    "supporting_actress": ["ACTRESS IN A SUPPORTING ROLE"],
    "original_screenplay": ["WRITING (Original Screenplay)"],
    "adapted_screenplay": ["WRITING (Adapted Screenplay)"],
    "international_feature": ["INTERNATIONAL FEATURE FILM"],
    "animated_feature": ["ANIMATED FEATURE FILM"],
    "documentary_feature": ["DOCUMENTARY (Feature)"],
    "cinematography": ["CINEMATOGRAPHY", "CINEMATOGRAPHY (Black-and-White)", "CINEMATOGRAPHY (Color)"],
    "film_editing": ["FILM EDITING"],
    "production_design": ["ART DIRECTION", "ART DIRECTION (Black-and-White)", "ART DIRECTION (Color)"],
    "costume_design": ["COSTUME DESIGN", "COSTUME DESIGN (Black-and-White)", "COSTUME DESIGN (Color)"],
    "makeup_and_hairstyling": ["MAKEUP AND HAIRSTYLING"],
    "original_score": ["MUSIC (Original Score)"],
    "original_song": ["MUSIC (Original Song)"],
    "sound": ["SOUND RECORDING", "SOUND MIXING"],
    "sound_editing": ["SOUND EDITING"],
    "visual_effects": ["VISUAL EFFECTS"],
    "casting": ["CASTING"],
    "animated_short": ["SHORT FILM (Animated)"],
    "live_action_short": ["SHORT FILM (Live Action)"],
    "documentary_short": ["DOCUMENTARY (Short Subject)"],
}
# The categories under international_feature's canonical one that were honorary, not competitive.
HONORARY = {"HONORARY FOREIGN LANGUAGE FILM AWARD"}
IGNORED = {
    "UNIQUE AND ARTISTIC PICTURE",
    "WRITING (Original Story)",
    "WRITING (Title Writing)",
    "ASSISTANT DIRECTOR",
    "DANCE DIRECTION",
    "MUSIC (Original Song Score or Adaptation Score)",
    "SHORT SUBJECT (Comedy)",
    "SHORT SUBJECT (Novelty)",
    "SHORT SUBJECT (Color)",
    "SHORT SUBJECT (One-reel)",
    "SHORT SUBJECT (Two-reel)",
    "SPECIAL AWARD",
    "SPECIAL FOREIGN LANGUAGE FILM AWARD",
    "HONORARY AWARD",
    "IRVING G. THALBERG MEMORIAL AWARD",
    "JEAN HERSHOLT HUMANITARIAN AWARD",
    "GORDON E. SAWYER AWARD",
    "AWARD OF COMMENDATION",
    "MEDAL OF COMMENDATION",
    "JOHN A. BONNER MEDAL OF COMMENDATION",
    "SPECIAL ACHIEVEMENT AWARD",
    "SPECIAL ACHIEVEMENT AWARD (Visual Effects)",
    "SPECIAL ACHIEVEMENT AWARD (Sound Effects)",
    "SPECIAL ACHIEVEMENT AWARD (Sound Effects Editing)",
    "SPECIAL ACHIEVEMENT AWARD (Sound Editing)",
    "SCIENTIFIC OR TECHNICAL AWARD (Class I)",
    "SCIENTIFIC OR TECHNICAL AWARD (Class II)",
    "SCIENTIFIC OR TECHNICAL AWARD (Class III)",
    "SCIENTIFIC AND TECHNICAL AWARD (Academy Award of Merit)",
    "SCIENTIFIC AND TECHNICAL AWARD (Scientific and Engineering Award)",
    "SCIENTIFIC AND TECHNICAL AWARD (Technical Achievement Award)",
    "SCIENTIFIC AND TECHNICAL AWARD (Special Award)",
}
FIRST_CEREMONY_YEAR = 1927


def read(name: str) -> str:
    data = gzip.decompress((OSCARS / name).read_bytes())
    if hashlib.sha256(data).hexdigest() != SHA256[name]:
        raise SystemExit(f"tests/oscars/{name} is not the pinned snapshot: its SHA-256 differs")
    return data.decode("utf-8")


def folded(text: str) -> str:
    """``text`` as verifier/checks.py compares titles: accents and curly quotes dropped, case folded, spaces made one."""
    plain = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    return " ".join(plain.translate(str.maketrans("‘’“”", "''\"\"")).casefold().split())


def film_year(ceremony: int, written: str) -> int:
    """The film year of a ceremony that honors ``written``, such as 1934 or the season 1927/28."""
    first, _, later = written.partition("/")
    year = int(first) + 1 if later else int(first)
    if later and later != f"{year % 100:02d}":
        raise SystemExit(f"ceremony {ceremony} honors {written!r}, which is not a two-year season")
    if year != FIRST_CEREMONY_YEAR + ceremony:
        raise SystemExit(f"ceremony {ceremony} honors {written!r}, not the year {FIRST_CEREMONY_YEAR + ceremony}")
    return year


def build() -> dict:
    # The snapshot writes every double quote as \" and quotes no field.
    text = io.StringIO(read("oscars.csv.gz"))
    table = csv.DictReader(text, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\")
    if table.fieldnames != COLUMNS:
        raise SystemExit(f"the snapshot's columns are {table.fieldnames}, not {COLUMNS}")
    award_of = {category: award for award, categories in AWARDS.items() for category in categories}
    ceremonies: dict[int, tuple[int, dict[str, list]]] = {}
    for row in table:
        number = int(row["Ceremony"])
        year = film_year(number, row["Year"])
        _, by_award = ceremonies.setdefault(year, (number, {award: [] for award in AWARDS}))
        canonical, won = row["CanonicalCategory"], row["Winner"]
        if won not in ("True", "", None):
            raise SystemExit(f"a nomination of ceremony {number} has Winner {won!r}")
        if canonical in IGNORED or row["Category"] in HONORARY:
            continue
        if canonical not in award_of:
            raise SystemExit(f"the snapshot has a category neither an award nor ignored: {canonical!r}")
        if not row["Film"]:
            continue
        titles = row["Film"].split("|")
        ids = row["FilmId"].split("|") if row["FilmId"] else [""] * len(titles)
        if len(ids) != len(titles):
            raise SystemExit(f"ceremony {number}'s nomination of {row['Film']!r} has {len(ids)} film ids")
        for title, film_id in zip(titles, ids):
            if title != " ".join(title.split()):
                raise SystemExit(f"the title {title!r} has spaces around it or a run of them")
            by_award[award_of[canonical]].append((title, film_id, row["Name"], won == "True"))
    if sorted(ceremonies) != list(range(min(ceremonies), max(ceremonies) + 1)):
        raise SystemExit("the snapshot leaves out a ceremony")
    kept = {}
    for year, (number, by_award) in ceremonies.items():
        named: dict[str, set[str]] = {}
        for award, nominations in by_award.items():
            if nominations and not any(won for *_, won in nominations):
                raise SystemExit(f"{award} has no winner in {year}")
            for title, film_id, _, _ in nominations:
                named.setdefault(folded(title), set()).add((title, film_id))
        for found in named.values():
            if len({title for title, _ in found}) > 1 or len({film_id for _, film_id in found} - {"", "?"}) > 1:
                raise SystemExit(f"{year} names two films alike or one film two ways: {sorted(found)}")
        ids = [film_id for found in named.values() for _, film_id in found if film_id not in ("", "?")]
        if len(ids) != len(set(ids)):
            raise SystemExit(f"{year} gives one film id to two titles")
        rows = [
            (award, title, nominee, won)
            for award, nominations in by_award.items()
            for title, _, nominee, won in nominations
        ]
        kept[year] = (number, rows)
    return {"ceremonies": kept}


def quoted(text: str) -> str:
    """``text`` as a Python string the way ruff formats one: double-quoted unless single quotes need fewer escapes."""
    double = json.dumps(text, ensure_ascii=False)
    if text.count('"') <= text.count("'"):
        return double
    return "'" + double[1:-1].replace('\\"', '"').replace("'", "\\'") + "'"


def nomination(award: str, title: str, nominee: str, won: bool) -> list[str]:
    """A nomination's line in CEREMONIES, or its lines where ruff would split one longer than 120 characters."""
    fields = [quoted(award), quoted(title), quoted(nominee), str(won)]
    line = f"            ({', '.join(fields)}),"
    if len(line) <= 120:
        return [line]
    return ["            (", *(f"                {field}," for field in fields), "            ),"]


def render(data: dict) -> str:
    ceremonies = data["ceremonies"]
    first, last = min(ceremonies), max(ceremonies)
    count = sum(len(rows) for _, rows in ceremonies.values())
    films = len({(year, folded(title)) for year, (_, rows) in ceremonies.items() for _, title, _, _ in rows})
    lines = [
        '"""Academy Award nominations and winners: a frozen snapshot, built by tests/build_data.py from tests/oscars/',
        f"(DLu/oscar_data at commit {COMMIT[:7]}, downloaded {SNAPSHOT_DAY}), which says how.",
        "",
        "This is the one copy of the data. The plugin's tools read it, and the verifier judges every tool output and every",
        "answer against it, so no verdict trusts what a tool returned.",
        "",
        (
            f"Ceremonies {ceremonies[first][0]} to {ceremonies[last][0]}, film years {first} to {last}; "
            f'{len(AWARDS)} awards; {count} nominations of {films} films."""'
        ),
        "",
        f"FIRST_YEAR = {first}",
        f"LAST_YEAR = {last}",
        "",
        "# film year -> (its ceremony's number, its nominations award by award in contract.Award's order, each award's in",
        "# the Academy's order, one for each film named: (award, film title, nominee, whether it won))",
        "CEREMONIES = {",
    ]
    for year, (number, rows) in ceremonies.items():
        lines += [f"    {year}: (", f"        {number},", "        ["]
        lines += [line for row in rows for line in nomination(*row)]
        lines += ["        ],", "    ),"]
    lines += ["}", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    TARGET.write_text(render(build()), encoding="utf-8")
    print(f"wrote {TARGET}")

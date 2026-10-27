# Oscar Film Finder

List the films that meet conditions on their Academy Awards. Give a range of years and up to three lists of awards:
awards the film won, awards it did not win, and awards it was nominated for but lost. You do not need to know any film
names. The agent reads each year's nominations, groups them by film, checks each candidate's full record, and lists
every film that meets all the conditions. A deterministic verifier works out the complete list from the same fixed copy
of the Academy's records, then reports any missing or wrong films with the records behind each one.

The data covers the 1st to the 98th Academy Awards, held 1929 to 2026, which honored the films of **1928 to 2025**. The
plugin runs offline and needs no API key.

## Example

Ask: **Which films from 2000 to 2024 won Best Picture and Best Director, but not Best Actor?**

Input:

```json
{"first_year": 2000, "last_year": 2024, "won": ["best_picture", "directing"], "not_won": ["actor"], "nominated_not_won": []}
```

Output:

```json
{"status": "found", "films": [
  {"title": "A Beautiful Mind", "year": 2001},
  {"title": "The Lord of the Rings: The Return of the King", "year": 2003},
  {"title": "Million Dollar Baby", "year": 2004},
  {"title": "The Departed", "year": 2006},
  {"title": "No Country for Old Men", "year": 2007},
  {"title": "Slumdog Millionaire", "year": 2008},
  {"title": "The Hurt Locker", "year": 2009},
  {"title": "Birdman or (The Unexpected Virtue of Ignorance)", "year": 2014},
  {"title": "The Shape of Water", "year": 2017},
  {"title": "Parasite", "year": 2019},
  {"title": "Nomadland", "year": 2020},
  {"title": "Everything Everywhere All at Once", "year": 2022},
  {"title": "Anora", "year": 2024}
]}
```

Sixteen films of those years won both Best Picture and Best Director. The King's Speech, The Artist and Oppenheimer
also won Best Actor, so they are left out. A Beautiful Mind (Russell Crowe was nominated and lost) and The Return of the
King (no one was nominated) both count as not winning it.

## Conditions

| Field | A film meets it when |
|---|---|
| `first_year`, `last_year` | It was nominated at a ceremony honoring a film year in this range, both ends included. |
| `won` | For every award listed, one of its nominations won. |
| `not_won` | For every award listed, none of its nominations won. **A film not nominated for an award has not won it.** |
| `nominated_not_won` | For every award listed, it was nominated and none of its nominations won. |

"Did not win" and "nominated but lost" are different conditions: to ask for films that were nominated for Best Actor
and lost, list `actor` under `nominated_not_won`, not `not_won`. From 2000 to 2024, 9 Best Picture winners did not win
Best Director, but only 6 were nominated for it and lost: Argo, Green Book and CODA had no directing nomination.

Any of the three award lists may be used alone. Searches cover films nominated for at least one of the dataset's
25 awards, not every film released. For example, "Which films from 2000 to 2024 did not win Best Actor?" lists every
film in that range in the dataset except Best Actor winners, including films with no Best Actor nomination.
With all three lists empty, every film in the dataset for the requested years is returned.
An award may appear in several lists; conditions that contradict each other match no film.

A **film year** is the year whose films a ceremony honors: the 96th Academy Awards, held on March 10, 2024, honored the
films of 2023, so its year is 2023. The first six ceremonies honored seasons spanning two years, such as 1927/28; each
counts as its later year, so every year from 1928 to 2025 has exactly one ceremony, numbered the year minus 1927.

A film is its title and its year. Each film is judged by its nominations at one ceremony. A film nominated at two
ceremonies, such as a foreign film nominated for International Feature one year and for other awards the next, is a
separate entry at each. A nomination naming several films, as some at the first ceremonies did, counts for each film:
Janet Gaynor's 1928 Best Actress award counts as a win for 7th Heaven, Street Angel and Sunrise.

## Awards

Each award includes its earlier names. Black-and-white and color awards, given separately in cinematography, art
direction and costume design until 1966, count as one award, so those years have two winners. Ties also give two.

| Award | Years | Includes |
|---|---|---|
| `best_picture` | 1928–2025 | Outstanding Picture, Outstanding Production, Outstanding Motion Picture, Best Motion Picture |
| `directing` | 1928–2025 | The 1st ceremony's comedy and dramatic directing awards |
| `actor`, `actress` | 1928–2025 | Leading roles |
| `supporting_actor`, `supporting_actress` | 1936–2025 | |
| `original_screenplay` | 1940–2025 | Story and Screenplay, Screenplay Written Directly for the Screen |
| `adapted_screenplay` | 1928–2025 | Adaptation, Screenplay, Screenplay Based on Material from Another Medium |
| `international_feature` | 1956–2025 | Foreign Language Film; the honorary awards before 1956 are left out |
| `animated_feature` | 2001–2025 | |
| `documentary_feature` | 1942–2025 | |
| `cinematography` | 1928–2025 | |
| `film_editing` | 1934–2025 | |
| `production_design` | 1928–2025 | Art Direction |
| `costume_design` | 1948–2025 | |
| `makeup_and_hairstyling` | 1981–2025 | Makeup |
| `original_score` | 1938–2025 | Music Score of a Dramatic or Comedy Picture, Original Dramatic Score |
| `original_song` | 1934–2025 | Song |
| `sound` | 1930–2025 | Sound Recording, Sound Mixing, Sound |
| `sound_editing` | 1963–2019 | Sound Effects, Sound Effects Editing |
| `visual_effects` | 1928–2025 | Engineering Effects, Special Effects, Special Visual Effects |
| `casting` | 2025 | |
| `animated_short` | 1932–2025 | Short Subject (Cartoon) |
| `live_action_short` | 1957–2025 | Short Subject (Live Action) |
| `documentary_short` | 1941–2025 | |

## Statuses

Checks run in this order, the first that holds deciding:

| Status | Meaning |
|---|---|
| `invalid_years` | `first_year` is after `last_year`. |
| `out_of_range` | A year is outside 1928 to 2025. |
| `no_matches` | The query is valid, but no films meet all conditions. |
| `found` | One or more films meet all conditions; the complete list is returned. |

Unless the status is `found`, `films` is empty.

For example, "Which 2025 films won the Oscar for Casting but did not win Best Picture?" returns
`{"status": "no_matches", "films": []}`. In the bundled dataset, One Battle after Another won both awards,
so it is excluded by the Best Picture condition.

## Tools

| Tool | Purpose |
|---|---|
| `get_ceremony` | Give one year's ceremony number and its nominations for the awards asked about: award, film, nominee, and whether it won. |
| `get_film_awards` | Give every nomination of a film, for every award, at each ceremony it was nominated at. Films sharing a title are told apart by year. |

The `find-films` task uses both. The agent reads the nominations for the `won` and `nominated_not_won` awards year by
year to find candidates, then reads each candidate's record to drop any that won a `not_won` award. No tool applies the
conditions: the agent filters the films itself.

For `not_won`-only or unfiltered searches, the agent reads all award categories for each year and filters those nominations directly.

## Verification

The verifier works out the status and the complete list of films from the data. A found list must name every film that
meets the conditions, each once, with its year, and no other. Titles are compared ignoring case, accents, curly quotes
and runs of spaces, and the order of the list is free.

A wrong list gets partial credit: the F1 score of its films against the right ones, which is 0 when no film is right.
The verdict names each missing film and each wrong one with its records for the awards the query names, such as
`Oppenheimer (2023): best_picture won, directing won, actor won`. A wrong film can also have no nomination in that year,
or be listed more than once. A wrong status is refused. Typed contracts refuse malformed answers, and every tool output
is checked against the data.

Tests cover each status and the order they are checked in, every Best Picture winner and the Best Director and Best
Actor winners of 2000 to 2025 against lists written down by hand, the README's example and other queries worked out by
hand, ties, black-and-white and color awards, nominations of several films, remakes, honorary awards, the difference
between `not_won` and `nominated_not_won`, and the agent's procedure played through the tools on 310 queries.

## Layout

`contract.py` defines typed inputs and outputs; `nanoagent.yaml` defines tools and task instructions. Tool
implementations live in `src/plugin/`, verification in `verifier/`, and tests and the Academy Awards snapshot in
`tests/`.

## Develop and run

Requires Git, uv, and Python 3.12 or later.

```bash
git clone https://github.com/ZhouxiangFang/task5-oscar-film-finder.git
cd task5-oscar-film-finder
uv sync --extra dev
uv run pytest
uv run ruff check .
```

Check plugin packaging:

```bash
uvx --from "git+https://github.com/RUSH-LAB/nanoagent#subdirectory=nanoagent" nanoagent plugin inspect .
```

Rebuild the generated data:

```bash
uv run python tests/build_data.py
```

## Data and limitations

Source: [DLu/oscar_data](https://github.com/DLu/oscar_data), a table of every Academy Award nomination parsed from the
Academy's own [Awards Database](https://awardsdatabase.oscars.org/). `tests/oscars/oscars.csv.gz` is its `oscars.csv`
at commit `c5e9716`, downloaded on October 26, 2026 and pinned by SHA-256 in `tests/build_data.py`; its BSD 2-Clause
license is `tests/oscars/LICENSE`. A test checks that `verifier/data.py` matches a fresh rebuild. The 98th ceremony's
winners were checked against Wikipedia's page for it.

This version covers 25 competitive awards. It leaves out honorary, special, and scientific and technical awards, and
discontinued categories: Unique and Artistic Picture, Original Story, Title Writing, Assistant Director, Dance
Direction, Song Score and Adaptation Score, and the one-reel, two-reel, color, comedy and novelty short subjects. A
nomination naming no film, such as a studio sound department's in 1931 and 1932, is left out. Titles are written as
the Academy's database writes them, such as One Battle after Another; other spellings and alternate titles do not
match. A film's year is its ceremony's, not its release year. Ceremonies after the 98th are not covered.

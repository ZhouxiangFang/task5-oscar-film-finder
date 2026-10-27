"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    GET_CEREMONY = "get_ceremony"
    GET_FILM_AWARDS = "get_film_awards"


class Task(Enum):
    FIND_FILMS = "find-films"


class Award(Enum):
    BEST_PICTURE = "best_picture"
    DIRECTING = "directing"
    ACTOR = "actor"
    ACTRESS = "actress"
    SUPPORTING_ACTOR = "supporting_actor"
    SUPPORTING_ACTRESS = "supporting_actress"
    ORIGINAL_SCREENPLAY = "original_screenplay"
    ADAPTED_SCREENPLAY = "adapted_screenplay"
    INTERNATIONAL_FEATURE = "international_feature"
    ANIMATED_FEATURE = "animated_feature"
    DOCUMENTARY_FEATURE = "documentary_feature"
    CINEMATOGRAPHY = "cinematography"
    FILM_EDITING = "film_editing"
    PRODUCTION_DESIGN = "production_design"
    COSTUME_DESIGN = "costume_design"
    MAKEUP_AND_HAIRSTYLING = "makeup_and_hairstyling"
    ORIGINAL_SCORE = "original_score"
    ORIGINAL_SONG = "original_song"
    SOUND = "sound"
    SOUND_EDITING = "sound_editing"
    VISUAL_EFFECTS = "visual_effects"
    CASTING = "casting"
    ANIMATED_SHORT = "animated_short"
    LIVE_ACTION_SHORT = "live_action_short"
    DOCUMENTARY_SHORT = "documentary_short"


class Status(Enum):
    FOUND = "found"
    NO_MATCHES = "no_matches"
    INVALID_YEARS = "invalid_years"
    OUT_OF_RANGE = "out_of_range"
    NO_CONDITION = "no_condition"


YEAR = (
    "A film year, 1928 to 2025: the year whose films a ceremony honors, so 2023 is the 96th Academy Awards, held in "
    "2024; a two-year season of the first six ceremonies, such as 1927/28, counts as its later year"
)
FIRST_YEAR = (
    "The first film year searched, such as 2000. A film year is the year whose films a ceremony honors, so 2023 is "
    "the 96th Academy Awards, held in 2024; a two-year season of the first six ceremonies, such as 1927/28, counts as "
    "its later year"
)
AWARDS = (
    "The awards whose nominations to read, each an Academy Award category under its present name, earlier names "
    "included: actor and actress are leading roles, production_design was art direction, sound was sound recording, "
    "then sound mixing; black-and-white and color awards count as one"
)
STATUS = (
    "found: one or more films match; no_matches: no films meet all conditions; "
    "invalid_years: first_year is after last_year; out_of_range: a year is outside "
    "1928 to 2025; no_condition: won and nominated_not_won are both empty"
)


@dataclass
class SearchInput(Output):
    first_year: Annotated[int, FIRST_YEAR]
    last_year: Annotated[int, "The last film year searched, such as 2024; the range includes it"]
    won: Annotated[list[Award], "The film won every one of these awards"]
    not_won: Annotated[
        list[Award], "The film won none of these awards; a film not nominated for an award has not won it"
    ]
    nominated_not_won: Annotated[list[Award], "The film was nominated for every one of these awards and won none"]


@dataclass
class Film(Output):
    title: Annotated[str, "The film's title as the Academy's records give it, such as Parasite"]
    year: Annotated[int, "The film year of the ceremony whose records meet the conditions, such as 2019"]


@dataclass
class FilmsOutput(Output):
    status: Annotated[Status, STATUS]
    films: Annotated[
        list[Film], "Every film that meets the conditions, each once and in any order; empty unless status is found"
    ]


@dataclass
class CeremonyInput(Output):
    year: Annotated[int, YEAR]
    awards: Annotated[list[Award], AWARDS]


@dataclass
class Nomination(Output):
    award: Annotated[Award, "The award"]
    film: Annotated[str, "The nominated film's title"]
    nominee: Annotated[str, "Who or what is nominated, as the Academy writes it, such as Cillian Murphy"]
    won: Annotated[bool, "Whether the nomination won the award"]


@dataclass
class CeremonyOutput(Output):
    year: Annotated[int, "The film year asked about"]
    ceremony: Annotated[int, "The ceremony's number, such as 96 for the 96th Academy Awards"]
    nominations: Annotated[
        list[Nomination], "Every nomination for the awards asked about, award by award, one for each film it names"
    ]


@dataclass
class FilmInput(Output):
    title: Annotated[str, "A film's title, such as Parasite; case, accents, and runs of spaces are ignored"]


@dataclass
class AwardRecord(Output):
    award: Annotated[Award, "The award"]
    nominee: Annotated[str, "Who or what is nominated, as the Academy writes it"]
    won: Annotated[bool, "Whether the nomination won the award"]


@dataclass
class FilmRecord(Output):
    title: Annotated[str, "The film's title as the Academy's records give it"]
    year: Annotated[int, "The film year of the ceremony"]
    ceremony: Annotated[int, "The ceremony's number"]
    nominations: Annotated[list[AwardRecord], "Every nomination of the film at this ceremony, award by award"]


@dataclass
class FilmAwardsOutput(Output):
    title: Annotated[str, "The title asked about, unchanged"]
    films: Annotated[list[FilmRecord], "Each ceremony at which a film with this title was nominated, earliest first"]


TOOLS = {
    Tool.GET_CEREMONY: (CeremonyInput, CeremonyOutput),
    Tool.GET_FILM_AWARDS: (FilmInput, FilmAwardsOutput),
}
TASKS = {Task.FIND_FILMS: (SearchInput, FilmsOutput)}

"""
Define data model for climbing database.

See overview-aoc.ipynb for more information.
"""

from dataclasses import dataclass, field


@dataclass
class ClimbInfo:
    """Information about a climb at Rumney.

    This is like the guidebook, not a specific ascent of the climb.

    Parameters
    ----------
    name : str
        The name of the climb, e.g. "Kundalini"
    grade : str
        The grade of the climb, e.g. "5.12d"
    aliases : list[str]
        A list of aliases for the climb, e.g. ["Kunda"]
    """

    name: str
    grade: str
    aliases: list[str] = field(default_factory=list)

    def __str__(self):
        return f"{self.name}: {self.grade}"


@dataclass
class ClimbingDay:
    """A day of climbing.

    This is a list of ClimbEntry objects corresponding to a day of climbing.

    Parameters
    ----------
    date : str
        The date of the climbing day, e.g. "2024-06-26"
    log_text : str
        The log entry for the day, e.g. "Holderness, Idiot, Misdemeanor, White Rhino
        (TA, AS found new beta), Espresso (TA)"
    place_and_climbers : str
        The place and climbers for the day, e.g. "Rumney TA AS w/ Art"
    climb_entries : list[ClimbEntry]
        A list of ClimbEntry objects corresponding to this day.
    """

    date: str
    log_text: str
    place_and_climbers: str
    climb_entries: list["ClimbEntry"] = field(default_factory=list)


@dataclass
class ClimbEntry:
    """Climb on a date.

    This is the bit of an climb log entry that corresponds to one Climb, e.g. "2 runs on
    Kundalini (so-so. linked to the top on lead from just after crux)". In this case::

      name_approx: "2 runs on Kundalini"
      comment: "so-so. linked to the top on lead from just after crux".

    The comment hopefully indicates who did it and repetitions and hangs. A ClimbEntry
    often corresponds to multiple ClimbEvent objects.

    Parameters
    ----------
    name_approx : str
        The approximate name of the climb parsed from the ATK comment. Often this is
        not quite right.
    comment : str
        The comment parsed from parenthesized text in the log entry. This often contains
        useful information about the climb, like who did it and repetitions and hangs.
    climbers : list[str]
        A initial list of climbers who did the climb based on the ClimbingDay
        place_and_climbers. It may be overridden by information in the comment.
    climb_info : ClimbInfo
        Information about the climb itself (name, grade, aliases).
    climb_events : list[ClimbEvent]
        A list of ClimbEvent objects corresponding to this climb.
    idx_entry_start : int
        The index in the original log text where this ClimbEntry starts.
    """

    name_approx: str
    comment: str
    climbers: list[str] = field(default_factory=list)
    climb_info: ClimbInfo = field(default=None)
    climb_events: list["ClimbEvent"] = field(default_factory=list)
    idx_entry_start: int = 0

    def __post_init__(self):
        climbers = [climber for climber in ["TA", "AS"] if climber in self.comment]
        if climbers == []:
            climbers = self.climbers.copy()
        for climber in climbers:
            self.climb_events.append(ClimbEvent(climber=climber, hang=False))

    def __str__(self):
        climb_events_str = " ".join(
            str(climb_event) for climb_event in self.climb_events
        )
        lines = [
            f"name_approx: {self.name_approx}",
            f"comment: {self.comment}",
            f"climb_info: {self.climb_info}",
            f"climb_events: {climb_events_str}",
        ]
        return "\n".join(lines)

    def replace_climb_events(self, climber: str, climb_events: list["ClimbEvent"]):
        """Remove all climb events for climber and add new ones"""
        new_climb_events = [
            climb_event
            for climb_event in self.climb_events
            if climb_event.climber != climber
        ]
        new_climb_events.extend(climb_events)
        self.climb_events = new_climb_events


@dataclass
class ClimbEvent:
    """A person doing a climb.

    This is the bit of an ATKlog entry that corresponds to one ascent of a climb.

    Parameters
    ----------
    climber : str
        The climber, e.g. "TA"
    hang : bool
        Did they hang?
    """

    climber: str
    hang: bool

    def __str__(self):
        return f"{self.climber}{' (hang)' if self.hang else ''}"

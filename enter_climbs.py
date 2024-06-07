import argparse
import os
from pathlib import Path
import re
import shelve
import shutil
import textwrap
import typing
import curses.ascii
import time

import numpy as np
import requests
from astropy.table import Table
from thefuzz import fuzz
from astropy.utils.console import Getch

from core import ClimbEntry, ClimbInfo, ClimbEvent, ClimbingDay
from doc_ids import DOC_ID, GIDS

# URL to download exclude Times google sheet
# See https://stackoverflow.com/questions/33713084 (2nd answer)
ATK_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/{doc_id}/export?"
    "format=csv"
    "&id={doc_id}"
    "&gid={gid}"
)

get_key_no_echo: typing.Callable = Getch()


def get_key(delay=0) -> str:
    """Get a single character from standard input without screen echo."""
    out = get_key_no_echo()
    if delay > 0:
        from pyfiglet import figlet_format
        key_repr = curses.ascii.unctrl(out)
        if key_repr == " ":
            key_repr = "<space>"
        key_repr = re.sub(r"\^", "<ctrl>-", key_repr)
        print()
        print(figlet_format(key_repr, font='univers'))
        time.sleep(delay)

    return out


def print_long_repr_of_char(char: str) -> None:
    """Print the long representation of a character.

    For instance " " => "space", "\n" => "newline", etc.
    """
    if char == " ":
        print("space")
    elif char == "\n":
        print("newline")
    elif char == "\t":
        print("tab")
    else:
        print(char)


def get_log_entries_for_date(date: str) -> Table:
    """Get log entries for a date from the ATK sheet.

    ``date`` can be any portion of an ISO date, e.g. "2024" or "2024-06-01", where the
    output will be filtered by matching the start of the date string.
    """
    url = ATK_SHEET_URL.format(doc_id=DOC_ID, gid=GIDS[date[:4]])
    print(f"Getting ATK climbs from {url}")
    req = requests.get(url, timeout=30)
    if req.status_code != 200:
        raise ValueError(f"Failed to get exclude times sheet {url}: {req.status_code}")

    out = Table.read(req.text, format="csv", fill_values=[])
    out = out[:369]
    ok0 = np.array(["rumney" in climb.lower() for climb in out["Climb"]])
    ok1 = np.array([date.strip() != "" for date in out["Date"]])
    log_entries = out["Date", "Climb", "Comments"][ok0 & ok1]

    # Convert date to ISO format
    dates = [date.split("/") for date in log_entries["Date"]]
    dates = [(int(year), int(mon), int(day)) for mon, day, year in dates]
    log_entries["Date"] = [f"{year}-{mon:02d}-{day:02d}" for year, mon, day in dates]

    # Filter by date
    ok = [date_iso.startswith(date) for date_iso in log_entries["Date"]]
    log_entries = log_entries[ok]

    return log_entries


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Enter ATK climbs")
    parser.add_argument(
        "date", default="2024", type=str, help="Year or date to enter times for"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force update of existing entries",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use demo files",
    )
    parser.add_argument(
        "--delay",
        type=float,
        help="Show each key press and delay for this many seconds",
    )
    return parser


def get_climb_entries_from_climbing_day(
    comment: str, date: str, place_and_climbers: str
) -> list[ClimbEntry]:
    """Get a list of ClimbEntry objects from the comments field of the ATK sheet.

    An example comment might be:

      Armed, Obi (AS), Jedi Mind Tricks (TA working moves), Centerpiece (AS 2xlead 2h,
      TA redpoint), Social O (TA,  AS to the top with 2 hangs)

    A ClimbEntry is a climb on a date with an optional comment that might indicate who
    did it and repetitions and hangs. A ClimbEntry can contain multiple ClimbEvent
    objects, each corresponding to one climber getting on the route once.

    This function works as a state machine, parsing the comment character by character.
    This is a bad way to do it, but it works well enough for this use case. A more
    robust solution would be to use a parser generator like PLY.
    """
    state = "name"
    climb_entries = []
    name_approx = ""
    climb_comment = ""
    comment_len = len(comment)
    climbers = [climber for climber in ["TA", "AS"] if climber in place_and_climbers]
    idx_entry_start = 0

    for idx, char in enumerate(comment):
        if char == "(":
            state = "comment"
            continue
        if char == ")":
            state = "name"
            if idx != comment_len - 1:
                continue
        if (
            state == "name"
            and (char in (",", ".", ";", "!", ":", "-") or idx == comment_len - 1)
            and not (name_approx and name_approx[-1] == "5")
        ):
            # Create ClimbEntry. Exact name and climb_events to be filled later.
            climb_entry = ClimbEntry(
                name_approx=name_approx.strip(),
                comment=climb_comment.strip(),
                climbers=climbers,
                idx_entry_start=idx_entry_start,
            )
            climb_entries.append(climb_entry)
            name_approx = ""
            climb_comment = ""
            idx_entry_start = idx + 1
            continue
        if state == "name":
            name_approx += char
        if state == "comment":
            climb_comment += char

    return climb_entries


def make_bold(text: str, climb_entry: ClimbEntry) -> str:
    """Make the approximate climb name bold in the log text."""
    idx = climb_entry.idx_entry_start
    name_approx = climb_entry.name_approx
    length = len(name_approx) + (
        len(climb_entry.comment) + 2 if climb_entry.comment else 0
    )
    out = (
        text[:idx]
        + f"\033[4m\033[1m{text[idx:idx + length + 1]}\033[0m"
        + text[idx + length + 1 :]
    )
    return out


def process_climb_entry(
    climbing_day: ClimbingDay,
    climb_entry: ClimbEntry,
    climbs_info: dict[str, ClimbInfo],
    delay: float = 0,
) -> list[ClimbEvent]:
    """Get a list of ClimbEvent objects from a ClimbEntry object.

    A ClimbEvent is a specific ascent of a climb.
    """
    matches = get_matches(climb_entry, climbs_info)

    if climb_entry.climb_info is None:
        climb_entry.climb_info = climbs_info[matches["name"][0]]

    log_text = "\n".join(textwrap.wrap(climbing_day.log_text, width=100))

    done = False
    while not done:
        os.system("clear")
        print("=" * 80)
        print(climbing_day.date, climbing_day.place_and_climbers)
        print(make_bold(log_text, climb_entry))
        print()
        print(climb_entry)
        print("=" * 80)
        print()
        print(matches[:8])
        print()
        print(
            "<space>, q(uit), [a,t]: 1h, [A,T: custom], ctrl-[a,t]: remove, 0..7, c(limb name) n(ot a climb)"
        )
        key = get_key(delay)

        if key in [" ", "q"]:
            done = True
        elif key in ("a", "t", "A", "T", chr(1), chr(20)):
            climber, new_climb_events = get_new_climb_events(key)
            climb_entry.replace_climb_events(climber, new_climb_events)
        elif key in "01234567":
            idx = int(key)
            if idx < len(matches):
                climb_entry.climb_info = climbs_info[matches["name"][idx]]
        elif key == "c":
            # Get raw input for climb name and grade
            name = input("Enter climb name: ")
            # Update climbs_info, which will be persisted in the shelf to disk
            if name in climbs_info:
                climb_info = climbs_info[name]
            else:
                grade = input("Enter climb grade: ")
                climb_info = ClimbInfo(
                    name=name,
                    grade=grade,
                    aliases=[name],
                )
                print(climb_info)
                update = input("Update climbs_info (y/n)?")
                if update == "y":
                    climbs_info[name] = climb_info
            climb_entry.climb_info = climb_info
        elif key == "n":
            climb_entry.climb_info = None
            climb_entry.climb_events.clear()

    return key


def get_matches(climb_entry: ClimbEntry, climbs_info: ClimbInfo) -> Table:
    """Get a table of climb name matches for a ClimbEntry object.

    This does a fuzzy match of the approximate climb name in the ClimbEntry object.
    """
    rows = []
    for climb_name, climb_info in climbs_info.items():
        for alias in climb_info.aliases:
            if climb_entry.name_approx == alias:
                match = 1000
            else:
                match = fuzz.partial_token_sort_ratio(climb_entry.name_approx, alias)
            row = (match, climb_name, alias, len(alias))
            rows.append(row)
    matches = Table(rows=rows, names=["match", "name", "alias", "alias_len"])
    matches.sort(("match", "alias_len"), reverse=True)
    if matches["match"][0] <= 60:
        matches = matches[:4]
    else:
        matches = matches[matches["match"] >= 60]
    matches.add_column(np.arange(len(matches)), index=0, name="Select")
    return matches


def get_new_climb_events(key: str) -> tuple[str, list[ClimbEvent]]:
    climber = "AS" if key in ("a", "A", chr(1)) else "TA"
    new_climb_events = []
    if key in ("A", "T"):
        # Custom number of reps and hangs
        reps_hangs = input(
            "Reps and h for rep with hangs and c for clean (e.g. '2hc'): "
        )
        try:
            reps = int(reps_hangs[0])
        except Exception:
            print("Invalid entry")
            reps = 0
        try:
            hangs = [reps_hangs[ii + 1] == "h" for ii in range(reps)]
        except Exception:
            print("Invalid entry")
            hangs = []
    elif key in ("a", "t"):
        # One rep with a hang
        hangs = [True]
    else:
        # No reps
        hangs = []

    for hang in hangs:
        new_climb_events.append(ClimbEvent(climber=climber, hang=hang))

    return climber, new_climb_events


def process_log_entries(
    log_entries: Table,
    climbs_info: dict[str, ClimbInfo],
    climbing_days: dict[str, ClimbingDay],
    force: bool = False,
    delay: float = 0,
) -> None:
    """Process log entries from the climbing log sheet.

    This updates `climbs_info` and `climbing_days` with new entries.
    """
    for log_entry in log_entries:
        date = log_entry["Date"]
        log_text = log_entry["Comments"]
        place_and_climbers = log_entry["Climb"]

        if date in climbing_days and not force:
            continue

        climbing_day = ClimbingDay(
            date=date, log_text=log_text, place_and_climbers=place_and_climbers
        )

        climb_entries = get_climb_entries_from_climbing_day(
            log_text, date, place_and_climbers
        )

        for climb_entry in climb_entries:
            key = process_climb_entry(climbing_day, climb_entry, climbs_info, delay=delay)
            if key == "q":
                return

        climbing_day.climb_entries = climb_entries

        # Update shelved climbing_days with new ClimbingDay object
        climbing_days[date] = climbing_day


def get_file_paths(demo: bool) -> tuple[str, str]:
    """Make demo file for db_name."""
    climbing_days = "climbing_days"
    climbs_info = "climb_info"
    if not demo:
        return climbing_days, climbs_info

    climbing_days_demo = f"{climbing_days}_demo"
    climbs_info_demo = f"{climbs_info}_demo"

    climbs_info_demo_db = Path(f"{climbs_info_demo}.db")
    if not climbs_info_demo_db.exists():
        print(f"Copying demo file {climbs_info}.db to {climbs_info_demo_db}")
        shutil.copy(f"{climbs_info}.db", climbs_info_demo_db)

    climbing_days_demo_db = Path(f"{climbing_days_demo}.db")
    if climbing_days_demo_db.exists():
        print(f"Removing demo file {climbing_days_demo_db}")
        climbing_days_demo_db.unlink()

    time.sleep(4)

    return climbing_days_demo, climbs_info_demo


def main():
    parser = get_arg_parser()
    args = parser.parse_args()
    log_entries = get_log_entries_for_date(args.date)

    climbing_days_db, climbs_info_db = get_file_paths(args.demo)

    with shelve.open(climbing_days_db) as climbing_days:
        with shelve.open(climbs_info_db) as climbs_info:
            process_log_entries(
                log_entries,
                climbs_info,
                climbing_days,
                force=args.force,
                delay=args.delay,
            )


if __name__ == "__main__":
    main()

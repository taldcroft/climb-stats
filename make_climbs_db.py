"""One-off to make climbs.db shelf file from climbs in scrape-atk.ipynb"""

import shelve

from core import ClimbInfo

CLIMBS_LIST = {
    ("10 of Spades", "Ten of Spades"): "10c",
    ("Lions Tigers and Bears", "lions"): "11b/c",
    (
        "Armed & Dangerous",
        "Arm & Dangerous",
        "Armed and Dangerous",
        "Arm and Dangerous",
        "Armed",
    ): "10b",
    "Big Easy": "7",
    ("Black Dog Crack", "Black Dog"): "10a",
    "Black Mamba": "11c",
    "Bolt and Run": "9+",
    "Bolt line": "8",
    ("Buried Treasure", "Buried"): "11b",
    "Captain Hook": "12a",
    "Centerpiece": "10d",
    ("Cereal Killer", "Cereal"): "11c",
    ("Curly for President" "Curly"): "8",
    ("Flesh for Lulu", "Flesh"): "12b",
    ("Flying Monkeys", "Flying"): "12c",
    "Get It On": "12c/d",
    "Glory Jeans": "6",
    ("Hippos on Parade", "Hippos"): "8",
    ("Holderness Arete", "Holderness"): "10b",
    "Holderness Corner": "8",
    ("Idiot Deluxe", "Idiot"): "10c",
    ("Lies and Propaganda", "Lies"): "9+",
    ("Black Mamba", "Mamba"): "11c",
    "Mamba P1": "11a",
    "Masterpiece": "10a",
    "Med Dose Madness": "10b",
    "Men in White Suits": "9",
    "Metamorphosis": "8",
    "Milktoast": "10d",
    "Misdemeanor": "10b",
    ("Know Ethics", "No Ethics"): "11a",
    "Orangahang": "12a",
    ("Polly Purebred", "Polly"): "10b",
    "Prime Climb": "11b",
    "Pump up the Volume": "12b",
    "Retrospade": "11d",
    ("Rhinobuckets", "Rhino bucket"): "10a",
    ("Romancing the Stone", "Romancing"): "10c",
    ("Sally's Alley", "Sally's"): "11c",
    ("Sesame Street", "Sesame"): "10b",
    "Sky Pilot": "11b",
    ("Social Distortion", "Social D"): "12b",
    ("Social Outcast", "Social", "Social O"): "12a",
    "Son of Sammy": "8+",
    "Clusterphobia": "10d",
    "Peer Presure": "10d",
    "Tin Man": "13a/b",
    "Tin Monkeys": "13a/b",
    "Toxic Gumbo": "8",
    "Tropicana": "11a",
    "Underdog": "10a",
    ("Vallee Daze", "Valle Daze", "Valley Daze"): "12a",
    ("Venus on a Halfshell", "Venus"): "12c",
    "War and Peace": "9+",
    "Weevil": "12a",
    "White Rhino": "11c",
}

def main():
    with shelve.open("climb_info") as db:
        for names, grade in CLIMBS_LIST.items():
            if not isinstance(names, tuple):
                names = (names,)
            climb = ClimbInfo(name=names[0], grade=grade, aliases=list(names))
            db[climb.name] = climb
            print(climb)


if __name__ == "__main__":
    main()

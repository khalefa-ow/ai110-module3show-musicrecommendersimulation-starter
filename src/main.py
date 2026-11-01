"""
Command line runner for the Music Recommender Simulation.

Examples:
    python -m src.main                         # default pop/happy profile
    python -m src.main --all                   # every profile below
    python -m src.main --profile chill_lofi --mode mood-first
    python -m src.main --all --diversity       # apply the diversity penalty
"""

import argparse
import textwrap

try:
    from src.recommender import STRATEGIES, load_songs, recommend_songs
except ModuleNotFoundError:  # allow `python main.py` from inside src/
    from recommender import STRATEGIES, load_songs, recommend_songs

try:
    from tabulate import tabulate
except ImportError:
    tabulate = None


PROFILES = {
    # Core profiles
    "pop_happy": {"genre": "pop", "mood": "happy", "energy": 0.8},
    "high_energy_pop": {"genre": "pop", "mood": "intense", "energy": 0.9, "likes_acoustic": False},
    "chill_lofi": {"genre": "lofi", "mood": "chill", "energy": 0.35, "likes_acoustic": True},
    "deep_intense_rock": {"genre": "rock", "mood": "intense", "energy": 0.95, "likes_acoustic": False},
    # Adversarial / edge cases
    "conflicted_sad_but_hyped": {"genre": "folk", "mood": "sad", "energy": 0.9},
    "ghost_genre": {"genre": "k-pop", "mood": "happy", "energy": 0.7},
    "acoustic_metalhead": {"genre": "metal", "mood": "aggressive", "energy": 0.2, "likes_acoustic": True},
    # Uses the advanced features from Challenge 1
    "nostalgic_road_trip": {
        "mood": "nostalgic", "energy": 0.55, "decade": 2000,
        "mood_tags": ["nostalgic", "warm", "carefree"], "prefers_popular": True,
    },
}


def format_table(user_prefs: dict, recs: list) -> str:
    """Render recommendations as a table that includes the reasons column."""
    rows = []
    for rank, (song, score, explanation) in enumerate(recs, start=1):
        reasons = "\n".join(textwrap.wrap(explanation, 60))
        rows.append([rank, song["title"], song["artist"], song["genre"], f"{score:.2f}", reasons])
    headers = ["#", "Title", "Artist", "Genre", "Score", "Reasons"]
    if tabulate:
        return tabulate(rows, headers=headers, tablefmt="grid", disable_numparse=True)
    return _ascii_table(headers, rows)


def _ascii_table(headers: list, rows: list) -> str:
    """Fallback table renderer for when tabulate isn't installed."""
    cells = [[str(c).split("\n") for c in row] for row in rows]
    widths = [max([len(h)] + [max(len(line) for line in r[i]) for r in cells]) for i, h in enumerate(headers)]
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    out = [sep, "| " + " | ".join(h.ljust(w) for h, w in zip(headers, widths)) + " |", sep.replace("-", "=")]
    for r in cells:
        height = max(len(c) for c in r)
        for i in range(height):
            out.append("| " + " | ".join((c[i] if i < len(c) else "").ljust(w) for c, w in zip(r, widths)) + " |")
        out.append(sep)
    return "\n".join(out)


def describe(user_prefs: dict) -> str:
    """One-line summary of a preference dict."""
    return ", ".join(f"{k}={v}" for k, v in user_prefs.items())


def run_profile(name: str, songs: list, k: int, mode: str, diversity: bool) -> None:
    """Print the top-k recommendations for one named profile."""
    prefs = PROFILES[name]
    recs = recommend_songs(prefs, songs, k=k, mode=mode, diversity=diversity)
    print(f"\n=== Profile: {name} | mode: {mode} | diversity: {'on' if diversity else 'off'} ===")
    print(f"User prefs: {describe(prefs)}")
    print(format_table(prefs, recs))


def main() -> None:
    parser = argparse.ArgumentParser(description="Music Recommender Simulation")
    parser.add_argument("--profile", choices=PROFILES, default="pop_happy")
    parser.add_argument("--all", action="store_true", help="run every profile")
    parser.add_argument("--mode", choices=STRATEGIES, default="genre-first")
    parser.add_argument("--diversity", action="store_true", help="penalize repeat artists/genres")
    parser.add_argument("-k", type=int, default=5)
    args = parser.parse_args()

    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")
    print(f"Mode '{args.mode}': {STRATEGIES[args.mode].description}")

    names = list(PROFILES) if args.all else [args.profile]
    for name in names:
        run_profile(name, songs, args.k, args.mode, args.diversity)


if __name__ == "__main__":
    main()

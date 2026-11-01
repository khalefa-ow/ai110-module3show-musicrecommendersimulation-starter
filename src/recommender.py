import csv
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INT_FIELDS = {"id", "popularity", "release_decade"}
FLOAT_FIELDS = {
    "energy", "tempo_bpm", "valence", "danceability",
    "acousticness", "instrumentalness", "liveness",
}
LIST_FIELDS = {"mood_tags"}


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    # Advanced features (Challenge 1). Defaults keep the original 10-field constructor working.
    popularity: int = 50
    release_decade: int = 2010
    mood_tags: List[str] = field(default_factory=list)
    instrumentalness: float = 0.0
    liveness: float = 0.0


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

    def to_prefs(self) -> Dict:
        """Convert the profile into the dict format used by score_song."""
        return {
            "genre": self.favorite_genre,
            "mood": self.favorite_mood,
            "energy": self.target_energy,
            "likes_acoustic": self.likes_acoustic,
        }


# ---------------------------------------------------------------------------
# Scoring strategies (Challenge 2)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ScoringStrategy:
    """A named set of feature weights; swapping strategies changes ranking without touching score_song."""
    name: str
    description: str
    weights: Dict[str, float]


BASE_WEIGHTS = {
    "genre": 2.0,          # full genre match; partial match (e.g. "indie pop" vs "pop") earns half
    "mood": 1.0,           # exact mood match
    "energy": 1.5,         # scaled by closeness: weight * (1 - |song - target|)
    "acoustic": 0.5,       # rewards acousticness (or its absence) when likes_acoustic is set
    "valence": 1.0,        # closeness to target_valence, if given
    "mood_tags": 0.5,      # per overlapping detailed mood tag
    "decade": 0.75,        # exact decade match; one decade off earns half
    "popularity": 0.5,     # scaled popularity, if prefers_popular is set
    "instrumental": 0.5,   # closeness to target_instrumentalness, if given
    "live": 0.5,           # closeness to target_liveness, if given
}

STRATEGIES: Dict[str, ScoringStrategy] = {
    "genre-first": ScoringStrategy(
        "genre-first",
        "Default recipe: genre dominates, mood and energy refine.",
        dict(BASE_WEIGHTS),
    ),
    "mood-first": ScoringStrategy(
        "mood-first",
        "Mood and mood tags matter most; genre is a tie-breaker.",
        {**BASE_WEIGHTS, "genre": 0.75, "mood": 2.5, "mood_tags": 0.75},
    ),
    "energy-focused": ScoringStrategy(
        "energy-focused",
        "Experiment: energy weight doubled (1.5 -> 3.0), genre halved (2.0 -> 1.0).",
        {**BASE_WEIGHTS, "genre": 1.0, "energy": 3.0},
    ),
}
DEFAULT_STRATEGY = "genre-first"


def get_strategy(name: Optional[str]) -> ScoringStrategy:
    """Look up a scoring strategy by name, falling back to the default."""
    if name is None:
        return STRATEGIES[DEFAULT_STRATEGY]
    if name not in STRATEGIES:
        raise ValueError(f"Unknown mode '{name}'. Choose from: {', '.join(STRATEGIES)}")
    return STRATEGIES[name]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _convert_row(row: Dict[str, str]) -> Dict:
    """Convert one CSV row's string values into ints, floats, and tag lists."""
    song: Dict = {}
    for key, value in row.items():
        value = (value or "").strip()
        if key in INT_FIELDS:
            song[key] = int(value)
        elif key in FLOAT_FIELDS:
            song[key] = float(value)
        elif key in LIST_FIELDS:
            song[key] = [t.strip().lower() for t in value.split(";") if t.strip()]
        else:
            song[key] = value
    return song


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    path = Path(csv_path)
    if not path.is_absolute() and not path.exists():
        path = PROJECT_ROOT / path
    with path.open(newline="", encoding="utf-8") as f:
        return [_convert_row(row) for row in csv.DictReader(f)]


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _closeness(value: float, target: float) -> float:
    """Return 1.0 for an exact match, falling linearly to 0.0 at a gap of 1.0."""
    return max(0.0, 1.0 - abs(value - target))


def _genre_match(user_genre: str, song_genre: str) -> float:
    """Return 1.0 for an exact genre match, 0.5 for a shared word (indie pop / pop), else 0."""
    user_genre, song_genre = user_genre.lower().strip(), song_genre.lower().strip()
    if user_genre == song_genre:
        return 1.0
    if set(user_genre.split()) & set(song_genre.split()):
        return 0.5
    return 0.0


def score_song(user_prefs: Dict, song: Dict, mode: Optional[str] = None) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.
    Required by recommend_songs() and src/main.py
    """
    w = get_strategy(mode).weights
    score = 0.0
    reasons: List[str] = []

    def add(points: float, label: str) -> None:
        nonlocal score
        if points > 0:
            score += points
            reasons.append(f"{label} (+{points:.2f})")

    if user_prefs.get("genre"):
        match = _genre_match(user_prefs["genre"], song["genre"])
        label = "genre match" if match == 1.0 else "partial genre match"
        add(w["genre"] * match, label)

    if user_prefs.get("mood") and user_prefs["mood"].lower() == song["mood"].lower():
        add(w["mood"], "mood match")

    if "energy" in user_prefs:
        gap = abs(song["energy"] - user_prefs["energy"])
        add(w["energy"] * _closeness(song["energy"], user_prefs["energy"]), f"energy gap {gap:.2f}")

    if "likes_acoustic" in user_prefs:
        acoustic = song.get("acousticness", 0.0)
        if user_prefs["likes_acoustic"]:
            add(w["acoustic"] * acoustic, "acoustic sound")
        else:
            add(w["acoustic"] * (1 - acoustic), "produced/electric sound")

    if "valence" in user_prefs:
        add(w["valence"] * _closeness(song["valence"], user_prefs["valence"]), "valence close")

    if user_prefs.get("mood_tags") and song.get("mood_tags"):
        shared = sorted(set(t.lower() for t in user_prefs["mood_tags"]) & set(song["mood_tags"]))
        if shared:
            add(w["mood_tags"] * len(shared), f"tags {'/'.join(shared)}")

    if "decade" in user_prefs and "release_decade" in song:
        decades_off = abs(song["release_decade"] - user_prefs["decade"]) // 10
        if decades_off == 0:
            add(w["decade"], f"{song['release_decade']}s match")
        elif decades_off == 1:
            add(w["decade"] / 2, f"{song['release_decade']}s near era")

    if user_prefs.get("prefers_popular") and "popularity" in song:
        add(w["popularity"] * song["popularity"] / 100, f"popularity {song['popularity']}")

    if "instrumentalness" in user_prefs and "instrumentalness" in song:
        add(w["instrumental"] * _closeness(song["instrumentalness"], user_prefs["instrumentalness"]),
            "instrumental level")

    if "liveness" in user_prefs and "liveness" in song:
        add(w["live"] * _closeness(song["liveness"], user_prefs["liveness"]), "live feel")

    return round(score, 4), reasons


# ---------------------------------------------------------------------------
# Ranking (with optional diversity penalty, Challenge 3)
# ---------------------------------------------------------------------------

ARTIST_PENALTY = 1.5  # subtracted if the artist is already in the picked list
GENRE_PENALTY = 0.75  # subtracted per already-picked song of the same genre


def _rerank_with_diversity(scored: List[Tuple[Dict, float, List[str]]], k: int) -> List[Tuple[Dict, float, List[str]]]:
    """Greedily pick the best song after penalizing repeat artists and genres among earlier picks."""
    remaining = list(scored)
    picked: List[Tuple[Dict, float, List[str]]] = []
    while remaining and len(picked) < k:
        best = None
        for song, base, reasons in remaining:
            artists = [p[0]["artist"] for p in picked]
            same_genre = sum(1 for p in picked if p[0]["genre"] == song["genre"])
            penalty = (ARTIST_PENALTY if song["artist"] in artists else 0.0) + GENRE_PENALTY * same_genre
            adjusted = base - penalty
            if best is None or adjusted > best[1]:
                extra = [f"diversity penalty (-{penalty:.2f})"] if penalty else []
                best = (song, adjusted, reasons + extra)
        picked.append(best)
        remaining = [r for r in remaining if r[0] is not best[0]]
    return picked


def rank_songs(user_prefs: Dict, songs: List[Dict], k: int = 5, mode: Optional[str] = None,
               diversity: bool = False) -> List[Tuple[Dict, float, List[str]]]:
    """Score every song and return the top k as (song, score, reasons), highest first."""
    scored = [(song, *score_song(user_prefs, song, mode)) for song in songs]
    scored.sort(key=lambda item: (-item[1], item[0]["title"]))
    if diversity:
        return _rerank_with_diversity(scored, k)
    return scored[:k]


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5, mode: Optional[str] = None,
                    diversity: bool = False) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    return [
        (song, score, "; ".join(reasons) or "no matching features")
        for song, score, reasons in rank_songs(user_prefs, songs, k, mode, diversity)
    ]


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song], mode: Optional[str] = None):
        self.songs = songs
        self.mode = mode

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k Song objects for this user, best first."""
        ranked = rank_songs(user.to_prefs(), [asdict(s) for s in self.songs], k, self.mode)
        by_id = {s.id: s for s in self.songs}
        return [by_id[song["id"]] for song, _, _ in ranked]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable sentence explaining the song's score."""
        score, reasons = score_song(user.to_prefs(), asdict(song), self.mode)
        if not reasons:
            return f"'{song.title}' scored {score:.2f}: it matched none of your preferences."
        return f"'{song.title}' scored {score:.2f} because of: " + ", ".join(reasons) + "."

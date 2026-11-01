from src.recommender import Song, UserProfile, Recommender

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# --- Tests for the functional API, modes, and diversity penalty ---

from src.recommender import load_songs, recommend_songs, score_song


def test_load_songs_converts_types():
    songs = load_songs("data/songs.csv")
    assert len(songs) >= 15
    first = songs[0]
    assert isinstance(first["energy"], float)
    assert isinstance(first["tempo_bpm"], float)
    assert isinstance(first["id"], int)
    assert isinstance(first["mood_tags"], list)


def test_score_song_returns_score_and_reasons():
    song = {"genre": "pop", "mood": "happy", "energy": 0.8, "valence": 0.9, "acousticness": 0.2}
    score, reasons = score_song({"genre": "pop", "mood": "happy", "energy": 0.8}, song)
    assert score == 2.0 + 1.0 + 1.5
    assert any("genre match" in r for r in reasons)
    assert any("mood match" in r for r in reasons)


def test_energy_rewards_closeness_not_magnitude():
    prefs = {"energy": 0.4}
    close, _ = score_song(prefs, {"genre": "x", "mood": "x", "energy": 0.45})
    loud, _ = score_song(prefs, {"genre": "x", "mood": "x", "energy": 0.95})
    assert close > loud


def test_partial_genre_match_gets_half_credit():
    score, reasons = score_song({"genre": "pop"}, {"genre": "indie pop", "mood": "x", "energy": 0.5})
    assert score == 1.0
    assert reasons == ["partial genre match (+1.00)"]


def test_modes_change_rankings():
    songs = load_songs("data/songs.csv")
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    default = [s["title"] for s, _, _ in recommend_songs(prefs, songs, k=5)]
    mood_first = [s["title"] for s, _, _ in recommend_songs(prefs, songs, k=5, mode="mood-first")]
    assert default != mood_first


def test_diversity_penalty_limits_repeat_artists():
    songs = load_songs("data/songs.csv")
    prefs = {"genre": "lofi", "mood": "chill", "energy": 0.4}
    plain = recommend_songs(prefs, songs, k=3)
    diverse = recommend_songs(prefs, songs, k=3, diversity=True)
    plain_genres = [s["genre"] for s, _, _ in plain]
    diverse_genres = [s["genre"] for s, _, _ in diverse]
    assert plain_genres.count("lofi") == 3
    assert diverse_genres.count("lofi") < 3

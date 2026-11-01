# 🎵 Music Recommender Simulation — VibeFinder 1.0

## Project Summary

VibeFinder is a small, CLI-first, content-based music recommender. It reads a 20-song catalog from `data/songs.csv`, compares every song to a user's "taste profile" (favorite genre, mood, target energy, and optional extras like decade or mood tags), gives each song a weighted score with a plain-English list of reasons, and prints the top *k* songs as a table.

On top of the core project it includes all four optional extensions:

| Challenge | What was added |
|---|---|
| 1. Advanced features | 5 new song attributes: `popularity`, `release_decade`, `mood_tags`, `instrumentalness`, `liveness` — all used in scoring |
| 2. Scoring modes | `genre-first` (default), `mood-first`, `energy-focused`, switchable with `--mode` (Strategy pattern) |
| 3. Diversity penalty | `--diversity` re-ranks so repeat artists (−1.5) and repeat genres (−0.75 each) get pushed down |
| 4. Summary table | Output is a `tabulate` grid with a Reasons column (plain ASCII fallback if `tabulate` isn't installed) |

---

## How The System Works

### How real recommenders work

Large platforms like Spotify and YouTube mix two families of techniques:

- **Collaborative filtering** uses *other people's behavior*: "users who liked the songs you like also liked X." It needs lots of interaction data (plays, likes, skips, playlist adds, replays) but no knowledge of what the music sounds like.
- **Content-based filtering** uses *attributes of the items*: genre, tempo, energy, mood, acousticness, and audio embeddings. It can recommend a brand-new song nobody has played yet, but tends to keep you close to what you already like.

Real systems blend both, then re-rank for freshness, diversity, and business goals. The key data types are implicit signals (skips, listen time, repeats), explicit signals (likes, follows, playlists), and song features (audio analysis, metadata, lyrics).

### What my version prioritizes

VibeFinder is purely **content-based**: there is only one user and no listening history, so it can only compare song attributes to stated preferences. It prioritizes **genre first, then energy, then mood**, because genre is the strongest single signal of "is this my kind of music," while energy captures the feel (workout vs. study) across genres.

### Features used

**`Song`**: `id`, `title`, `artist`, `genre`, `mood`, `energy` (0–1), `tempo_bpm`, `valence` (0–1), `danceability` (0–1), `acousticness` (0–1), plus the Challenge 1 features `popularity` (0–100), `release_decade`, `mood_tags` (list such as `nostalgic;warm`), `instrumentalness` (0–1), `liveness` (0–1).

**`UserProfile`** / preference dict: `favorite_genre`, `favorite_mood`, `target_energy`, `likes_acoustic`. The dict version also accepts the optional keys `valence`, `mood_tags`, `decade`, `prefers_popular`, `instrumentalness`, and `liveness`. Any key that is left out is simply not scored.

### Algorithm recipe (default `genre-first` mode)

| Rule | Points |
|---|---|
| Genre exact match | +2.0 |
| Genre partial match (shares a word, e.g. `indie pop` vs `pop`) | +1.0 |
| Mood exact match | +1.0 |
| Energy closeness | +1.5 × (1 − \|song energy − target\|) |
| Acoustic preference | +0.5 × acousticness if `likes_acoustic`, else +0.5 × (1 − acousticness) |
| Valence closeness (optional) | +1.0 × (1 − \|gap\|) |
| Each shared mood tag (optional) | +0.5 |
| Decade match / one decade off (optional) | +0.75 / +0.375 |
| Popularity (if `prefers_popular`) | +0.5 × popularity / 100 |
| Instrumentalness / liveness closeness (optional) | +0.5 × (1 − \|gap\|) each |

The **scoring rule** judges one song at a time and returns `(score, reasons)`. The **ranking rule** applies that judge to every song, sorts by score (highest first, ties broken by title), and keeps the top *k*. We need both: the scoring rule decides what "good" means, the ranking rule turns many independent judgments into an ordered list. The diversity penalty only lives in the ranking rule, because "is this too similar?" depends on what's already been picked, not on the song alone.

Energy uses *closeness* rather than "higher is better", so a user who wants 0.4 energy is served by a 0.42 song, not punished for not choosing 0.95.

### Data flow

```
User prefs ──► for each song in songs.csv ──► score_song() ──► (song, score, reasons)
                                                                      │
                                    sort by score, desc  ◄────────────┘
                                             │
                          (optional) diversity re-rank
                                             │
                                     top k ──► table in terminal
```

### Expected biases (written before building)

- Genre is worth more than mood, so a pop fan may get "intense" pop songs ahead of "happy" songs from other genres.
- Most genres have only one song in the catalog, so whichever single song matches the genre will almost always rank first.
- Energy closeness gives every song some points, so songs from completely unrelated genres can still fill out the bottom of the list.

---

## Getting Started

### Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac / Linux / Git Bash
   .venv\Scripts\Activate.ps1     # Windows PowerShell
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app from the project root:

   ```bash
   python -m src.main                                  # default pop/happy profile
   python -m src.main --all                            # all 8 profiles
   python -m src.main --profile chill_lofi --mode mood-first
   python -m src.main --all --diversity -k 5
   ```

   Modes: `genre-first`, `mood-first`, `energy-focused`. Profiles are defined in `PROFILES` in `src/main.py`.

### Running Tests

```bash
pytest
```

8 tests cover the OOP `Recommender`, CSV type conversion, the score/reasons format, energy closeness, partial genre matching, mode switching, and the diversity penalty.

---

## Sample Recommendation Output

`python -m src.main` (default `pop/happy` profile):

```
Loaded songs: 20
Mode 'genre-first': Default recipe: genre dominates, mood and energy refine.

=== Profile: pop_happy | mode: genre-first | diversity: off ===
User prefs: genre=pop, mood=happy, energy=0.8
+-----+------------------+---------------+-----------+---------+-------------------------------------------------------------+
| #   | Title            | Artist        | Genre     | Score   | Reasons                                                     |
+=====+==================+===============+===========+=========+=============================================================+
| 1   | Sunrise City     | Neon Echo     | pop       | 4.47    | genre match (+2.00); mood match (+1.00); energy gap 0.02    |
|     |                  |               |           |         | (+1.47)                                                     |
+-----+------------------+---------------+-----------+---------+-------------------------------------------------------------+
| 2   | Rooftop Lights   | Indigo Parade | indie pop | 3.44    | partial genre match (+1.00); mood match (+1.00); energy gap |
|     |                  |               |           |         | 0.04 (+1.44)                                                |
+-----+------------------+---------------+-----------+---------+-------------------------------------------------------------+
| 3   | Gym Hero         | Max Pulse     | pop       | 3.31    | genre match (+2.00); energy gap 0.13 (+1.30)                |
+-----+------------------+---------------+-----------+---------+-------------------------------------------------------------+
| 4   | Fiesta Brillante | Los Soles     | latin     | 2.42    | mood match (+1.00); energy gap 0.05 (+1.43)                 |
+-----+------------------+---------------+-----------+---------+-------------------------------------------------------------+
| 5   | Concrete Verses  | MC Halcyon    | hip hop   | 1.47    | energy gap 0.02 (+1.47)                                     |
+-----+------------------+---------------+-----------+---------+-------------------------------------------------------------+
```

---

## Experiments You Tried

### Stress test with 8 profiles

Full output for every profile (`python -m src.main --all`) is in [model_card.md](model_card.md#7-evaluation). Three core profiles plus three adversarial ones and one that uses the advanced features:

```
Top 3 per profile (genre-first):
pop_happy                  Sunrise City (4.47), Rooftop Lights (3.44), Gym Hero (3.31)
high_energy_pop            Gym Hero (4.93), Sunrise City (3.79), Storm Runner (2.94)
chill_lofi                 Library Rain (4.93), Midnight Coding (4.75), Focus Flow (3.81)
deep_intense_rock          Storm Runner (4.89), Gym Hero (2.94), Pulse Reactor (1.99)
conflicted_sad_but_hyped   Lantern Fields (3.60), Storm Runner (1.49), Gym Hero (1.46)
ghost_genre                Rooftop Lights (2.41), Sunrise City (2.32), Fiesta Brillante (2.27)
acoustic_metalhead         Iron Cathedral (3.36), Moonlit Sonata Redux (1.96), Spacewalk Thoughts (1.84)
nostalgic_road_trip        Dusty Backroads (5.07), Lantern Fields (3.10), Coffee Shop Stories (2.85)
```

### Weight-shift experiment (`--mode energy-focused`)

Energy weight doubled (1.5 → 3.0) and genre weight halved (2.0 → 1.0). Top 5 titles for each profile, before vs. after:

```
pop_happy
  before: Sunrise City, Rooftop Lights, Gym Hero, Fiesta Brillante, Concrete Verses
  after:  Sunrise City, Rooftop Lights, Fiesta Brillante, Gym Hero, Concrete Verses
high_energy_pop
  before: Gym Hero, Sunrise City, Storm Runner, Rooftop Lights, Pulse Reactor
  after:  Gym Hero, Storm Runner, Sunrise City, Rooftop Lights, Pulse Reactor
chill_lofi
  before: Library Rain, Midnight Coding, Focus Flow, Spacewalk Thoughts, Coffee Shop Stories
  after:  Library Rain, Midnight Coding, Spacewalk Thoughts, Focus Flow, Coffee Shop Stories
deep_intense_rock
  before: Storm Runner, Gym Hero, Pulse Reactor, Iron Cathedral, Sunrise City
  after:  Storm Runner, Gym Hero, Pulse Reactor, Iron Cathedral, Fiesta Brillante
conflicted_sad_but_hyped
  before: Lantern Fields, Storm Runner, Gym Hero, Fiesta Brillante, Pulse Reactor
  after:  Lantern Fields, Storm Runner, Gym Hero, Fiesta Brillante, Pulse Reactor
ghost_genre
  before: Rooftop Lights, Sunrise City, Fiesta Brillante, Night Drive Loop, Concrete Verses
  after:  Rooftop Lights, Sunrise City, Fiesta Brillante, Night Drive Loop, Concrete Verses
acoustic_metalhead
  before: Iron Cathedral, Moonlit Sonata Redux, Spacewalk Thoughts, Lantern Fields, Library Rain
  after:  Moonlit Sonata Redux, Spacewalk Thoughts, Lantern Fields, Library Rain, Coffee Shop Stories
nostalgic_road_trip
  before: Dusty Backroads, Lantern Fields, Coffee Shop Stories, Island Time, Night Drive Loop
  after:  Dusty Backroads, Lantern Fields, Island Time, Coffee Shop Stories, Night Drive Loop
```

What changed: for the pop/happy profile, **Gym Hero** (pop but *intense*) fell from #3 to #4 and **Fiesta Brillante** (latin but *happy*, 0.85 energy) moved up — arguably *more* accurate for a "happy pop" listener. For the acoustic metalhead, the only metal song (**Iron Cathedral**, energy 0.97) dropped out of the top 5 entirely, because the user asked for 0.2 energy. That's not more accurate — it's just different: it now ignores the genre the user named. The experiment shows the weights decide *whose* preference wins when preferences conflict.

### Diversity penalty (`--diversity`)

For `chill_lofi`, the plain ranking returns three lofi songs, two of them by LoRoom. With the penalty, **Focus Flow** (second LoRoom song, third lofi song) drops out and **Lantern Fields** (folk) enters at #5:

```
Without --diversity:
=== Profile: chill_lofi | mode: genre-first | diversity: off ===
User prefs: genre=lofi, mood=chill, energy=0.35, likes_acoustic=True
+-----+---------------------+----------------+---------+---------+--------------------------------------------------------------+
| #   | Title               | Artist         | Genre   | Score   | Reasons                                                      |
+=====+=====================+================+=========+=========+==============================================================+
| 1   | Library Rain        | Paper Lanterns | lofi    | 4.93    | genre match (+2.00); mood match (+1.00); energy gap 0.00     |
|     |                     |                |         |         | (+1.50); acoustic sound (+0.43)                              |
+-----+---------------------+----------------+---------+---------+--------------------------------------------------------------+
| 2   | Midnight Coding     | LoRoom         | lofi    | 4.75    | genre match (+2.00); mood match (+1.00); energy gap 0.07     |
|     |                     |                |         |         | (+1.40); acoustic sound (+0.35)                              |
+-----+---------------------+----------------+---------+---------+--------------------------------------------------------------+
| 3   | Focus Flow          | LoRoom         | lofi    | 3.81    | genre match (+2.00); energy gap 0.05 (+1.42); acoustic sound |
|     |                     |                |         |         | (+0.39)                                                      |
+-----+---------------------+----------------+---------+---------+--------------------------------------------------------------+
| 4   | Spacewalk Thoughts  | Orbit Bloom    | ambient | 2.85    | mood match (+1.00); energy gap 0.07 (+1.40); acoustic sound  |
|     |                     |                |         |         | (+0.46)                                                      |
+-----+---------------------+----------------+---------+---------+--------------------------------------------------------------+
| 5   | Coffee Shop Stories | Slow Stereo    | jazz    | 1.92    | energy gap 0.02 (+1.47); acoustic sound (+0.45)              |
+-----+---------------------+----------------+---------+---------+--------------------------------------------------------------+

With --diversity:
=== Profile: chill_lofi | mode: genre-first | diversity: on ===
User prefs: genre=lofi, mood=chill, energy=0.35, likes_acoustic=True
+-----+---------------------+----------------+---------+---------+-------------------------------------------------------------+
| #   | Title               | Artist         | Genre   | Score   | Reasons                                                     |
+=====+=====================+================+=========+=========+=============================================================+
| 1   | Library Rain        | Paper Lanterns | lofi    | 4.93    | genre match (+2.00); mood match (+1.00); energy gap 0.00    |
|     |                     |                |         |         | (+1.50); acoustic sound (+0.43)                             |
+-----+---------------------+----------------+---------+---------+-------------------------------------------------------------+
| 2   | Midnight Coding     | LoRoom         | lofi    | 4.00    | genre match (+2.00); mood match (+1.00); energy gap 0.07    |
|     |                     |                |         |         | (+1.40); acoustic sound (+0.35); diversity penalty (-0.75)  |
+-----+---------------------+----------------+---------+---------+-------------------------------------------------------------+
| 3   | Spacewalk Thoughts  | Orbit Bloom    | ambient | 2.85    | mood match (+1.00); energy gap 0.07 (+1.40); acoustic sound |
|     |                     |                |         |         | (+0.46)                                                     |
+-----+---------------------+----------------+---------+---------+-------------------------------------------------------------+
| 4   | Coffee Shop Stories | Slow Stereo    | jazz    | 1.92    | energy gap 0.02 (+1.47); acoustic sound (+0.45)             |
+-----+---------------------+----------------+---------+---------+-------------------------------------------------------------+
| 5   | Lantern Fields      | Willow & Wren  | folk    | 1.89    | energy gap 0.05 (+1.42); acoustic sound (+0.47)             |
+-----+---------------------+----------------+---------+---------+-------------------------------------------------------------+
```

---

## Limitations and Risks

- Tiny catalog (20 songs, mostly one song per genre), so genre matches are nearly decisive.
- No listening history and no collaborative signal, so it can never surprise a user with something outside their stated taste.
- It doesn't understand lyrics, language, or culture; genre and mood labels were hand-assigned.
- Conflicting preferences (sad + high energy) can't be satisfied; the system silently picks a compromise.
- A genre that isn't in the catalog (`k-pop`) earns no points at all, with no warning to the user.

See the [model card](model_card.md) for the full analysis.

---

## Reflection

See [**model_card.md**](model_card.md) for the full model card and personal reflection.

The biggest lesson is that a "recommendation" is nothing more than a score plus a sort, yet it already *feels* personal because the reasons column explains each pick in human terms. The judgment calls hide in the weights: deciding that genre is worth twice as much as mood is a value decision, and every user whose taste doesn't fit that assumption gets worse results without knowing why.

Bias shows up in two places: in the **data** (who chose which genres to include, and how many songs each got) and in the **scoring** (which features count, and how much). In this project the `acoustic_metalhead` and `conflicted_sad_but_hyped` profiles showed that users with unusual combinations get the weakest recommendations — a small-scale version of how real platforms can under-serve listeners whose taste isn't well represented in the data.

# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Intended Use

**Goal / task:** VibeFinder suggests the top 5 songs from a small catalog that best match one listener's stated taste: a favorite genre, a mood, a target energy level, and optionally things like a preferred decade or mood tags.

- It assumes the user can describe their taste in those terms and that their taste is the same right now as it always is.
- It is built for **classroom exploration**: learning how data becomes a ranked list and where bias creeps in.

**Not intended for:** real users or a real product. It has no listening history, no feedback loop, no fairness guarantees for artists, and its genre/mood labels were hand-assigned. It should not be used to decide which artists get exposure or to make claims about what any real person "should" like.

---

## 3. How the Model Works

**Algorithm summary.** Think of it as a judge holding a score sheet. For every song in the catalog, the judge hands out points:

- **2 points** if the song is the user's favorite genre (1 point if it's a close cousin, like "indie pop" for a pop fan).
- **1 point** if the song's mood is exactly the user's mood.
- **Up to 1.5 points** for energy, more points the closer the song is to the energy the user asked for. A perfect match gets all 1.5, a song that's the opposite gets nothing.
- **Up to 0.5 points** for sounding acoustic (or for *not* sounding acoustic, if the user prefers produced music).
- Small bonuses for the extra features if the user cares about them: shared mood tags like "nostalgic" (0.5 each), the right decade (0.75), popularity, instrumental level, and live feel.

The judge writes down every reason it gave points, then all songs are lined up from highest score to lowest and the top 5 are shown with their reasons.

**Changes from the starter:** the starter had no logic at all. I added the partial-genre rule, the closeness-based energy formula, five new song features, three switchable scoring modes (genre-first, mood-first, energy-focused), and an optional diversity penalty that knocks points off a song if its artist is already in the list (−1.5) or its genre already appears (−0.75 per repeat).

---

## 4. Data

- **Size:** 20 songs. The starter had 10; I added 10 more (hip hop, classical, metal, country, r&b, edm, reggae, folk, blues, latin) so every major mood and energy range has at least one example.
- **Features:** genre, mood, energy, tempo, valence, danceability, acousticness, plus the five added features: popularity (0–100), release decade (1960s–2020s), detailed mood tags, instrumentalness, and liveness.
- **Genres:** 15 genres. lofi has 3 songs, pop has 2 (+1 indie pop); every other genre has exactly one.
- **Moods:** happy, chill, intense, relaxed, moody, focused, confident, melancholy, aggressive, nostalgic, romantic, euphoric, sad.
- **Limits:** the catalog is tiny and hand-labeled. There is nothing for K-pop, Afrobeats, gospel, or most non-English music; nothing that is both sad *and* high-energy; and the numbers (energy, valence, etc.) are my estimates, not audio analysis.

---

## 5. Strengths

- For "typical" profiles where genre, mood, and energy agree (pop/happy, chill lofi, intense rock), the #1 result is exactly the song a person would pick by hand.
- The reasons column makes every ranking explainable. You can see that Gym Hero got 2.00 for genre and 1.30 for energy and nothing for mood.
- Energy closeness works well across genres: low-energy requests surface ambient, jazz, and folk; high-energy requests surface rock, edm, and metal.
- The advanced features let the `nostalgic_road_trip` profile (no genre at all) find a sensible top pick — Dusty Backroads matched mood, energy, all three tags, and the decade.

---

## 6. Limitations and Bias

**Observed behavior / biases.** The clearest weakness is that **the genre weight overrides mood**. For the "happy pop" profile, *Gym Hero* — a pop song tagged *intense* — ranks #3, ahead of *Fiesta Brillante*, which is happy, high-energy, and only loses because it's labeled "latin." Because most genres in the catalog have a single song, whoever happens to own the matching genre label gets a 2-point head start that mood and energy combined can rarely overcome. This creates a mild **filter bubble**: listeners are kept inside their stated genre even when a song from another genre fits the moment better. It also means **users whose genre isn't in the catalog** (the `ghost_genre` "k-pop" profile) silently lose a third of their possible points and get results driven only by mood and energy, with no message telling them their genre was never matched. Finally, users with **unusual combinations** (sad + high energy, or acoustic + metal) are under-served because no song in the data fits them; the system picks a compromise without saying so.

Features it ignores: tempo and danceability are in the data but not scored by default, and there are no lyrics, language, or listening-history signals.

---

## 7. Evaluation

**Evaluation process.** I tested 8 profiles: three "normal" ones (high-energy pop, chill lofi, deep intense rock, plus the starter's pop/happy), three adversarial ones suggested while brainstorming edge cases (`conflicted_sad_but_hyped`, `ghost_genre`, `acoustic_metalhead`), and one profile that only uses the new advanced features (`nostalgic_road_trip`). For each I checked whether the top 5 matched my own intuition, then re-ran everything under the two alternate modes and with the diversity penalty on. I also wrote 8 automated tests (`pytest`).

**What surprised me:**

- *Gym Hero* shows up for almost every high-energy request, including "happy pop" and "deep intense rock," because it scores well on energy for everyone and earns genre points from pop fans.
- The `conflicted_sad_but_hyped` user gets a slow folk song at #1 (energy gap 0.60) because genre + mood (3 points) beat any energy match (max 1.5). The other four picks are high-energy songs that are not sad at all, so the list feels incoherent.
- The `acoustic_metalhead` gets one metal song and then four quiet acoustic songs (classical, ambient, folk, lofi). Technically correct, but nobody would call that a metal playlist.

**Profile-pair comparisons:**

- **pop_happy vs. high_energy_pop:** both start from pop, but asking for *intense* and 0.9 energy flips Gym Hero from #3 to #1 and pulls in Storm Runner (rock) and Pulse Reactor (edm). Makes sense: the mood point moved from "happy" songs to "intense" songs.
- **high_energy_pop vs. chill_lofi:** zero overlap. One list is all 0.75+ energy produced tracks, the other is all ≤0.42 energy and highly acoustic. The energy closeness rule is clearly doing its job at both ends of the scale.
- **chill_lofi vs. deep_intense_rock:** again zero overlap. Lofi fills 3 of 5 slots because the catalog has 3 lofi songs; rock gets only Storm Runner as a genre match and the rest are filled by energy alone (pop, edm, metal).
- **deep_intense_rock vs. acoustic_metalhead:** both are "heavy" genres, but because the metalhead asked for 0.2 energy, they share no songs except that Iron Cathedral appears at #4 for rock and #1 for metal. This shows energy matters more than the "heaviness" of a genre name.
- **ghost_genre vs. pop_happy:** nearly the same songs (Rooftop Lights, Sunrise City, Fiesta Brillante) but in a different order with lower scores, because without a genre match the mood point and energy closeness decide everything.
- **conflicted_sad_but_hyped vs. nostalgic_road_trip:** the road-trip profile gives a coherent, warm, mid-energy list, while the conflicted profile gives a sad song plus four party songs. More matching features (tags, decade) make results more coherent; contradictory features make them fall apart.

**Plain-language explanation of the "Gym Hero" problem:** The recommender thinks of "pop" as the most important thing about your taste. Gym Hero is a pop song, so it starts 2 points ahead of every non-pop song. It's also loud and energetic, which is close to what most people asked for, so it picks up another 1.3 points. A happy latin song that fits your mood perfectly can't catch up, because "happy" is only worth 1 point. So Gym Hero keeps showing up even for people who just want something cheerful.

**Weight-shift experiment.** Doubling energy (1.5 → 3.0) and halving genre (2.0 → 1.0) made pop/happy results *more* accurate (Fiesta Brillante passed Gym Hero) but made acoustic_metalhead results *less* faithful (the only metal song disappeared). The change didn't make the system better overall, it changed whose preferences win when they conflict.

**Full output, default mode (`python -m src.main --all`):**

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

=== Profile: high_energy_pop | mode: genre-first | diversity: off ===
User prefs: genre=pop, mood=intense, energy=0.9, likes_acoustic=False
+-----+----------------+---------------+-----------+---------+----------------------------------------------------------+
| #   | Title          | Artist        | Genre     | Score   | Reasons                                                  |
+=====+================+===============+===========+=========+==========================================================+
| 1   | Gym Hero       | Max Pulse     | pop       | 4.93    | genre match (+2.00); mood match (+1.00); energy gap 0.03 |
|     |                |               |           |         | (+1.46); produced/electric sound (+0.47)                 |
+-----+----------------+---------------+-----------+---------+----------------------------------------------------------+
| 2   | Sunrise City   | Neon Echo     | pop       | 3.79    | genre match (+2.00); energy gap 0.08 (+1.38);            |
|     |                |               |           |         | produced/electric sound (+0.41)                          |
+-----+----------------+---------------+-----------+---------+----------------------------------------------------------+
| 3   | Storm Runner   | Voltline      | rock      | 2.94    | mood match (+1.00); energy gap 0.01 (+1.48);             |
|     |                |               |           |         | produced/electric sound (+0.45)                          |
+-----+----------------+---------------+-----------+---------+----------------------------------------------------------+
| 4   | Rooftop Lights | Indigo Parade | indie pop | 2.62    | partial genre match (+1.00); energy gap 0.14 (+1.29);    |
|     |                |               |           |         | produced/electric sound (+0.33)                          |
+-----+----------------+---------------+-----------+---------+----------------------------------------------------------+
| 5   | Pulse Reactor  | DJ Kinetic    | edm       | 1.92    | energy gap 0.05 (+1.43); produced/electric sound (+0.49) |
+-----+----------------+---------------+-----------+---------+----------------------------------------------------------+

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

=== Profile: deep_intense_rock | mode: genre-first | diversity: off ===
User prefs: genre=rock, mood=intense, energy=0.95, likes_acoustic=False
+-----+----------------+-------------+---------+---------+----------------------------------------------------------+
| #   | Title          | Artist      | Genre   | Score   | Reasons                                                  |
+=====+================+=============+=========+=========+==========================================================+
| 1   | Storm Runner   | Voltline    | rock    | 4.89    | genre match (+2.00); mood match (+1.00); energy gap 0.04 |
|     |                |             |         |         | (+1.44); produced/electric sound (+0.45)                 |
+-----+----------------+-------------+---------+---------+----------------------------------------------------------+
| 2   | Gym Hero       | Max Pulse   | pop     | 2.94    | mood match (+1.00); energy gap 0.02 (+1.47);             |
|     |                |             |         |         | produced/electric sound (+0.47)                          |
+-----+----------------+-------------+---------+---------+----------------------------------------------------------+
| 3   | Pulse Reactor  | DJ Kinetic  | edm     | 1.99    | energy gap 0.00 (+1.50); produced/electric sound (+0.49) |
+-----+----------------+-------------+---------+---------+----------------------------------------------------------+
| 4   | Iron Cathedral | Black Anvil | metal   | 1.96    | energy gap 0.02 (+1.47); produced/electric sound (+0.48) |
+-----+----------------+-------------+---------+---------+----------------------------------------------------------+
| 5   | Sunrise City   | Neon Echo   | pop     | 1.72    | energy gap 0.13 (+1.30); produced/electric sound (+0.41) |
+-----+----------------+-------------+---------+---------+----------------------------------------------------------+

=== Profile: conflicted_sad_but_hyped | mode: genre-first | diversity: off ===
User prefs: genre=folk, mood=sad, energy=0.9
+-----+------------------+---------------+---------+---------+----------------------------------------------------------+
| #   | Title            | Artist        | Genre   | Score   | Reasons                                                  |
+=====+==================+===============+=========+=========+==========================================================+
| 1   | Lantern Fields   | Willow & Wren | folk    | 3.60    | genre match (+2.00); mood match (+1.00); energy gap 0.60 |
|     |                  |               |         |         | (+0.60)                                                  |
+-----+------------------+---------------+---------+---------+----------------------------------------------------------+
| 2   | Storm Runner     | Voltline      | rock    | 1.49    | energy gap 0.01 (+1.48)                                  |
+-----+------------------+---------------+---------+---------+----------------------------------------------------------+
| 3   | Gym Hero         | Max Pulse     | pop     | 1.46    | energy gap 0.03 (+1.46)                                  |
+-----+------------------+---------------+---------+---------+----------------------------------------------------------+
| 4   | Fiesta Brillante | Los Soles     | latin   | 1.43    | energy gap 0.05 (+1.42)                                  |
+-----+------------------+---------------+---------+---------+----------------------------------------------------------+
| 5   | Pulse Reactor    | DJ Kinetic    | edm     | 1.43    | energy gap 0.05 (+1.43)                                  |
+-----+------------------+---------------+---------+---------+----------------------------------------------------------+

=== Profile: ghost_genre | mode: genre-first | diversity: off ===
User prefs: genre=k-pop, mood=happy, energy=0.7
+-----+------------------+---------------+-----------+---------+---------------------------------------------+
| #   | Title            | Artist        | Genre     | Score   | Reasons                                     |
+=====+==================+===============+===========+=========+=============================================+
| 1   | Rooftop Lights   | Indigo Parade | indie pop | 2.41    | mood match (+1.00); energy gap 0.06 (+1.41) |
+-----+------------------+---------------+-----------+---------+---------------------------------------------+
| 2   | Sunrise City     | Neon Echo     | pop       | 2.32    | mood match (+1.00); energy gap 0.12 (+1.32) |
+-----+------------------+---------------+-----------+---------+---------------------------------------------+
| 3   | Fiesta Brillante | Los Soles     | latin     | 2.27    | mood match (+1.00); energy gap 0.15 (+1.27) |
+-----+------------------+---------------+-----------+---------+---------------------------------------------+
| 4   | Night Drive Loop | Neon Echo     | synthwave | 1.43    | energy gap 0.05 (+1.42)                     |
+-----+------------------+---------------+-----------+---------+---------------------------------------------+
| 5   | Concrete Verses  | MC Halcyon    | hip hop   | 1.38    | energy gap 0.08 (+1.38)                     |
+-----+------------------+---------------+-----------+---------+---------------------------------------------+

=== Profile: acoustic_metalhead | mode: genre-first | diversity: off ===
User prefs: genre=metal, mood=aggressive, energy=0.2, likes_acoustic=True
+-----+----------------------+----------------+-----------+---------+----------------------------------------------------------+
| #   | Title                | Artist         | Genre     | Score   | Reasons                                                  |
+=====+======================+================+===========+=========+==========================================================+
| 1   | Iron Cathedral       | Black Anvil    | metal     | 3.36    | genre match (+2.00); mood match (+1.00); energy gap 0.77 |
|     |                      |                |           |         | (+0.34); acoustic sound (+0.01)                          |
+-----+----------------------+----------------+-----------+---------+----------------------------------------------------------+
| 2   | Moonlit Sonata Redux | Clara Vey      | classical | 1.96    | energy gap 0.02 (+1.47); acoustic sound (+0.48)          |
+-----+----------------------+----------------+-----------+---------+----------------------------------------------------------+
| 3   | Spacewalk Thoughts   | Orbit Bloom    | ambient   | 1.84    | energy gap 0.08 (+1.38); acoustic sound (+0.46)          |
+-----+----------------------+----------------+-----------+---------+----------------------------------------------------------+
| 4   | Lantern Fields       | Willow & Wren  | folk      | 1.81    | energy gap 0.10 (+1.35); acoustic sound (+0.47)          |
+-----+----------------------+----------------+-----------+---------+----------------------------------------------------------+
| 5   | Library Rain         | Paper Lanterns | lofi      | 1.71    | energy gap 0.15 (+1.28); acoustic sound (+0.43)          |
+-----+----------------------+----------------+-----------+---------+----------------------------------------------------------+

=== Profile: nostalgic_road_trip | mode: genre-first | diversity: off ===
User prefs: mood=nostalgic, energy=0.55, decade=2000, mood_tags=['nostalgic', 'warm', 'carefree'], prefers_popular=True
+-----+---------------------+---------------+-----------+---------+-------------------------------------------------------------+
| #   | Title               | Artist        | Genre     | Score   | Reasons                                                     |
+=====+=====================+===============+===========+=========+=============================================================+
| 1   | Dusty Backroads     | June Holloway | country   | 5.07    | mood match (+1.00); energy gap 0.00 (+1.50); tags           |
|     |                     |               |           |         | carefree/nostalgic/warm (+1.50); 2000s match (+0.75);       |
|     |                     |               |           |         | popularity 63 (+0.32)                                       |
+-----+---------------------+---------------+-----------+---------+-------------------------------------------------------------+
| 2   | Lantern Fields      | Willow & Wren | folk      | 3.10    | energy gap 0.25 (+1.12); tags nostalgic/warm (+1.00); 2000s |
|     |                     |               |           |         | match (+0.75); popularity 44 (+0.22)                        |
+-----+---------------------+---------------+-----------+---------+-------------------------------------------------------------+
| 3   | Coffee Shop Stories | Slow Stereo   | jazz      | 2.85    | energy gap 0.18 (+1.23); tags nostalgic/warm (+1.00); 1990s |
|     |                     |               |           |         | near era (+0.38); popularity 48 (+0.24)                     |
+-----+---------------------+---------------+-----------+---------+-------------------------------------------------------------+
| 4   | Island Time         | Coral Sound   | reggae    | 2.74    | energy gap 0.03 (+1.46); tags carefree/warm (+1.00);        |
|     |                     |               |           |         | popularity 57 (+0.28)                                       |
+-----+---------------------+---------------+-----------+---------+-------------------------------------------------------------+
| 5   | Night Drive Loop    | Neon Echo     | synthwave | 2.40    | energy gap 0.20 (+1.20); tags nostalgic (+0.50); 2010s near |
|     |                     |               |           |         | era (+0.38); popularity 66 (+0.33)                          |
+-----+---------------------+---------------+-----------+---------+-------------------------------------------------------------+
```

---

## 8. Future Work / Ideas for Improvement

1. **Warn when a preference can't be met.** If no song matches the genre (k-pop) or the combination is contradictory, say so instead of quietly returning a compromise.
2. **Learn weights from feedback.** Let the user thumbs-up/down results and nudge the weights, which would turn this into a tiny feedback loop instead of fixed rules.
3. **Make the catalog more balanced** (several songs per genre) and turn on the diversity penalty by default, so no single genre label or artist dominates.

---

## 9. Personal Reflection

**How I built this:** I worked agentically. I gave an AI coding agent (Claude Code) the full project instructions and the starter repo, and asked it to complete the core project and all four optional challenges. It read the starter code, flagged problems in it (for example, `main.py` imported `recommender` in a way that breaks `python -m src.main`), then expanded the data, implemented and tested the code, ran every profile and experiment, and wrote up the results. My job was to direct the work, read the results, and decide what to submit.

**Biggest learning moment:** the code turned out to be the easy part. `score_song` plus a sort is only a few dozen lines. The real decisions are the weights. Saying a genre match is worth 2 points and a mood match is worth 1 is a claim about what matters to listeners, and the edge-case profiles (`acoustic_metalhead`, `conflicted_sad_but_hyped`, `ghost_genre`) showed how quickly that claim breaks down for people who don't fit it.

**How AI helped, and where I had to double-check it:** the agent was fast. It produced a working, tested recommender, three scoring modes, a diversity penalty, and documentation in one session. It also caught things I might have missed, like the broken import and the mismatched return shapes in the starter. But I had to watch what it claimed. The first draft of the reflection and the AI log was written in the agent's voice and listed tidied-up "example prompts" instead of what I actually asked, so I had both corrected to describe the real workflow. The lesson for me: AI output reads as confident whether it's accurate or not, so anything going out under my name has to be checked against what actually happened.

**What surprised me:** a plain list of reasons like "genre match (+2.00); mood match (+1.00)" makes a simple weighted sum *feel* like the system understands you. That's also why it's persuasive when it's wrong. The "Gym Hero" song kept appearing for happy-pop listeners, and the explanation made that look reasonable.

**What I'd try next:** simulate a few hundred users with listening histories, add a collaborative-filtering score alongside the content score, and compare how the two handle a user whose favorite genre isn't in the catalog. I'd also have the system say when it can't satisfy a preference instead of quietly returning a compromise.

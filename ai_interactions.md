# AI Interactions Log

> **Stretch features only.** This file documents the optional extensions (Challenges 1–4).

---

## Agentic Workflow (SF8) — Challenge 1: Advanced Song Features

**What task did you give the agent?**

Add five new attributes to every song in `data/songs.csv`, expand the catalog from 10 to 20 songs with genres and moods not already present, and update `src/recommender.py` so the loader parses the new columns and `score_song` can use them. Existing tests had to keep passing.

**Prompts used:**

> "Here is `data/songs.csv`. Add 10 songs in valid CSV using the same headers, covering genres and moods that aren't present yet (e.g. hip hop, classical, metal, country, r&b, edm, reggae, folk, blues, latin). Then add five new columns to all 20 rows: `popularity` (0–100 int), `release_decade` (int like 1990), `mood_tags` (2–3 lowercase tags separated by `;`), `instrumentalness` (0–1), `liveness` (0–1). Keep all 0–1 values realistic for the genre."

> "Update `load_songs` in `src/recommender.py` to convert `id`, `popularity`, `release_decade` to int, every 0–1 feature and `tempo_bpm` to float, and split `mood_tags` on `;` into a lowercase list. Add the five new fields to the `Song` dataclass **with defaults**, so `tests/test_recommender.py` can still construct a `Song` with only the original 10 fields."

> "Extend `score_song` so each new feature is only scored when the user's preference dict contains the matching key (`decade`, `mood_tags`, `prefers_popular`, `instrumentalness`, `liveness`). Every contribution must add a reason string like `2000s match (+0.75)`."

**What did the agent generate or change?**

- `data/songs.csv`: 10 new rows (ids 11–20), 5 new columns on all 20 rows.
- `src/recommender.py`: `INT_FIELDS` / `FLOAT_FIELDS` / `LIST_FIELDS` sets and `_convert_row()`; new defaulted fields on `Song`; new scoring branches for tags (+0.5 per shared tag), decade (+0.75 exact, half for one decade off), popularity, instrumentalness, and liveness.
- `src/main.py`: a `nostalgic_road_trip` profile that uses only the new features.
- `tests/test_recommender.py`: `test_load_songs_converts_types`.

**What did you verify or fix manually?**

- Checked every new row has 15 comma-separated values and that all 0–1 values are in range (a stray value outside the range would silently produce negative closeness points; `_closeness` also clamps at 0 as a safeguard).
- Confirmed the original two starter tests still pass with the 10-argument `Song(...)` constructor — the defaults on the new fields were essential.
- Ran the `nostalgic_road_trip` profile and checked by hand that Dusty Backroads' 5.07 is the sum of its five listed reasons (1.00 + 1.50 + 1.50 + 0.75 + 0.32).
- Made `load_songs` resolve `data/songs.csv` relative to the project root if the working directory is different, after noticing the starter's `main.py` would only find the file when run from the repo root.

---

## Design Pattern (SF10) — Challenge 2: Multiple Scoring Modes

**Which design pattern did you use?**

**Strategy pattern**, in a lightweight data-driven form. Each mode is a `ScoringStrategy` (name, description, weight dict), registered in a `STRATEGIES` dictionary. `score_song(user_prefs, song, mode=...)` looks up the strategy and reads its weights; the scoring logic itself never changes.

**How did AI help you brainstorm or implement it?**

I attached `recommender.py` and asked: *"I want genre-first, mood-first and energy-focused ranking modes switchable from main.py without copy-pasting score_song three times. What design pattern keeps this modular?"* The suggestions were (a) a Strategy class hierarchy with one `score()` method per subclass, (b) a dict of weight profiles, or (c) passing a scoring function as a parameter. I chose (b) because all three modes use the same rules and differ only in how much each rule is worth — a class per mode would have duplicated the logic. A frozen dataclass gives each strategy a name and description for the CLI.

The `energy-focused` mode doubles as the Phase 4 "weight shift" experiment (energy 1.5 → 3.0, genre 2.0 → 1.0), so the experiment is reproducible with `--mode energy-focused` instead of editing code and reverting it.

**How does the pattern appear in your final code?**

- `ScoringStrategy`, `BASE_WEIGHTS`, `STRATEGIES`, `get_strategy()` in `src/recommender.py`.
- `score_song(..., mode=None)` reads `get_strategy(mode).weights`.
- `Recommender(songs, mode=...)` for the OOP API; `--mode` flag (choices pulled from `STRATEGIES`) in `src/main.py`.
- `test_modes_change_rankings` verifies that switching mode reorders results.

---

## Challenge 3: Diversity and Fairness Logic

**Prompt:** *"After scoring, re-rank the list greedily: at each step pick the song with the highest score after subtracting 1.5 if its artist is already in the picked list and 0.75 for each picked song that shares its genre. Add a reason like `diversity penalty (-0.75)`. Keep it in the ranking step, not in score_song, because the penalty depends on what's already picked."*

**Result:** `_rerank_with_diversity()` in `src/recommender.py`, enabled with `--diversity`. For `chill_lofi` it replaces the third lofi song (a second LoRoom track) with a folk song. Verified with `test_diversity_penalty_limits_repeat_artists`.

---

## Challenge 4: Visual Summary Table

**Prompt:** *"Format the recommendations in main.py as a table using `tabulate`, with columns rank, title, artist, genre, score, and reasons. Wrap the reasons column at ~60 characters. Fall back to a plain ASCII table if tabulate isn't installed."*

**Manual fix:** `tabulate` re-parsed the score strings and printed `3.6` instead of `3.60`; passing `disable_numparse=True` fixed it. Added `tabulate` to `requirements.txt` and removed the unused `pandas` and `streamlit`.

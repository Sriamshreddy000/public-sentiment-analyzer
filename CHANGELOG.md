# Changelog

This changelog is reconstructed from the available git history and the current repository structure. The visible commit history is minimal, so version groupings below reflect the major architectural phases represented in the codebase today.

## v2.1 — Topic Stance Mode

Introduced a dedicated topic-level stance path for posts that do not produce two valid entities.

### Added

- `comment_topic_stance` table for storing per-comment topic stance labels and scores.
- `analyze_topic_stance.py` to classify comments toward the post title using `support`, `oppose`, and `neutral`.
- Topic-mode reporting path in `topic_detail.py`.

### Changed

- Split stance processing into two explicit modes:
  - entity-vs-entity stance for posts with two valid entities
  - topic stance for posts with zero or one valid entity
- Updated `topic_detail.py` to detect mode automatically based on extracted entities.
- Updated the refresh workflow in `app.py` to run both entity stance and topic stance analysis.

### Improved

- Reporting now covers a wider range of topics instead of depending on two-entity extraction.
- Reset and cleanup scripts now clear topic-stance outputs alongside entity-stance outputs.

## v2.0 — Interactive CLI & Topic Analysis

Introduced the interactive terminal workflow and topic-level reporting experience.

### Added

- `app.py` as the primary CLI entrypoint.
- `list_topics.py` for viewing stored topics.
- `topic_detail.py` for inspecting a single topic report.
- `about.py` for project information inside the CLI.

### Features

- Menu-driven workflow for viewing topics, refreshing analysis, and exiting cleanly.
- Topic reports with stance distribution bars.
- TF-IDF keyword extraction to summarize likely reasons behind non-neutral comment groups.
- Representative example comments to make reports easier to interpret.

## v1.5 — Entity Stance Analysis

Expanded the project from general topic processing into comparative stance analysis between extracted entities.

### Added

- `comment_entity_stance` table for storing per-comment entity stance outputs.
- `entity_stance.py` for zero-shot stance classification toward extracted entities.
- `analyze_entity_stance_auto.py` for automatic entity-aware comment analysis.
- Combined labels such as `pro-X`, `anti-X`, and `neutral`.

### Improved

- Shifted analysis from simple topic-level interpretation toward actor-based public opinion mapping.
- Enabled entity-based reasoning and summaries for headline topics involving two sides or actors.

## v1.0 — Initial Reddit Sentiment Pipeline

Established the project foundation for collecting and storing Reddit discussion data locally.

### Added

- `db.py` with the initial SQLite schema and persistence helpers.
- `fetch_rising.py` for Reddit post ingestion.
- `fetch_comments.py` for comment ingestion.
- `entity_extractor.py` for spaCy-based named entity recognition on post titles.
- `extract_post_entities.py` for selecting and storing topic entities.
- Core repository structure for local NLP experimentation and analysis.

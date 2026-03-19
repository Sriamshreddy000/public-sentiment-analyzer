# Public Sentiment Analyzer

A Python CLI project that ingests trending Reddit discussions, extracts topic entities, classifies public stance, and summarizes the reasoning behind comment patterns using practical NLP workflows.

## Project Overview

Public Sentiment Analyzer is a lightweight NLP pipeline for exploring how people react to trending public topics on Reddit. Instead of limiting analysis to simple positive or negative sentiment, the project focuses on stance: what commenters support, oppose, or remain neutral about.

The system was built as a portfolio-style applied NLP project that demonstrates end-to-end data collection, entity extraction, stance classification, structured storage, and human-readable reporting in a terminal interface.

## Key Features

- Trending topic ingestion from Reddit
- Entity extraction from news-style post headlines
- Dual stance analysis modes:
  - Entity vs entity stance for topics with two valid entities
  - Topic stance for topics with zero or one valid entity
- CLI-based analysis workflow
- TF-IDF reason extraction for non-neutral groups
- Example comment explanations using representative comments
- SQLite-backed local data pipeline for repeatable analysis

## Architecture

The project is organized as a script-driven pipeline with SQLite as the shared data layer.

### Data Ingestion

- Fetches rising Reddit posts and stores post metadata locally
- Fetches top-level comments for saved posts
- Persists raw inputs in SQLite for downstream processing

### Entity Extraction

- Uses spaCy named entity recognition on post titles
- Extracts likely actors such as countries, organizations, and people
- Normalizes aliases, removes noisy entities, and stores up to two selected entities per post

### Stance Analysis

- For posts with two valid entities, each comment is classified toward both entities
- Results are combined into final labels such as `pro-US`, `anti-Iran`, or `neutral`

### Topic Stance Analysis

- For posts with zero or one valid entity, each comment is classified toward the overall post topic
- Labels are stored as `support`, `oppose`, or `neutral`

### Reporting

- Generates console reports for individual topics
- Shows label distribution, TF-IDF keywords, and representative comments
- Supports both entity-mode and topic-mode reports in the same interface

### CLI Interface

- Provides a simple menu-driven workflow
- Lets users refresh the full dataset, browse topics, inspect detailed reports, and clear cached data

### SQLite Database

The local database stores:

- `posts`
- `comments`
- `post_entities`
- `comment_entity_stance`
- `comment_topic_stance`

## System Pipeline

When running `python app.py`, the application follows this end-to-end flow:

```text
app.py
  -> reset_db.py
  -> fetch_rising.py
  -> fetch_comments.py
  -> extract_post_entities.py
  -> clear_entity_stance.py
  -> analyze_entity_stance_auto.py
  -> analyze_topic_stance.py
  -> list_topics.py
  -> topic_detail.py
```

### Step-by-Step Pipeline

1. Start the CLI menu from `app.py`.
2. Choose `Refresh trending topics`.
3. Reset cached posts, comments, entities, and stance tables.
4. Fetch trending Reddit posts and save them to SQLite.
5. Fetch comments for stored posts and save them locally.
6. Extract up to two valid entities from each post title.
7. Clear prior stance outputs.
8. Run entity-vs-entity stance analysis for topics with two valid entities.
9. Run topic stance analysis for topics without two valid entities.
10. Show the topic list.
11. Open a detailed report for a selected topic.

If the user chooses `View trending topics + analyze one`, the app skips the refresh pipeline and works from the existing stored dataset.

## Example CLI Workflow

```bash
python app.py
```

```text
==============================
Public Sentiment CLI
==============================
1) View trending topics + analyze one
2) Refresh trending topics (reset + refetch + analyze)
3) About
4) Exit (and clear cached data)
```

Typical user flow:

1. Run `python app.py`
2. Select `2` to refresh the dataset
3. Wait for the pipeline to complete
4. Review the generated list of topics
5. Enter a topic number to inspect
6. Read the topic report with stance distribution, keywords, and example comments

## Example Output

```text
===============================================================================================
TOPIC #3: US and Iran exchange warnings after regional escalation
subreddit=r/worldnews | post_id=abc123
url=https://www.reddit.com/...
entities = (US, Iran)

Labeled comments used: 42  (min comment length filter = 40)

pro-US             ████████████░░░░░░░░░░░░░░  14 (33.3%)
anti-US            ████████░░░░░░░░░░░░░░░░░  10 (23.8%)
pro-Iran           █████░░░░░░░░░░░░░░░░░░░░   6 (14.3%)
neutral            ██████████░░░░░░░░░░░░░░░  12 (28.6%)

Reasons (non-neutral only):

--- pro-US ---
keywords: deterrence, retaliation, regional security, military response
examples:
  1. The US is responding because...
  2. This was a justified warning...
  3. Their position is meant to prevent...

--- anti-US ---
keywords: intervention, escalation, hypocrisy, foreign policy
examples:
  1. The US helped create this problem...
  2. This is another example of...
  3. Their actions are making things worse...
```

For topics without two valid entities, the report uses `support`, `oppose`, and `neutral` instead.

## Applied NLP Techniques Demonstrated

- Named Entity Recognition with spaCy for extracting actors from post titles
- Rule-based entity normalization and filtering for cleaner topic representation
- Zero-shot stance classification with transformer models
- Topic-level stance classification against full post headlines
- Comparative entity-level stance labeling
- TF-IDF keyword extraction for lightweight explanation of opinion clusters
- Representative example selection for qualitative interpretation

## Installation

Install project dependencies:

```bash
pip install -r requirements.txt
```

Install the spaCy English model:

```bash
python -m spacy download en_core_web_sm
```

## Running the Project

```bash
python app.py
```

## Repository Structure

```text
app.py                         CLI entrypoint and workflow orchestration
db.py                          SQLite schema and database helpers
fetch_rising.py                Fetches trending Reddit posts
fetch_comments.py              Fetches comments for saved posts
extract_post_entities.py       Extracts and stores topic entities
entity_extractor.py            spaCy-based named entity extraction
entity_stance.py               Zero-shot entity stance classification logic
stance.py                      Zero-shot topic stance classification logic
analyze_entity_stance_auto.py  Entity-vs-entity stance pipeline
analyze_topic_stance.py        Single-topic stance pipeline
topic_detail.py                Topic report rendering
list_topics.py                 Lists stored topics
reset_db.py                    Clears cached data
clear_entity_stance.py         Clears stance output tables
about.py                       CLI about screen
```

## Future Improvements

- Multi-platform sentiment and stance ingestion across Reddit, X, YouTube, and news comments
- Web dashboard for interactive browsing and visualization
- Better topic clustering and normalization across similar headlines
- Argument extraction to surface common claims, evidence, and counterarguments
- Stronger entity ranking and disambiguation for noisy headlines

## License

This project is currently provided for educational and portfolio use. Add a formal license file if you plan to distribute it publicly.

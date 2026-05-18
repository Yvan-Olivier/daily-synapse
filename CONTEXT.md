# Daily Synapse — Domain Glossary

This file is a **glossary only**. No implementation details, no specs.
Updated inline as terms are resolved.

---

## Pipeline

The daily end-to-end process that transforms raw RSS feeds into curated
email and podcast outputs. Runs once per day (cron or manual trigger).
Idempotent: running it twice produces no duplicate outputs.

## Article

A single piece of content scraped from an RSS feed. Has a unique `guid`,
a title, a URL, and optional description. Stored in `anthropic_articles`.
Not yet validated or summarised at insertion time.

## Summary

A structured LLM-generated condensation of an Article: a short title
(5–10 words) and a 2–3 sentence body. Produced by the **Summarizer**.
Stored alongside the Article in the same DB row.

## Critic verdict

The output of the **Critic** agent for a given Summary. Persisted on the
Article as `criticized_at` (timestamp of evaluation) + `critic_approved`
(bool). `criticized_at IS NULL` means "no verdict yet" — either a fresh
Article or a previous API failure; the Resumer will retry it. An approved
verdict enters the curation phase. A rejected verdict is discarded
definitively — the Article is never included in a Digest or Episode.
The `reason` returned by the agent is ephemeral (logged, not persisted).

## Curated articles

The ordered list of Articles (with approved Summaries) produced by the
**Curator**. Ordered by relevance to the target user profile. This list
is the shared input to both the Email and Podcast producers.

## Digest

The daily HTML email sent via Resend. Contains the Curated articles for
the day, including any approved Articles from previous runs that were
not delivered (Resend failure, run crash). Per-Article idempotence:
`emailed_at` is stamped on success; on failure it stays NULL and the
Resumer picks the Article up at the next run.

## Episode

The daily podcast MP3 file. Generated from a monologue Script (400–600
words) synthesised by the Podcast producer and converted to audio by the
TTS client. Stored as `output/podcasts/daily-synapse-YYYY-MM-DD.mp3`.
Per-Article idempotence: `podcasted_at` is stamped on success; on
failure it stays NULL and the Resumer picks the Article up at the next
run. Per-episode idempotence: `podcast_episodes.mp3_path` set once TTS
succeeds (NULL allows TTS-only retry without regenerating the Script).

## Script

The plain-text monologue (400–600 words, English) written by the Podcast
producer as input to the TTS step. Stored in `podcast_episodes.script`.
Persisted before TTS is attempted so TTS can be retried independently.

## Agent

A LangGraph node that performs a single, well-scoped task in the
Pipeline. Each Agent reads from `PipelineState`, does its work (LLM
call, DB write, external API call), and writes its result back to
`PipelineState`. Agents are isolated: no agent calls another directly.

## Scraper

The LangGraph node that fetches each configured RSS feed and inserts new
Articles into the DB. Sole producer of fresh content in the Pipeline.
Does not load anything pre-existing — that is the Resumer's job.

## Resumer

The LangGraph node that runs immediately after the Scraper. Loads from
the DB every Article still pending some downstream stage (`summary IS
NULL`, or `summary IS NOT NULL AND criticized_at IS NULL`, or
`critic_approved = TRUE` with `emailed_at` or `podcasted_at` still NULL)
and merges them into `state["articles"]`. The single point where the
Pipeline rehydrates in-flight work from previous runs. Downstream Agents
do not query the DB for reads.

## Graph

The LangGraph `StateGraph` that composes all Agents into the Pipeline.
Defined in `app/graph/pipeline.py`. Entry point: `run_graph()`.
Replaces `process_summaries.py` from M0–M2.

## PipelineState

The `TypedDict` that flows through the Graph. Carries all data produced
by each Agent so downstream Agents do not re-query the DB for reads.
Populated at the head of the Graph by the Scraper (new RSS Articles)
and the Resumer (in-flight Articles from previous runs). All subsequent
Agents only read from `PipelineState`; they still write to the DB to
persist their stage outcomes.

## User profile

A description of the target reader used by the Curator to rank Articles.
Hardcoded as a prompt string in M3. Will be read from the `users` DB
table in M6.

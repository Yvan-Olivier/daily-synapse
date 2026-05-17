# ADR 0001 — LLM provider for M3 agents

**Date:** 2026-05-17
**Status:** Superseded

## Context

TECHNICAL.md defines a cost-aware LLM strategy. M3 introduces the full multi-agent graph (Summarizer, Critic, Curator, EmailProducer, PodcastProducer).

## Initial decision

Use Ollama (qwen3.5:9b) for all agents in M3.

**Reasons at the time:**
- Zero marginal cost during development
- The architectural value of M3 (LangGraph graph, agent isolation) is independent of which LLM runs inside each node
- Switching providers later requires only changing the LLM client inside each agent node

## What happened

During integration testing, Ollama failed to produce reliable structured JSON outputs for Critic and Curator, even with `format=schema` enforced:
- Critic returned plain text ("APPROVED\n\nReasoning:...") instead of `{"approved": true, "reason": "..."}`
- Curator returned a bare list `[{...}]` instead of `{"scores": [{...}]}`

Adding prompt workarounds and fallback parsing degraded the code quality without solving the root cause.

## Revised decision

- **Summarizer + ScriptWriter**: stay on Ollama qwen3.5:9b — free-form text generation, no structured output required
- **Critic + Curator**: switch to **OpenAI gpt-4o-mini** via `client.beta.chat.completions.parse(response_format=PydanticModel)` — reliable structured outputs, low cost (~$0.15/1M tokens input)

## Consequences

- `OPENAI_API_KEY` is now required for the full pipeline (already present for TTS)
- Ollama remains required for Summarizer and ScriptWriter
- Cost per run remains near-zero at current article volume (< 10 articles/day)

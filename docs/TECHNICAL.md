# Daily Synapse — Plateforme de veille IA multi-agents

> 📌 **Document de travail — Vision produit.**
> Ce fichier évolue au fur et à mesure des décisions validées lors de la phase de cadrage.
> Seuls les éléments explicitement validés ensemble y figurent.
> Un README public en anglais sera créé en fin de Phase 2.

---

## 🎯 Pitch en une phrase

Une plateforme de veille IA multi-canal, propulsée par un système multi-agents (LangGraph), qui transforme chaque jour l'actualité IA en plusieurs formats personnalisés, dont un **podcast audio quotidien généré par TTS**.

---

## 📖 La vision — Une journée dans la vie du produit

> **Tôt le matin.** Le pipeline se déclenche automatiquement (cron quotidien) ou peut être lancé manuellement via une API REST.
>
> **Collecte.** Le système agrège du contenu depuis plusieurs sources IA / GenAI.
>
> **Enrichissement.** Le contenu brut est nettoyé, complété et préparé pour l'analyse.
>
> **Curation multi-agents (LangGraph).** Un système d'agents spécialisés traite le contenu : résumé, contrôle qualité, classement personnalisé selon le profil utilisateur.
>
> **Production multi-canal.** Plusieurs formats sont générés en sortie. L'un d'eux est un **podcast audio quotidien** (monologue solo, 1 voix narratrice, 3-5 min) produit par TTS.
>
> **Réveil utilisateur.** L'utilisateur consomme ses livrables via les canaux qu'il préfère.

_Note : le détail des sources, canaux et agents sera fixé au Bloc 2._

---

## ✅ Décisions produit verrouillées (Bloc 1)

| Dimension | Choix validé |
|---|---|
| Angle principal | Veille IA multi-canal (Research Agent gardé pour plus tard) |
| Persona cible | Soi-même + ingénieurs IA |
| Scope | Projet ambitieux sur 5-6 semaines |
| Killer features | **Multi-agents LangGraph + Podcast audio TTS** |
| Direction architecturale | **AI-first avec code domain-agnostic dès le jour 1** |
| Domaine fonctionnel (MVP) | IA / GenAI exclusivement |
| Langue des outputs | Anglais (sources EN → outputs EN) |
| Format du podcast | Monologue solo, 1 voix narratrice, 3-5 min |
| Modèle multi-user | Latent (table users en DB, pas d'auth pour démarrer) |
| Trigger d'exécution | Cron quotidien + déclenchement manuel via API REST |
| Modèle multi-user | Latent — destinataire email fixe dans `.env` (M1) ; table `users` en DB introduite en M3/M6 quand le multi-utilisateur sera nécessaire |

---

## 🚀 Killer features (validées)

1. **Système multi-agents orchestré avec LangGraph**
2. **Podcast audio quotidien généré par TTS** — monologue solo, 1 voix narratrice, 3-5 min

---

## 📅 État d'avancement

- [x] Phase 1 — Compréhension du repo de base (datalumina/ai-news-aggregator)
- [x] **Bloc 1** — Vision produit (verrouillé)
- [x] **Bloc 2** — Fonctionnalités core (verrouillé)
- [x] **Bloc 3** — Architecture & stack technique (verrouillé)
- [x] **Bloc 4** — Intégration IA (verrouillé)
- [x] **Bloc 5** — Data pipeline (verrouillé)
- [x] **Bloc 6** — DevOps & production (verrouillé)
- [x] **Bloc 7** — Différenciation & CV (verrouillé)
- [x] **Phase 3 — Roadmap** (verrouillée)
- [x] Phase 3 — Implémentation M0 ✅ M1 ✅ M2 ✅ (M3 à venir)

---

## 🧩 Fonctionnalités core (Bloc 2)

### Sources de contenu (approche phasée)

| Phase | Sources | Complexité |
|---|---|---|
| **Sprint 1-2** | Core labs IA : OpenAI, Anthropic, Mistral, Hugging Face, DeepMind | Faible — flux RSS officiels |
| **Sprint 3-4** | arXiv (papers cs.AI / cs.CL / cs.LG) + Créateurs YouTube + Newsletters experts | Moyenne — PDF parsing, transcript API, web scraping |
| Post-MVP | Communauté (Reddit ML/LocalLLaMA, Hacker News, GitHub Trending) | Non retenu pour l'instant |

### Canaux de sortie

| Canal | Statut |
|---|---|
| **Email HTML quotidien** | ✅ Validé |
| **Podcast audio TTS** (monologue solo, 1 voix, 3-5 min) | ✅ Validé (killer feature) |
| **Dashboard Streamlit minimal** (demo entretien uniquement) | ✅ Validé — affiche les digests du jour + player audio |
| Web dashboard complet / chat agentic / LinkedIn posts | ❌ Non retenu pour le MVP |

### Architecture multi-agents

**Pipeline principal + fan-out parallèle pour les Producers (LangGraph)**

```
Scrape → Summarize → Critic → Curate
                                  ↓
                    ┌─────────────┴─────────────┐
                EmailProducer          PodcastProducer
```

Logique :
- Phase séquentielle : collecte → enrichissement → résumé → contrôle qualité → curation personnalisée
- Phase parallèle : chaque Producer génère son format en simultané (email et podcast)

---

## ⚙️ Stack technique (Bloc 3)

### Stratégie LLM — 3 niveaux (cost-aware)

| Niveau | Modèle | Usage | Coût |
|---|---|---|---|
| **Local** | Ollama (Mistral / Llama 3) | Pré-filtrage des articles | $0 |
| **Cheap** | Claude Haiku (Anthropic) | Résumés des articles (volume) | ~$0.25/1M tokens |
| **Quality** | Claude Sonnet (Anthropic) | Curation / ranking / script podcast | ~$3/1M tokens |

### Services & outils

| Composant | Choix | Raison |
|---|---|---|
| **Vector DB** | Qdrant | DB vectorielle dédiée, Docker-ready, production-grade |
| **Cloud** | Azure | 2 certifications Microsoft, Azure Container Apps + Blob Storage |
| **Email** | Resend | SDK Python simple, 3 000 emails/mois gratuits, sandbox sans domaine pour M1 ; domaine custom à vérifier en M8 |
| **TTS** | OpenAI TTS (M2) → Azure AI Speech (M8) | OpenAI pour démarrer (Azure for Students région-bloqué) ; swap Azure en M8 via adaptateur `TTSClient` |
| **Backend API** | FastAPI | Standard Python IA, OpenAPI auto-générée, Pydantic intégré |
| **Base de données** | PostgreSQL (déjà dans le repo de base) | |

---

## 🤖 Intégration IA (Bloc 4)

### Modèle d'embeddings

**Ollama local** — `nomic-embed-text` (768 dimensions). Coût : $0. Cohérent avec la stratégie cost-aware.

### Graphe d'agents LangGraph (mis à jour)

```
Scrape → Summarize → Critic → Curate
                                  ↓
                    ┌─────────────┴─────────────┐
             EmailProducer          PodcastProducer
```

| Agent | Modèle | Rôle |
|---|---|---|
| Scraper | — | Collecte depuis les sources RSS/API |
| Summarizer | Claude Haiku | Résumé de chaque article |
| Critic | Claude Haiku | Vérifie le résumé contre la source, rejette si hallucination |
| Curator | Claude Sonnet | Classe les articles par pertinence selon le profil user |
| EmailProducer | Claude Haiku | Génère le mail HTML structuré |
| PodcastProducer | Claude Sonnet | Écrit le script podcast → Azure AI Speech → MP3 |

### Anti-hallucination

Agent **Critic** dédié dans le graphe LangGraph : chaque résumé est vérifié contre le contenu source avant d'être validé.

### Observabilité LLM

**LangSmith** (natif LangGraph) — tracing des appels, latence, coûts par étape, inspection des inputs/outputs.

---

## 🔄 Data pipeline (Bloc 5)

### Stratégie d'ingestion

- **Fréquence** : batch quotidien (cron) + déclenchement manuel via API REST
- **Idempotence** : chaque étape filtre sur l'absence de données traitées (`processed_at IS NULL`)

### Filtrage du volume arXiv

~100 papers/jour → filtrage par **similarité d'embeddings** avec le profil utilisateur (Ollama `nomic-embed-text` + Qdrant). Seuls les papers au-dessus d'un seuil de similarité passent à l'étape de résumé.

### Stockage

| Donnée | Stockage |
|---|---|
| Articles, résumés, digests | PostgreSQL |
| Embeddings vectoriels | Qdrant |
| Fichiers MP3 (podcasts) | Azure Blob Storage |

---

## 🛠️ DevOps & Production (Bloc 6)

| Élément | Choix |
|---|---|
| **CI/CD** | GitHub Actions — lint + build Docker + tests sur chaque push, CD vers Azure sur merge `main` |
| **Tests** | Unitaires sur les agents critiques (Summarizer, Critic, Curator) |
| **Déploiement** | Azure Container Apps (pipeline) + Azure Blob Storage (MP3) + Azure PostgreSQL |
| **Observabilité LLM** | LangSmith |
| **Conteneurisation** | Docker + Docker Compose (local), Azure Container Apps (prod) |

---

## 📣 Différenciation & CV (Bloc 7)

### Livrables de visibilité

- **README public professionnel en anglais** — architecture diagram, stack badges, démo GIF/screenshot, instructions setup
- **Article LinkedIn de lancement** — décisions clés, challenges, apports techniques

### Mots-clés techniques clés (pour les offres CDI)

`LangGraph` · `Multi-agent AI` · `RAG` · `Qdrant` · `FastAPI` · `Azure` · `Docker` · `CI/CD` · `LangSmith` · `Anthropic Claude` · `TTS` · `Pydantic` · `PostgreSQL`

---

## 🗺️ Roadmap d'implémentation (Phase 3)

### Principe directeur : **Walking Skeleton + évolution**

Construire d'abord un squelette qui marche de bout en bout avec les technos cibles principales (Postgres + Docker dès M0), puis ajouter les composants spécialisés (LangGraph, Qdrant, FastAPI, Azure, etc.) couche par couche. Chaque jalon est **démoable** et constitue une étape valorisable.

### Jalons (milestones)

| # | Jalon | Livrable concret | CV-able |
|---|---|---|---|
| **M0** | Squelette minimal | Scrape RSS (1-2 sources) → Postgres (Docker) → résumé LLM → print console | — |
| **M1** | Mail HTML quotidien | Mail HTML reçu chaque jour avec top articles + résumés | partiel |
| **M2** | Podcast TTS quotidien | MP3 généré chaque jour (OpenAI TTS → Azure en M8), fichier local ✅ | partiel |
| **M3** | **Migration vers LangGraph** + Agent Critic | Pipeline multi-agents LangGraph avec Critic anti-hallucination | ✅ **CV-able ici** |
| **M4** | Embeddings + Qdrant | Embeddings calculés (Ollama nomic-embed-text), stockés dans Qdrant | ✅ |
| **M5** | Sources élargies | arXiv (filtrage embeddings) + YouTube creators + Newsletters | ✅ |
| **M6** | FastAPI + trigger manuel | API REST avec endpoint `POST /run`, doc OpenAPI | ✅ |
| **M7** | Dashboard Streamlit | UI démo : digests du jour, player audio, graphe LangGraph | ✅ |
| **M8** | Déploiement Azure + CI/CD | Container Apps + Blob Storage + Postgres + GitHub Actions | ✅✅ |
| **M9** | Tests + LangSmith + Polish | Tests unitaires agents critiques, tracing LLM complet | ✅✅ |
| **M10** | README EN + LinkedIn post | Visibilité publique : repo GitHub propre + post de lancement | ✅✅ |

### Logique des dépendances

```
M0 (base) ─→ M1 (mail) ─→ M2 (audio) ─→ M3 (LangGraph) ─→ M4 (embeddings) ─→ M5 (sources +)
                                                                                ↓
                                                                              M6 (FastAPI)
                                                                                ↓
                                                                              M7 (Streamlit)
                                                                                ↓
                                                                              M8 (Azure CI/CD)
                                                                                ↓
                                                                              M9 (tests + obs)
                                                                                ↓
                                                                              M10 (visibilité)
```

### Substitutions / choix incrémentaux

Certains composants seront introduits progressivement pour éviter de tout configurer en même temps :

| Composant | M0-M2 | M3+ |
|---|---|---|
| Orchestration agents | Fonctions Python séquentielles | LangGraph (M3) |
| LLM provider | À valider (OpenAI ou Anthropic direct) | Multi-tier Ollama + Claude (M3+) |
| Vector DB | Aucune (pas besoin) | Qdrant (M4) |
| API | Aucune | FastAPI (M6) |
| Dashboard | Aucun | Streamlit (M7) |
| Déploiement | Local Docker Compose | Azure Container Apps (M8) |
| Observabilité | Logs Python | LangSmith (M9) |

---

## 🎯 Spécification M0 — Squelette minimal

### Choix techniques pour M0

| Aspect | Choix |
|---|---|
| Source de contenu | **Anthropic uniquement** (3 flux RSS communautaires Olshansk) |
| LLM provider | **Ollama local** (modèle à confirmer — Mistral 7B ou Llama 3.1 8B) |
| Gestionnaire de paquets | **uv** |
| Structure du code | **Modulaire dès le départ** (`app/scrapers`, `app/database`, `app/llm`, `app/services`) |
| Base de données | **PostgreSQL 17** via Docker Compose |
| ORM | SQLAlchemy 2.x |

### Livrables M0

- [x] Projet Python initialisé avec `uv` (`pyproject.toml`)
- [x] `docker-compose.yml` avec Postgres 17
- [x] Modèle SQLAlchemy `AnthropicArticle` + script `create_tables.py`
- [x] Scraper RSS Anthropic (`app/scrapers/anthropic.py`) avec déduplication
- [x] Client LLM Ollama (`app/llm/ollama_client.py`) pour résumer un article
- [x] Repository pattern (`app/database/repository.py`) pour insert/update
- [x] Service d'orchestration (`app/services/process_summaries.py`)
- [x] Point d'entrée CLI (`main.py`) qui exécute le pipeline complet
- [x] `.env.example` et `.gitignore`
- [x] Mini-README technique (`README-tech.md`)

**Statut** : Code M0 livré ✅ — en attente du premier test utilisateur.

### Structure de dossiers cible

```
ai-news-platform/
├── README.md                  # ce document (vision)
├── README-tech.md             # instructions techniques de setup
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
├── docker-compose.yml
├── main.py
└── app/
    ├── __init__.py
    ├── config.py              # config centrale (URLs RSS, etc.)
    ├── database/
    │   ├── __init__.py
    │   ├── connection.py
    │   ├── models.py
    │   ├── repository.py
    │   └── create_tables.py
    ├── scrapers/
    │   ├── __init__.py
    │   └── anthropic.py
    ├── llm/
    │   ├── __init__.py
    │   └── ollama_client.py
    └── services/
        ├── __init__.py
        └── process_summaries.py
```

### Critère de complétion M0

Le M0 est considéré **terminé** lorsque l'exécution de `python main.py` :

1. Lance Postgres (déjà actif via Docker Compose)
2. Scrape les 3 flux RSS Anthropic et insère les nouveaux articles en DB
3. Appelle Ollama pour résumer chaque nouvel article (titre + 2-3 phrases)
4. Stocke chaque résumé en DB
5. Affiche dans la console : `Processed N articles (M new, K already in DB)`

Une seconde exécution successive doit afficher `0 new` (idempotence).

### Prérequis utilisateur pour M0

- **Docker Desktop** installé et lancé
- **Ollama** installé localement (https://ollama.com) + un modèle pull
- **uv** installé (https://docs.astral.sh/uv/)

---

## 🛠️ Mise en route locale

**Prérequis** : Docker Desktop, Ollama (`ollama pull qwen3.5:9b`), uv.

```bash
cp .env.example .env          # renseigner RESEND_API_KEY + DIGEST_EMAIL
uv sync                       # installer les dépendances
docker compose up -d          # démarrer Postgres
uv run python -m app.database.create_tables  # créer les tables (1 fois)
uv run python main.py         # lancer le pipeline
```

Vérification en DB :
```sql
SELECT title, summary_title, emailed_at FROM anthropic_articles ORDER BY published_at DESC LIMIT 5;
```

**Dépannage** :
- Postgres ne démarre pas → port 5432 déjà utilisé
- Ollama connection refused → lancer `ollama serve`
- Email non reçu → vérifier `RESEND_API_KEY` dans `.env` ; sandbox peut aller en spam

---

## 🎙️ Spécification M2 — Podcast TTS quotidien

### Pipeline complet (M2)

```
Scrape → Store → Summarize → Email → Podcast
```

Le podcast est la 5e et dernière étape. Si elle échoue, le pipeline ne crashe pas — l'email a déjà été envoyé.

### Déclenchement

Même logique d'idempotence que l'email : le podcast est généré uniquement si des articles ont un résumé et `podcasted_at IS NULL`. Un seul épisode par jour.

### Script

| Paramètre | Valeur |
|---|---|
| LLM | Ollama local (`qwen3.5:9b`) |
| Langue | Anglais |
| Format | Monologue fluide (pas une liste lue) |
| Structure | Intro avec date, corps libre, outro court |
| Longueur cible | 400-600 mots (~3-4 min audio) |

### TTS — OpenAI TTS (M2) → Azure AI Speech (M8)

**M2 local** : OpenAI TTS (Azure for Students bloque les régions Speech Services).
**M8 déploiement** : swap vers Azure AI Speech si la subscription le permet — `tts_client.py` est un adaptateur interchangeable.

| Paramètre | Valeur |
|---|---|
| SDK M2 | `openai` Python SDK |
| Modèle | `tts-1` |
| Voix par défaut | `nova` |
| Override | `PODCAST_VOICE` dans `.env` |
| Coût estimé | ~$0.0014/mois (500 mots/épisode × 30 jours) |
| Interface | Classe abstraite `TTSClient` — `AzureTTSClient` ajouté en M8 |

### Stockage

| Donnée | Où |
|---|---|
| Script texte | Table `podcast_episodes` en DB |
| Chemin MP3 | Table `podcast_episodes` (`mp3_path`) |
| Fichier MP3 | `output/podcasts/daily-synapse-YYYY-MM-DD.mp3` |
| Flag article | `podcasted_at` sur `AnthropicArticle` |

### Table `podcast_episodes`

```
id          SERIAL PRIMARY KEY
episode_date DATE UNIQUE
script      TEXT
mp3_path    TEXT (NULL si TTS a échoué)
article_guids TEXT[] (liste des articles inclus)
created_at  TIMESTAMPTZ
```

### Résilience

- Script généré → sauvegardé en DB même si TTS échoue (`mp3_path = NULL`)
- Au prochain run : si script existe mais `mp3_path IS NULL` → retente uniquement le TTS
- Pipeline continue sans crasher dans tous les cas

### Variables `.env` ajoutées

```
OPENAI_API_KEY=          # utilisé pour TTS en M2
PODCAST_VOICE=nova       # voix OpenAI TTS (nova, alloy, echo, fable, onyx, shimmer)
```

### Nouveaux fichiers

```
app/
└── podcast/
    ├── __init__.py
    ├── tts_client.py     ← Azure AI Speech SDK
    └── producer.py       ← orchestration script → TTS → MP3
app/llm/
└── script_writer.py      ← génération du script via Ollama
output/
└── podcasts/             ← MP3 locaux (gitignored)
```

---

## 🔮 Idées en réserve (post-MVP, non engagées)

- Research Agent conversationnel (extension future explicitement gardée pour plus tard)

---

## 🔗 Inspirations & références

- **Repo de base** : [datalumina/ai-news-aggregator](https://github.com/datalumina/ai-news-aggregator) — utilisé comme base d'inspiration, non clonée

---

_Dernière mise à jour : M0 + M1 + M2 validés. Prochaine étape : M3 (LangGraph + agent Critic)._

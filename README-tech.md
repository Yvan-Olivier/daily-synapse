# Daily Synapse — Setup technique (M0)

Instructions de mise en route du squelette M0.

## Prérequis

- **macOS / Linux** (Windows non testé)
- **Python 3.12+**
- **Docker Desktop** installé et lancé
- **Ollama** installé : https://ollama.com
- **uv** installé : `curl -LsSf https://astral.sh/uv/install.sh | sh`

## 1. Récupérer le modèle Ollama

```bash
ollama pull qwen2.5:7b
```

Vérifier que le modèle est disponible :

```bash
ollama list
```

Tester rapidement :

```bash
ollama run qwen2.5:7b "Reply with only: OK"
```

## 2. Configurer l'environnement

```bash
cd /Users/yvanngame/Documents/daily-synapse
cp .env.example .env
```

Le fichier `.env` est déjà configuré avec des valeurs par défaut fonctionnelles en local. Aucune modification nécessaire pour M0.

## 3. Installer les dépendances Python

```bash
uv sync
```

Cela crée un environnement virtuel `.venv/` et installe toutes les dépendances listées dans `pyproject.toml`.

## 4. Lancer Postgres (Docker)

```bash
docker compose up -d
```

Vérifier que Postgres est sain :

```bash
docker compose ps
```

Tu dois voir le service `postgres` avec le statut `healthy`.

## 5. Créer les tables

```bash
uv run python -m app.database.create_tables
```

Sortie attendue : `Tables created successfully.`

## 6. Exécuter le pipeline

```bash
uv run python main.py
```

Ou avec une fenêtre temporelle personnalisée (en heures) :

```bash
uv run python main.py 72
```

## 7. Vérifier les résultats en DB

Tu peux te connecter à Postgres avec n'importe quel client (DBeaver, TablePlus, `psql`, etc.) :

- Host : `localhost`
- Port : `5432`
- User : `postgres`
- Password : `postgres`
- Database : `daily_synapse`

Requête de vérification :

```sql
SELECT title, summary_title, summary
FROM anthropic_articles
WHERE summary IS NOT NULL
ORDER BY published_at DESC
LIMIT 5;
```

## 8. Tester l'idempotence

Relance simplement `uv run python main.py`. Tu dois voir :

- `Inserted 0 new article(s)` (les articles sont déjà en DB)
- `0 article(s) pending summarization` (déjà résumés)

## Tests rapides des modules isolés

Le scraper :

```bash
uv run python -m app.scrapers.anthropic
```

Le client Ollama :

```bash
uv run python -m app.llm.ollama_client
```

## Arrêter Postgres

```bash
docker compose down
```

Pour effacer aussi les données :

```bash
docker compose down -v
```

## Architecture des modules (M0)

```
daily-synapse/
├── main.py                       # Point d'entrée CLI
├── docker-compose.yml            # Postgres local
├── pyproject.toml                # Dépendances Python (uv)
├── .env                          # Config locale (non versionné)
└── app/
    ├── config.py                 # Constantes (URLs RSS, lookback)
    ├── database/
    │   ├── connection.py         # Engine + session SQLAlchemy
    │   ├── models.py             # ORM : AnthropicArticle
    │   ├── repository.py         # Repository pattern (CRUD)
    │   └── create_tables.py      # Init des tables
    ├── scrapers/
    │   └── anthropic.py          # Parse les 3 RSS Anthropic
    ├── llm/
    │   └── ollama_client.py      # Wrapper Ollama avec structured output
    └── services/
        └── process_summaries.py  # Orchestrateur du pipeline
```

## Flux d'exécution M0

```
main.py
  └─ run_pipeline()
      ├─ AnthropicScraper.get_articles()       (RSS → list[AnthropicArticle])
      ├─ Repository.bulk_insert_anthropic_articles()  (skip duplicates)
      ├─ Repository.get_articles_without_summary()
      └─ pour chaque article pending :
          ├─ OllamaClient.summarize()          (titre + résumé via LLM local)
          └─ Repository.update_summary()
```

## Dépannage courant

**Postgres ne démarre pas** → vérifier que le port 5432 n'est pas déjà utilisé.

**`ollama` connection refused** → vérifier qu'Ollama tourne :
```bash
ollama serve  # dans un autre terminal, si pas lancé en daemon
```

**`uv: command not found`** → relancer le shell après installation ou ajouter `~/.local/bin` au `PATH`.

**Pipeline lent au premier appel** → normal, Qwen 2.5 7B charge ~5 GB en RAM/VRAM au premier appel. Les appels suivants sont rapides.

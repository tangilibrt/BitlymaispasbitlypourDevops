# URL Shortener — Projet DevOps

Raccourcisseur d'URL "Bitly-like" en Python/FastAPI, construit selon une démarche
DevOps : architecture en couches, deux microservices conteneurisés, tests à toutes
les couches (avec mocks web), couverture ≥ 85 % et pipeline CI.

## Architecture (3 couches, dépendances descendantes uniquement)

```
Controller  (FastAPI endpoints)   app/controllers/url_controller.py
    │  ▼
Services    (logique métier)      app/services/shortener_service.py
    │  ▼                          app/services/validator_service.py  ──HTTP──┐
Data        (SQLAlchemy/SQLite)   app/data/{models,repository,database}.py   │
                                                                             ▼
                                          Microservice « validator-service » (port 8001)
                                          validator/{main,validator_logic}.py
```

Deux services back orchestrés par Docker :

| Service | Port | Rôle | Endpoints |
|---|---|---|---|
| `shortener-service` | 8000 | Création / résolution / stats | `POST /shorten`, `GET /{code}`, `GET /stats/{code}`, `GET /` (front) |
| `validator-service` | 8001 | Validation d'URL (format + joignabilité) | `POST /validate`, `GET /health` |

Avant de créer un lien, `shortener-service` appelle `validator-service` en HTTP.
C'est cet appel réseau qui est **mocké** dans les tests (jamais d'accès Internet).

## API

```bash
# Créer un lien court (l'URL est validée via le validator-service)
curl -X POST http://localhost:8000/shorten \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com"}'
# => {"code":"Ab3xZ9","short_url":"http://localhost:8000/Ab3xZ9"}

# Résoudre (redirection 302 + incrément du compteur)
curl -i http://localhost:8000/Ab3xZ9

# Statistiques
curl http://localhost:8000/stats/Ab3xZ9
# => {"url":"https://example.com","clicks":1}
```

Codes HTTP : `200` (OK), `302` (redirection), `400` (URL invalide/injoignable),
`404` (code inconnu).

## Lancement local (sans Docker)

```bash
python -m venv .venv
source .venv/bin/activate           # Windows : .venv\Scripts\activate
pip install -r requirements.txt

# Terminal 1 — validator
uvicorn validator.main:app --port 8001

# Terminal 2 — shortener (il joint le validator en local)
VALIDATOR_URL=http://localhost:8001 uvicorn app.main:app --port 8000
```

Front web : ouvrir <http://localhost:8000/>.

## Lancement avec Docker

```bash
docker-compose up --build
```

`docker-compose up` suffit à démarrer l'application complète. Le `shortener-service`
joint le `validator-service` par son nom de service (`http://validator-service:8001`).

## Tests, couverture et qualité

```bash
pytest                       # tests + couverture (échoue si < 85 %)
black --check app validator tests
flake8 app validator tests
pylint app validator
```

- Rapport de couverture HTML généré dans `htmlcov/` (ouvrir `htmlcov/index.html`)
  pour l'inclure dans le rapport final.
- Couverture courante : **~93 %** (seuil CI : 85 %).

| Couche | Tests |
|---|---|
| Data | `tests/test_data/` — CRUD sur SQLite en mémoire, incrément atomique, collisions |
| Services | `tests/test_services/` — logique mockée + **mock web** (`respx`) de l'appel validator |
| Controller | `tests/test_controllers/` — `TestClient`, codes 200/302/400/404, service mocké |
| Validator | `tests/test_validator/` — logique + endpoint, requêtes HTTP sortantes mockées |

## Pipeline CI

`.github/workflows/ci.yml` (push + pull request) :
lint (black/flake8/pylint) → tests + couverture (`--cov-fail-under=85`) →
upload des rapports en artefacts → build des deux images Docker.

## Choix de conception

- **Code court** : base62 aléatoire sur 6 caractères, régénéré en cas de collision.
- **Comptage de clics** : compteur atomique (`UPDATE ... clicks = clicks + 1`) sur la
  ligne `Link`, incrémenté à chaque `GET /{code}`.
- **Validation déléguée** : le shortener « fail closed » (refuse le lien) si le
  validator est injoignable ou renvoie une erreur.

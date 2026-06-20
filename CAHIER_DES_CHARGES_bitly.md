# Cahier des charges — Projet DevOps : Raccourcisseur d'URL ("Bitly-like")

## 1. Contexte & objectif

Développer une application de raccourcissement d'URL en **Python**, en respectant
strictement les règles DevOps imposées par le sujet : dépôt Git, pipeline CI,
architecture logicielle en couches, au moins deux services back conteneurisés,
tests de toutes les couches (unitaires + mocks web), bonne couverture de code et
qualité logicielle élevée.

> **Hors périmètre** : Continuous Delivery (non demandée).
> **Bonus** : front web + base de données (à faire si le reste est solide).

L'application doit :
- Accepter une URL longue et renvoyer un **code court** unique.
- Résoudre un code court vers l'URL d'origine (redirection HTTP 301/302).
- Compter le **nombre de clics** par lien.

## 2. Stack technique imposée

| Élément | Choix |
|---|---|
| Langage | Python 3.11+ |
| Framework web | FastAPI |
| Serveur ASGI | Uvicorn |
| Tests | pytest |
| Mocks | pytest-mock + `respx` (mock HTTP) ou `unittest.mock` |
| Couverture | pytest-cov |
| Qualité | pylint + flake8 + black (format) |
| Conteneurs | Docker + docker-compose |
| Persistance (couche data) | SQLite via SQLAlchemy (en mémoire pour les tests) |

## 3. Architecture en couches (obligatoire)

L'architecture doit être **strictement** découpée en 3 couches, avec dépendances
descendantes uniquement (Controller → Services → Data). Aucune couche ne doit
sauter une couche ni remonter.

```
url-shortener/
├── app/
│   ├── data/                 # Couche DATA : persistance + accès externe
│   │   ├── models.py         # Modèles SQLAlchemy (Link, Click)
│   │   ├── repository.py     # CRUD : create_link, get_by_code, increment_clicks
│   │   └── database.py       # Session / engine SQLite
│   ├── services/             # Couche SERVICES : logique métier
│   │   ├── shortener_service.py   # génération du code court, création de lien
│   │   └── validator_service.py   # validation de l'URL via service HTTP externe
│   ├── controllers/          # Couche CONTROLLER (web) : endpoints FastAPI
│   │   └── url_controller.py
│   └── main.py               # Point d'entrée FastAPI
├── tests/
│   ├── test_data/
│   ├── test_services/
│   └── test_controllers/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini                # config coverage
├── .pylintrc
└── README.md
```

## 4. Les deux services back (exigence clé)

Le sujet impose **au moins deux services back intégrés avec Docker**. On expose
donc deux microservices distincts orchestrés par docker-compose :

### Service 1 — `shortener-service` (port 8000)
Service principal. Gère la création de liens, la résolution et le comptage.
- `POST /shorten` → `{ "url": "https://..." }` ⇒ `{ "code": "abc123", "short_url": "..." }`
- `GET /{code}` → redirige (302) vers l'URL longue + incrémente le compteur
- `GET /stats/{code}` → `{ "url": "...", "clicks": 42 }`

Avant de créer un lien, ce service **appelle le Service 2** pour valider l'URL.

### Service 2 — `validator-service` (port 8001)
Microservice séparé qui valide qu'une URL est bien formée et joignable.
- `POST /validate` → `{ "url": "https://..." }` ⇒ `{ "valid": true, "reachable": true }`

> **Pourquoi ce découpage ?** L'appel HTTP de `shortener-service` vers
> `validator-service` est ce qui rend les **mocks web** naturels et obligatoires
> dans les tests (on mocke la réponse du validator au lieu de l'appeler vraiment).

## 5. Logique métier à implémenter

- **Génération du code court** : hash court déterministe ou aléatoire base62
  (6 caractères). Gérer les collisions (régénérer si le code existe déjà).
- **Idempotence optionnelle** : la même URL peut renvoyer le même code (au choix,
  documenter le comportement).
- **Validation** : déléguée au `validator-service` (format + tentative de requête
  HEAD/GET). En cas d'URL invalide → `400 Bad Request`.
- **Comptage de clics** : à chaque `GET /{code}`, incrémenter `clicks` dans la
  couche data de façon atomique.
- **Code inexistant** → `404 Not Found`.

## 6. Stratégie de tests (toutes les couches)

Chaque couche doit avoir ses tests dédiés. Viser **≥ 85 % de couverture**.

| Couche | Type de test | Points clés |
|---|---|---|
| Data | Unitaires | CRUD sur SQLite en mémoire, incrément clics, collisions |
| Services | Unitaires + **mocks web** | `shortener_service` testé en **mockant** l'appel HTTP au `validator-service` (avec `respx` ou `unittest.mock`). `validator_service` testé en mockant la requête HTTP sortante vers l'URL cible |
| Controller | Unitaires | `TestClient` FastAPI, codes HTTP (200/302/400/404), services mockés |

**Exigence mock web explicite** : au moins un test où l'appel réseau réel est
remplacé par un mock (ne jamais dépendre d'Internet pendant les tests).

## 7. Pipeline CI (GitHub Actions)

Fichier `.github/workflows/ci.yml` déclenché sur push et pull request :

1. Checkout
2. Setup Python 3.11
3. Install des dépendances
4. **Lint** : `black --check`, `flake8`, `pylint` (échec si score < seuil défini)
5. **Tests + couverture** : `pytest --cov=app --cov-report=xml --cov-report=term`
6. **Échec du build si couverture < 85 %** (`--cov-fail-under=85`)
7. (Optionnel) Build des images Docker pour vérifier qu'elles compilent

Le job doit produire les rapports (tests, couverture) en artefacts téléchargeables.

## 8. Docker

- **Un Dockerfile** par service (ou un Dockerfile paramétré).
- **docker-compose.yml** qui lance les deux services sur le même réseau, le
  `shortener-service` pouvant joindre `validator-service` par son nom de service
  (`http://validator-service:8001`).
- `docker-compose up` doit suffire à démarrer l'application complète.

## 9. Bonus (notés en plus)

- **Front web** : page HTML simple (un champ URL + bouton + affichage du lien
  court et des stats). Peut être servie par FastAPI (`StaticFiles` / Jinja2).
- **Base de données** : déjà couverte par SQLite ; bonus si passage à PostgreSQL
  via un 3e conteneur dans docker-compose.

## 10. Livrables attendus (rappel sujet)

- Dépôt Git propre (commits réguliers, `.gitignore` Python).
- Rapport écrit contenant :
  - le **schéma d'architecture logicielle**,
  - les **rapports de tests**, de **couverture de code**, de **qualité**,
  - une **copie d'écran des Google labs** réalisés.
- Remise sur Moodle.

## 11. Consignes pour Claude Code

1. Initialise le repo Git et la structure de dossiers ci-dessus.
2. Implémente couche par couche, **de bas en haut** : data → services → controller.
3. Écris les tests **en même temps** que chaque couche (TDD léger).
4. Configure `pytest.ini`, `.pylintrc`, `requirements.txt` dès le départ.
5. Crée le `docker-compose.yml` avec les deux services et vérifie l'intégration.
6. Ajoute le workflow GitHub Actions.
7. Rédige un `README.md` clair (lancement local, lancement Docker, lancement des tests).
8. Génère un rapport de couverture HTML que je pourrai inclure dans le rapport final.
9. Commits atomiques et messages clairs (convention : `feat:`, `test:`, `ci:`, `docs:`).

> Code en anglais (noms de variables, fonctions, commentaires), documentation
> utilisateur (README) bilingue ou en français au choix.

# Legitima Backend

Backend initialisé (ultra safe) pour le produit **Legitima**.

## ✅ Ce que fournit ce squelette
- FastAPI opérationnel avec un endpoint de santé.
- Un endpoint transitoire `POST /analyze` pour le flux iOS onboarding -> analyse -> résultat.
- Un endpoint déterministe `POST /cv/parse` pour extraire les expériences depuis un CV PDF textuel, sans appel OpenAI.
- Structure modulaire alignée sur les concepts métiers.
- Endpoints CRUD V1 pour les objets métiers (scopés par `user_id`).
- Gestion d'erreurs centralisée (scaffold) + logging minimal.
- Tests minimaux (scaffold).

## 🔐 Authentification (V1)
Supabase Auth est l’unique système d’authentification en V1.

- L’app iOS s’authentifie directement avec Supabase.
- Le backend FastAPI fait confiance à Supabase pour l’identité.
- Les requêtes peuvent inclure `Authorization: Bearer <supabase_jwt>`.
- Le backend n’effectue **aucune** validation/décodage de JWT pour l’instant.
- Les règles d’ownership et de contrôle d’accès seront ajoutées plus tard.

Variables d’environnement attendues (placeholders) :
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `X-User-Id` (header requis pour toutes les routes CRUD, transmis par le client)

## 🚫 Ce qui est intentionnellement NON implémenté (V1)
- Aucune logique métier.
- Aucune gestion d’authentification côté backend (pas de login/signup, pas de JWT).
- Aucun contrôle d’accès avancé (seulement filtrage par `user_id`).

Exception transitoire :
- `POST /analyze` est supporté pour stabiliser le flux V1 frontend actuel, mais ce n’est pas le design cible long terme.

## 📁 Arborescence (résumé)
```
legitima-backend/
  app/
    api/
      health.py
      routes/
    auth/
    config/
    domain/
    observability/
    main.py
  tests/
  requirements.txt
  README.md
```

## ▶️ Lancer localement
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## ✅ Endpoint de santé
```
GET /health
{"status": "ok"}
```

## 📘 Contrat d'API
Le contrat d'API actuellement supporté par le backend est documenté dans [docs/api-contract.md](/Users/milehanalivecomm/Documents/Developer/legitima-backend/docs/api-contract.md).

Ce document fait foi pour le V1 backend. Toute route non montée dans [app/main.py](/Users/milehanalivecomm/Documents/Developer/legitima-backend/app/main.py) et non documentée dans ce contrat doit être considérée comme non supportée par le frontend.

Les scénarios contrôlés de validation d'erreurs pour `POST /cv/parse` sont documentés dans [docs/cv-parse-error-testing.md](/Users/milehanalivecomm/Documents/Developer/legitima-backend/docs/cv-parse-error-testing.md).

## 🤖 Analyse V1 transitoire
Le backend supporte aussi `POST /analyze` comme endpoint transitoire officiel pour le flux iOS actuel `onboarding -> analyse -> résultat`.

- Il nécessite `OPENAI_API_KEY` côté backend.
- Il supporte actuellement de manière fiable uniquement la sortie en français.
- Son contrat exact est documenté dans [docs/api-contract.md](/Users/milehanalivecomm/Documents/Developer/legitima-backend/docs/api-contract.md).
- Il est destiné à être remplacé plus tard par des endpoints métier plus explicites.

## 📌 API (CRUD V1)
Toutes les routes CRUD nécessitent le header `X-User-Id` et sont filtrées par `user_id`.

Routes disponibles (POST/GET list/GET by id/PATCH/DELETE) :
- `/contexte`
- `/parcours`
- `/elements`
- `/zones`
- `/requalifications`
- `/fil-conducteur`
- `/reponses`

## ⚠️ Remarque
Les routes métiers sont désormais disponibles en CRUD V1 et nécessitent `X-User-Id`.

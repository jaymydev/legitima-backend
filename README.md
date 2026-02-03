# Legitima Backend

Backend initialisé (ultra safe) pour le produit **Legitima**.

## ✅ Ce que fournit ce squelette
- FastAPI opérationnel avec un endpoint de santé.
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
- Aucune orchestration IA.
- Aucune gestion d’authentification côté backend (pas de login/signup, pas de JWT).
- Aucun contrôle d’accès avancé (seulement filtrage par `user_id`).

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

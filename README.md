# Legitima Backend

Backend initialisé (ultra safe) pour le produit **Legitima**.

## ✅ Ce que fournit ce squelette
- FastAPI opérationnel avec un endpoint de santé.
- Un endpoint transitoire `POST /analyze` pour le flux iOS onboarding -> analyse -> résultat.
- Un endpoint déterministe `POST /cv/parse` pour extraire les expériences depuis un CV PDF textuel ou une image JPEG/PNG via OCR classique, sans appel OpenAI.
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

## 🚦 Limitation de débit

Les endpoints d'IA ne sont pas authentifiés. La seule chose qui sépare une
boucle automatisée du compte OpenAI est la limitation par adresse IP :

- `POST /analyze`, `/v2/interview-preparation/analyze`, `/v2/interview-preparation/kickoff` : **10 / heure**
- `POST /cv/parse` : **20 / heure**
- toutes les autres routes : **120 / heure**
- `GET /health` : jamais compté (Render l'interroge en continu)

L'app iOS tenait autrefois un quota dans `UserDefaults`. Il ne protégeait rien
— une réinstallation le remettait à zéro — et il a été retiré au passage en app
gratuite. Ceci le remplace.

L'adresse est lue **par la gauche** de `X-Forwarded-For`, c'est-à-dire au bout
client de la chaîne.

La première version lisait par la droite, en supposant que le bout droit était
ce que notre propre proxy avait observé. Mesuré sur le service déployé, c'était
faux : Render ajoute un intermédiaire dont l'adresse **change d'une requête à
l'autre**, donc chaque appel ouvrait un seau neuf : le compteur renvoyé dans
`X-RateLimit-Remaining` remontait au lieu de descendre. Depuis le correctif il
décroît d'une unité par requête. Lire l'IP du socket
serait tout aussi faux dans l'autre sens : tout le monde dans un seul seau,
derrière le proxy, et l'app refuserait du trafic réel.

Contrepartie assumée : quelqu'un qui forge l'entrée de gauche s'offre un quota
neuf à chaque requête. Le filet contre ça n'est pas cette limite, c'est le
plafond mensuel OpenAI. Le choix est entre une limite qui s'applique à tout le
monde et une limite qui ne s'appliquait à personne.

`SKIPPED_FORWARDED_ENTRIES` (défaut `0`) ignore autant d'entrées de tête, si un
proxy à nous est un jour placé devant.

Les compteurs vivent en mémoire, ce qui est correct pour une instance unique.
Passer à plusieurs instances donnerait à chacune ses propres compteurs et
multiplierait chaque limite d'autant : c'est le moment où il faudra Redis.

**Ce n'est pas un plafond de dépense.** Le filet de sécurité reste la limite
mensuelle à régler dans le tableau de bord OpenAI.

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

Les prérequis de déploiement OCR pour les images JPEG/PNG sont documentés dans [docs/cv-parse-ocr-deployment.md](/Users/milehanalivecomm/Documents/Developer/legitima-backend/docs/cv-parse-ocr-deployment.md).

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

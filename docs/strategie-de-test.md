# Stratégie de test — MiniShop

> Modèle à compléter pendant l'Atelier 12. Une stratégie de test tient sur 2 pages : si elle est plus longue, personne ne la lit.

## 1. Périmètre et risques
| Zone | Risque métier | Probabilité | Impact | Niveau de test principal |
|---|---|---|---|---|
| Calcul des prix (`pricing.py`) | Mauvais montant facturé | Moyenne | Élevé | Unitaire + génération IA |
| API commandes | Commande perdue | Faible | Élevé | API + contrat |
| Interface | Parcours bloqué | Moyenne | Moyen | E2E + visuel |
| Performance | Abandon de panier | … | … | Charge (Locust/JMeter) |
| Sécurité | Fuite / injection | … | … | SAST, SCA, DAST (ZAP) |

## 2. Pyramide et quality gates
| Étape pipeline | Tests | Seuil bloquant |
|---|---|---|
| PR | lint, unitaires, API | 100 % OK, couverture ≥ 85 % |
| main | + E2E, visuel, sécurité | 0 vulnérabilité HIGH/CRITICAL |
| nocturne | charge, ZAP complet | p95 < 300 ms, erreurs < 1 % |

## 3. Règles pour les tests générés par IA
- Un test généré est **relu** avant fusion (marqueur `@pytest.mark.generated`).
- Il doit échouer si on casse la règle qu'il prétend vérifier (vérifié par mutation).
- Pas de secret ni de donnée client dans les prompts.
- Le prompt de génération inclut toujours le **code source** testé, pas seulement la spec :
  sans lui, le LLM ne connaît pas l'API et produit des tests inexécutables
  (mesuré : 20 tests sur 20 en échec avec la spec seule).
- À la relecture, on vérifie en priorité les **seuils** : chaque limite doit être testée
  pile dessus et juste en dessous (le LLM a tendance à choisir des valeurs trop éloignées).
- La **personne qui génère et fusionne** un test en est responsable, comme si elle l'avait écrit :
  l'IA est un outil, pas un auteur.
- Le LLM **n'exécute pas** les tests qu'il génère : on veut voir sa production brute,
  sinon il peut corriger ses erreurs en silence et masquer ses hallucinations.

## 4. Gestion des tests instables (flaky)
- Détection : `ai_tools/test_history.py` (score ≥ 0,6).
- Quarantaine : marqueur `flaky`, ticket ouvert, délai de correction 5 jours.

## 5. Indicateurs suivis
Taux de réussite sur main, durée de la suite, nombre de tests flaky, couverture, MTTR d'une régression.

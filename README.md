# Données publiques de l'application MédiGuide

Fichiers téléchargés automatiquement par l'application Android MédiGuide (aucune donnée personnelle).

| Fichier | Contenu | Mise à jour |
|---|---|---|
| `actualites.json` | Actualités sanitaires « À la une » | Quotidienne (si nouveauté) |
| `cas_cliniques.json` | Cas cliniques de la section Formation | Hebdomadaire (nouvelle série) |
| `meds.json` | Contenu complet : médicaments, pathologies, scores, protocoles, quiz | Hebdomadaire (si mise à jour des recommandations) |
| `corrections.json` | Journal de chaque modification de fiche (date, champ, source, motif) | À chaque modification |

Règles :
- Toujours lancer `python3 outils/valider.py` avant de publier ; ne jamais publier un fichier qui échoue.
- Ne jamais renuméroter ni supprimer une fiche : les identifiants sont utilisés par les favoris et les liens.
- Toute modification d'une fiche de `meds.json` incrémente `version`, met à jour `dateMiseAJour` et est inscrite dans `corrections.json` avec sa source.
- Les modifications de fiches (`meds.json`) sont préparées sur une branche `propositions-<date>` et ne sont fusionnées dans `main` qu'après validation explicite du médecin responsable. Les cas cliniques et les actualités sont publiés directement.

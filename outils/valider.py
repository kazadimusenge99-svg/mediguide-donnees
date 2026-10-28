#!/usr/bin/env python3
"""Validation des fichiers publiés pour l'application MédiGuide.
Usage : python3 outils/valider.py   (depuis la racine du dépôt). Code de sortie 0 = tout est valide.
Les téléphones téléchargent ces fichiers automatiquement : ne jamais publier un fichier qui échoue ici."""
import json, sys, re

erreurs = []
def err(m): erreurs.append(m)

PICTOS = {"virus", "bacterie", "moustique", "goutte", "pomme", "thermometre", "poumons", "coeur", "bebe",
          "grossesse", "seringue", "alerte", "globe"}
THEMES = {"paludisme", "vihtb", "urgences", "pediatrie", "obstetrique", "antibiotiques", "epidemies", "pharmaco", "scores"}

meds = json.load(open("meds.json", encoding="utf-8"))
pid = {p["id"] for p in meds["pathologies"]}
mid = {m["id"] for m in meds["medicaments"]}
dcis = {m["dci"] for m in meds["medicaments"]}

# --- meds.json : structure minimale attendue par l'application ---
for cle in ("version", "dateMiseAJour", "classes", "medicaments", "categoriesPathologies", "pathologies"):
    if cle not in meds: err(f"meds.json : clé manquante {cle}")
if len(meds["medicaments"]) < 50: err("meds.json : moins de 50 médicaments")
if sorted(mid) != list(range(1, len(mid) + 1)): err("meds.json : identifiants des médicaments non contigus (ne jamais renuméroter)")
if sorted(pid) != list(range(1, len(pid) + 1)): err("meds.json : identifiants des pathologies non contigus (ne jamais renuméroter)")
cats = {c["id"] for c in meds["categoriesPathologies"]}; classes = {c["id"] for c in meds["classes"]}
for m in meds["medicaments"]:
    for k in ("dci", "noms", "classe", "formes", "indications", "posologieAdulte", "posologieEnfant", "contreIndications",
              "precautions", "effetsIndesirables", "grossesse"):
        if k not in m: err(f"médicament {m.get('id')} : champ {k} manquant")
    if m.get("classe") not in classes: err(f"médicament {m['id']} : classe inconnue {m.get('classe')}")
for p in meds["pathologies"]:
    for k in ("nom", "categorie", "synonymes", "resume", "signes", "diagnostic", "traitement", "gravite", "prevention", "medicaments"):
        if k not in p: err(f"pathologie {p.get('id')} : champ {k} manquant")
    if p.get("categorie") not in cats: err(f"pathologie {p['id']} : catégorie inconnue")
    for d in p.get("medicaments", []):
        if d not in dcis: err(f"pathologie {p['id']} : médicament inconnu « {d} » (utiliser la DCI exacte)")

# --- symptômes (dans meds.json) ---
for y in meds.get("symptomes", []):
    for k in ("id", "nom", "pictogramme", "couleur", "resume", "alarme", "questions", "examens", "orientations", "conduite"):
        if k not in y: err(f"symptôme {y.get('id')} : champ {k} manquant")
    for o in y.get("orientations", []):
        if o.get("pathologie") not in pid: err(f"symptôme {y.get('id')} : pathologie {o.get('pathologie')} inexistante")

# --- actualites.json ---
a = json.load(open("actualites.json", encoding="utf-8"))
if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.get("dateIsoActualites", "")): err("actualites.json : dateIsoActualites invalide")
for i, x in enumerate(a.get("actualites", [])):
    for k in ("etiquette", "titre", "lieu", "chiffre", "texte", "details", "couleur", "icone", "pathologie", "source", "pictogramme"):
        if k not in x: err(f"actualité {i} : champ {k} manquant")
    if x.get("pathologie") not in pid: err(f"actualité {i} : pathologie {x.get('pathologie')} inexistante")
    if x.get("pictogramme") not in PICTOS: err(f"actualité {i} : pictogramme invalide")
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", x.get("couleur", "")): err(f"actualité {i} : couleur invalide")
if not a.get("actualites"): err("actualites.json : liste vide")

# --- cas_cliniques.json ---
c = json.load(open("cas_cliniques.json", encoding="utf-8"))
if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", c.get("dateIsoCas", "")): err("cas_cliniques.json : dateIsoCas invalide")
ids = [x.get("id") for x in c.get("casCliniques", [])]
if len(ids) != len(set(ids)): err("cas_cliniques.json : identifiants de cas en double")
for x in c.get("casCliniques", []):
    for k in ("id", "titre", "theme", "niveau", "presentation", "etapes", "conclusion", "pathologie", "source"):
        if k not in x: err(f"cas {x.get('id')} : champ {k} manquant")
    if x.get("theme") not in THEMES: err(f"cas {x.get('id')} : thème invalide")
    if x.get("pathologie") not in pid: err(f"cas {x.get('id')} : pathologie inexistante")
    if not x.get("etapes"): err(f"cas {x.get('id')} : aucune étape")
    for e in x.get("etapes", []):
        if not (isinstance(e.get("bonne"), int) and 0 <= e["bonne"] < len(e.get("options", [])) and len(e["options"]) >= 3):
            err(f"cas {x.get('id')} : réponse ou options invalides")
        for k in ("info", "question", "explication"):
            if k not in e: err(f"cas {x.get('id')} : champ d'étape {k} manquant")
if not c.get("casCliniques"): err("cas_cliniques.json : liste vide")

# --- corrections.json (journal des mises à jour des fiches) ---
try:
    corr = json.load(open("corrections.json", encoding="utf-8"))
    for i, k in enumerate(corr):
        for cle in ("date", "cible", "id", "champ", "valeur", "source", "motif"):
            if cle not in k: err(f"correction {i} : clé {cle} manquante")
        cible = meds["pathologies"] if k.get("cible") == "pathologie" else meds["medicaments"]
        obj = next((o for o in cible if o["id"] == k.get("id")), None)
        if obj is None: err(f"correction {i} : fiche {k.get('cible')} {k.get('id')} inexistante")
        elif obj.get(k["champ"]) != k["valeur"]: err(f"correction {i} : non appliquée dans meds.json")
except FileNotFoundError:
    pass

if erreurs:
    print("ÉCHEC :"); [print(" -", e) for e in erreurs]; sys.exit(1)
print(f"OK : meds.json v{meds['version']} ({len(mid)} médicaments, {len(pid)} pathologies), "
      f"{len(a['actualites'])} actualités du {a['dateIsoActualites']}, {len(ids)} cas cliniques du {c['dateIsoCas']}")

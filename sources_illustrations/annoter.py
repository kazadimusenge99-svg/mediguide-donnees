# Annotation des vraies images (flèches et étiquettes en français) — MédiGuide.
# A[nom] = {"l": [(tx, ty, [(ax, ay), ...], texte)], "m": [(x0, y0, x1, y1, texte)]}
#   l : étiquette dont le coin haut-gauche est en (tx, ty) (fractions de l'image), avec flèches vers les points (ax, ay)
#   m : zone à masquer (légende anglaise d'origine) remplacée par le texte français
import os, sys, math, json
from PIL import Image, ImageDraw, ImageFont

A = {
 "ct-covid-r": {"l": [(0.02, 0.03, [(0.33, 0.52), (0.75, 0.55)], "Verre dépoli périphérique, bilatéral")]},
 "ct-cysticercose-r": {"l": [(0.42, 0.47, [(0.30, 0.62), (0.70, 0.82)], "Calcifications (points blancs)"), (0.30, 0.02, [(0.78, 0.15)], "Kystes (points sombres)")]},
 "ct-ep-r": {"l": [(0.02, 0.05, [(0.40, 0.33)], "Ventricule droit dilaté"), (0.62, 0.62, [(0.68, 0.40)], "Ventricule gauche comprimé")]},
 "ct-extradural-r": {"l": [(0.05, 0.03, [(0.86, 0.50)], "Hématome extradural : lentille biconvexe hyperdense")]},
 "ct-hemorragie-r": {"l": [(0.03, 0.02, [(0.50, 0.35)], "Sang dans les ventricules (blanc)"), (0.35, 0.86, [(0.70, 0.62)], "Hématome hyperdense")]},
 "ct-sousdural-r": {"l": [(0.03, 0.86, [(0.86, 0.48)], "Hématome sous-dural : croissant le long de l'os")]},
 "ecg-bav1-r": {"l": [(0.25, 0.20, [(0.27, 0.42)], "PR allongé > 0,20 s (BAV 1er degré)")]},
 "ecg-bav3-r": {"l": [(0.25, 0.02, [(0.17, 0.27)], "Ondes P régulières (flèches pointillées)"), (0.25, 0.86, [(0.50, 0.72)], "QRS lents, sans lien avec les P (dissociation)")]},
 "ecg-ep-r": {"l": [(0.12, 0.19, [(0.09, 0.13)], "S1 (DI)"), (0.12, 0.72, [(0.10, 0.66)], "Q3 et T3 négative (DIII)"), (0.55, 0.88, [], "Tachycardie sinusale")]},
 "ecg-fa-r": {"l": [(0.30, 0.66, [(0.52, 0.88), (0.62, 0.88)], "Intervalles R-R irréguliers"), (0.02, 0.66, [(0.15, 0.92)], "Pas d'onde P")]},
 "ecg-fa-r2": {"l": [(0.30, 0.35, [(0.27, 0.12), (0.47, 0.12)], "R-R irréguliers"), (0.30, 0.55, [(0.70, 0.80)], "Pas d'onde P, ligne de base trémulante")]},
 "ecg-flutter-r": {"l": [(0.30, 0.52, [(0.10, 0.43), (0.12, 0.66)], "Ondes F « en dents de scie » (DII, DIII, aVF)")]},
 "ecg-fv-r": {"l": [(0.30, 0.15, [(0.45, 0.68)], "Ondulations anarchiques, aucun QRS : choc électrique")]},
 "ecg-hvg-r": {"l": [(0.35, 0.03, [(0.66, 0.30)], "S profondes (V1–V3)"), (0.30, 0.50, [(0.72, 0.62)], "R amples (V5–V6)"), (0.25, 0.88, [(0.77, 0.94)], "T négatives (surcharge)")]},
 "ecg-hyperk-r": {"l": [(0.05, 0.38, [(0.69, 0.33), (0.62, 0.46)], "Ondes T amples, pointues, symétriques (V2–V4)")]},
 "ecg-pericardite-r": {"l": [(0.28, 0.43, [(0.15, 0.33), (0.83, 0.31)], "Sus-décalage du ST diffus, concave vers le haut")]},
 "ecg-qt-r": {"l": [(0.03, 0.05, [(0.73, 0.70)], "Fin de l'onde T retardée")]},
 "ecg-stemi-r": {"l": [(0.25, 0.25, [(0.83, 0.16), (0.60, 0.42)], "Sus-décalage du ST (précordiales)")]},
 "ecg-stemi-r2": {"l": [(0.58, 0.45, [(0.53, 0.36), (0.53, 0.71)], "Sus-décalage du ST (V2–V3)")]},
 "ecg-tdp-r": {"l": [(0.42, 0.86, [(0.30, 0.40), (0.55, 0.62)], "QRS larges dont l'amplitude « tourne » autour de la ligne de base")]},
 "ecg-tv-r": {"l": [(0.05, 0.45, [(0.62, 0.30), (0.62, 0.70)], "QRS larges (> 0,12 s), réguliers, rapides")]},
 "echo-abces-foie-r": {"m": [(0.12, 0.28, 0.34, 0.46, "Abcès du foie (segment VI), hétérogène"), (0.66, 0.21, 0.87, 0.34, "Veine porte"), (0.54, 0.92, 0.72, 0.99, "Diaphragme")]},
 "echo-appendicite-r": {"l": [(0.05, 0.62, [(0.45, 0.43)], "Appendice épaissi (> 6 mm), non compressible")]},
 "echo-ascite-r": {"m": [(0.55, 0.16, 0.70, 0.23, "Ascite")], "l": [(0.03, 0.88, [(0.42, 0.62)], "Organe entouré de liquide noir (anéchogène)")]},
 "echo-cirrhose-r": {"l": [(0.02, 0.86, [(0.45, 0.42)], "Parenchyme hétérogène, nodulaire"), (0.02, 0.03, [(0.25, 0.42)], "Surface irrégulière")]},
 "echo-geu-r": {"l": [(0.42, 0.86, [(0.58, 0.62)], "Masse latéro-utérine (grossesse extra-utérine)")]},
 "echo-grossesse-r": {"l": [(0.02, 0.86, [(0.28, 0.55)], "Sac gestationnel intra-utérin"), (0.60, 0.30, [(0.55, 0.52)], "Vessie")]},
 "echo-hydronephrose-r": {"m": [(0.35, 0.28, 0.61, 0.35, "Calice dilaté"), (0.36, 0.79, 0.67, 0.88, "Rein droit, coupe longitudinale")]},
 "echo-invagination-r": {"l": [(0.03, 0.78, [(0.48, 0.40)], "Image en cocarde (anses invaginées)")]},
 "echo-lithiase-r": {"l": [(0.03, 0.15, [(0.43, 0.45)], "Calcul hyperéchogène"), (0.55, 0.85, [(0.48, 0.80)], "Cône d'ombre"), (0.55, 0.03, [(0.55, 0.30)], "Vésicule (liquide)")]},
 "echo-mole-r": {"l": [(0.03, 0.03, [(0.40, 0.55), (0.60, 0.72)], "Multiples vésicules : aspect « en tempête de neige »")]},
 "echo-pericarde-r": {"l": [(0.60, 0.12, [(0.48, 0.17)], "Épanchement (en avant)"), (0.45, 0.90, [(0.52, 0.83)], "Épanchement péricardique (en arrière)")]},
 "echo-tvp-r": {"l": [(0.25, 0.03, [(0.45, 0.25)], "Artère fémorale"), (0.10, 0.86, [(0.45, 0.65)], "Veine fémorale : thrombus = zone sans couleur")]},
 "echo-vegetation-r": {"l": [(0.30, 0.86, [(0.62, 0.40)], "Végétation sur la valve")]},
 "fo-cmv": {"l": [(0.55, 0.15, [(0.55, 0.45)], "Nécrose blanche et hémorragies (« pizza »)"), (0.55, 0.80, [(0.48, 0.86)], "Papille")]},
 "fo-hta": {"l": [(0.05, 0.10, [(0.70, 0.30)], "Artères rétrécies, croisements artério-veineux"), (0.70, 0.75, [(0.62, 0.50)], "Papille")]},
 "fo-papille": {"l": [(0.03, 0.03, [(0.48, 0.45)], "Papille œdémateuse, bords flous"), (0.40, 0.80, [(0.62, 0.52)], "Hémorragies en flammèches")]},
 "fo-retino": {"l": [(0.55, 0.05, [(0.62, 0.22)], "Exsudats durs (points jaunes)"), (0.05, 0.62, [(0.25, 0.42)], "Papille"), (0.60, 0.70, [(0.62, 0.52)], "Macula")]},
 "hsg-normal-r": {"l": [(0.28, 0.05, [(0.42, 0.28)], "Cavité utérine"), (0.30, 0.86, [(0.16, 0.32), (0.70, 0.56)], "Trompes perméables (le produit passe)")]},
 "irm-toxo-r": {"l": [(0.03, 0.88, [(0.36, 0.72)], "Lésion avec œdème (toxoplasmose)")]},
 "mi-amibe": {"m": [(0.38, 0.22, 0.99, 0.31, "Globules rouges ingérés"), (0.40, 0.38, 0.97, 0.70, "Noyau avec caryosome central"), (0.43, 0.79, 0.75, 0.87, "Pseudopode")]},
 "mi-ankylo": {"l": [(0.02, 0.03, [(0.40, 0.55)], "Œuf ovale à coque fine, embryon segmenté")]},
 "mi-ascaris": {"l": [(0.03, 0.10, [(0.62, 0.58)], "Œuf d'ascaris : coque épaisse mamelonnée")]},
 "mi-baar": {"l": [(0.03, 0.03, [(0.45, 0.73), (0.72, 0.53)], "Bacilles rouges (BAAR)")]},
 "mi-burkitt": {"l": [(0.02, 0.03, [(0.37, 0.30)], "Cytoplasme bleu foncé avec vacuoles"), (0.02, 0.88, [(0.55, 0.80)], "Gros noyau, chromatine fine")]},
 "mi-candida": {"l": [(0.03, 0.03, [(0.40, 0.35)], "Pseudo-filaments"), (0.40, 0.86, [(0.65, 0.66)], "Levures")]},
 "mi-clue": {"l": [(0.03, 0.03, [(0.30, 0.50)], "Clue cell : cellule couverte de bactéries, bords flous")]},
 "mi-crypto": {"l": [(0.35, 0.86, [(0.47, 0.53), (0.63, 0.33)], "Levures entourées d'une capsule (halo clair)")]},
 "mi-drepano": {"l": [(0.03, 0.03, [(0.46, 0.47), (0.75, 0.32)], "Drépanocytes (globules en faucille)"), (0.55, 0.86, [(0.60, 0.62)], "Polynucléaire")]},
 "mi-ferriprive": {"l": [(0.03, 0.86, [(0.30, 0.55)], "Globules rouges petits et pâles"), (0.50, 0.03, [(0.57, 0.40)], "Lymphocyte (taille de référence)")]},
 "mi-giardia": {"l": [(0.03, 0.03, [(0.38, 0.25)], "Deux noyaux"), (0.60, 0.88, [(0.88, 0.30)], "Flagelles")]},
 "mi-gono": {"l": [(0.40, 0.55, [(0.32, 0.40)], "Diplocoques Gram négatif dans un polynucléaire")]},
 "mi-lal": {"l": [(0.03, 0.86, [(0.53, 0.62)], "Blastes : grandes cellules, peu de cytoplasme")]},
 "mi-lcr": {"l": [(0.55, 0.40, [(0.35, 0.38)], "Diplocoques Gram négatif"), (0.55, 0.88, [(0.20, 0.55)], "Polynucléaires")]},
 "mi-leish": {"l": [(0.03, 0.03, [(0.58, 0.20), (0.48, 0.80)], "Corps de Leishman (amastigotes)"), (0.03, 0.86, [(0.42, 0.42)], "Macrophage")]},
 "mi-lmc": {"l": [(0.25, 0.88, [(0.62, 0.60), (0.38, 0.75)], "Myélémie : cellules granuleuses à tous les stades")]},
 "mi-loa": {"l": [(0.03, 0.85, [(0.55, 0.55)], "Microfilaire de Loa loa (gainée)")]},
 "mi-palu-frottis": {"l": [(0.02, 0.86, [(0.36, 0.33), (0.65, 0.25)], "Anneaux de P. falciparum dans les globules rouges")]},
 "mi-palu-ge": {"l": [(0.55, 0.85, [(0.45, 0.55)], "Trophozoïtes (petits anneaux)"), (0.40, 0.03, [(0.30, 0.20)], "Leucocyte")]},
 "mi-pneumocoque": {"l": [(0.25, 0.88, [(0.51, 0.45)], "Diplocoques Gram positif lancéolés")]},
 "mi-reed": {"m": [(0.00, 0.39, 0.27, 0.60, "Lymphocyte normal"), (0.70, 0.40, 1.00, 0.56, "Cellule de Reed-Sternberg")]},
 "mi-schisto-h": {"l": [(0.03, 0.80, [(0.16, 0.56)], "Éperon terminal (S. haematobium)")]},
 "mi-schisto-m": {"l": [(0.30, 0.85, [(0.24, 0.70)], "Éperon latéral (S. mansoni)")]},
 "mi-trichomonas": {"l": [(0.45, 0.03, [(0.27, 0.27)], "Trichomonas (mobile à l'état frais)"), (0.55, 0.86, [(0.55, 0.65)], "Cellules épithéliales")]},
 "mi-trypano": {"l": [(0.35, 0.86, [(0.15, 0.35), (0.40, 0.25)], "Trypanosomes (flagelle, membrane ondulante)")]},
 "mi-vivax": {"l": [(0.02, 0.86, [(0.55, 0.48)], "Schizonte de P. vivax (nombreux noyaux)")]},
 "photo-burkitt": {"l": [(0.02, 0.86, [(0.25, 0.55)], "Tumeur de la mâchoire")]},
 "photo-retinoblastome": {"l": [(0.55, 0.75, [(0.72, 0.45)], "Leucocorie (reflet blanc)"), (0.02, 0.75, [(0.30, 0.45)], "Reflet normal")]},
 "piece-wilms-r": {"l": [(0.35, 0.03, [(0.30, 0.40)], "Tumeur blanchâtre (encéphaloïde)"), (0.40, 0.86, [(0.25, 0.85)], "Rein résiduel")]},
 "rx-abces-r": {"m": [(0.21, 0.26, 0.31, 0.32, "Air"), (0.16, 0.41, 0.28, 0.47, "Liquide"), (0.36, 0.43, 0.56, 0.53, "Opacités alvéolaires"), (0.45, 0.55, 0.63, 0.64, "Opacités nodulaires"), (0.36, 0.76, 0.71, 0.85, "Bord droit du cœur effacé")],
               "l": [(0.55, 0.15, [(0.20, 0.38)], "Niveau hydro-aérique (abcès)")]},
 "rx-emphyseme-r": {"l": [(0.30, 0.03, [(0.30, 0.35), (0.78, 0.70)], "Hyperclarté, vaisseaux raréfiés, bulles"), (0.55, 0.86, [(0.30, 0.88)], "Coupoles aplaties")]},
 "rx-epanchement-r": {"l": [(0.03, 0.86, [(0.72, 0.68)], "Opacité de la base gauche (épanchement)")]},
 "rx-fracture-r": {"crop": (0.0, 0.30, 1.0, 0.80), "l": [(0.55, 0.30, [(0.38, 0.48)], "Fracture du tibia"), (0.55, 0.88, [(0.60, 0.78)], "Fracture de la fibula")]},
 "rx-miliaire-r": {"l": [(0.30, 0.03, [(0.20, 0.45), (0.85, 0.55)], "Micronodules diffus « en grains de mil »")]},
 "rx-mmh-r": {"l": [(0.25, 0.88, [(0.30, 0.50), (0.72, 0.55)], "Opacités réticulo-granitées bilatérales")]},
 "rx-myelome-r": {"m": [(0.00, 0.62, 0.46, 0.98, "Lacunes lytiques")], "l": [(0.45, 0.03, [(0.33, 0.25), (0.20, 0.45)], "Lacunes « à l'emporte-pièce »")]},
 "rx-oap-r": {"m": [(0.09, 0.35, 0.31, 0.48, "Épanchement pleural"), (0.37, 0.38, 0.69, 0.51, "Redistribution vers les sommets"), (0.40, 0.51, 0.72, 0.59, "Lignes de Kerley B"), (0.23, 0.76, 0.91, 0.85, "Rapport cardio-thoracique augmenté")]},
 "rx-oap-r2": {"l": [(0.30, 0.88, [(0.12, 0.75), (0.90, 0.72)], "Lignes de Kerley B (bases)"), (0.55, 0.03, [(0.70, 0.62)], "Cœur augmenté de volume")]},
 "rx-occlusion-r": {"l": [(0.30, 0.03, [(0.27, 0.58), (0.55, 0.60)], "Niveaux hydro-aériques")]},
 "rx-osteomyelite-r": {"crop": (0.0, 0.15, 1.0, 0.65), "l": [(0.02, 0.03, [(0.53, 0.56)], "Lacune cernée d'os dense (abcès de Brodie)")]},
 "rx-pneumatocele-r": {"l": [(0.30, 0.85, [(0.34, 0.38), (0.88, 0.46)], "Pneumatocèle (cavité aérique ronde)")]},
 "rx-pneumocystose-r": {"l": [(0.25, 0.88, [(0.20, 0.50), (0.82, 0.55)], "Infiltrats interstitiels bilatéraux"), (0.70, 0.03, [(0.58, 0.64)], "Kyste")]},
 "rx-pneumonie-r": {"l": [(0.03, 0.86, [(0.22, 0.58)], "Opacité alvéolaire du lobe moyen"), (0.50, 0.30, [(0.32, 0.66)], "Bord droit du cœur effacé")]},
 "rx-pneumoperitoine-r": {"m": [(0.07, 0.92, 0.31, 0.99, "Air sous la coupole"), (0.45, 0.29, 0.63, 0.34, "Pneumopéritoine"), (0.88, 0.28, 0.99, 0.33, "Estomac")]},
 "rx-pneumothorax-r": {"m": [(0.30, 0.02, 0.76, 0.11, "Pneumothorax gauche"), (0.65, 0.28, 0.99, 0.35, "Pas de trame pulmonaire"), (0.09, 0.42, 0.39, 0.53, "Médiastin dévié à droite"), (0.80, 0.62, 0.99, 0.73, "Poumon rétracté")]},
 "rx-pr-r": {"l": [(0.03, 0.03, [(0.50, 0.70)], "Carpe détruit, ankylosé"), (0.45, 0.86, [(0.68, 0.60)], "Érosions")]},
 "rx-pr-r2": {"l": [(0.03, 0.03, [(0.60, 0.62)], "Érosions, pincement articulaire")]},
 "rx-tb-r": {"l": [(0.55, 0.88, [(0.70, 0.28)], "Lésions fibro-cavitaires du sommet")]},
 "rx-tb-r2": {"l": [(0.25, 0.88, [(0.25, 0.30), (0.72, 0.30)], "Infiltrats et nodules, surtout aux sommets")]},
}

POLICE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
JAUNE = (255, 213, 79)

def police(t):
    return ImageFont.truetype(POLICE, t)

def boite_texte(d, x, y, texte, f, W, H, fond=(0, 0, 0, 190), coul=JAUNE):
    bb = d.textbbox((0, 0), texte, font=f)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    pad = max(4, f.size // 4)
    x = min(max(2, x), W - w - 2 * pad - 2)
    y = min(max(2, y), H - h - 2 * pad - 2)
    d.rectangle([x, y, x + w + 2 * pad, y + h + 2 * pad], fill=fond)
    d.text((x + pad - bb[0], y + pad - bb[1]), texte, font=f, fill=coul)
    return (x, y, x + w + 2 * pad, y + h + 2 * pad)

def fleche(d, p0, p1, ep):
    (x0, y0), (x1, y1) = p0, p1
    ang = math.atan2(y1 - y0, x1 - x0)
    L = ep * 4.5
    tete = [(x1, y1), (x1 - L * math.cos(ang - 0.45), y1 - L * math.sin(ang - 0.45)), (x1 - L * math.cos(ang + 0.45), y1 - L * math.sin(ang + 0.45))]
    xb, yb = x1 - L * 0.8 * math.cos(ang), y1 - L * 0.8 * math.sin(ang)
    d.line([(x0, y0), (xb, yb)], fill=(0, 0, 0, 255), width=ep + 4)
    d.polygon(tete, fill=(0, 0, 0, 255))
    d.line([(x0, y0), (xb, yb)], fill=JAUNE + (255,), width=ep)
    t2 = [(x1 - 1.5 * math.cos(ang), y1 - 1.5 * math.sin(ang))] + tete[1:]
    d.polygon(t2, fill=JAUNE + (255,))

def annoter(src, dst, spec, titre):
    im = Image.open(src).convert("RGB")
    if "crop" in spec:
        c = spec["crop"]; im = im.crop((int(c[0] * im.width), int(c[1] * im.height), int(c[2] * im.width), int(c[3] * im.height)))
    if im.width < 700:
        im = im.resize((700, round(im.height * 700 / im.width)), Image.LANCZOS)
    W, H = im.size
    t = max(17, W // 38)
    f = police(t)
    calque = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(calque)
    for (x0, y0, x1, y1, texte) in spec.get("m", []):
        X0, Y0, X1, Y1 = x0 * W, y0 * H, x1 * W, y1 * H
        d.rectangle([X0, Y0, X1, Y1], fill=(0, 0, 0, 255))
        mots = texte.split()
        choix = None
        for ft in range(t, 10, -1):
            fm = police(ft)
            for n in (1, 2, 3):
                if n > len(mots): break
                k = -(-len(mots) // n)
                lignes = [" ".join(mots[i:i + k]) for i in range(0, len(mots), k)]
                larg = max(d.textbbox((0, 0), l, font=fm)[2] for l in lignes)
                haut = n * (ft + 3)
                if larg <= X1 - X0 - 6 and haut <= Y1 - Y0 - 2:
                    choix = (fm, lignes, ft); break
            if choix: break
        if not choix:
            fm = police(max(12, int(t * 0.75))); lignes = [texte]
            larg = d.textbbox((0, 0), texte, font=fm)[2]
            d.rectangle([X0, Y0, min(W, X0 + larg + 10), Y1], fill=(0, 0, 0, 255)); choix = (fm, lignes, fm.size)
        fm, lignes, ft = choix
        y = (Y0 + Y1) / 2 - len(lignes) * (ft + 3) / 2
        for l in lignes:
            d.text((X0 + 4, y), l, font=fm, fill=JAUNE); y += ft + 3
    boites = []
    for (tx, ty, pointes, texte) in spec.get("l", []):
        bb = d.textbbox((0, 0), texte, font=f)
        boites.append((tx * W, ty * H, pointes, texte))
    ep = max(3, W // 220)
    for (x, y, pointes, texte) in boites:
        bb = d.textbbox((0, 0), texte, font=f); pad = max(4, t // 4)
        w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
        x = min(max(2, x), W - w - 2); y = min(max(2, y), H - h - 2)
        for (ax, ay) in pointes:
            AX, AY = ax * W, ay * H
            sx = min(max(AX, x), x + w); sy = y + h if AY > y + h else (y if AY < y else min(max(AY, y), y + h))
            if abs(AX - sx) + abs(AY - sy) > 12:
                fleche(d, (sx, sy), (AX, AY), ep)
    for (x, y, pointes, texte) in boites:
        boite_texte(d, x, y, texte, f, W, H)
    im = Image.alpha_composite(im.convert("RGBA"), calque).convert("RGB")
    # bandeau de titre en haut
    ft = police(max(15, W // 45))
    bb = ImageDraw.Draw(im).textbbox((0, 0), titre, font=ft)
    lignes = [titre]
    if bb[2] - bb[0] > W - 20:  # couper en deux lignes
        mots = titre.split(); m = len(mots) // 2
        lignes = [" ".join(mots[:m]), " ".join(mots[m:])]
    hl = bb[3] - bb[1] + 8
    bande = len(lignes) * hl + 12
    out = Image.new("RGB", (W, H + bande), (20, 20, 20))
    out.paste(im, (0, bande))
    dd = ImageDraw.Draw(out)
    for i, l in enumerate(lignes):
        dd.text((10, 6 + i * hl - bb[1]), l, font=ft, fill=(255, 255, 255))
    if out.width > 900:
        out = out.resize((900, round(out.height * 900 / out.width)), Image.LANCZOS)
    out.save(dst, "WEBP", quality=82, method=6)

if __name__ == "__main__":
    src_dir, dst_dir, legendes = sys.argv[1], sys.argv[2], json.load(open(sys.argv[3], encoding="utf-8"))
    os.makedirs(dst_dir, exist_ok=True)
    noms = [n[:-5] for n in sorted(os.listdir(src_dir)) if n.endswith(".webp")]
    manque = [n for n in noms if n not in A and n not in ("hsg-r",)]
    print("sans annotation :", manque)
    for n in noms:
        annoter(os.path.join(src_dir, n + ".webp"), os.path.join(dst_dir, n + ".webp"), A.get(n, {}), legendes.get(n, n))
    print(len(noms), "images annotées")

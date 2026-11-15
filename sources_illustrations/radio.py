# Radiographies, scanners et échographies schématiques — illustrations originales MédiGuide.
import math, random

W, H = 800, 520

DEFS = """
<filter id="b2"><feGaussianBlur stdDeviation="2"/></filter>
<filter id="b4"><feGaussianBlur stdDeviation="4"/></filter>
<filter id="b8"><feGaussianBlur stdDeviation="8"/></filter>
<filter id="b14"><feGaussianBlur stdDeviation="14"/></filter>
<filter id="b25"><feGaussianBlur stdDeviation="25"/></filter>
<filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3"/>
  <feColorMatrix type="matrix" values="0 0 0 0 0.5  0 0 0 0 0.5  0 0 0 0 0.5  0 0 0 1.2 -0.3"/>
</filter>
<filter id="speckle" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.22 0.5" numOctaves="3" seed="8"/>
  <feColorMatrix type="matrix" values="0.33 0.33 0.33 0 -0.05  0.33 0.33 0.33 0 -0.05  0.33 0.33 0.33 0 -0.05  0 0 0 0 1"/>
  <feComponentTransfer><feFuncR type="gamma" exponent="1.6" amplitude="1.5"/><feFuncG type="gamma" exponent="1.6" amplitude="1.5"/><feFuncB type="gamma" exponent="1.6" amplitude="1.5"/></feComponentTransfer>
</filter>
"""

JAUNE = "#FFD54F"

def svg(corps, titre, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<defs>{DEFS}{defs}</defs><rect width="{W}" height="{H}" fill="#000"/>{corps}'
            f'<rect x="0" y="{H-34}" width="{W}" height="34" fill="#111"/>'
            f'<text x="{W/2}" y="{H-11}" text-anchor="middle" font-family="Arial" font-size="16" fill="#eee">{titre}</text></svg>')

def fleche(x1, y1, x2, y2, texte, anchor="start", c=JAUNE):
    ang = math.atan2(y2 - y1, x2 - x1)
    a1 = (x2 - 12 * math.cos(ang - 0.4), y2 - 12 * math.sin(ang - 0.4))
    a2 = (x2 - 12 * math.cos(ang + 0.4), y2 - 12 * math.sin(ang + 0.4))
    dy = -8 if y1 > 40 else 20
    larg = len(texte) * 8.6
    if anchor == "start" and x1 + larg > W - 8: anchor = "end"
    if anchor == "end" and x1 - larg < 8: anchor = "start"
    if anchor == "middle":
        x1t = min(max(x1, larg / 2 + 8), W - larg / 2 - 8)
    else:
        x1t = x1
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="2.5"/>'
            f'<polygon points="{x2},{y2} {a1[0]:.1f},{a1[1]:.1f} {a2[0]:.1f},{a2[1]:.1f}" fill="{c}"/>'
            f'<text x="{x1t}" y="{y1 + dy}" text-anchor="{anchor}" font-family="Arial" font-size="16" font-weight="bold" fill="{c}" '
            f'stroke="#000" stroke-width="3" paint-order="stroke">{texte}</text>')

def grain(op=0.18):
    return f'<rect width="{W}" height="{H-34}" filter="url(#grain)" opacity="{op}"/>'

# ------------------------------------------------------------------ thorax de face
POUMON_D = "M352,82 C300,88 250,150 232,240 C220,310 222,380 236,428 C280,410 330,404 368,418 L372,130 Z"   # poumon droit du patient (à gauche de l'image)

import re as _re
def miroir(d):
    return _re.sub(r"(-?[\d.]+),(-?[\d.]+)", lambda m: f"{800-float(m.group(1)):g},{m.group(2)}", d)

def poumon(dome=0, larg=1.0, cote=1):
    # dome : abaissement des coupoles (distension) ; larg : facteur de largeur ; cote : 1 droit (image gauche), -1 gauche
    cx = 372 if cote == 1 else 428
    d = POUMON_D if cote == 1 else miroir(POUMON_D)
    return f'<path d="{d}" transform="translate({cx},0) scale({larg},1) translate({-cx},0) translate(0,{dome*0.2}) scale(1,{1+dome/430})"/>'

def thorax(coeur=1.0, dome=0, larg=1.0, lumiere=0.0, poumons_extra="", enfant=False, sans_poumon_droit=False):
    p = poumon(dome, larg)
    q = poumon(dome, larg, -1)
    defs = f'<clipPath id="pd">{p}</clipPath><clipPath id="pg">{q}</clipPath><clipPath id="pp">{p}{q}</clipPath>'
    fond_poumon = f"#{int(16+lumiere*10):02x}{int(16+lumiere*10):02x}{int(16+lumiere*10):02x}"
    s = '<ellipse cx="400" cy="300" rx="300" ry="300" fill="#6a6a6a" filter="url(#b25)"/>'
    s += '<rect x="0" y="420" width="800" height="70" fill="#777" filter="url(#b14)"/>'
    s += f'<g fill="{fond_poumon}" filter="url(#b4)">{"" if sans_poumon_droit else p}{q}</g>'
    # vaisseaux
    v = ""
    random.seed(2)
    for side in (1, -1):
        for k in range(7):
            a = math.radians(200 + k * 22) if side == 1 else math.radians(-20 - k * 22)
            x0, y0 = 400 - side * 40, 235
            x1, y1 = x0 + math.cos(a) * 120 * (1 if side == 1 else 1), y0 - math.sin(a) * 120
            v += f'<path d="M{x0},{y0} Q{(x0+x1)/2},{(y0+y1)/2+10} {x1:.0f},{y1:.0f}" stroke="#5a5a5a" stroke-width="5" fill="none" opacity="0.55"/>'
    s += f'<g clip-path="url(#pp)" filter="url(#b2)">{v}</g>'
    s += poumons_extra
    # médiastin et coeur
    s += '<path d="M372,70 L428,70 L436,250 L364,250 Z" fill="#b5b5b5" filter="url(#b8)"/>'
    s += '<rect x="392" y="40" width="16" height="200" fill="#333" filter="url(#b2)"/>'
    s += (f'<g transform="translate(410,330) scale({coeur}) translate(-410,-330)"><path d="M372,250 C340,300 348,385 380,415 C440,430 520,425 548,402 C565,360 520,290 440,250 Z" '
          'fill="#c4c4c4" filter="url(#b8)"/></g>')
    # côtes
    cotes = ""
    for side in (1, -1):
        for i in range(9):
            y = 105 + i * 34
            pts = f"M{400-side*25},{y} C{400-side*95},{y-34} {400-side*150},{y-12} {400-side*178},{y+28}"
            cotes += f'<path d="{pts}" stroke="#e8e8e8" stroke-width="10" fill="none" opacity="0.32"/>'
            ant = f"M{400-side*178},{y+28} C{400-side*150},{y+60} {400-side*90},{y+75} {400-side*45},{y+100}"
            cotes += f'<path d="{ant}" stroke="#e8e8e8" stroke-width="7" fill="none" opacity="0.14"/>'
    s += f'<g filter="url(#b2)">{cotes}</g>'
    s += '<path d="M392,98 C340,84 280,90 222,74" stroke="#ddd" stroke-width="13" fill="none" opacity="0.6" filter="url(#b2)"/>'
    s += '<path d="M408,98 C460,84 520,90 578,74" stroke="#ddd" stroke-width="13" fill="none" opacity="0.6" filter="url(#b2)"/>'
    s += '<rect x="386" y="40" width="28" height="430" fill="#ddd" opacity="0.18" filter="url(#b4)"/>'
    s += f'<text x="30" y="40" font-family="Arial" font-size="20" font-weight="bold" fill="#ddd">D</text>'
    return s, defs

def rx_pneumonie():
    extra = ('<g clip-path="url(#pd)"><path d="M232,300 C260,250 330,262 368,290 L368,420 C320,404 270,408 236,428 Z" fill="#cfcfcf" opacity="0.75" filter="url(#b14)"/>'
             '<g stroke="#2a2a2a" stroke-width="5" fill="none" opacity="0.8" filter="url(#b2)"><path d="M360,300 L320,340 L290,390"/><path d="M320,340 L280,330"/><path d="M340,320 L330,380"/></g></g>')
    s, d = thorax(poumons_extra=extra)
    s += fleche(150, 200, 270, 330, "Opacité alvéolaire systématisée", "middle")
    s += fleche(620, 470, 315, 360, "Bronchogramme aérien", "middle")
    return svg(s + grain(), "Pneumonie lobaire (base droite) — radiographie du thorax de face (schéma)", d)

def rx_tb_caverne():
    random.seed(5)
    nod = "".join(f'<circle cx="{random.uniform(250,370):.0f}" cy="{random.uniform(95,210):.0f}" r="{random.uniform(5,12):.0f}" fill="#bbb" opacity="0.7"/>' for _ in range(22))
    nod2 = "".join(f'<circle cx="{800-random.uniform(270,370):.0f}" cy="{random.uniform(100,190):.0f}" r="{random.uniform(4,9):.0f}" fill="#bbb" opacity="0.5"/>' for _ in range(10))
    extra = (f'<g clip-path="url(#pp)" filter="url(#b4)">{nod}{nod2}<path d="M250,110 C290,90 350,100 370,140 L370,220 C320,215 270,210 245,200 Z" fill="#999" opacity="0.5"/></g>'
             '<circle cx="300" cy="150" r="34" fill="#1a1a1a" stroke="#d8d8d8" stroke-width="10" filter="url(#b2)"/>')
    s, d = thorax(poumons_extra=extra)
    s += fleche(110, 80, 268, 140, "Caverne (paroi épaisse)", "middle")
    s += fleche(680, 90, 470, 150, "Infiltrats et nodules des sommets", "middle")
    return svg(s + grain(), "Tuberculose pulmonaire — radiographie du thorax (schéma)", d)

def rx_miliaire():
    random.seed(9)
    pts = "".join(f'<circle cx="{random.uniform(220,580):.0f}" cy="{random.uniform(80,430):.0f}" r="{random.uniform(1.8,3.2):.1f}" fill="#d0d0d0"/>' for _ in range(900))
    s, d = thorax(poumons_extra=f'<g clip-path="url(#pp)" filter="url(#b2)" opacity="0.85">{pts}</g>')
    s += fleche(110, 470, 280, 300, "Micronodules diffus « en grains de mil »", "start")
    return svg(s + grain(), "Miliaire tuberculeuse — radiographie du thorax (schéma)", d)

def rx_pneumothorax():
    s, d = thorax(sans_poumon_droit=True)
    # poumon droit rétracté + hyperclarté sans vaisseaux
    s = s.replace('<rect x="0" y="420"', '<path d="M352,82 C300,88 250,150 232,240 C220,310 222,380 236,428 C280,410 330,404 368,418 L372,130 Z" fill="#050505" filter="url(#b2)"/><rect x="0" y="420"', 1)
    s += '<path d="M372,170 C335,175 315,230 318,300 C320,350 340,385 368,395 Z" fill="#3a3a3a" stroke="#cfcfcf" stroke-width="2.5" filter="url(#b2)"/>'
    s += fleche(110, 120, 262, 250, "Hyperclarté sans trame vasculaire", "middle")
    s += fleche(110, 470, 318, 310, "Ligne pleurale (poumon rétracté)", "start")
    return svg(s + grain(), "Pneumothorax droit — radiographie du thorax (schéma)", d)

def rx_oap():
    extra = ('<g clip-path="url(#pp)">'
             '<ellipse cx="320" cy="270" rx="80" ry="110" fill="#bbb" opacity="0.6" filter="url(#b25)"/>'
             '<ellipse cx="480" cy="270" rx="80" ry="110" fill="#bbb" opacity="0.6" filter="url(#b25)"/>'
             '<g stroke="#ddd" stroke-width="2" opacity="0.8">' + "".join(f'<line x1="228" y1="{350+k*12}" x2="258" y2="{350+k*12}"/><line x1="542" y1="{350+k*12}" x2="572" y2="{350+k*12}"/>' for k in range(5)) + '</g>'
             '<path d="M226,400 C260,395 300,405 340,425 L240,430 Z" fill="#aaa" opacity="0.8" filter="url(#b4)"/>'
             '<path d="M574,400 C540,395 500,405 460,425 L560,430 Z" fill="#aaa" opacity="0.8" filter="url(#b4)"/></g>')
    s, d = thorax(coeur=1.35, poumons_extra=extra)
    s += fleche(400, 60, 340, 250, "Opacités péri-hilaires « en ailes de papillon »", "middle")
    s += fleche(110, 300, 240, 370, "Lignes de Kerley B", "middle")
    s += fleche(690, 160, 560, 360, "Cardiomégalie", "middle")
    s += fleche(690, 470, 545, 418, "Épanchement (comblement du cul-de-sac)", "end")
    return svg(s + grain(), "Œdème aigu du poumon, insuffisance cardiaque — radiographie du thorax (schéma)", d)

def rx_pneumocystose():
    extra = ('<g clip-path="url(#pp)" opacity="0.55" filter="url(#b14)"><ellipse cx="310" cy="260" rx="85" ry="150" fill="#a8a8a8"/><ellipse cx="490" cy="260" rx="85" ry="150" fill="#a8a8a8"/></g>'
             '<g clip-path="url(#pp)" opacity="0.35">' + "".join(f'<circle cx="{random.Random(k).uniform(230,570):.0f}" cy="{random.Random(k+999).uniform(100,420):.0f}" r="6" fill="#ccc" filter="url(#b4)"/>' for k in range(140)) + '</g>')
    s, d = thorax(poumons_extra=extra)
    s += fleche(150, 80, 280, 220, "Opacités interstitielles bilatérales", "middle")
    s += fleche(650, 470, 500, 300, "« Verre dépoli » symétrique, péri-hilaire", "middle")
    return svg(s + grain(), "Pneumocystose (aussi COVID-19 : verre dépoli plutôt périphérique) — schéma", d)

def rx_distension():
    s, d = thorax(coeur=0.8, dome=16, larg=1.08, lumiere=-0.6)
    s += fleche(130, 90, 270, 220, "Hyperclarté des champs pulmonaires", "middle")
    s += fleche(660, 470, 540, 432, "Coupoles aplaties et abaissées", "middle")
    s += fleche(660, 120, 440, 330, "Cœur étroit, vertical", "middle")
    return svg(s + grain(), "Distension thoracique (asthme, bronchiolite, BPCO) — schéma", d)

def rx_staph():
    bulles = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#0c0c0c" stroke="#cfcfcf" stroke-width="2.2"/>' for x, y, r in [(300, 180, 26), (330, 250, 18), (280, 240, 14)])
    extra = (f'<g clip-path="url(#pp)">{bulles}</g>'
             '<g clip-path="url(#pg)"><rect x="420" y="280" width="200" height="170" fill="#bdbdbd" filter="url(#b2)"/><rect x="420" y="170" width="200" height="110" fill="#050505"/>'
             '<line x1="430" y1="280" x2="590" y2="280" stroke="#eee" stroke-width="3"/></g>')
    s, d = thorax(poumons_extra=extra)
    s += fleche(110, 120, 278, 175, "Pneumatocèles (bulles à paroi fine)", "middle")
    s += fleche(690, 470, 565, 282, "Pyopneumothorax : niveau hydro-aérique", "end")
    return svg(s + grain(), "Staphylococcie pleuro-pulmonaire de l'enfant — schéma", d)

def rx_mmh():
    random.seed(12)
    gr = "".join(f'<circle cx="{random.uniform(225,575):.0f}" cy="{random.uniform(110,420):.0f}" r="{random.uniform(2,4):.1f}" fill="#e0e0e0"/>' for _ in range(700))
    extra = (f'<g clip-path="url(#pp)"><rect x="200" y="60" width="400" height="400" fill="#9a9a9a" opacity="0.6" filter="url(#b8)"/><g opacity="0.55" filter="url(#b2)">{gr}</g>'
             '<g stroke="#1b1b1b" stroke-width="5" fill="none" filter="url(#b2)"><path d="M380,240 L330,300 L290,370"/><path d="M420,240 L470,300 L510,370"/><path d="M330,300 L280,290"/><path d="M470,300 L520,290"/></g></g>')
    s, d = thorax(dome=-30, larg=0.9, poumons_extra=extra)
    s += fleche(120, 90, 280, 220, "Opacités réticulo-granitées (verre dépoli)", "middle")
    s += fleche(660, 470, 480, 320, "Bronchogramme aérien", "middle")
    return svg(s + grain(), "Maladie des membranes hyalines du prématuré — schéma", d)

# ------------------------------------------------------------------ abdomen
def abdomen_base():
    s = '<ellipse cx="400" cy="280" rx="330" ry="330" fill="#6e6e6e" filter="url(#b25)"/>'
    for i in range(6):
        y = 60 + i * 62
        s += f'<rect x="372" y="{y}" width="56" height="48" rx="8" fill="#c8c8c8" opacity="0.75" filter="url(#b2)"/>'
    s += '<path d="M250,440 C300,400 360,420 400,470 C440,420 500,400 550,440" stroke="#d0d0d0" stroke-width="22" fill="none" opacity="0.6" filter="url(#b4)"/>'
    s += '<path d="M130,40 C200,60 260,140 270,200 C230,230 170,230 120,200 Z" fill="#8a8a8a" filter="url(#b14)"/>'
    return s

def rx_occlusion():
    s = abdomen_base()
    anses = [(230, 170), (320, 130), (470, 140), (560, 190), (300, 260), (480, 270), (390, 340), (250, 350), (540, 360)]
    for x, y in anses:
        s += (f'<g><path d="M{x-48},{y} A48,34 0 0 1 {x+48},{y} Z" fill="#141414" filter="url(#b2)"/>'
              f'<rect x="{x-48}" y="{y}" width="96" height="26" rx="10" fill="#a8a8a8" filter="url(#b2)"/>'
              f'<line x1="{x-46}" y1="{y}" x2="{x+46}" y2="{y}" stroke="#ddd" stroke-width="2.5"/></g>')
    s += fleche(120, 470, 250, 352, "Niveaux hydro-aériques", "start")
    s += fleche(690, 70, 470, 132, "Anses grêles dilatées (plus larges que hautes)", "end")
    return svg(s + grain(), "Occlusion intestinale — abdomen sans préparation debout (schéma)")

def rx_pneumoperitoine():
    s, d = thorax(poumons_extra="")
    s += '<rect x="0" y="425" width="800" height="61" fill="#7a7a7a"/>'
    s += '<path d="M236,428 C280,404 330,398 370,418 C330,414 280,420 240,440 Z" fill="#050505" filter="url(#b2)"/>'
    s += fleche(110, 470, 290, 418, "Croissant gazeux sous la coupole droite", "start")
    return svg(s + grain(), "Pneumopéritoine (perforation d'organe creux) — radiographie debout (schéma)", d)

# ------------------------------------------------------------------ os
def os_long(fracture=False, osteo=False):
    s = '<rect x="250" y="20" width="300" height="470" rx="120" fill="#555" filter="url(#b25)"/>'
    s += '<path d="M360,30 L440,30 L432,460 L368,460 Z" fill="#cfcfcf" filter="url(#b2)"/>'
    s += '<path d="M378,40 L422,40 L416,450 L384,450 Z" fill="#9a9a9a" filter="url(#b4)"/>'
    s += '<path d="M470,60 L492,60 L486,450 L474,450 Z" fill="#bdbdbd" filter="url(#b2)"/>'
    if fracture:
        s = s.replace('<path d="M360,30 L440,30 L432,460 L368,460 Z" fill="#cfcfcf" filter="url(#b2)"/>',
                      '<path d="M360,30 L440,30 L437,235 L363,262 Z" fill="#cfcfcf" filter="url(#b2)"/><path d="M386,268 L460,241 L452,470 L392,470 Z" fill="#cfcfcf" filter="url(#b2)"/>')
        s = s.replace('<path d="M378,40 L422,40 L416,450 L384,450 Z" fill="#9a9a9a" filter="url(#b4)"/>', '')
        s += fleche(140, 140, 380, 255, "Trait de fracture oblique", "middle")
        s += fleche(660, 330, 452, 300, "Déplacement (chevauchement)", "middle")
    if osteo:
        s += '<path d="M352,280 C340,300 340,380 352,420" stroke="#d8d8d8" stroke-width="5" fill="none"/><path d="M344,285 C330,310 330,375 344,415" stroke="#c8c8c8" stroke-width="3" fill="none"/>'
        s += '<ellipse cx="400" cy="350" rx="22" ry="40" fill="#2a2a2a" filter="url(#b2)"/><ellipse cx="400" cy="350" rx="8" ry="16" fill="#eee"/>'
        s += fleche(140, 470, 344, 360, "Appositions périostées", "middle")
        s += fleche(660, 470, 408, 355, "Lacune avec séquestre", "middle")
    return s

def rx_fracture():
    return svg(os_long(fracture=True) + grain(), "Fracture diaphysaire — radiographie (schéma)")

def rx_osteomyelite():
    return svg(os_long(osteo=True) + grain(), "Ostéomyélite (après 10 à 14 jours) — radiographie (schéma)")

def rx_pott():
    s = '<rect x="200" y="10" width="400" height="480" fill="#555" filter="url(#b25)"/>'
    ys = [40, 115, 190, 270, 330, 400]
    for i, y in enumerate(ys):
        x = 330 + (30 if i in (3, 4) else 0) - (10 if i == 5 else 0)
        if i == 3:
            s += f'<path d="M{x},{y} L{x+130},{y-10} L{x+130},{y+40} L{x},{y+25} Z" fill="#bdbdbd" filter="url(#b2)"/>'
        elif i == 4:
            s += f'<path d="M{x},{y-5} L{x+130},{y+10} L{x+130},{y+55} L{x},{y+60} Z" fill="#bdbdbd" filter="url(#b2)"/>'
        else:
            s += f'<rect x="{x}" y="{y}" width="130" height="62" rx="8" fill="#cfcfcf" filter="url(#b2)"/>'
    s += '<ellipse cx="560" cy="320" rx="45" ry="80" fill="#8a8a8a" opacity="0.8" filter="url(#b8)"/>'
    s += fleche(130, 250, 365, 300, "Pincement discal et destruction des 2 vertèbres", "middle")
    s += fleche(690, 470, 570, 360, "Abcès paravertébral", "end")
    s += fleche(690, 120, 500, 300, "Cyphose angulaire (gibbosité)", "end")
    return svg(s + grain(), "Mal de Pott (spondylodiscite tuberculeuse) — rachis de profil (schéma)")

def rx_polyarthrite():
    s = '<path d="M210,500 C190,330 230,250 260,60 L540,60 C570,250 610,330 590,500 Z" fill="#555" filter="url(#b25)"/>'
    for k, x in enumerate([280, 350, 420, 490]):
        s += f'<rect x="{x}" y="300" width="40" height="160" rx="16" fill="#b8b8b8" filter="url(#b2)"/>'
        s += f'<rect x="{x+3}" y="190" width="34" height="95" rx="14" fill="#bdbdbd" filter="url(#b2)"/>'
        s += f'<rect x="{x+5}" y="110" width="30" height="66" rx="12" fill="#bdbdbd" filter="url(#b2)"/>'
        s += f'<rect x="{x+7}" y="60" width="26" height="40" rx="10" fill="#bdbdbd" filter="url(#b2)"/>'
        s += f'<circle cx="{x+4}" cy="305" r="7" fill="#3a3a3a"/><circle cx="{x+36}" cy="300" r="6" fill="#3a3a3a"/>'
    s += '<rect x="270" y="270" width="270" height="70" fill="#000" opacity="0.25" filter="url(#b8)"/>'
    s += fleche(130, 400, 282, 306, "Érosions des têtes métacarpiennes", "middle")
    s += fleche(680, 200, 532, 290, "Pincement articulaire", "middle")
    s += fleche(680, 470, 520, 320, "Déminéralisation en bande", "end")
    return svg(s + grain(), "Polyarthrite rhumatoïde — radiographie des mains (schéma)")

def rx_myelome():
    s = '<ellipse cx="400" cy="250" rx="300" ry="200" fill="#6a6a6a" filter="url(#b14)"/>'
    s += '<ellipse cx="400" cy="250" rx="280" ry="185" fill="none" stroke="#d6d6d6" stroke-width="18" filter="url(#b2)"/>'
    random.seed(7)
    trous = "".join(f'<circle cx="{random.uniform(170,630):.0f}" cy="{random.uniform(100,380):.0f}" r="{random.uniform(5,16):.0f}" fill="#1a1a1a"/>' for _ in range(28))
    s += f'<g clip-path="url(#crane)">{trous}</g>'
    defs = '<clipPath id="crane"><ellipse cx="400" cy="250" rx="290" ry="194"/></clipPath>'
    s += fleche(400, 470, 400, 260, "Lacunes « à l'emporte-pièce » sans liseré", "middle")
    return svg(s + grain(), "Myélome multiple — crâne de profil (schéma)", defs)

# ------------------------------------------------------------------ scanner cérébral
def crane(lesions="", hemis=True):
    s = '<ellipse cx="400" cy="245" rx="185" ry="225" fill="#e8e8e8"/>'
    s += '<ellipse cx="400" cy="245" rx="170" ry="210" fill="#7d7d7d"/>'
    s += '<ellipse cx="400" cy="245" rx="160" ry="200" fill="#888" filter="url(#b8)"/>'
    s += '<line x1="400" y1="40" x2="400" y2="450" stroke="#a5a5a5" stroke-width="3"/>'
    s += '<path d="M385,190 C360,200 355,250 375,290 L392,280 C380,250 382,215 392,200 Z" fill="#2c2c2c" filter="url(#b2)"/>'
    s += '<path d="M415,190 C440,200 445,250 425,290 L408,280 C420,250 418,215 408,200 Z" fill="#2c2c2c" filter="url(#b2)"/>'
    s += lesions
    s += '<text x="30" y="40" font-family="Arial" font-size="20" font-weight="bold" fill="#ddd">D</text>'
    return s

def ct_avc():
    l = '<ellipse cx="300" cy="230" rx="50" ry="36" fill="#f0f0f0" filter="url(#b2)"/><ellipse cx="300" cy="230" rx="70" ry="52" fill="none" stroke="#5a5a5a" stroke-width="10" filter="url(#b4)"/>'
    l += '<path d="M410,120 C470,110 545,160 555,240 C520,250 470,230 420,210 Z" fill="#555" opacity="0.9" filter="url(#b4)"/>'
    s = crane(l)
    s += fleche(110, 470, 290, 245, "AVC hémorragique : hématome hyperdense (blanc)", "start")
    s += fleche(690, 70, 505, 180, "AVC ischémique constitué : hypodensité (sombre)", "end")
    return svg(s + grain(0.1), "Scanner cérébral sans injection : AVC (schéma)")

def ct_hematome():
    l = '<path d="M248,120 C215,170 215,250 250,300 C275,250 278,170 248,120 Z" fill="#f2f2f2" filter="url(#b2)"/>'
    l += '<path d="M560,110 C615,170 620,300 560,380 C585,300 585,180 548,118 Z" fill="#e6e6e6" filter="url(#b2)"/>'
    s = crane(l)
    s += fleche(110, 470, 246, 260, "Hématome extradural : lentille biconvexe", "start")
    s += fleche(690, 470, 590, 300, "Hématome sous-dural : croissant", "end")
    return svg(s + grain(0.1), "Scanner cérébral : hématomes post-traumatiques (schéma)")

def ct_toxoplasmose():
    l = ""
    for x, y, r in [(330, 250, 26), (470, 170, 20), (450, 320, 15)]:
        l += f'<circle cx="{x}" cy="{y}" r="{r*2.2}" fill="#5f5f5f" filter="url(#b8)"/><circle cx="{x}" cy="{y}" r="{r}" fill="#6a6a6a" stroke="#f5f5f5" stroke-width="5"/>'
    s = crane(l)
    s += fleche(110, 470, 312, 268, "Prise de contraste en anneau (« cocarde »)", "start")
    s += fleche(690, 70, 495, 160, "Œdème périlésionnel (hypodense)", "end")
    return svg(s + grain(0.1), "Scanner avec injection : toxoplasmose cérébrale (VIH) (schéma)")

def ct_cysticercose():
    l = ""
    for x, y in [(310, 160), (480, 210), (350, 330), (460, 360), (280, 260)]:
        l += f'<circle cx="{x}" cy="{y}" r="15" fill="#3a3a3a" stroke="#9a9a9a" stroke-width="1.5"/><circle cx="{x+5}" cy="{y-3}" r="3.5" fill="#f2f2f2"/>'
    for x, y in [(520, 120), (290, 400), (520, 300)]:
        l += f'<circle cx="{x}" cy="{y}" r="5" fill="#ffffff"/>'
    s = crane(l)
    s += fleche(110, 470, 300, 270, "Kystes avec scolex (point blanc)", "start")
    s += fleche(690, 70, 522, 118, "Calcifications (stade séquellaire)", "end")
    return svg(s + grain(0.1), "Scanner cérébral : neurocysticercose (schéma)")

# ------------------------------------------------------------------ échographie
def secteur(organes, titre, annot):
    defs = '<clipPath id="sect"><path d="M400,20 L120,420 A440,440 0 0 0 680,420 Z"/></clipPath>'
    s = (f'<g clip-path="url(#sect)"><rect width="800" height="486" filter="url(#speckle)"/>'
         f'<rect width="800" height="486" fill="#000" opacity="0.35"/>{organes}</g>'
         '<path d="M400,20 L120,420 A440,440 0 0 0 680,420 Z" fill="none" stroke="#333" stroke-width="2"/>')
    return svg(s + annot, titre, defs)

def echo_abces_foie():
    o = ('<path d="M120,110 C300,80 600,120 700,200 L700,486 L100,486 Z" fill="#888" opacity="0.35"/>'
         '<ellipse cx="380" cy="270" rx="85" ry="72" fill="#0a0a0a" opacity="0.85" filter="url(#b4)"/>'
         '<ellipse cx="380" cy="270" rx="70" ry="58" fill="#333" opacity="0.6" filter="url(#b8)"/>')
    a = fleche(110, 470, 330, 300, "Lésion arrondie hypoéchogène (pus)", "start") + fleche(690, 90, 520, 180, "Parenchyme hépatique", "end")
    return secteur(o, "Abcès amibien du foie — échographie (schéma)", a)

def echo_ascite():
    o = ('<rect width="800" height="486" fill="#000" opacity="0.0"/>'
         '<path d="M120,140 L700,140 L700,486 L100,486 Z" fill="#000" opacity="0.92"/>'
         '<path d="M220,230 C260,200 300,220 340,205 C380,190 420,215 470,200 C520,190 560,215 600,230 C620,300 560,400 420,410 C300,410 220,330 220,230 Z" fill="#666" filter="url(#b2)"/>'
         '<path d="M230,330 C300,300 380,340 470,320" stroke="#aaa" stroke-width="2" fill="none"/>')
    a = fleche(110, 120, 300, 170, "Ascite (anéchogène, noire)", "start") + fleche(690, 470, 470, 210, "Foie à contours bosselés", "end")
    return secteur(o, "Cirrhose avec ascite — échographie (schéma)", a)

def echo_geu():
    o = ('<ellipse cx="330" cy="230" rx="110" ry="70" fill="#7a7a7a" opacity="0.5"/>'
         '<line x1="250" y1="230" x2="410" y2="230" stroke="#ddd" stroke-width="3"/>'
         '<circle cx="530" cy="270" r="34" fill="none" stroke="#e0e0e0" stroke-width="12"/><circle cx="530" cy="270" r="16" fill="#111"/>'
         '<path d="M220,360 C300,340 380,350 460,380 L440,420 L240,420 Z" fill="#000" opacity="0.9"/>')
    a = (fleche(110, 120, 290, 225, "Utérus vide (ligne de vacuité)", "start") + fleche(690, 120, 545, 250, "Masse latéro-utérine (anneau tubaire)", "end")
         + fleche(110, 470, 300, 380, "Épanchement du Douglas", "start"))
    return secteur(o, "Grossesse extra-utérine — échographie pelvienne (schéma)", a)

def echo_grossesse():
    o = ('<ellipse cx="400" cy="250" rx="190" ry="130" fill="#6a6a6a" opacity="0.4"/>'
         '<ellipse cx="400" cy="250" rx="120" ry="80" fill="#050505"/>'
         '<path d="M330,270 C330,220 380,205 420,215 C470,225 480,260 460,285 C430,300 360,300 330,270 Z" fill="#bdbdbd" filter="url(#b2)"/>'
         '<circle cx="345" cy="232" r="22" fill="#c8c8c8" filter="url(#b2)"/>'
         '<circle cx="480" cy="215" r="12" fill="none" stroke="#e0e0e0" stroke-width="3"/>')
    a = fleche(110, 120, 285, 220, "Sac gestationnel intra-utérin", "start") + fleche(690, 120, 492, 210, "Vésicule vitelline", "end") + fleche(690, 470, 430, 270, "Embryon (activité cardiaque à vérifier)", "end")
    return secteur(o, "Grossesse intra-utérine du 1er trimestre — échographie (schéma)", a)

def echo_hydronephrose():
    o = ('<ellipse cx="400" cy="250" rx="200" ry="105" fill="#9a9a9a" opacity="0.45"/>'
         '<ellipse cx="400" cy="250" rx="185" ry="92" fill="none" stroke="#ddd" stroke-width="4"/>'
         '<path d="M330,250 C330,210 370,190 410,210 C440,190 470,200 480,230 C500,260 470,300 430,290 C400,310 340,300 330,250 Z" fill="#050505"/>'
         + "".join(f'<ellipse cx="{x}" cy="{y}" rx="22" ry="16" fill="#050505"/>' for x, y in [(300, 205), (300, 295), (500, 200), (505, 300)]))
    a = fleche(110, 120, 300, 200, "Calices dilatés (anéchogènes)", "start") + fleche(690, 470, 450, 270, "Bassinet dilaté", "end")
    return secteur(o, "Dilatation des cavités pyélocalicielles (hydronéphrose) — échographie (schéma)", a)

def echo_vesicule():
    o = ('<ellipse cx="400" cy="230" rx="170" ry="80" fill="#050505"/>'
         '<ellipse cx="460" cy="270" rx="32" ry="24" fill="#f5f5f5"/>'
         '<path d="M430,290 L490,290 L520,486 L410,486 Z" fill="#000" opacity="0.95"/>')
    a = fleche(110, 120, 300, 220, "Vésicule biliaire (liquide anéchogène)", "start") + fleche(690, 120, 490, 262, "Calcul hyperéchogène", "end") + fleche(690, 470, 470, 400, "Cône d'ombre postérieur", "end")
    return secteur(o, "Lithiase vésiculaire — échographie (schéma)", a)

def echo_wilms():
    o = ('<ellipse cx="400" cy="300" rx="165" ry="115" fill="#bdbdbd" opacity="0.55" filter="url(#b4)"/>'
         '<ellipse cx="400" cy="300" rx="165" ry="115" fill="none" stroke="#eee" stroke-width="3"/>'
         '<circle cx="360" cy="290" r="28" fill="#222" opacity="0.8" filter="url(#b4)"/><circle cx="450" cy="340" r="16" fill="#222" opacity="0.7" filter="url(#b4)"/>'
         '<path d="M455,195 C520,200 560,240 568,290 C548,268 515,232 462,212 Z" fill="#9a9a9a" stroke="#ddd" stroke-width="2"/>')
    a = fleche(110, 470, 330, 330, "Volumineuse masse solide hétérogène", "start") + fleche(690, 120, 535, 230, "Rein refoulé, étiré autour de la masse (éperon)", "end")
    return secteur(o, "Néphroblastome (tumeur de Wilms) — échographie (schéma)", a)

FIGURES = {
 "rx-pneumonie": rx_pneumonie, "rx-tb-caverne": rx_tb_caverne, "rx-miliaire": rx_miliaire, "rx-pneumothorax": rx_pneumothorax,
 "rx-oap": rx_oap, "rx-pneumocystose": rx_pneumocystose, "rx-distension": rx_distension, "rx-staph": rx_staph, "rx-mmh": rx_mmh,
 "rx-occlusion": rx_occlusion, "rx-pneumoperitoine": rx_pneumoperitoine, "rx-fracture": rx_fracture, "rx-osteomyelite": rx_osteomyelite,
 "rx-pott": rx_pott, "rx-polyarthrite": rx_polyarthrite, "rx-myelome": rx_myelome,
 "ct-avc": ct_avc, "ct-hematome": ct_hematome, "ct-toxoplasmose": ct_toxoplasmose, "ct-cysticercose": ct_cysticercose,
 "echo-abces-foie": echo_abces_foie, "echo-ascite": echo_ascite, "echo-geu": echo_geu, "echo-grossesse": echo_grossesse,
 "echo-hydronephrose": echo_hydronephrose, "echo-vesicule": echo_vesicule, "echo-wilms": echo_wilms,
}

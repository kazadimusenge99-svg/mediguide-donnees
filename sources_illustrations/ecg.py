# Tracés ECG schématiques (synthétiques) — illustrations originales MédiGuide.
# Papier millimétré : 1 mm = 5 px ; 25 mm/s ; 10 mm/mV.
import math, random

W = 800
MM = 5.0
PX_S = 25 * MM      # px par seconde
PX_MV = 10 * MM     # px par mV

def g(t, c, w, a):
    return a * math.exp(-((t - c) ** 2) / (2 * w * w))

def sig(x):
    return 1 / (1 + math.exp(-max(-60, min(60, x))))

def battement(t, p):
    """Un complexe PQRST, t relatif au sommet de R (s)."""
    v = 0.0
    if p.get("P", 0.15):
        v += g(t, -p.get("PR", 0.16), 0.025, p.get("P", 0.15))
    qw = p.get("qrs_w", 1.0)
    v += g(t, -0.022 * qw, 0.008 * qw, p.get("Q", -0.1))
    v += g(t, 0, 0.011 * qw, p.get("R", 1.2))
    v += g(t, 0.025 * qw, 0.010 * qw, p.get("S", -0.3))
    v += g(t, p.get("Tc", 0.30), p.get("Tw", 0.05), p.get("T", 0.3))
    st = p.get("ST", 0)
    if st:
        v += st * sig((t - 0.035 * qw) / 0.008) * sig((p.get("Tc", 0.30) + 0.02 - t) / 0.03)
    return v

def trace(duree, rr_list, p, extra=None, x0=0):
    """Renvoie les points (t, mV) d'une piste."""
    r_times = []
    t = 0.35
    i = 0
    while t < duree + 1:
        r_times.append(t)
        t += rr_list[i % len(rr_list)]
        i += 1
    pts = []
    n = int(duree * 250)
    for k in range(n + 1):
        tt = k / 250
        v = sum(battement(tt - r, p) for r in r_times if -0.6 < tt - r < 0.8)
        if extra:
            v += extra(tt)
        pts.append((tt, v))
    return pts, r_times

def grille(x, y, w, h):
    s = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FFF5F5"/>']
    for i in range(int(w / MM) + 1):
        xx = x + i * MM
        s.append(f'<line x1="{xx}" y1="{y}" x2="{xx}" y2="{y+h}" stroke="#F4C2C2" stroke-width="{1.1 if i % 5 == 0 else 0.4}"/>')
    for j in range(int(h / MM) + 1):
        yy = y + j * MM
        s.append(f'<line x1="{x}" y1="{yy}" x2="{x+w}" y2="{yy}" stroke="#F4C2C2" stroke-width="{1.1 if j % 5 == 0 else 0.4}"/>')
    return "".join(s)

def piste(y, h, pts, base_frac=0.6, nom=""):
    base = y + h * base_frac
    d = " ".join(f"{'M' if k == 0 else 'L'}{10 + t * PX_S:.1f},{base - v * PX_MV:.1f}" for k, (t, v) in enumerate(pts))
    s = grille(10, y, W - 20, h)
    s += f'<path d="{d}" fill="none" stroke="#111" stroke-width="1.8" stroke-linejoin="round"/>'
    if nom:
        s += f'<text x="18" y="{y+20}" font-family="Arial" font-weight="bold" font-size="16" fill="#333">{nom}</text>'
    return s, base

def fleche(x1, y1, x2, y2, texte, anchor="start", couleur="#1565C0"):
    ang = math.atan2(y2 - y1, x2 - x1)
    a1 = (x2 - 10 * math.cos(ang - 0.4), y2 - 10 * math.sin(ang - 0.4))
    a2 = (x2 - 10 * math.cos(ang + 0.4), y2 - 10 * math.sin(ang + 0.4))
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{couleur}" stroke-width="2.2"/>'
            f'<polygon points="{x2},{y2} {a1[0]:.1f},{a1[1]:.1f} {a2[0]:.1f},{a2[1]:.1f}" fill="{couleur}"/>'
            f'<text x="{x1}" y="{y1 - 6}" text-anchor="{anchor}" font-family="Arial" font-size="15" font-weight="bold" fill="{couleur}">{texte}</text>')

def X(t):
    return 10 + t * PX_S

def svg(h, corps, titre):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}">'
            f'<rect width="{W}" height="{h}" fill="#fff"/>{corps}'
            f'<text x="{W/2}" y="{h-12}" text-anchor="middle" font-family="Arial" font-size="15" fill="#444">{titre}</text></svg>')

DUREE = (W - 20) / PX_S

def ecg_stemi():
    p = dict(R=1.0, S=0.0, Q=-0.05, ST=0.85, T=0.75, Tw=0.07, Tc=0.26)
    pts, rr = trace(DUREE, [0.85], p)
    a, b1 = piste(10, 200, pts, 0.62, "V3")
    q = dict(R=0.7, S=-0.2, ST=-0.25, T=-0.2)
    pts2, _ = trace(DUREE, [0.85], q)
    b, b2 = piste(220, 170, pts2, 0.45, "aVL (miroir)")
    r = rr[2]
    ann = fleche(X(r) + 110, 40, X(r + 0.10) + 2, b1 - 0.85 * PX_MV - 4, "Sus-décalage du segment ST (onde de Pardee)")
    ann += fleche(X(rr[3]) + 110, b2 + 60, X(rr[3] + 0.12), b2 + 0.25 * PX_MV + 4, "Sous-décalage en miroir")
    return svg(430, a + b + ann, "Infarctus avec sus-décalage du ST (schéma)")

def ecg_hyperk():
    p = dict(P=0.05, R=0.9, S=-0.5, qrs_w=1.7, T=1.1, Tw=0.032, Tc=0.28)
    pts, rr = trace(DUREE, [0.8], p)
    a, b = piste(10, 260, pts, 0.68, "V2")
    ann = fleche(X(rr[2]) + 140, b - 170, X(rr[2] + 0.28) + 3, b - 1.1 * PX_MV + 6, "Ondes T amples et pointues")
    ann += fleche(X(rr[3]) + 60, b + 70, X(rr[3] + 0.03), b + 0.4 * PX_MV, "QRS élargis, P aplaties")
    return svg(330, a + ann, "Hyperkaliémie (schéma)")

def ecg_fa():
    random.seed(4)
    rr = [random.uniform(0.42, 0.95) for _ in range(20)]
    p = dict(P=0, R=1.1, S=-0.25, T=0.25)
    f = lambda t: 0.06 * math.sin(2 * math.pi * 6.1 * t) + 0.045 * math.sin(2 * math.pi * 7.7 * t + 1.3) + 0.03 * math.sin(2 * math.pi * 5.2 * t + 0.4)
    pts, r = trace(DUREE, rr, p, f)
    a, b = piste(10, 220, pts, 0.62, "DII")
    ann = fleche(X(r[1]) + 40, b + 70, X((r[1] + r[2]) / 2) + 10, b + 6, "Pas d'onde P, trémulation de la ligne de base")
    ann += f'<text x="{W/2}" y="{b-130}" text-anchor="middle" font-family="Arial" font-size="15" font-weight="bold" fill="#1565C0">Intervalles R-R irréguliers</text>'
    return svg(290, a + ann, "Fibrillation auriculaire (schéma)")

def ecg_bav():
    p = dict(PR=0.34, R=1.0, S=-0.25, T=0.3, Tc=0.32)
    pts, rr = trace(DUREE, [0.9], p)
    a, b1 = piste(10, 170, pts, 0.65, "BAV 1er degré")
    ann = f'<line x1="{X(rr[2]-0.36)}" y1="{b1+28}" x2="{X(rr[2]-0.03)}" y2="{b1+28}" stroke="#1565C0" stroke-width="2"/>'
    ann += f'<text x="{X(rr[2]-0.2)}" y="{b1+46}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#1565C0">PR = 0,34 s (&gt; 0,20 s)</text>'
    # BAV complet : P régulières à 85/min, QRS larges lents à 38/min, indépendants
    p_times = [0.2 + k * 0.7 for k in range(12)]
    def onde_p(t):
        return sum(g(t, pt, 0.025, 0.18) for pt in p_times)
    q = dict(P=0, R=1.0, S=-0.4, qrs_w=2.2, T=-0.35, Tc=0.40, Tw=0.07)
    pts2, r2 = trace(DUREE, [1.6], q, onde_p)
    b, b2 = piste(190, 190, pts2, 0.58, "BAV complet (3e degré)")
    for pt in p_times:
        if X(pt) < W - 20:
            b += f'<text x="{X(pt)}" y="{b2+40}" text-anchor="middle" font-family="Arial" font-size="13" font-weight="bold" fill="#C62828">P</text>'
    b += f'<text x="{W/2}" y="{b2+62}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#1565C0">Ondes P régulières sans lien avec les QRS (larges et lents)</text>'
    return svg(440, a + ann + b, "Blocs auriculo-ventriculaires (schéma)")

def ecg_hvg():
    p = dict(R=0.3, S=-2.3, Q=0, T=0.3)
    pts, rr = trace(DUREE / 2, [0.9], p)
    q = dict(R=2.8, S=-0.2, ST=-0.15, T=-0.45, Tw=0.06)
    pts2, rr2 = trace(DUREE / 2, [0.9], q)
    # deux pistes côte à côte
    a, b1 = piste(10, 250, pts, 0.30, "V1")
    off = (W - 20) / 2
    base = 10 + 250 * 0.72
    d2 = " ".join(f"{'M' if k == 0 else 'L'}{10 + off + t * PX_S:.1f},{base - v * PX_MV:.1f}" for k, (t, v) in enumerate(pts2))
    a += f'<line x1="{10+off}" y1="10" x2="{10+off}" y2="260" stroke="#999" stroke-width="2"/>'
    a += f'<path d="{d2}" fill="none" stroke="#111" stroke-width="1.8"/><text x="{18+off}" y="30" font-family="Arial" font-weight="bold" font-size="16" fill="#333">V5</text>'
    ann = fleche(X(rr[1]) + 70, b1 + 120, X(rr[1] + 0.025), b1 + 2.3 * PX_MV - 6, "S profonde")
    ann += fleche(off + X(rr2[1]) + 70, 60, off + X(rr2[1]) + 4, base - 2.8 * PX_MV + 4, "R ample")
    ann += fleche(off + X(rr2[2]) + 20, base + 70, off + X(rr2[1] + 0.3), base + 0.45 * PX_MV, "T négative (surcharge)", "middle")
    return svg(330, a + ann, "Hypertrophie ventriculaire gauche : S V1 + R V5 > 35 mm (schéma)")

def ecg_ep():
    p = dict(R=0.8, S=-0.6, Q=0, T=0.25)
    pts, rr = trace(DUREE, [0.52], p)
    a, b1 = piste(10, 170, pts, 0.55, "DI")
    q = dict(R=0.6, Q=-0.35, S=-0.1, T=-0.3)
    pts2, rr2 = trace(DUREE, [0.52], q)
    b, b2 = piste(190, 170, pts2, 0.55, "DIII")
    ann = fleche(X(rr[3]) + 40, b1 + 60, X(rr[3] + 0.025), b1 + 0.6 * PX_MV, "S1")
    ann += fleche(X(rr2[3]) - 50, b2 + 70, X(rr2[3] - 0.022), b2 + 0.35 * PX_MV, "Q3", "end")
    ann += fleche(X(rr2[4]) + 40, b2 + 70, X(rr2[4] + 0.30), b2 + 0.3 * PX_MV, "T3 négative")
    ann += f'<text x="{W-20}" y="{b1-60}" text-anchor="end" font-family="Arial" font-size="15" font-weight="bold" fill="#1565C0">Tachycardie sinusale (115/min)</text>'
    return svg(400, a + b + ann, "Embolie pulmonaire : aspect S1Q3T3 (inconstant) (schéma)")

def ecg_fv():
    def f(t):
        return (0.55 + 0.3 * math.sin(2 * math.pi * 0.35 * t)) * math.sin(2 * math.pi * (4.8 * t + 0.4 * math.sin(2 * math.pi * 0.9 * t))) \
            + 0.15 * math.sin(2 * math.pi * 7.3 * t + 1)
    pts = [(k / 250, f(k / 250)) for k in range(int(DUREE * 250) + 1)]
    a, b = piste(10, 220, pts, 0.5, "DII")
    ann = f'<text x="{W/2}" y="{b-85}" text-anchor="middle" font-family="Arial" font-size="15" font-weight="bold" fill="#C62828">Ondulations anarchiques sans QRS identifiable : choc électrique</text>'
    return svg(290, a + ann, "Fibrillation ventriculaire (schéma)")

def ecg_qt_long():
    p = dict(R=1.0, S=-0.25, T=0.35, Tc=0.40, Tw=0.06)
    pts, rr = trace(DUREE, [1.05], p)
    a, b = piste(10, 220, pts, 0.62, "DII")
    r = rr[2]
    q0, t1 = X(r - 0.03), X(r + 0.55)
    ann = f'<line x1="{q0}" y1="{b+40}" x2="{t1}" y2="{b+40}" stroke="#C62828" stroke-width="2.4"/>'
    ann += f'<line x1="{q0}" y1="{b+32}" x2="{q0}" y2="{b+48}" stroke="#C62828" stroke-width="2.4"/><line x1="{t1}" y1="{b+32}" x2="{t1}" y2="{b+48}" stroke="#C62828" stroke-width="2.4"/>'
    ann += f'<text x="{(q0+t1)/2}" y="{b+66}" text-anchor="middle" font-family="Arial" font-size="15" font-weight="bold" fill="#C62828">QT ≈ 0,58 s, RR = 1,05 s ; QTc ≈ 570 ms (&gt; 500 ms : risque de torsades de pointes)</text>'
    return svg(300, a + ann, "QT long : QTc = QT / √RR (schéma)")

FIGURES = {"ecg-stemi": ecg_stemi, "ecg-hyperk": ecg_hyperk, "ecg-fa": ecg_fa, "ecg-bav": ecg_bav, "ecg-hvg": ecg_hvg,
           "ecg-ep": ecg_ep, "ecg-fv": ecg_fv, "ecg-qt-long": ecg_qt_long}

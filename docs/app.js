/* MédiGuide – version web (Windows, Mac, tablette) installable et utilisable hors connexion.
   Données : les mêmes fichiers que l'application Android (dépôt mediguide-donnees). */
"use strict";

const BASE_DONNEES = "https://raw.githubusercontent.com/kazadimusenge99-svg/mediguide-donnees/main/";
const $ = (s) => document.querySelector(s);
const contenu = $("#contenu");
let D = null;          // meds.json
let ACT = null;        // actualites.json
let CAS = null;        // cas_cliniques.json
let IDX = null;        // index de recherche

// ---------------------------------------------------------------------------
// Utilitaires
// ---------------------------------------------------------------------------
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const norm = (s) => String(s ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const fmt = (x) => {
  if (x == null || isNaN(x)) return "";
  const a = Math.abs(x);
  const d = a >= 100 ? 0 : a >= 10 ? 1 : a >= 1 ? 2 : 3;
  return Number(x.toFixed(d)).toLocaleString("fr-FR", { maximumFractionDigits: d });
};
const nombre = (s) => { const v = parseFloat(String(s ?? "").replace(",", ".").trim()); return isNaN(v) ? null : v; };
const sto = {
  get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* stockage indisponible */ } },
};
const COUL = { ok: "var(--ok)", attention: "var(--attention)", danger: "var(--danger)" };
const PICTO = { thermometre: "🌡️", poumons: "🫁", coeur: "❤️", cerveau: "🧠", psy: "🧠", estomac: "🫃", goutte: "💧", bebe: "👶",
  grossesse: "🤰", oeil: "👁️", os: "🦴", rein: "🫘", moustique: "🦟", virus: "🦠", bacterie: "🦠", alerte: "⚠️", globe: "🌍",
  glucometre: "🩸", ruban: "🎗️", pomme: "🍎", seringue: "💉", comprime: "💊", balance: "⚖️", sirene: "🚨", pansement: "🩹",
  ver: "🪱", eclair: "⚡", cellule: "🔬", patient: "🧑", peau: "🖐️", oreille: "👂", douleur: "🤕", masque: "😷", savon: "🧼",
  bouclier: "🛡️", stethoscope: "🩺", trousse: "🧰", sang: "🩸", toux: "😮‍💨" };
const picto = (n) => PICTO[n] || "🩺";
const poids = () => { const p = nombre(sto.get("poids", "")); return p && p > 0 && p < 300 ? p : null; };

// ---------------------------------------------------------------------------
// Chargement des données (réseau d'abord, puis cache du navigateur)
// ---------------------------------------------------------------------------
async function charger(nom) {
  try {
    const r = await fetch(BASE_DONNEES + nom, { cache: "no-cache" });
    if (!r.ok) throw new Error(r.status);
    const j = await r.json();
    sto.set("maj-" + nom, new Date().toISOString());
    return j;
  } catch (e) {
    const c = await caches.match(BASE_DONNEES + nom).catch(() => null);
    if (c) return c.json();
    throw e;
  }
}

async function demarrer() {
  try {
    [D, ACT, CAS] = await Promise.all([charger("meds.json"), charger("actualites.json").catch(() => null), charger("cas_cliniques.json").catch(() => null)]);
  } catch (e) {
    contenu.innerHTML = `<div class="fiche"><h1>Données indisponibles</h1><p>Connectez l'ordinateur à Internet pour le premier chargement de MédiGuide. Ensuite, l'application fonctionne hors connexion.</p></div>`;
    return;
  }
  if (!ACT) ACT = { dateActualites: D.dateActualites, dateIsoActualites: D.dateIsoActualites, actualites: D.actualites || [] };
  if (!CAS) CAS = { casCliniques: D.casCliniques || [] };
  preparer();
  const maj = sto.get("maj-meds.json", null);
  $("#etatDonnees").innerHTML = `Données v${esc(D.version)} · ${esc(D.dateMiseAJour || "")}<br>${D.medicaments.length} médicaments · ${D.pathologies.length} pathologies` +
    (maj ? `<br>Vérifié le ${new Date(maj).toLocaleDateString("fr-FR")}` : "") + (navigator.onLine ? "" : "<br>Hors connexion");
  window.addEventListener("hashchange", router);
  router();
}

// ---------------------------------------------------------------------------
// Index et recherche classée (portage de Classement.kt)
// ---------------------------------------------------------------------------
const MOTS_VIDES = new Set("de du des la le les l d et ou a au aux en un une avec sans chez par pour sur dans qui que est j il elle mal".split(" "));
const decouper = (t) => norm(t).split(/[^a-z0-9]+/).filter(Boolean);
function mots(q) { const t = [...new Set(decouper(q))]; const u = t.filter((m) => !MOTS_VIDES.has(m)); return u.length ? u : t; }
function racine(m) {
  for (const s of ["iques", "ique", "ites", "ite", "euses", "euse", "eux", "aux", "es", "s", "x", "e"])
    if (m.length > s.length + 3 && m.endsWith(s)) return m.slice(0, -s.length);
  return m;
}
function qualite(m, j) {
  if (j === m) return 1;
  if (m.length >= 2 && j.startsWith(m)) return m.length >= 4 ? 0.9 : 0.7;
  if (m.length >= 4) {
    const rm = racine(m);
    if (rm.length >= 4 && racine(j) === rm) return 0.85;
    let c = 0; while (c < j.length && c < m.length && j[c] === m[c]) c++;
    if (c >= 5 && c >= m.length - 2) return 0.75;
    if (j.includes(m)) return 0.5;
  }
  return 0;
}
const meilleure = (m, jetons) => { let q = 0; for (const j of jetons) { const v = qualite(m, j); if (v > q) { q = v; if (q >= 1) break; } } return q; };

function classer(elements, ms, champsDe, nomDe, bonusDe) {
  if (!ms.length) return [];
  const minimum = ms.length >= 3 ? Math.ceil(ms.length / 2) : 1;
  const phrase = ms.join(" ");
  const res = [];
  for (const e of elements) {
    const cs = champsDe(e);
    let total = 0, n = 0;
    for (const m of ms) {
      let b = 0;
      for (const [jetons, poidsChamp] of cs) { const q = meilleure(m, jetons); if (q > 0) b = Math.max(b, q * poidsChamp); }
      if (b > 0) { total += b; n++; }
    }
    if (n < minimum) continue;
    if (ms.length >= 2 && cs.slice(0, 3).some(([j]) => ms.every((m) => meilleure(m, j) > 0))) total += 3;
    total *= bonusDe ? bonusDe(e) : 1;
    const nn = decouper(nomDe(e)).join(" ");
    if (nn.startsWith(phrase)) total += 8; else if (nn.includes(phrase)) total += 4;
    total += n * 10;
    res.push({ e, s: total, n, l: nn.length });
  }
  res.sort((a, b) => b.s - a.s || a.l - b.l);
  if (!res.length) return res;
  const top = res[0].s;
  for (const r of res) r.niveau = r.n === ms.length && r.s >= top * 0.8 ? 3 : r.n === ms.length && r.s >= top * 0.55 ? 2 : 1;
  return res;
}
const LIB_NIV = { 3: "Très probable", 2: "Probable", 1: "Possible" };
const badge = (n) => `<span class="badge b${n}">${LIB_NIV[n]}</span>`;

function preparer() {
  D.classesParId = Object.fromEntries(D.classes.map((c) => [c.id, c]));
  D.catParId = Object.fromEntries((D.categoriesPathologies || []).map((c) => [c.id, c]));
  D.pathoParId = Object.fromEntries(D.pathologies.map((p) => [String(p.id), p]));
  D.medParDci = Object.fromEntries(D.medicaments.map((m) => [m.dci, m]));
  D.usage = {};
  for (const p of D.pathologies) for (const d of p.medicaments || []) D.usage[d] = (D.usage[d] || 0) + 1;
  D.medicaments.sort((a, b) => a.dci.localeCompare(b.dci, "fr"));
  D.pathologies.sort((a, b) => a.nom.localeCompare(b.nom, "fr"));
  const L = (a) => (a || []).join(" ");
  IDX = {
    med: (m, plusieurs) => [[decouper(m.dci), 10], [decouper(m.noms), 9], [decouper(m.motsCles), 6], [decouper(m.famille), 5], [decouper(L(m.indications)), 4]],
    patho: (p, plusieurs) => [[decouper(p.nom), plusieurs ? 7 : 10], [decouper(p.synonymes), 7], [decouper(L(p.signes)), plusieurs ? 6 : 4], [decouper(p.resume), 2.5], [decouper(L(p.diagnostic)), 1]],
    sympt: (s) => [[decouper(s.nom), 10], [decouper((s.orientations || []).map((o) => o.indice).join(" ")), 4], [decouper(s.resume), 3]],
  };
}
const rechMed = (ms, liste = D.medicaments) => classer(liste, ms, (m) => IDX.med(m), (m) => m.dci, (m) => 1 + 0.015 * Math.min(D.usage[m.dci] || 0, 20));
const rechPatho = (ms, liste = D.pathologies) => classer(liste, ms, (p) => IDX.patho(p, ms.length >= 2), (p) => p.nom, (p) => 1 + 0.12 * (Math.min(Math.max(p.frequence || 1, 1), 3) - 1));
const rechSympt = (ms) => classer(D.symptomes || [], ms, IDX.sympt, (s) => s.nom);

// ---------------------------------------------------------------------------
// Doses par kilo dans un texte (portage de DispensaireScreen.kt)
// ---------------------------------------------------------------------------
const RE_KG = /(\d+(?:[  ]\d{3})*(?:[.,]\d+)?)(?:\s*[–-]\s*(\d+(?:[  ]\d{3})*(?:[.,]\d+)?))?\s*(mg|ml|g|µg|UI)\/kg(\/j|\/h)?/g;
const num = (s) => parseFloat(s.replace(/[  ]/g, "").replace(",", "."));
function texteDoses(t, p, gras = true) {
  let html = "";
  const calc = p != null && p <= 35;
  let pos = 0;
  const i = t.indexOf(" : ");
  const debut = gras && i > 0 && i <= 60 ? i : 0;
  const ajouter = (fin) => {
    if (pos < debut) { const f = Math.min(fin, debut); html += `<b>${esc(t.slice(pos, f))}</b>`; pos = f; }
    if (pos < fin) { html += esc(t.slice(pos, fin)); pos = fin; }
  };
  if (calc) {
    for (const m of t.matchAll(RE_KG)) {
      ajouter(m.index + m[0].length);
      const bas = num(m[1]), haut = m[2] ? num(m[2]) : null, u = m[3], j = m[4] || "";
      const v = haut != null ? `${fmt(bas * p)}–${fmt(haut * p)} ${u}` : `${fmt(bas * p)} ${u}`;
      html += ` <span class="calc">→ ${v}${j}</span>`;
    }
  }
  ajouter(t.length);
  return html;
}

// ---------------------------------------------------------------------------
// Routeur
// ---------------------------------------------------------------------------
function router() {
  const [, route = "accueil", a = "", b = ""] = location.hash.split("/");
  document.querySelectorAll(".menu a").forEach((x) => x.classList.toggle("actif", x.dataset.r === route ||
    (x.dataset.r === "medicaments" && route === "med") || (x.dataset.r === "pathologies" && route === "patho") ||
    (x.dataset.r === "symptomes" && route === "sympt") || (x.dataset.r === "dispensaire" && route === "disp") ||
    (x.dataset.r === "scores" && route === "score") || (x.dataset.r === "protocoles" && route === "proto")));
  $("#menu").classList.remove("ouvert");
  if (route !== "recherche") $("#champRecherche").value = "";
  const r = decodeURIComponent(a), r2 = decodeURIComponent(b);
  const vues = { accueil, recherche, sujet, medicaments, med: medicaments, pathologies, patho: pathologies, symptomes, sympt: symptomes,
    dispensaire, disp: dispensaire, croissance, quiz, protocoles, proto: protocoles, scores, score: scores, cas, apropos };
  (vues[route] || accueil)(route, r, r2);
  if (route !== "recherche") window.scrollTo(0, 0);
}

// ---------------------------------------------------------------------------
// Accueil
// ---------------------------------------------------------------------------
function carteUne(a, grande) {
  const p = D.pathoParId[String(a.pathologie)];
  if (!grande) return `<a class="mini-une" style="background:${esc(a.couleur)}" href="#/sujet">
      <div class="petit" style="color:#fff;opacity:.85;font-weight:700">${esc(a.etiquette)}</div>
      <b style="font-size:16px">${esc(a.icone || "")} ${esc(a.titre)}</b><div style="font-size:13px;margin-top:4px">${esc(a.chiffre)}</div></a>`;
  return `<div class="une" style="background:${esc(a.couleur)}">
      <div class="etq">${esc(a.etiquette)}</div><h2>${esc(a.icone || "")} ${esc(a.titre)}</h2>
      <div>${esc(a.lieu)}</div><div class="chiffre">${esc(a.chiffre)}</div><div>${esc(a.texte)}</div>
      <ul>${(a.details || []).map((d) => `<li>${esc(d)}</li>`).join("")}</ul>
      <div class="petit" style="color:#fff;opacity:.85;margin-top:10px">Source : ${esc(a.source)}${p ? ` · <a href="#/patho/${p.id}">Voir la fiche « ${esc(p.nom)} »</a>` : ""}</div></div>`;
}

function accueil() {
  const act = ACT.actualites || [];
  const tuiles = [
    ["#/medicaments", "💊", "Médicaments", `${D.medicaments.length} fiches`, "#1565C0"],
    ["#/pathologies", "🩺", "Pathologies", `${D.pathologies.length} fiches`, "#00695C"],
    ["#/symptomes", "🤒", "Symptômes", `${(D.symptomes || []).length} motifs`, "#C62828"],
    ["#/dispensaire", "🧰", "Dispensaire", "Doses et conduites", "#00838F"],
    ["#/protocoles", "🚨", "Protocoles d'urgence", `${(D.protocoles || []).length} protocoles`, "#B71C1C"],
    ["#/scores", "🧮", "Scores médicaux", `${(D.scores || []).length} scores`, "#4527A0"],
    ["#/croissance", "📈", "Courbes de croissance", "OMS et Fenton", "#2E7D32"],
    ["#/quiz", "❓", "Quiz", `${(D.quiz || []).length} questions`, "#AD1457"],
    ["#/cas", "🎓", "Cas cliniques", `${(CAS.casCliniques || []).length} cas`, "#6D4C41"],
  ];
  contenu.innerHTML = `
    <h1>Bienvenue</h1><p class="sous">${D.medicaments.length} médicaments · ${D.pathologies.length} pathologies · ${(D.scores || []).length} scores</p>
    ${act.length ? `<h2>🌍 Sujet du jour · ${esc(ACT.dateActualites)}</h2>
      <div class="grille" style="grid-template-columns:repeat(auto-fill,minmax(260px,1fr))">${act.slice(0, 4).map((a) => carteUne(a, false)).join("")}</div>
      <p><a href="#/sujet">Tout lire →</a></p>` : ""}
    <h2>Accès rapide</h2>
    <div class="grille">${tuiles.map(([h, i, n, d, c]) => `<a class="tuile" href="${h}"><span class="ico" style="background:${c}22;color:${c}">${i}</span><b>${n}</b><span class="petit">${d}</span></a>`).join("")}</div>`;
}

// ---------------------------------------------------------------------------
// Recherche globale
// ---------------------------------------------------------------------------
function recherche(_r, q) {
  const ms = mots(q || "");
  if (!ms.length) return accueil();
  const pa = rechPatho(ms), me = rechMed(ms), sy = rechSympt(ms).filter((r) => r.niveau >= 2 || ms.length === 1);
  const bloc = (titre, items, rendu) => items.length ? `<h2>${titre} (${items.length})</h2><div class="liste">${items.slice(0, 25).map(rendu).join("")}</div>` : "";
  contenu.innerHTML = `<h1>Résultats pour « ${esc(q)} »</h1><p class="sous">Classés du plus probable au moins probable.</p>` +
    [[pa, () => bloc("Pathologies", pa, (r) => lignePatho(r.e, null, r.niveau)), 2], [me, () => bloc("Médicaments", me, (r) => ligneMed(r.e)), 1], [sy, () => bloc("Symptômes", sy, (r) => ligneSympt(r.e)), 0]]
      .sort((a, b) => ((b[0][0]?.n || 0) - (a[0][0]?.n || 0)) || ((b[0][0]?.s || 0) - (a[0][0]?.s || 0)) || b[2] - a[2]).map((x) => x[1]()).join("") +
    (!pa.length && !me.length && !sy.length ? `<p>Aucun résultat. Essayez un autre mot (nom commercial, DCI, symptôme).</p>` : "");
}

// ---------------------------------------------------------------------------
// Lignes de liste
// ---------------------------------------------------------------------------
function ligneMed(m, actif) {
  const c = D.classesParId[m.classe];
  return `<a class="ligne${actif ? " actif" : ""}" href="#/med/${m.id}"><span class="ico" style="background:var(--surface2)">${esc(c?.icone || "💊")}</span>
    <span class="txt"><b>${esc(m.dci)}</b><span>${esc(m.noms || c?.nom || "")}</span></span></a>`;
}
function lignePatho(p, actif, niveau) {
  const c = D.catParId[p.categorie];
  return `<a class="ligne${actif ? " actif" : ""}" href="#/patho/${p.id}"><span class="ico" style="background:${esc(c?.couleur || "#00695C")}22">${esc(c?.icone || "🩺")}</span>
    <span class="txt"><b>${esc(p.nom)}</b><span>${esc(c?.nom || "")}</span></span>${niveau ? badge(niveau) : ""}</a>`;
}
function ligneSympt(s, actif) {
  return `<a class="ligne${actif ? " actif" : ""}" href="#/sympt/${encodeURIComponent(s.id)}"><span class="ico" style="background:${esc(s.couleur)}22">${picto(s.pictogramme)}</span>
    <span class="txt"><b>${esc(s.nom)}</b><span>${esc(s.resume)}</span></span></a>`;
}
const liste = (titre, arr, ico, cls = "") => arr && arr.length ? `<div class="section ${cls}"><h3>${ico} ${esc(titre)}</h3><ul>${arr.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>` : "";

// ---------------------------------------------------------------------------
// Médicaments
// ---------------------------------------------------------------------------
let filtreMed = "", classeMed = "";
function medicaments(route, id) {
  const m = route === "med" ? D.medicaments.find((x) => String(x.id) === id) : null;
  const ms = mots(filtreMed);
  let l = D.medicaments.filter((x) => !classeMed || x.classe === classeMed);
  l = ms.length ? rechMed(ms, l).map((r) => r.e) : l;
  contenu.innerHTML = `<div class="deux${m ? " avec-detail" : ""}"><div class="col-liste">
      <h1>Médicaments</h1><p class="sous">${l.length} fiches</p>
      <input class="filtre" id="fMed" placeholder="Filtrer (DCI, nom commercial, famille, indication)…" value="${esc(filtreMed)}">
      <div class="puces"><button class="puce${classeMed ? "" : " actif"}" data-c="">Toutes</button>${D.classes.map((c) => `<button class="puce${classeMed === c.id ? " actif" : ""}" data-c="${esc(c.id)}">${esc(c.icone)} ${esc(c.nom)}</button>`).join("")}</div>
      <div class="liste">${l.map((x) => ligneMed(x, m && x.id === m.id)).join("")}</div></div>
    <div>${m ? ficheMed(m) : `<div class="fiche"><p class="sous">Choisissez un médicament dans la liste.</p></div>`}</div></div>`;
  const f = $("#fMed");
  f.addEventListener("input", () => { filtreMed = f.value; medicaments(route, id); const g = $("#fMed"); g.focus(); g.setSelectionRange(g.value.length, g.value.length); });
  contenu.querySelectorAll(".puce").forEach((b) => b.addEventListener("click", () => { classeMed = b.dataset.c; medicaments(route, id); }));
}

function blocCalcul(c) {
  const p = poids();
  const regle = `${fmt(c.doseKg)}${c.doseKgMax ? " à " + fmt(c.doseKgMax) : ""} ${c.unite}/kg${c.doseMax ? ` (max ${fmt(c.doseMax)} ${c.unite})` : ""}`;
  if (p == null) return `<div class="dose"><b>${esc(c.titre)}</b><div>Règle : ${esc(regle)} · ${esc(c.frequence)}</div><div class="petit">Saisissez le poids en haut de la page pour obtenir la dose.</div></div>`;
  const borne = (d) => Math.max(c.doseMin ?? -Infinity, Math.min(c.doseMax ?? Infinity, d));
  const b1 = p * c.doseKg, b2 = c.doseKgMax ? p * c.doseKgMax : null;
  const d1 = borne(b1); let d2 = b2 != null ? borne(b2) : null; if (d2 != null && d2 <= d1) d2 = null;
  const pres = (c.presentations || []).map((pr) => {
    const q1 = d1 / pr.dose * pr.par, q2 = d2 != null ? d2 / pr.dose * pr.par : null;
    return `<li>${esc(pr.nom)} : ${fmt(q1)}${q2 != null ? " à " + fmt(q2) : ""} ${esc(pr.unite)}</li>`;
  }).join("");
  const plaf = c.doseMax && (b2 ?? b1) > c.doseMax ? `<div><b>Attention : dose plafonnée à ${fmt(c.doseMax)} ${esc(c.unite)} par prise.</b></div>` : "";
  return `<div class="dose"><b>${esc(c.titre)}</b> <span class="petit">(${esc(regle)})</span>
    <div class="val">${fmt(d1)}${d2 != null ? " à " + fmt(d2) : ""} ${esc(c.unite)}</div><div>${esc(c.frequence)} · pour ${fmt(p)} kg</div>${plaf}
    ${pres ? `<div style="margin-top:6px"><b>Soit :</b><ul style="margin:2px 0 0;padding-left:20px">${pres}</ul></div>` : ""}${c.note ? `<div class="petit">${esc(c.note)}</div>` : ""}</div>`;
}

function ficheMed(m) {
  const c = D.classesParId[m.classe];
  const pathos = D.pathologies.filter((p) => (p.medicaments || []).includes(m.dci));
  return `<div class="fiche"><div class="tete"><span class="ico" style="background:var(--surface2)">${esc(c?.icone || "💊")}</span>
      <div><h1>${esc(m.dci)}</h1><div class="sous" style="margin:0">${esc(m.noms)}</div></div></div>
    <div class="petit">${esc(c?.nom || "")} · ${esc(m.formes)}</div>
    ${m.famille || m.mecanisme ? `<div class="section"><h3>🔬 Famille et mécanisme d'action</h3>${m.famille ? `<div><b>Famille :</b> ${esc(m.famille)}</div>` : ""}<div>${esc(m.mecanisme || "")}</div></div>` : ""}
    ${(m.calculs || []).length ? `<h3>🧮 Calcul de la dose</h3>${m.calculs.map(blocCalcul).join("")}` : ""}
    ${liste("Indications", m.indications, "✅")}
    ${liste("Posologie adulte", m.posologieAdulte, "🧑")}
    ${liste("Posologie enfant", m.posologieEnfant, "👶")}
    ${liste("Contre-indications", m.contreIndications, "⛔", "danger")}
    ${liste("Précautions", m.precautions, "⚠️")}
    ${liste("Effets indésirables", m.effetsIndesirables, "💢")}
    ${m.grossesse ? `<div class="section"><h3>🤰 Grossesse et allaitement</h3><div>${esc(m.grossesse)}</div></div>` : ""}
    ${pathos.length ? `<div class="section"><h3>🩺 Utilisé dans</h3><div class="liens">${pathos.map((p) => `<a class="lien" href="#/patho/${p.id}">${esc(p.nom)}</a>`).join("")}</div></div>` : ""}
  </div>`;
}

// ---------------------------------------------------------------------------
// Pathologies
// ---------------------------------------------------------------------------
let filtrePatho = "", catPatho = "";
function pathologies(route, id) {
  const p = route === "patho" ? D.pathoParId[id] : null;
  const ms = mots(filtrePatho);
  let l = D.pathologies.filter((x) => !catPatho || x.categorie === catPatho);
  const classes = ms.length ? rechPatho(ms, l) : l.map((e) => ({ e }));
  contenu.innerHTML = `<div class="deux${p ? " avec-detail" : ""}"><div class="col-liste">
      <h1>Pathologies</h1><p class="sous">${classes.length} fiches</p>
      <input class="filtre" id="fPatho" placeholder="Filtrer, ou taper des signes (ex. fièvre toux)…" value="${esc(filtrePatho)}">
      <div class="puces"><button class="puce${catPatho ? "" : " actif"}" data-c="">Toutes</button>${(D.categoriesPathologies || []).map((c) => `<button class="puce${catPatho === c.id ? " actif" : ""}" data-c="${esc(c.id)}">${esc(c.icone)} ${esc(c.nom)}</button>`).join("")}</div>
      <div class="liste">${classes.map((r) => lignePatho(r.e, p && r.e.id === p.id, r.niveau)).join("")}</div></div>
    <div>${p ? fichePatho(p) : `<div class="fiche"><p class="sous">Choisissez une pathologie dans la liste.</p></div>`}</div></div>`;
  const f = $("#fPatho");
  f.addEventListener("input", () => { filtrePatho = f.value; pathologies(route, id); const g = $("#fPatho"); g.focus(); g.setSelectionRange(g.value.length, g.value.length); });
  contenu.querySelectorAll(".puce").forEach((b) => b.addEventListener("click", () => { catPatho = b.dataset.c; pathologies(route, id); }));
}

function fichePatho(p) {
  const c = D.catParId[p.categorie];
  const meds = (p.medicaments || []).map((d) => D.medParDci[d]).filter(Boolean);
  return `<div class="fiche"><div class="tete"><span class="ico" style="background:${esc(c?.couleur || "#00695C")}22">${esc(c?.icone || "🩺")}</span>
      <div><h1>${esc(p.nom)}</h1><div class="sous" style="margin:0">${esc(c?.nom || "")}${p.synonymes ? " · " + esc(p.synonymes) : ""}</div></div></div>
    <p>${esc(p.resume)}</p>
    ${p.physiopathologie ? `<div class="section"><h3>🔬 Physiopathologie</h3><div>${esc(p.physiopathologie)}</div></div>` : ""}
    ${liste("Signes cliniques", p.signes, "🧑")}
    ${liste("Diagnostic", p.diagnostic, "🔎")}
    ${liste("Traitement", p.traitement, "💊", "ok")}
    ${liste("Signes de gravité", p.gravite, "🚩", "danger")}
    ${liste("Prévention", p.prevention, "🛡️")}
    ${meds.length ? `<div class="section"><h3>💊 Médicaments</h3><div class="liens">${meds.map((m) => `<a class="lien" href="#/med/${m.id}">${esc(m.dci)}</a>`).join("")}</div></div>` : ""}
  </div>`;
}

// ---------------------------------------------------------------------------
// Symptômes
// ---------------------------------------------------------------------------
function symptomes(route, id) {
  const s = route === "sympt" ? (D.symptomes || []).find((x) => x.id === id) : null;
  contenu.innerHTML = `<div class="deux${s ? " avec-detail" : ""}"><div class="col-liste"><h1>Symptômes</h1>
      <p class="sous">Partir d'un motif de consultation pour orienter le diagnostic.</p>
      <div class="liste">${(D.symptomes || []).map((x) => ligneSympt(x, s && x.id === s.id)).join("")}</div></div>
    <div>${s ? ficheSympt(s) : `<div class="fiche"><p class="sous">Choisissez un symptôme.</p></div>`}</div></div>`;
}
function ficheSympt(s) {
  const or = (s.orientations || []).map((o) => { const p = D.pathoParId[String(o.pathologie)]; return p ? `<a class="ligne" href="#/patho/${p.id}"><span class="txt"><b>${esc(p.nom)}</b><span>${esc(o.indice)}</span></span></a>` : ""; }).join("");
  return `<div class="fiche"><div class="tete"><span class="ico" style="background:${esc(s.couleur)}22">${picto(s.pictogramme)}</span><h1>${esc(s.nom)}</h1></div>
    <p>${esc(s.resume)}</p>${liste("Signes d'alarme : référer", s.alarme, "🚩", "danger")}${liste("Questions à poser", s.questions, "❓")}
    ${liste("Examens", s.examens, "🧪")}${or ? `<h3>🧭 Orientations diagnostiques</h3><div class="liste">${or}</div>` : ""}${liste("Conduite à tenir", s.conduite, "✅", "ok")}</div>`;
}

// ---------------------------------------------------------------------------
// Dispensaire
// ---------------------------------------------------------------------------
const estAttention = (c) => /^(attention|remarque)/i.test(c);
function blocDisp(b, coul) {
  const p = poids();
  const titre = b.titre ? `<h3 style="color:${esc(coul)}">${esc(b.titre)}</h3>` : "";
  if (b.type === "liste") return titre + `<div class="section"><ul>${b.elements.map((e) => `<li>${texteDoses(e, p)}</li>`).join("")}</ul></div>`;
  if (b.type === "tableau") {
    let corps;
    if (b.colonnes.length >= 4) {
      corps = b.lignes.map((l) => `<div class="carte-tab"><div class="titre" style="background:${esc(coul)}1a;color:${esc(coul)}">${esc(l[0])}</div>
        <div class="corps-c">${b.colonnes.slice(1).map((c, j) => { const v = l[j + 1] || ""; return !v || v === "—" || estAttention(c) ? "" : `<span class="lab">${esc(c)}</span><span>${texteDoses(v, /^adulte/i.test(c) ? null : p, false)}</span>`; }).join("")}</div>
        ${b.colonnes.map((c, j) => j > 0 && estAttention(c) && l[j] && l[j] !== "—" ? `<div class="att">⚠ ${esc(l[j])}</div>` : "").join("")}</div>`).join("");
    } else {
      corps = `<table class="tab"><thead><tr style="background:${esc(coul)}22">${b.colonnes.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead>
        <tbody>${b.lignes.map((l) => `<tr>${l.map((c) => `<td>${texteDoses(c, p, false)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
    }
    return titre + corps + (b.note ? `<p class="petit">${esc(b.note)}</p>` : "");
  }
  return titre + `<p>${texteDoses(b.texte || "", p, false)}</p>`;
}
function dispensaire(route, id) {
  const ch = route === "disp" ? (D.dispensaire || []).find((x) => x.id === id) : null;
  if (!ch) {
    contenu.innerHTML = `<h1>Dispensaire</h1><p class="sous">Les indispensables du poste et du centre de santé. Saisissez le poids en haut de la page pour voir les doses calculées.</p>
      <div class="grille">${(D.dispensaire || []).map((c) => `<a class="tuile" href="#/disp/${encodeURIComponent(c.id)}"><span class="ico" style="background:${esc(c.couleur)}22">${picto(c.pictogramme)}</span><b>${esc(c.titre)}</b><span class="petit">${esc(c.intro.slice(0, 90))}…</span></a>`).join("")}</div>
      <p class="petit" style="margin-top:20px">Repères OMS/PCIME et MSF. En cas de différence, l'ordinogramme national et la notice du produit font foi.</p>`;
    return;
  }
  const p = poids();
  const avecKg = ch.blocs.some((b) => [...(b.elements || []), ...(b.lignes || []).flat(), b.texte || ""].some((t) => /\/kg/.test(t)));
  contenu.innerHTML = `<p><a href="#/dispensaire">← Dispensaire</a></p><div class="fiche">
    <div class="tete"><span class="ico" style="background:${esc(ch.couleur)}22">${picto(ch.pictogramme)}</span><h1>${esc(ch.titre)}</h1></div>
    <div class="section" style="background:${esc(ch.couleur)}1a"><b>${esc(ch.intro)}</b></div>
    ${avecKg ? `<div class="alerte-poids">${p == null ? "Saisissez le poids de l'enfant en haut de la page pour voir les doses calculées." : p <= 35 ? `Doses calculées pour <b>${fmt(p)} kg</b> (en couleur). Vérifiez toujours la dose maximale.` : `Poids de ${fmt(p)} kg : utilisez les doses adultes (pas de calcul par kilo au-delà de 35 kg).`}</div>` : ""}
    ${ch.blocs.map((b) => blocDisp(b, ch.couleur)).join("")}</div>`;
}

// ---------------------------------------------------------------------------
// Protocoles d'urgence (avec minuteurs)
// ---------------------------------------------------------------------------
let minuteur = null;
function protocoles(route, id) {
  const pr = route === "proto" ? (D.protocoles || []).find((x) => x.id === id) : null;
  if (!pr) {
    contenu.innerHTML = `<h1>Protocoles d'urgence</h1><p class="sous">Conduites étape par étape, avec minuteurs.</p>
      <div class="liste">${(D.protocoles || []).map((x) => `<a class="ligne" href="#/proto/${encodeURIComponent(x.id)}"><span class="ico" style="background:${esc(x.couleur)}22">${esc(x.icone)}</span><span class="txt"><b>${esc(x.nom)}</b><span>${esc(x.public || "")}</span></span></a>`).join("")}</div>`;
    return;
  }
  const lienP = D.pathoParId[String(pr.pathologie)];
  contenu.innerHTML = `<p><a href="#/protocoles">← Protocoles</a></p><h1>${esc(pr.icone)} ${esc(pr.nom)}</h1><p class="sous">${esc(pr.public || "")}${lienP ? ` · <a href="#/patho/${lienP.id}">Fiche « ${esc(lienP.nom)} »</a>` : ""}</p>
    ${pr.etapes.map((e, i) => `<div class="etape"><span class="num" style="background:${esc(pr.couleur)}">${i + 1}</span><div style="flex:1"><b>${esc(e.titre)}</b><div>${esc(e.texte)}</div>
      ${e.minuteur ? `<button class="bouton second" data-t="${e.minuteur}" style="margin-top:8px">⏱ Minuteur ${Math.round(e.minuteur / 60) >= 1 ? fmt(e.minuteur / 60) + " min" : e.minuteur + " s"}</button> <span class="petit" id="t${i}"></span>` : ""}</div></div>`).join("")}`;
  contenu.querySelectorAll("[data-t]").forEach((b) => b.addEventListener("click", () => {
    clearInterval(minuteur);
    let reste = +b.dataset.t; const aff = b.nextElementSibling;
    const tic = () => { aff.textContent = reste > 0 ? `${Math.floor(reste / 60)}:${String(reste % 60).padStart(2, "0")}` : "⏰ Temps écoulé"; if (reste-- <= 0) clearInterval(minuteur); };
    tic(); minuteur = setInterval(tic, 1000);
  }));
}

// ---------------------------------------------------------------------------
// Scores
// ---------------------------------------------------------------------------
let specScore = "";
function scores(route, id) {
  const sc = route === "score" ? (D.scores || []).find((x) => x.id === id) : null;
  if (!sc) {
    const l = (D.scores || []).filter((x) => !specScore || x.specialite === specScore);
    contenu.innerHTML = `<h1>Scores médicaux</h1><p class="sous">${l.length} scores et formules</p>
      <div class="puces"><button class="puce${specScore ? "" : " actif"}" data-c="">Tous</button>${(D.specialitesScores || []).map((c) => `<button class="puce${specScore === c.id ? " actif" : ""}" data-c="${esc(c.id)}">${esc(c.icone)} ${esc(c.nom)}</button>`).join("")}</div>
      <div class="liste">${l.map((x) => `<a class="ligne" href="#/score/${encodeURIComponent(x.id)}"><span class="txt"><b>${esc(x.nom)}</b><span>${esc(x.description)}</span></span></a>`).join("")}</div>`;
    contenu.querySelectorAll(".puce").forEach((b) => b.addEventListener("click", () => { specScore = b.dataset.c; scores(route, id); }));
    return;
  }
  const entete = `<p><a href="#/scores">← Scores</a></p><div class="fiche"><h1>${esc(sc.nom)}</h1><p class="sous">${esc(sc.description)}</p>`;
  const pied = `${sc.note ? `<div class="section"><div class="petit">${esc(sc.note)}</div></div>` : ""}<p class="petit">Source : ${esc(sc.source || "")}</p></div>`;
  if (sc.type === "formule") { contenu.innerHTML = entete + formule(sc.id) + `<div id="resF"></div>` + pied; brancherFormule(sc.id); return; }
  contenu.innerHTML = entete + sc.items.map((it, i) => `<div class="score-item"><b>${esc(it.titre)}</b>${it.options.map((o, j) =>
      `<label class="option"><input type="radio" name="i${i}" value="${o.points}"><span>${esc(o.texte)} <span class="petit">(${fmt(o.points)})</span></span></label>`).join("")}</div>`).join("") +
    `<div id="resS"></div>` + pied;
  const maj = () => {
    const ch = sc.items.map((_, i) => contenu.querySelector(`input[name=i${i}]:checked`));
    const n = ch.filter(Boolean).length;
    const tot = ch.reduce((s, x) => s + (x ? +x.value : 0), 0);
    const it = (sc.interpretation || []).find((r) => tot >= r.min - 1e-9 && tot <= r.max + 1e-9);
    $("#resS").innerHTML = `<div class="resultat" style="background:${COUL[it?.niveau] || "var(--primaire)"}"><b style="font-size:20px">Total : ${fmt(tot)}</b>
      ${n < sc.items.length ? `<span class="petit" style="color:#fff"> (${n}/${sc.items.length} critères renseignés)</span>` : ""}<div>${esc(it?.texte || "")}</div></div>`;
  };
  contenu.querySelectorAll("input[type=radio]").forEach((r) => r.addEventListener("change", maj));
  maj();
}
const CHAMPS_F = {
  imc: [["a", "Poids (kg)"], ["b", "Taille (cm)"]], surface: [["a", "Poids (kg)"], ["b", "Taille (cm)"]],
  cockcroft: [["a", "Âge (ans)"], ["b", "Poids (kg)"], ["c", "Créatinine (µmol/l)"], ["s", "Sexe"]],
  ckdepi: [["a", "Âge (ans)"], ["c", "Créatinine (µmol/l)"], ["s", "Sexe"]],
  calcemie: [["a", "Calcémie mesurée (mmol/l)"], ["b", "Albumine (g/l)"]],
  trouanionique: [["a", "Sodium Na⁺ (mmol/l)"], ["b", "Chlore Cl⁻ (mmol/l)"], ["c", "Bicarbonates HCO₃⁻ (mmol/l)"]],
};
function formule(id) {
  return (CHAMPS_F[id] || []).map(([k, l]) => k === "s"
    ? `<label class="champ">${l}<select id="f_s"><option value="h">Homme</option><option value="f">Femme</option></select></label>`
    : `<label class="champ">${l}<input id="f_${k}" inputmode="decimal" value="${k === "b" && /Poids/.test(l) || k === "a" && /Poids/.test(l) ? esc(sto.get("poids", "")) : ""}"></label>`).join("");
}
function stadeRenal(v) {
  return v >= 90 ? ["Fonction rénale normale (G1)", "ok"] : v >= 60 ? ["Diminution légère (G2)", "ok"] : v >= 45 ? ["Diminution légère à modérée (G3a)", "attention"]
    : v >= 30 ? ["Diminution modérée à sévère (G3b)", "attention"] : v >= 15 ? ["Diminution sévère (G4)", "danger"] : ["Insuffisance rénale terminale (G5)", "danger"];
}
function brancherFormule(id) {
  const calc = () => {
    const v = (k) => nombre($("#f_" + k)?.value), f = $("#f_s")?.value === "f";
    const a = v("a"), b = v("b"), c = v("c");
    let r = null;
    if (id === "imc" && a > 0 && b > 30) { const x = a / (b / 100) ** 2; r = [fmt(x), "kg/m²", ...(x < 16 ? ["Maigreur sévère (dénutrition)", "danger"] : x < 18.5 ? ["Maigreur", "attention"] : x < 25 ? ["Corpulence normale", "ok"] : x < 30 ? ["Surpoids", "attention"] : x < 35 ? ["Obésité modérée (classe I)", "attention"] : x < 40 ? ["Obésité sévère (classe II)", "danger"] : ["Obésité morbide (classe III)", "danger"])]; }
    if (id === "surface" && a > 0 && b > 0) r = [fmt(Math.sqrt(a * b / 3600)), "m²", "Surface corporelle (Mosteller)", "ok"];
    if (id === "cockcroft" && a > 0 && b > 0 && c > 0) { const x = (140 - a) * b * (f ? 1.04 : 1.23) / c; const [t, n] = stadeRenal(x); r = [fmt(x), "ml/min", t + " — adapter les doses des médicaments éliminés par le rein", n]; }
    if (id === "ckdepi" && a > 0 && c > 0) { const scr = c / 88.4, k = f ? 0.7 : 0.9, al = f ? -0.241 : -0.302; const x = 142 * Math.min(scr / k, 1) ** al * Math.max(scr / k, 1) ** -1.2 * 0.9938 ** a * (f ? 1.012 : 1); const [t, n] = stadeRenal(x); r = [fmt(x), "ml/min/1,73 m²", t, n]; }
    if (id === "calcemie" && a > 0 && b > 0) { const x = a + 0.02 * (40 - b); r = [fmt(x), "mmol/l", ...(x < 1.9 ? ["Hypocalcémie sévère", "danger"] : x < 2.2 ? ["Hypocalcémie", "attention"] : x <= 2.6 ? ["Calcémie normale", "ok"] : x < 3 ? ["Hypercalcémie", "attention"] : ["Hypercalcémie sévère (urgence)", "danger"])]; }
    if (id === "trouanionique" && a > 0 && b != null && c != null) { const x = a - (b + c); r = [fmt(x), "mmol/l", ...(x > 16 ? ["Trou anionique élevé : acidocétose, acidose lactique, insuffisance rénale, intoxication", "danger"] : x < 8 ? ["Trou anionique bas (hypoalbuminémie fréquente)", "attention"] : ["Trou anionique normal (si acidose : perte digestive ou rénale de bicarbonates)", "ok"])]; }
    $("#resF").innerHTML = r ? `<div class="resultat" style="background:${COUL[r[3]]}"><b style="font-size:20px">${r[0]} ${r[1]}</b><div>${esc(r[2])}</div></div>` : "";
  };
  contenu.querySelectorAll("input,select").forEach((x) => x.addEventListener("input", calc));
  calc();
}

// ---------------------------------------------------------------------------
// Sujet du jour
// ---------------------------------------------------------------------------
function sujet() {
  const a = ACT.actualites || [];
  contenu.innerHTML = `<h1>🌍 Sujet du jour</h1><p class="sous">${esc(ACT.dateActualites || "")} · tendances de santé dans le monde, renouvelées chaque matin</p>
    ${a.length ? carteUne(a[0], true) : "<p>Pas de sujet disponible.</p>"}
    ${a.length > 1 ? `<h2>Autres sujets et alertes du jour</h2>${a.slice(1).map((x) => carteUne(x, true)).join("")}` : ""}`;
}

// ---------------------------------------------------------------------------
// Cas cliniques
// ---------------------------------------------------------------------------
function cas(_r, id) {
  const l = CAS.casCliniques || [];
  const c = l.find((x) => x.id === id);
  if (!c) {
    contenu.innerHTML = `<h1>🎓 Cas cliniques</h1><p class="sous">Nouvelle série chaque semaine${CAS.dateIsoCas ? " · " + esc(new Date(CAS.dateIsoCas).toLocaleDateString("fr-FR")) : ""}</p>
      <div class="liste">${l.map((x) => `<a class="ligne" href="#/cas/${encodeURIComponent(x.id)}"><span class="txt"><b>${esc(x.titre)}</b><span>${esc(x.niveau)} · ${esc(x.theme)}</span></span></a>`).join("")}</div>`;
    return;
  }
  let etape = 0;
  const rendre = () => {
    const faites = c.etapes.slice(0, etape);
    const e = c.etapes[etape];
    contenu.innerHTML = `<p><a href="#/cas">← Cas cliniques</a></p><div class="fiche"><h1>${esc(c.titre)}</h1><p class="sous">${esc(c.niveau)} · ${esc(c.theme)}</p>
      <div class="section">${esc(c.presentation)}</div>
      ${faites.map((f) => `${f.info ? `<div class="section">${esc(f.info)}</div>` : ""}<p><b>${esc(f.question)}</b></p><div class="choix bon">✔ ${esc(f.options[f.bonne])}</div><p class="petit">${esc(f.explication)}</p>`).join("")}
      ${e ? `${e.info ? `<div class="section">${esc(e.info)}</div>` : ""}<p><b>${esc(e.question)}</b></p>${e.options.map((o, i) => `<button class="choix" data-i="${i}">${esc(o)}</button>`).join("")}<div id="expl"></div>`
          : `<div class="section ok"><h3>Conclusion</h3>${esc(c.conclusion)}</div><p class="petit">Source : ${esc(c.source)}</p>${D.pathoParId[String(c.pathologie)] ? `<a class="bouton" href="#/patho/${c.pathologie}">Voir la fiche</a>` : ""}`}</div>`;
    contenu.querySelectorAll("[data-i]").forEach((b) => b.addEventListener("click", () => {
      const i = +b.dataset.i;
      contenu.querySelectorAll("[data-i]").forEach((x) => { x.disabled = true; if (+x.dataset.i === e.bonne) x.classList.add("bon"); });
      if (i !== e.bonne) b.classList.add("faux");
      $("#expl").innerHTML = `<p>${i === e.bonne ? "✅ <b>Bonne réponse.</b>" : "❌ <b>Pas tout à fait.</b>"} ${esc(e.explication)}</p><button class="bouton" id="suiv">Continuer</button>`;
      $("#suiv").addEventListener("click", () => { etape++; rendre(); });
    }));
  };
  rendre();
}

// ---------------------------------------------------------------------------
// À propos
// ---------------------------------------------------------------------------
function apropos() {
  contenu.innerHTML = `<div class="fiche"><h1>À propos de MédiGuide</h1>
    <p>Aide-mémoire clinique pour les professionnels de santé de la RDC : médicaments essentiels, pathologies, symptômes, dispensaire, protocoles d'urgence, scores et cas cliniques.</p>
    <p>Cette version web s'installe sur Windows, Mac ou tablette (bouton « Installer » ou menu du navigateur → « Installer MédiGuide »). Elle fonctionne hors connexion et se met à jour automatiquement dès que l'ordinateur est connecté.</p>
    <p><b>Données :</b> version ${esc(D.version)} du ${esc(D.dateMiseAJour || "")}.</p>
    <p class="petit">Sources principales : OMS (Liste des médicaments essentiels, PCIME, directives), MSF (Guide clinique et thérapeutique), programmes nationaux de la RDC. Cet outil ne remplace pas le jugement clinique ; en cas de doute, se référer aux protocoles nationaux et à la notice des produits.</p>
    <button class="bouton" id="majD">Vérifier les mises à jour</button> <span id="majTxt" class="petit"></span></div>`;
  $("#majD").addEventListener("click", async () => { $("#majTxt").textContent = "Vérification…"; try { await demarrer(); } catch { $("#majTxt").textContent = "Pas de connexion."; } });
}

// ---------------------------------------------------------------------------
// En-tête : recherche, poids, menu, installation, hors connexion
// ---------------------------------------------------------------------------
let tempo = null;
$("#champRecherche").addEventListener("input", (e) => {
  clearTimeout(tempo);
  tempo = setTimeout(() => { const q = e.target.value.trim(); if (D) location.hash = q ? "#/recherche/" + encodeURIComponent(q) : "#/accueil"; }, 220);
});
const cp = $("#champPoids");
cp.value = sto.get("poids", "");
cp.addEventListener("input", () => { sto.set("poids", cp.value.replace(/[^\d.,]/g, "")); if (D) router(); cp.focus(); });
$("#boutonMenu").addEventListener("click", () => $("#menu").classList.toggle("ouvert"));
let invite = null;
window.addEventListener("beforeinstallprompt", (e) => { e.preventDefault(); invite = e; $("#boutonInstaller").hidden = false; });
$("#boutonInstaller").addEventListener("click", async () => { if (!invite) return; invite.prompt(); await invite.userChoice; invite = null; $("#boutonInstaller").hidden = true; });
if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});


// ---------------------------------------------------------------------------
// Courbes de croissance : OMS (0–5 ans) et Fenton (prématurés, 22–50 semaines)
// ---------------------------------------------------------------------------
const NORMES = {};
async function normes(nom) {
  if (!NORMES[nom]) NORMES[nom] = await fetch(`croissance_${nom}.json`).then((r) => r.json());
  return NORMES[nom];
}
function lmsA(t, x) {
  if (!t || !t.length || x < t[0][0] - 1e-9 || x > t[t.length - 1][0] + 1e-9) return null;
  let i = 0; while (i < t.length - 1 && t[i + 1][0] <= x + 1e-9) i++;
  const p = t[i]; if (i === t.length - 1 || Math.abs(p[0] - x) < 1e-9) return p;
  const q = t[i + 1], k = (x - p[0]) / (q[0] - p[0]);
  return [x, p[1] + k * (q[1] - p[1]), p[2] + k * (q[2] - p[2]), p[3] + k * (q[3] - p[3])];
}
const valZ = ([, L, M, S], z) => Math.abs(L) < 1e-9 ? M * Math.exp(S * z) : M * (1 + L * S * z) ** (1 / L);
function zScore(lms, x, restreint) {
  const [, L, M, S] = lms;
  const z = Math.abs(L) < 1e-9 ? Math.log(x / M) / S : ((x / M) ** L - 1) / (L * S);
  if (!restreint) return z;
  if (z > 3) { const s3 = valZ(lms, 3); return 3 + (x - s3) / (s3 - valZ(lms, 2)); }
  if (z < -3) { const s3 = valZ(lms, -3); return -3 + (x - s3) / (valZ(lms, -2) - s3); }
  return z;
}
function phi(z) {
  const t = 1 / (1 + 0.2316419 * Math.abs(z)), d = 0.3989422804014327 * Math.exp(-z * z / 2);
  const p = d * t * (0.31938153 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))));
  return z >= 0 ? 1 - p : p;
}
const texteCentile = (z) => { const p = phi(z) * 100; return p < 1 ? "< 1er percentile" : p > 99 ? "> 99e percentile" : `${Math.max(1, Math.floor(p))}e percentile`; };
const texteZ = (z) => (z >= 0 ? "+" : "−") + Math.abs(z).toFixed(1).replace(".", ",");
function interpOms(ind, z) {
  if (ind === "poidsAge") return z < -3 ? ["Insuffisance pondérale sévère", "danger"] : z < -2 ? ["Insuffisance pondérale", "attention"] : z > 2 ? ["Poids élevé pour l'âge : interpréter avec le poids pour la taille", "attention"] : ["Normal", "ok"];
  if (ind === "tailleAge") return z < -3 ? ["Retard de croissance sévère (malnutrition chronique)", "danger"] : z < -2 ? ["Retard de croissance (malnutrition chronique)", "attention"] : z > 3 ? ["Très grande taille : rechercher une cause endocrinienne", "attention"] : ["Normal", "ok"];
  if (ind === "pcAge") return z < -3 ? ["Microcéphalie sévère", "danger"] : z < -2 ? ["Microcéphalie : surveiller le développement", "attention"] : z > 3 ? ["Macrocéphalie sévère : rechercher une hydrocéphalie", "danger"] : z > 2 ? ["Macrocéphalie : surveiller (fontanelle, développement)", "attention"] : ["Normal", "ok"];
  return z < -3 ? ["Émaciation sévère (malnutrition aiguë sévère)", "danger"] : z < -2 ? ["Émaciation (malnutrition aiguë modérée)", "attention"] : z > 3 ? ["Obésité", "danger"] : z > 2 ? ["Surpoids", "attention"] : z > 1 ? ["Risque de surpoids", "ok"] : ["Normal", "ok"];
}
function interpFenton(ind, z) {
  const p = phi(z) * 100;
  if (ind === "pc") return p < 3 ? ["Périmètre crânien < 3e percentile : microcéphalie, rechercher une cause (infection congénitale, asphyxie)", "danger"] : p < 10 ? ["Petit périmètre crânien (< 10e percentile) : surveiller", "attention"] : p > 97 ? ["Périmètre crânien > 97e percentile : rechercher une hydrocéphalie (fontanelle, échographie)", "danger"] : p > 90 ? ["Grand périmètre crânien (> 90e percentile) : surveiller", "attention"] : ["Normal (entre le 10e et le 90e percentile)", "ok"];
  return p < 3 ? ["Très petit pour l'âge gestationnel (< 3e percentile) : retard de croissance sévère, risque d'hypoglycémie et d'hypothermie", "danger"] : p < 10 ? ["Petit pour l'âge gestationnel (< 10e percentile) : hypotrophie, surveiller glycémie, température et alimentation", "attention"] : p > 97 ? ["Très gros pour l'âge gestationnel (> 97e percentile) : rechercher un diabète maternel, surveiller la glycémie", "attention"] : p > 90 ? ["Gros pour l'âge gestationnel (> 90e percentile) : surveiller la glycémie", "attention"] : ["Eutrophe (entre le 10e et le 90e percentile)", "ok"];
}
function graphique(t, x, v, zl, coul) {
  const W = 560, H = 260, g = 40, b = 28;
  const x0 = t[0][0], x1 = t[t.length - 1][0];
  const ys = t.flatMap((p) => [valZ(p, zl[0]), valZ(p, zl[zl.length - 1])]).concat([v]);
  const y0 = Math.min(...ys) * 0.97, y1 = Math.max(...ys) * 1.03;
  const X = (a) => g + (a - x0) / (x1 - x0) * (W - g - 10), Y = (a) => H - b - (a - y0) / (y1 - y0) * (H - b - 10);
  const pas = Math.max(1, Math.floor(t.length / 120));
  const ligne = (z) => t.filter((_, i) => i % pas === 0 || i === t.length - 1).map((p, i) => `${i ? "L" : "M"}${X(p[0]).toFixed(1)},${Y(valZ(p, z)).toFixed(1)}`).join("");
  const cl = (z) => Math.abs(z) < 0.01 ? "var(--ok)" : Math.abs(z) > 2.5 || Math.abs(z) > 1.8 && Math.abs(z) < 1.9 ? "var(--danger)" : "var(--attention)";
  const ticks = (a, c, n) => Array.from({ length: n + 1 }, (_, i) => a + (c - a) * i / n);
  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;max-width:640px;background:var(--surface);border-radius:12px;border:1px solid var(--bord)">
    ${ticks(y0, y1, 4).map((a) => `<line x1="${g}" x2="${W - 10}" y1="${Y(a)}" y2="${Y(a)}" stroke="var(--bord)"/><text x="${g - 4}" y="${Y(a) + 4}" font-size="10" text-anchor="end" fill="var(--texte2)">${fmt(a)}</text>`).join("")}
    ${ticks(x0, x1, 6).map((a) => `<text x="${X(a)}" y="${H - 10}" font-size="10" text-anchor="middle" fill="var(--texte2)">${fmt(a)}</text>`).join("")}
    ${zl.map((z) => `<path d="${ligne(z)}" fill="none" stroke="${cl(z)}" stroke-width="${Math.abs(z) < 0.01 ? 2 : 1.3}" opacity=".85"/>`).join("")}
    <circle cx="${X(x)}" cy="${Y(v)}" r="6" fill="${coul}" stroke="#fff" stroke-width="2"/></svg>`;
}
let etatCr = { mode: "oms", sexe: "garcon" };
async function croissance() {
  const [oms, fen] = await Promise.all([normes("oms"), normes("fenton")]);
  const champ = (k, l, u, aide, val = "") => `<label class="champ">${l}${u ? ` (${u})` : ""}<input id="c_${k}" inputmode="decimal" value="${esc(etatCr[k] ?? val)}">${aide ? `<span class="petit">${aide}</span>` : ""}</label>`;
  const puce = (k, v, l) => `<button class="puce${etatCr[k] === v ? " actif" : ""}" data-k="${k}" data-v="${v}">${l}</button>`;
  const fenton = etatCr.mode === "fenton";
  contenu.innerHTML = `<h1>📈 Courbes de croissance</h1><p class="sous">${fenton ? "Prématurés : courbes de Fenton (22 à 50 semaines d'âge post-menstruel)" : "Normes OMS, de la naissance à 5 ans"}</p>
    <div class="puces">${puce("mode", "oms", "Enfant 0–5 ans (OMS)")}${puce("mode", "fenton", "Prématuré (Fenton)")}</div>
    <div class="puces">${puce("sexe", "garcon", "Garçon")}${puce("sexe", "fille", "Fille")}</div>
    <div class="grille" style="grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:0 16px">
    ${fenton ? champ("sa", "Âge post-menstruel", "semaines", "22 à 50") + champ("j", "Jours en plus", "0–6", "") + champ("pg", "Poids", "g", "") + champ("lf", "Longueur", "cm", "") + champ("pcf", "Périmètre crânien", "cm", "")
             : champ("age", "Âge", "mois", "Ex. 7,5 pour 7 mois et demi") + champ("terme", "Terme de naissance (facultatif)", "SA", "Âge corrigé jusqu'à 24 mois") + champ("p", "Poids", "kg", "", sto.get("poids", "")) + champ("t", "Longueur ou taille", "cm", "Couché avant 2 ans") + champ("pc", "Périmètre crânien (facultatif)", "cm", "")}
    </div><div id="resCr"></div>
    <p class="petit">${fenton ? "Courbes : 3e, 10e, 50e, 90e et 97e percentiles. Source : Fenton TR et al., courbes de croissance des prématurés de 3e génération (2025), Université de Calgary, licence CC BY-NC-ND 4.0." : "Z-score : écart à la médiane de référence OMS (−2 à +2 : zone normale). Courbes −3, −2, 0, +2, +3. Source : OMS, Normes de croissance de l'enfant (2006)."}</p>`;
  contenu.querySelectorAll("[data-k]").forEach((b) => b.addEventListener("click", () => { etatCr[b.dataset.k] = b.dataset.v; croissance(); }));
  const calc = () => {
    contenu.querySelectorAll("input[id^=c_]").forEach((i) => (etatCr[i.id.slice(2)] = i.value));
    const n = (k, a, c) => { const v = nombre(etatCr[k]); return v != null && v >= a && v <= c ? v : null; };
    const res = [];
    if (fenton) {
      const sa = n("sa", 22, 50), j = n("j", 0, 6) || 0, age = sa != null ? Math.min(Math.floor(sa) + j / 7, 50) : null;
      const T = fen.indicateurs[etatCr.sexe];
      const aj = (ind, titre, u, v) => { if (age == null || v == null) return; const l = lmsA(T[ind], age); if (!l) return; const z = zScore(l, v, false); res.push({ titre, u, v, z, x: age, t: T[ind], i: interpFenton(ind, z), f: true, axe: "semaines" }); };
      aj("poids", "Poids", "g", n("pg", 200, 8000)); aj("longueur", "Longueur", "cm", n("lf", 20, 70)); aj("pc", "Périmètre crânien", "cm", n("pcf", 15, 50));
    } else {
      const am = n("age", 0, 60), sa = n("terme", 22, 42);
      const ac = am != null && sa != null && sa < 37 && am < 24 ? Math.max(am - (40 - sa) * 7 / 30.4375, 0) : am;
      const T = oms.indicateurs[etatCr.sexe], p = n("p", 0.3, 60), h = n("t", 30, 130), c = n("pc", 20, 60);
      const aj = (ind, titre, u, axe, x, v, r) => { if (x == null || v == null || !T[ind]) return; const l = lmsA(T[ind], x); if (!l) return; const z = zScore(l, v, r); res.push({ titre, u, v, z, x, t: T[ind], i: interpOms(ind, z), axe }); };
      aj("poidsAge", "Poids pour l'âge", "kg", "âge (mois)", ac, p, true);
      aj("tailleAge", "Taille pour l'âge", "cm", "âge (mois)", ac, h, false);
      if (ac != null && ac < 24) aj("poidsTaille02", "Poids pour la longueur", "kg", "longueur (cm)", h, p, true); else aj("poidsTaille25", "Poids pour la taille", "kg", "taille (cm)", h, p, true);
      if (p != null && h != null) aj("imcAge", "IMC pour l'âge", "kg/m²", "âge (mois)", ac, p / (h / 100) ** 2, true);
      aj("pcAge", "Périmètre crânien pour l'âge", "cm", "âge (mois)", ac, c, false);
      if (ac != null && am != null && Math.abs(ac - am) > 0.01) res.unshift({ info: `Âge corrigé utilisé : ${fmt(ac)} mois` });
    }
    $("#resCr").innerHTML = res.length ? res.map((r) => r.info ? `<p><b style="color:var(--primaire)">${r.info}</b></p>` : `<div class="fiche" style="margin:14px 0">
        <div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap"><b>${r.titre} : ${fmt(r.v)} ${r.u}</b><span class="badge" style="color:#fff;background:${COUL[r.i[1]]}">${r.f ? texteCentile(r.z) : "z = " + texteZ(r.z)}</span></div>
        <div style="color:${COUL[r.i[1]]};font-weight:600;margin:6px 0">${esc(r.i[0])}</div>
        ${graphique(r.t, r.x, r.v, r.f ? [-1.8808, -1.2816, 0, 1.2816, 1.8808] : [-3, -2, 0, 2, 3], COUL[r.i[1]])}
        <div class="petit">${r.f ? `z = ${texteZ(r.z)} · ` : ""}axe horizontal : ${r.axe}</div></div>`).join("")
      : `<p class="petit">Saisissez le sexe, l'âge et au moins une mesure.</p>`;
  };
  contenu.querySelectorAll("input[id^=c_]").forEach((i) => i.addEventListener("input", calc));
  calc();
}

// ---------------------------------------------------------------------------
// Quiz
// ---------------------------------------------------------------------------
function quiz(_r, theme) {
  const themes = D.themesQuiz || [];
  const th = themes.find((t) => t.id === theme);
  if (!theme) {
    const meilleur = sto.get("quiz-scores", {});
    contenu.innerHTML = `<h1>❓ Quiz</h1><p class="sous">${(D.quiz || []).length} questions pour réviser, par thème</p>
      <div class="grille"><a class="tuile" href="#/quiz/tout"><span class="ico" style="background:#00695C22">🎲</span><b>Tous les thèmes</b><span class="petit">10 questions au hasard</span></a>
      ${themes.map((t) => { const n = D.quiz.filter((q) => q.theme === t.id).length; return n ? `<a class="tuile" href="#/quiz/${encodeURIComponent(t.id)}"><span class="ico" style="background:${esc(t.couleur)}22">${esc(t.icone)}</span><b>${esc(t.nom)}</b><span class="petit">${n} questions${meilleur[t.id] != null ? ` · meilleur score ${meilleur[t.id]} %` : ""}</span></a>` : ""; }).join("")}</div>`;
    return;
  }
  const qs = (theme === "tout" ? D.quiz : D.quiz.filter((q) => q.theme === theme)).map((q) => [Math.random(), q]).sort((a, b) => a[0] - b[0]).map((x) => x[1]).slice(0, 10);
  let i = 0, bons = 0;
  const rendre = () => {
    const q = qs[i];
    if (!q) {
      const pc = Math.round(bons / qs.length * 100);
      const m = sto.get("quiz-scores", {}); if (m[theme] == null || pc > m[theme]) { m[theme] = pc; sto.set("quiz-scores", m); }
      contenu.innerHTML = `<p><a href="#/quiz">← Quiz</a></p><div class="fiche" style="text-align:center"><h1>${pc >= 80 ? "🏆" : pc >= 50 ? "👍" : "📚"} ${bons} / ${qs.length}</h1>
        <p>${pc >= 80 ? "Excellent !" : pc >= 50 ? "Bien, continuez à réviser." : "Relisez les fiches de ce thème et réessayez."}</p>
        <button class="bouton" id="rejouer">Rejouer</button> <a class="bouton second" href="#/quiz">Autres thèmes</a></div>`;
      $("#rejouer").addEventListener("click", () => quiz(_r, theme));
      return;
    }
    const p = D.pathoParId[String(q.pathologie)];
    contenu.innerHTML = `<p><a href="#/quiz">← Quiz</a> · ${esc(th?.nom || "Tous les thèmes")}</p><div class="fiche">
      <div class="petit">Question ${i + 1} / ${qs.length} · score ${bons}</div><h2 style="margin-top:8px">${esc(q.question)}</h2>
      ${q.options.map((o, k) => `<button class="choix" data-i="${k}">${esc(o)}</button>`).join("")}<div id="expl"></div></div>`;
    contenu.querySelectorAll("[data-i]").forEach((b) => b.addEventListener("click", () => {
      const k = +b.dataset.i;
      contenu.querySelectorAll("[data-i]").forEach((x) => { x.disabled = true; if (+x.dataset.i === q.bonne) x.classList.add("bon"); });
      if (k === q.bonne) bons++; else b.classList.add("faux");
      $("#expl").innerHTML = `<p>${k === q.bonne ? "✅ <b>Bonne réponse.</b>" : "❌ <b>Pas tout à fait.</b>"} ${esc(q.explication)}</p>
        ${p ? `<p class="petit"><a href="#/patho/${p.id}">Revoir la fiche « ${esc(p.nom)} »</a></p>` : ""}<button class="bouton" id="suiv">${i + 1 < qs.length ? "Question suivante" : "Voir le résultat"}</button>`;
      $("#suiv").addEventListener("click", () => { i++; rendre(); });
    }));
  };
  rendre();
}

demarrer();

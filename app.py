"""
Phoenix Environmental Labs - Chain of Custody trainer  (mobile-first)
====================================================================
Two modes:
  * CoC Generator - random chain of custody + the containers you'd grab.
  * Quiz          - drills all analysis->container pairings with scoring,
                    streaks, running accuracy, coverage, and miss-weighting.

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""

import os
import random
import datetime as dt
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "images")

# --------------------------------------------------------------------------- #
#  Reference data                                                             #
# --------------------------------------------------------------------------- #
PRESERVATIVE_DOT = {
    "AS IS":     ("#ffffff", "#333333"),
    "HNO3":      ("#d1202f", "#ffffff"),
    "H2SO4":     ("#f2c200", "#333333"),
    "HCL":       ("#8f7fd4", "#ffffff"),
    "NAOH":      ("#1f2f6e", "#ffffff"),
    "Na2S2O3":   ("#3aa0e0", "#ffffff"),
    "NAHSO4":    ("#b0a99a", "#333333"),
    "H3PO4":     ("#b0a99a", "#333333"),
    "NH4CL":     ("#b0a99a", "#333333"),
    "C6H7KO7":   ("#b0a99a", "#333333"),
    "AA,K Citrate,EDTA": ("#b0a99a", "#333333"),
    "Methanol / DI Water": ("#8a8a8a", "#ffffff"),
    "None (Summa vacuum)": ("#cfcfcf", "#333333"),
}

CONTAINERS = {
    "soil_clear_jars":    ("Clear Glass Soil Jar (4 / 8 / 32 oz)", "soil_clear_jars.png",
                           "Wide-mouth clear glass jar for soils and solids."),
    "soil_amber_jars":    ("Amber Glass Soil Jar (4 / 8 oz)", "soil_amber_jars.png",
                           "Wide-mouth amber jar for light-sensitive soil analytes."),
    "soil_voa_vials":     ("40 mL Soil VOA Vials (Methanol + DI Water)", "soil_voa_vials.png",
                           "Pre-preserved vials for soil volatiles."),
    "pl_asis_bottles":    ("Plastic (PL) Bottle (120 / 250 / 500 / 1000 mL)", "pl_asis_bottles.png",
                           "White HDPE bottle. Preservative depends on the label."),
    "amber_glass_1l":     ("1 L Amber Glass (Narrow Neck / Wide Mouth)", "amber_glass_1l.png",
                           "Amber glass liter for extractable organics."),
    "amber_boston_round": ("Amber Boston Round (4 / 8 oz)", "amber_boston_round.png",
                           "Small amber glass bottle."),
    "amber_voa_60ml":     ("60 mL Amber VOA Vials", "amber_voa_60ml.png",
                           "Amber septum vials for light-sensitive volatiles."),
    "clear_voa_40ml":     ("40 mL Clear VOA Vials", "clear_voa_40ml.png",
                           "Clear septum vials, no preservative."),
    "hcl_vials_40ml":     ("40 mL Clear VOA Vials, HCl-preserved", "hcl_vials_40ml.png",
                           "Clear VOA vials with HCl (purple dot)."),
    "bacteria_thio":      ("120 mL Sterile Bottle w/ Thio (blue dot)", "bacteria_thio.png",
                           "Sterile bottle with Na2S2O3 to neutralize chlorine."),
    "bacteria_asis":      ("120 mL Sterile Bottle, As-Is", "bacteria_asis.png",
                           "Sterile bottle, no dechlorination."),
    "summa_canister":     ("Summa Canister + Flow Controller", None,
                           "Evacuated stainless canister for TO-15 / APH air sampling."),
}

ANALYSES = [
    ("EPA 504.1  EDB / DBCP",            "Water", "AS IS",   "clear_voa_40ml"),
    ("EPA 508  Chlorinated Pesticides",  "Water", "AS IS",   "amber_glass_1l"),
    ("EPA 515  Chlorinated Herbicides",  "Water", "AS IS",   "amber_glass_1l"),
    ("EPA 524.2  Volatile Organics",     "Water", "HCL",     "hcl_vials_40ml"),
    ("EPA 525.2  SVOCs / Pesticides",    "Water", "AA,K Citrate,EDTA", "amber_glass_1l"),
    ("EPA 531.1  Carbamates",            "Water", "C6H7KO7", "amber_glass_1l"),
    ("EPA 547  Glyphosate",              "Water", "Na2S2O3", "amber_glass_1l"),
    ("EPA 548.1  Endothall",             "Water", "Na2S2O3", "amber_glass_1l"),
    ("EPA 549.2  Diquat / Paraquat",     "Water", "Na2S2O3", "pl_asis_bottles"),
    ("HAA5  Haloacetic Acids",           "Water", "NH4CL",   "amber_glass_1l"),
    ("Total Organic Carbon (TOC)",       "Water", "H3PO4",   "amber_boston_round"),
    ("Phenolics / TOX",                  "Water", "H2SO4",   "amber_glass_1l"),
    ("1,4-Dioxane",                      "Water", "NAHSO4",  "amber_voa_60ml"),
    ("Total Metals (EPA 200.8)",         "Water", "HNO3",    "pl_asis_bottles"),
    ("Total Cyanide",                    "Water", "NAOH",    "pl_asis_bottles"),
    ("Nutrients (Ammonia / TKN / TP)",   "Water", "H2SO4",   "pl_asis_bottles"),
    ("Nitrate / Nitrite",                "Water", "AS IS",   "pl_asis_bottles"),
    ("Gen Chem (Alk / Hardness / Cl / SO4)", "Water", "AS IS", "pl_asis_bottles"),
    ("VOCs (EPA 8260)",                  "Soil", "Methanol / DI Water", "soil_voa_vials"),
    ("SVOCs (EPA 8270)",                 "Soil", "AS IS",   "soil_amber_jars"),
    ("PAHs (EPA 8270-SIM)",              "Soil", "AS IS",   "soil_amber_jars"),
    ("Pesticides / PCBs (8081 / 8082)",  "Soil", "AS IS",   "soil_amber_jars"),
    ("TPH / EPH (petroleum)",            "Soil", "AS IS",   "soil_amber_jars"),
    ("RCRA-8 Metals",                    "Soil", "AS IS",   "soil_clear_jars"),
    ("Gen Soil (pH / Moisture / Solids)","Soil", "AS IS",   "soil_clear_jars"),
    ("Total Coliform / E. coli (chlorinated)",     "Bacteria", "Na2S2O3", "bacteria_thio"),
    ("Total Coliform / E. coli (non-chlorinated)", "Bacteria", "AS IS",   "bacteria_asis"),
    ("TO-15  VOCs in Air",               "Air", "None (Summa vacuum)", "summa_canister"),
    ("APH  Air-Phase Hydrocarbons",      "Air", "None (Summa vacuum)", "summa_canister"),
]

CANISTERS = [("6.0 L", (3.0, 3.3), "24 hr"), ("1.4 L", (70, 80), "15 min")]

COMPANIES = ["Castleton Environmental Geological Svcs", "Green Ledge Consulting",
             "TerraProbe LLC", "BlueRock Geosciences", "Atlas Site Services Inc.",
             "Northeast Enviro Group", "Granite State Drilling & Testing"]
SAMPLERS  = ["J. Ferngren", "M. Alvarez", "T. Okafor", "S. Petrov", "R. Nguyen",
             "D. Callahan", "K. Whitmore", "L. Bianchi"]
PROJECTS  = ["Former Gas Station RI-04", "Elm St. Redevelopment", "Harbor Marine Terminal",
             "Route 9 Widening", "Old Mill Brownfield", "Cedar Pond Landfill",
             "Downtown Parcel B", "Riverside Housing Ph. II"]
CITIES    = ["Providence, RI", "Manchester, CT", "Babylon, NY", "Worcester, MA",
             "New Haven, CT", "Warwick, RI", "Springfield, MA"]
PREFIX = {
    "Water":    ["MW-", "GW-", "B-", "TB-", "DUP-", "SW-", "TAP-"],
    "Soil":     ["SB-", "B-", "TP-", "SS-", "GP-"],
    "Bacteria": ["TAP-", "WELL-", "DW-", "KIT-"],
    "Air":      ["IA-", "SG-", "AA-", "SS-"],
}
MATRICES = ["All", "Water", "Soil", "Bacteria", "Air"]


def _pick_analyses(matrix, n):
    pool = [a for a in ANALYSES if (matrix == "All" or a[1] == matrix)]
    random.shuffle(pool)
    rows = []
    while len(rows) < n:
        if not pool:
            pool = [a for a in ANALYSES if (matrix == "All" or a[1] == matrix)]
            random.shuffle(pool)
        rows.append(pool.pop())
    return rows


def generate_coc(matrix="All", n=5):
    picks = _pick_analyses(matrix, n)
    base_date = dt.date.today() - dt.timedelta(days=random.randint(0, 20))
    company = random.choice(COMPANIES)
    header = {
        "form": "AIR ANALYSES" if matrix == "Air" else "CT / MA / RI",
        "customer": company, "report_to": random.choice(SAMPLERS),
        "project": random.choice(PROJECTS), "address": random.choice(CITIES),
        "sampled_by": random.choice(SAMPLERS), "po": f"PO-{random.randint(1000, 9999)}",
        "quote": f"Q{random.randint(20000, 39999)}", "date": base_date.strftime("%m/%d/%Y"),
        "temp": f"{random.uniform(1.5, 5.9):.1f}", "cooler": random.choice(["Yes", "Yes", "No"]),
        "coolant": random.choice(["ICE", "IPK", "ICE"]),
    }
    rows, counts = [], {}
    for i, (name, amx, pres, ckey) in enumerate(picks, start=1):
        row_mx = amx if amx != "All" else matrix
        pfx = random.choice(PREFIX.get(row_mx, ["S-"]))
        counts[pfx] = counts.get(pfx, 0) + 1
        sid = f"{pfx}{counts[pfx]:02d}"
        t = (dt.datetime.combine(base_date, dt.time(8, 0))
             + dt.timedelta(minutes=random.randint(0, 480)))
        row = {"n": i, "sample_id": sid, "matrix": row_mx, "time": t.strftime("%H:%M"),
               "analysis": name, "preservative": pres, "container_key": ckey,
               "qty": random.randint(1, 3)}
        if row_mx == "Air":
            size, frange, dur = random.choice(CANISTERS)
            row.update({"canister_id": f"{random.randint(100, 29999)}", "size": size,
                        "flow_id": f"{random.randint(1000, 10999)}",
                        "flow_set": (f"{random.uniform(*frange):.0f}" if frange[1] > 10
                                     else f"{random.uniform(*frange):.2f}"),
                        "duration": dur})
        rows.append(row)
    return {"header": header, "rows": rows, "matrix": matrix}


# --------------------------------------------------------------------------- #
#  Rendering helpers                                                          #
# --------------------------------------------------------------------------- #
def dot_html(pres):
    bg, fg = PRESERVATIVE_DOT.get(pres, ("#b0a99a", "#333"))
    border = "#999" if bg.lower() == "#ffffff" else bg
    return (f'<span style="display:inline-block;min-width:18px;height:18px;'
            f'padding:0 6px;border-radius:9px;background:{bg};color:{fg};'
            f'border:1.5px solid {border};font-size:11px;line-height:18px;'
            f'text-align:center;font-weight:700;">{pres}</span>')


COC_CSS = """
<style>
.pcoc{font-family:Georgia,'Times New Roman',serif;color:#14346b;background:#fffdf8;
      border:2px solid #5f1a1c;border-radius:4px;overflow:hidden;margin:4px 0 8px;}
.pcoc *{box-sizing:border-box;}
.pcoc .top{border-bottom:2px solid #5f1a1c;padding:10px 12px;display:flex;
           flex-wrap:wrap;gap:8px;justify-content:space-between;align-items:flex-start;}
.pcoc .brand{font-size:20px;font-weight:700;color:#5f1a1c;letter-spacing:.5px;line-height:1;}
.pcoc .brand small{display:block;font-size:9px;font-style:italic;font-weight:400;}
.pcoc .brand .addr{font-size:9px;font-style:normal;color:#5f1a1c;margin-top:2px;}
.pcoc .title{text-align:center;color:#5f1a1c;font-weight:700;font-size:15px;letter-spacing:.5px;}
.pcoc .title small{display:block;font-size:10px;}
.pcoc .phone{font-size:10px;color:#5f1a1c;text-align:center;}
.pcoc .rt{font-size:10px;color:#5f1a1c;text-align:right;}
.pcoc .rt b{color:#14346b;}
.pcoc .info{display:grid;grid-template-columns:1fr 1fr 1fr;gap:3px 14px;padding:8px 12px;
            border-bottom:2px solid #5f1a1c;font-size:12px;}
.pcoc .lab{color:#5f1a1c;font-weight:700;}
.pcoc .val{color:#14346b;border-bottom:1px dotted #b9a;}
.pcoc .tablewrap{overflow-x:auto;-webkit-overflow-scrolling:touch;}
.pcoc table.grid{width:100%;border-collapse:collapse;font-size:12px;min-width:520px;}
.pcoc table.grid th{background:#f3e9e3;color:#5f1a1c;border:1px solid #5f1a1c;
                    padding:4px 3px;font-size:10.5px;line-height:1.1;}
.pcoc table.grid td{border:1px solid #c9b7a8;padding:5px;text-align:center;color:#5f1a1c;}
.pcoc table.grid td.ent{color:#14346b;font-weight:600;}
.pcoc table.grid td.al{text-align:left;}
.pcoc .foot{font-size:10px;color:#8a7f72;padding:6px 12px;border-top:1px solid #c9b7a8;
            font-family:Arial,sans-serif;}
@media (max-width:640px){
  .pcoc .top{flex-direction:column;}
  .pcoc .title,.pcoc .phone,.pcoc .rt{text-align:left;}
  .pcoc .info{grid-template-columns:1fr;}
  .pcoc .tablewrap{overflow-x:visible;}
  .pcoc table.grid{min-width:0;font-size:13px;}
  .pcoc table.grid thead{display:none;}
  .pcoc table.grid tr{display:block;border:1.5px solid #5f1a1c;border-radius:4px;
                      margin:0 8px 8px;padding:2px 0;background:#fff;}
  .pcoc table.grid td{display:flex;justify-content:space-between;align-items:center;
                      gap:12px;text-align:right;border:none;
                      border-bottom:1px dotted #d8c9ba;padding:7px 12px;}
  .pcoc table.grid tr td:last-child{border-bottom:none;}
  .pcoc table.grid td.al{text-align:right;}
  .pcoc table.grid td::before{content:attr(data-label);color:#5f1a1c;font-weight:700;
                      text-align:left;font-family:Arial,sans-serif;font-size:11px;flex:0 0 auto;}
}
</style>
"""


def _cell(label, value, cls=""):
    return f'<td class="{cls}" data-label="{label}">{value}</td>'


def render_coc_html(coc):
    h = coc["header"]
    air = coc["matrix"] == "Air"
    body = ""
    for r in coc["rows"]:
        if air:
            body += "<tr>" + "".join([
                _cell("#", r["n"]), _cell("Sample ID", r["sample_id"], "ent al"),
                _cell("Canister ID", r["canister_id"], "ent"), _cell("Size", r["size"]),
                _cell("Flow Reg ID", r["flow_id"], "ent"),
                _cell("Flow mL/min", r["flow_set"], "ent"),
                _cell("Analysis", r["analysis"], "ent al"), _cell("Duration", r["duration"]),
            ]) + "</tr>"
        else:
            cname = CONTAINERS[r["container_key"]][0]
            body += "<tr>" + "".join([
                _cell("#", r["n"]), _cell("Sample ID", r["sample_id"], "ent al"),
                _cell("Matrix", r["matrix"]), _cell("Time", r["time"], "ent"),
                _cell("Analysis", r["analysis"], "ent al"), _cell("Container", cname, "al"),
                _cell("Preserv.", dot_html(r["preservative"])), _cell("Qty", r["qty"], "ent"),
            ]) + "</tr>"
    if air:
        cols = ("<th>#</th><th>Client Sample ID</th><th>Canister ID</th><th>Size</th>"
                "<th>Flow Reg ID</th><th>Flow<br>mL/min</th><th>Analysis</th><th>Dur.</th>")
    else:
        cols = ("<th>#</th><th>Client Sample ID</th><th>Matrix</th><th>Time<br>Sampled</th>"
                "<th>Analysis Request</th><th>Container</th><th>Pres.</th><th>#</th>")
    return f"""{COC_CSS}
<div class="pcoc">
  <div class="top">
    <div class="brand">PHOENIX<small>Environmental Laboratories, Inc.</small>
      <div class="addr">587 East Middle Turnpike, Manchester, CT 06040</div></div>
    <div><div class="title">CHAIN OF CUSTODY RECORD<small>{h['form']}</small></div>
      <div class="phone">Client Services (860)&nbsp;645-1102</div></div>
    <div class="rt">Page 1 of 1<br>Temp <b>{h['temp']} &deg;C</b><br>
      Cooler <b>{h['cooler']}</b> / <b>{h['coolant']}</b></div>
  </div>
  <div class="info">
    <div><span class="lab">Customer:</span> <span class="val">{h['customer']}</span></div>
    <div><span class="lab">Project:</span> <span class="val">{h['project']}</span></div>
    <div><span class="lab">Project P.O.:</span> <span class="val">{h['po']}</span></div>
    <div><span class="lab">Report to:</span> <span class="val">{h['report_to']}</span></div>
    <div><span class="lab">Sampled by:</span> <span class="val">{h['sampled_by']}</span></div>
    <div><span class="lab">Quote #:</span> <span class="val">{h['quote']}</span></div>
    <div><span class="lab">Address:</span> <span class="val">{h['address']}</span></div>
    <div><span class="lab">Date:</span> <span class="val">{h['date']}</span></div>
    <div><span class="lab">Invoice to:</span> <span class="val">{h['customer']}</span></div>
  </div>
  <div class="tablewrap">
    <table class="grid"><thead><tr>{cols}</tr></thead><tbody>{body}</tbody></table>
  </div>
  <div class="foot">Auto-generated practice CoC &mdash; fictional project data.
    Container / preservative pairings follow the Phoenix reference binder.</div>
</div>
"""


def img_path(key):
    fn = CONTAINERS[key][1]
    if not fn:
        return None
    p = os.path.join(IMG_DIR, fn)
    return p if os.path.exists(p) else None


# --------------------------------------------------------------------------- #
#  Quiz engine                                                                #
# --------------------------------------------------------------------------- #
def scope_indices(scope):
    return [i for i, a in enumerate(ANALYSES) if scope == "All" or a[1] == scope]


def init_quiz():
    st.session_state.setdefault("qstats", {i: {"seen": 0, "wrong": 0} for i in range(len(ANALYSES))})
    st.session_state.setdefault("qscore", {"correct": 0, "total": 0})
    st.session_state.setdefault("qstreak", 0)
    st.session_state.setdefault("qbest", 0)
    st.session_state.setdefault("qnum", 0)
    st.session_state.setdefault("qcur", None)


def reset_quiz():
    st.session_state.qstats = {i: {"seen": 0, "wrong": 0} for i in range(len(ANALYSES))}
    st.session_state.qscore = {"correct": 0, "total": 0}
    st.session_state.qstreak = 0
    st.session_state.qbest = 0
    st.session_state.qnum = 0
    st.session_state.qcur = None


def pick_next(scope, exclude=None):
    """Unseen first (guarantees coverage), then weight by how often missed."""
    idxs = scope_indices(scope)
    stats = st.session_state.qstats
    unseen = [i for i in idxs if stats[i]["seen"] == 0]
    if unseen:
        return random.choice(unseen)
    weights = [1 + 3 * stats[i]["wrong"] for i in idxs]
    for _ in range(6):
        choice = random.choices(idxs, weights=weights, k=1)[0]
        if choice != exclude or len(idxs) == 1:
            return choice
    return choice


def make_options(correct_key, air):
    pool = [k for k in CONTAINERS if k != correct_key]
    if not air:
        pool = [k for k in pool if k != "summa_canister"]
    distractors = random.sample(pool, min(3, len(pool)))
    opts = [correct_key] + distractors
    random.shuffle(opts)
    return opts


def new_question(scope):
    exclude = st.session_state.qcur["idx"] if st.session_state.qcur else None
    idx = pick_next(scope, exclude)
    air = ANALYSES[idx][1] == "Air"
    st.session_state.qnum += 1
    st.session_state.qcur = {"idx": idx, "options": make_options(ANALYSES[idx][3], air),
                             "answered": False, "chosen": None, "nonce": st.session_state.qnum}


# --------------------------------------------------------------------------- #
#  Streamlit UI                                                               #
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="Phoenix CoC Trainer", page_icon="🧪",
                   layout="centered", initial_sidebar_state="collapsed")
st.markdown("""
<style>
  .block-container{padding-top:1.1rem;padding-bottom:3rem;max-width:820px;}
  h1{color:#5f1a1c;font-family:Georgia,serif;margin-bottom:.1rem;}
  div[data-testid="stImage"] img{border-radius:8px;border:1px solid #e4ddce;}
  hr{margin:.6rem 0;}
  div[data-testid="stMetric"]{background:#faf6ee;border:1px solid #e4d9c6;
       border-radius:8px;padding:6px 4px;text-align:center;}
</style>
""", unsafe_allow_html=True)

st.markdown("# Phoenix CoC &amp; Bottle Trainer", unsafe_allow_html=True)
init_quiz()
mode = st.radio("Mode", ["🎲 CoC Generator", "🎯 Quiz"], horizontal=True,
                label_visibility="collapsed")

# =========================== GENERATOR MODE ================================= #
if mode == "🎲 CoC Generator":
    st.caption("Generate a random chain of custody, then see the containers you'd grab.")
    c1, c2 = st.columns(2)
    with c1:
        matrix = st.selectbox("Matrix", MATRICES)
    with c2:
        n = st.slider("Sample lines", 1, 10, 5)
    go = st.button("🔄 Generate new CoC", use_container_width=True, type="primary")

    key = (matrix, n)
    if go or "coc" not in st.session_state or st.session_state.get("key") != key:
        st.session_state.coc = generate_coc(matrix, n)
        st.session_state.key = key
    coc = st.session_state.coc

    st.markdown(render_coc_html(coc), unsafe_allow_html=True)
    st.markdown("### Containers to grab")
    groups = {}
    for r in coc["rows"]:
        g = groups.setdefault(r["container_key"], {"pres": set(), "lines": []})
        g["pres"].add(r["preservative"])
        g["lines"].append(f"{r['sample_id']} — {r['analysis']} ×{r['qty']}")
    for ckey, info in groups.items():
        name, fn, desc = CONTAINERS[ckey]
        st.markdown(f"**{name}**")
        st.markdown("Preservative: " + " ".join(dot_html(p) for p in sorted(info["pres"])),
                    unsafe_allow_html=True)
        p = img_path(ckey)
        if p:
            st.image(p, use_container_width=True)
        else:
            st.info("📷 No photo on file — " + desc)
        st.caption(desc + "  \nUsed for: " + "; ".join(info["lines"]))
        st.divider()

# ============================== QUIZ MODE =================================== #
else:
    st.caption("Which container do you grab? Unseen pairings come first; the ones "
               "you miss come back more often.")
    scope = st.selectbox("Drill", MATRICES, key="qscope")

    idxs = scope_indices(scope)
    stats = st.session_state.qstats
    score = st.session_state.qscore
    seen = sum(1 for i in idxs if stats[i]["seen"] > 0)
    review = sum(1 for i in idxs if stats[i]["wrong"] > 0)
    acc = (score["correct"] / score["total"] * 100) if score["total"] else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Score", f"{score['correct']}/{score['total']}")
    m2.metric("Accuracy", f"{acc:.0f}%")
    m3.metric("Streak", st.session_state.qstreak, f"best {st.session_state.qbest}",
              delta_color="off")
    m4.metric("Seen", f"{seen}/{len(idxs)}")
    st.progress(seen / len(idxs) if idxs else 0,
                text=f"Coverage — {seen}/{len(idxs)} pairings seen"
                     + (f" · {review} to review" if review else ""))

    # make sure there's a question in the current scope
    if st.session_state.qcur is None or st.session_state.qcur["idx"] not in idxs:
        new_question(scope)
    q = st.session_state.qcur
    name, amx, pres, correct_key = ANALYSES[q["idx"]]

    st.markdown(
        f"<div style='background:#fffdf8;border:2px solid #5f1a1c;border-radius:8px;"
        f"padding:12px 14px;margin:6px 0 10px;font-family:Georgia,serif;'>"
        f"<div style='font-size:11px;color:#8a7f72;letter-spacing:.05em'>"
        f"CoC LINE &middot; {amx.upper()}</div>"
        f"<div style='font-size:19px;color:#14346b;font-weight:700;margin-top:2px'>{name}</div>"
        f"<div style='font-size:13px;color:#5f1a1c;margin-top:4px'>"
        f"Which container do you grab?</div></div>", unsafe_allow_html=True)

    if not q["answered"]:
        for i, ckey in enumerate(q["options"]):
            if st.button(CONTAINERS[ckey][0], key=f"opt{q['nonce']}_{i}",
                         use_container_width=True):
                q["answered"] = True
                q["chosen"] = ckey
                stats[q["idx"]]["seen"] += 1
                score["total"] += 1
                if ckey == correct_key:
                    score["correct"] += 1
                    st.session_state.qstreak += 1
                    st.session_state.qbest = max(st.session_state.qbest,
                                                 st.session_state.qstreak)
                else:
                    stats[q["idx"]]["wrong"] += 1
                    st.session_state.qstreak = 0
                st.rerun()
    else:
        right = q["chosen"] == correct_key
        if right:
            st.success("✅ Correct!")
        else:
            st.error(f"❌ You picked {CONTAINERS[q['chosen']][0]}")
        cname, cfn, cdesc = CONTAINERS[correct_key]
        st.markdown(f"**Answer: {cname}**")
        st.markdown("Preservative: " + dot_html(pres), unsafe_allow_html=True)
        p = img_path(correct_key)
        if p:
            st.image(p, use_container_width=True)
        else:
            st.info("📷 No photo on file — " + cdesc)
        st.caption(cdesc)
        if st.button("Next question →", use_container_width=True, type="primary"):
            new_question(scope)
            st.rerun()

    st.divider()
    st.button("↺ Reset score & progress", on_click=reset_quiz)

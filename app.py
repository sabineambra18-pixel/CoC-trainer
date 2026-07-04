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
    "NaOH/Zinc Acetate": ("#1f2f6e", "#ffffff"),
    "Na2S2O3":   ("#3aa0e0", "#ffffff"),
    "NAHSO4":    ("#b0a99a", "#333333"),
    "H3PO4":     ("#b0a99a", "#333333"),
    "NH4CL":     ("#b0a99a", "#333333"),
    "C6H7KO7":   ("#b0a99a", "#333333"),
    "AA,K Citrate,EDTA": ("#b0a99a", "#333333"),
    "Methanol / DI Water": ("#8a8a8a", "#ffffff"),
    "Methanol": ("#8a8a8a", "#ffffff"),
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

# Plain-English "what usually goes in this container" (shown on a correct answer)
CONTAINER_CONTENTS = {
    "soil_clear_jars":
        "Phoenix's go-to 4 oz clear glass jar for most soil tests — metals, "
        "semi-volatiles, pesticides/PCBs, petroleum, and general soil chemistry. "
        "Pack it full with as little air as possible.",
    "soil_amber_jars":
        "Amber glass soil jar used for certain light-sensitive petroleum work "
        "(like Massachusetts EPH). The dark glass keeps light out.",
    "soil_voa_vials":
        "Small plugs of soil for volatile chemicals (gasoline-type vapors). They "
        "come pre-filled with methanol or water to lock the vapors in the moment "
        "you add the soil.",
    "pl_asis_bottles":
        "Water. Plain plastic bottles for general water chemistry, and — with the "
        "right preservative already added — for metals, nutrients, and cyanide.",
    "amber_glass_1l":
        "About a liter of water for extractable organics — pesticides, herbicides, "
        "PCBs and similar. Amber glass protects the light-sensitive compounds.",
    "amber_boston_round":
        "A small pour of water for tests like TOC. Amber glass again for light "
        "protection.",
    "amber_voa_60ml":
        "Water for light-sensitive volatile-type analyses (e.g., 1,4-dioxane). "
        "Amber vial with a septum cap, filled to the top with no air bubble.",
    "clear_voa_40ml":
        "Water for volatile chemicals when light isn't a concern. Small septum-cap "
        "vial filled right to the top — zero headspace, no bubble.",
    "hcl_vials_40ml":
        "The same 40 mL water VOA vial, but pre-dosed with a little hydrochloric "
        "acid to hold the volatiles (EPA 524). Fill with no bubble.",
    "bacteria_thio":
        "Drinking water for bacteria tests. Sterile bottle with a dab of sodium "
        "thiosulfate (the blue dot) that neutralizes chlorine so it stops killing "
        "bacteria before the lab can count them.",
    "bacteria_asis":
        "Water for bacteria tests when there's no chlorine to worry about. Sterile "
        "bottle, nothing added.",
    "summa_canister":
        "Air. An evacuated stainless-steel canister that slowly pulls in an air "
        "sample over the sampling period (e.g., 24 hours) through a flow controller.",
}

# Plain-English "what is this test and why would they run it" (shown when correct)
ANALYSIS_INFO = {
    "Volatiles (VOC, EPA 8260/624)":
        "Solvents and fuel chemicals that evaporate easily (benzene, TCE); common at gas stations and dry cleaners and harmful to drink or breathe.",
    "1,4-Dioxane (by 8260)":
        "A stubborn industrial solvent additive found in groundwater; the 8260 version is run in acid-preserved VOA vials.",
    "EDB / DBCP":
        "Two old farm fumigants linked to cancer that can seep into groundwater.",
    "Trihalomethanes (THMs)":
        "Byproducts of chlorinating water; watched because long-term exposure is a health concern.",
    "TPH-GRO / VPH (gasoline range)":
        "Gasoline-range petroleum in water; volatile, so it goes in acid-preserved VOA vials.",
    "1,4-Dioxane (low level, 522/8270)":
        "The trace-level 1,4-dioxane method; needs NaHSO4 preservative and goes in an 8 oz amber glass bottle, NOT a VOA vial.",
    "Phenolics":
        "Industrial pollution-indicator chemicals; acid-preserved in amber glass.",
    "TOC (Total Organic Carbon)":
        "How much carbon-based material is in the water; high levels feed bacteria and form disinfection byproducts.",
    "TOX":
        "Total organic halogens — a broad flag for chlorinated-organic contamination.",
    "Haloacetic Acids (HAA5)":
        "Disinfection byproducts formed when chlorine reacts with natural matter; a health concern over time.",
    "Semi-Volatiles (SVOC, 8270)":
        "Heavier organic pollutants including PAHs; a broad screen at contaminated sites.",
    "Pesticides":
        "Bug-killing chemicals that can wash into water and linger.",
    "Herbicides":
        "Weed-killer chemicals from lawns and farms that can reach water supplies.",
    "PCBs":
        "Banned industrial oils that persist for decades and are toxic.",
    "EPH (extractable petroleum)":
        "Diesel/oil-range petroleum in water; acid-preserved and collected in amber liter bottles.",
    "ETPH / TPH-DRO (diesel range)":
        "Diesel-range petroleum measure for oil/fuel contamination.",
    "Oil & Grease":
        "Total oily material in water, often from industrial or wastewater discharge.",
    "Total Metals":
        "Metals like lead and arsenic that can leach from pipes, soil, or industry; acid-preserved.",
    "Mercury":
        "A highly toxic metal tracked separately; acid-preserved.",
    "Hardness":
        "How 'hard' the water is (calcium/magnesium); acid-preserved for the metals measurement.",
    "Total Cyanide":
        "Highly toxic cyanide from industrial or mining waste; base-preserved with NaOH.",
    "Ammonia":
        "A nitrogen form from sewage or fertilizer; too much signals pollution.",
    "Nitrogen, Total (TKN)":
        "Total nitrogen measure; indicates sewage or fertilizer loading.",
    "Phosphorus / Phosphate":
        "Nutrient that fuels algae blooms; acid-preserved.",
    "Nitrate/Nitrite (combined)":
        "Nitrogen forms from fertilizer or septic systems; acid-preserved when run together.",
    "Nitrate (alone)":
        "High nitrate is dangerous for infants ('blue baby'), so wells are tested; no preservative.",
    "Chloride / Sulfate":
        "Common salts measured for general water quality.",
    "Alkalinity":
        "The water's acid-buffering capacity; a basic quality measure.",
    "Total Suspended / Dissolved Solids":
        "How much solid material is floating in or dissolved in the water.",
    "Bacteria — Coliform / E. coli (chlorinated)":
        "Safety test for waste contamination in chlorinated water; the thio bottle neutralizes chlorine so it stops killing bacteria before they're counted.",
    "Bacteria — Coliform / E. coli (non-chlorinated)":
        "Same safety test for water with no chlorine, like a private well; plain sterile bottle.",
    "Soil Volatiles (VOC, 8260 / 5035)":
        "Evaporating solvents and fuels in soil; captured in methanol and water VOA vials the instant you add the soil.",
    "Soil TPH-GRO / VPH (methanol VOA)":
        "Gasoline-range petroleum in soil; collected in methanol VOA vials to trap the vapors.",
    "Soil Semi-Volatiles (SVOC, 8270)":
        "Heavier organic pollutants in soil, including PAHs. Phoenix collects these in the 4 oz clear glass jar.",
    "Soil Pesticides / PCBs":
        "Old pesticides and banned PCB oils that persist in soil for decades; 4 oz clear glass jar.",
    "Soil Herbicides":
        "Weed-killer residues in soil; 4 oz clear glass jar.",
    "Soil Metals":
        "Toxic metals in soil that determine if it's hazardous and how it must be handled.",
    "Soil EPH / TPH":
        "Oil and fuel content in soil at spill and tank sites; 4 oz clear glass jar.",
    "Soil EPH (Massachusetts)":
        "The Massachusetts petroleum method — the one soil test Phoenix runs in an amber jar, to protect light-sensitive compounds.",
    "Soil pH / Solids / General":
        "Basic soil properties used as background for the other results.",
    "TO-15 (VOCs in Air)":
        "Volatile chemicals in indoor or soil-gas air; tests whether vapors from contamination are seeping into a building.",
    "APH (Air-Phase Hydrocarbons)":
        "Petroleum vapors in air, tested for vapor intrusion from fuel contamination.",
    "TCLP Metals":
        "Leaching test that checks whether a waste will release toxic metals (like lead) into groundwater at a landfill. 500 mL plastic.",
    "TCLP Volatiles":
        "Leaching test for volatile chemicals — decides if a waste is hazardous by how much VOC leaches out. 40 mL VOA vials.",
    "TCLP Semi-Volatiles":
        "Leaching test for heavier organics. 1 L amber glass.",
    "TCLP Pesticides":
        "Leaching test for pesticides. 1 L amber glass.",
    "TCLP Herbicides":
        "Leaching test for herbicides. 1 L amber glass.",
    "Odor":
        "A basic drinking-water check for smell; no preservative.",
    "Turbidity":
        "How cloudy the water is — a basic quality and treatment measure.",
    "UV 254":
        "A quick optical measure of organic material tied to disinfection-byproduct potential; 8 oz amber glass.",
    "Sulfide":
        "Rotten-egg sulfide in water; preserved with NaOH and zinc acetate to hold it.",
    "Sulfite":
        "A treatment-chemical residual measured quickly with no preservative.",
    "Ortho-Phosphate":
        "The dissolved form of phosphorus; a nutrient measure.",
    "Volatile Fatty Acids":
        "Acids that build up in digesters and wastewater; acid-preserved.",
    "Dissolved / Settleable Solids":
        "More solids measures for water quality; plastic, no preservative.",
    "Soil Formaldehyde":
        "Formaldehyde in soil; 4 oz clear glass jar.",
    "Soil Age Dating (petroleum)":
        "Lab 'fingerprinting' to estimate how old a petroleum release is; 4 oz glass jar.",
}


ANALYSES = [
    ("Volatiles (VOC, EPA 8260/624)", "Water", "HCL", "hcl_vials_40ml"),
    ("1,4-Dioxane (by 8260)", "Water", "HCL", "hcl_vials_40ml"),
    ("EDB / DBCP", "Water", "AS IS", "clear_voa_40ml"),
    ("Trihalomethanes (THMs)", "Water", "Na2S2O3", "clear_voa_40ml"),
    ("TPH-GRO / VPH (gasoline range)", "Water", "HCL", "hcl_vials_40ml"),
    ("1,4-Dioxane (low level, 522/8270)", "Water", "NAHSO4", "amber_boston_round"),
    ("Phenolics", "Water", "H2SO4", "amber_boston_round"),
    ("TOC (Total Organic Carbon)", "Water", "H3PO4", "amber_boston_round"),
    ("TOX", "Water", "H2SO4", "amber_boston_round"),
    ("Haloacetic Acids (HAA5)", "Water", "NH4CL", "amber_boston_round"),
    ("Semi-Volatiles (SVOC, 8270)", "Water", "AS IS", "amber_glass_1l"),
    ("Pesticides", "Water", "AS IS", "amber_glass_1l"),
    ("Herbicides", "Water", "AS IS", "amber_glass_1l"),
    ("PCBs", "Water", "AS IS", "amber_glass_1l"),
    ("EPH (extractable petroleum)", "Water", "HCL", "amber_glass_1l"),
    ("ETPH / TPH-DRO (diesel range)", "Water", "AS IS", "amber_glass_1l"),
    ("Oil & Grease", "Water", "H2SO4", "amber_glass_1l"),
    ("Total Metals", "Water", "HNO3", "pl_asis_bottles"),
    ("Mercury", "Water", "HNO3", "pl_asis_bottles"),
    ("Hardness", "Water", "HNO3", "pl_asis_bottles"),
    ("Total Cyanide", "Water", "NAOH", "pl_asis_bottles"),
    ("Ammonia", "Water", "H2SO4", "pl_asis_bottles"),
    ("Nitrogen, Total (TKN)", "Water", "H2SO4", "pl_asis_bottles"),
    ("Phosphorus / Phosphate", "Water", "H2SO4", "pl_asis_bottles"),
    ("Nitrate/Nitrite (combined)", "Water", "H2SO4", "pl_asis_bottles"),
    ("Nitrate (alone)", "Water", "AS IS", "pl_asis_bottles"),
    ("Chloride / Sulfate", "Water", "AS IS", "pl_asis_bottles"),
    ("Alkalinity", "Water", "AS IS", "pl_asis_bottles"),
    ("Total Suspended / Dissolved Solids", "Water", "AS IS", "pl_asis_bottles"),
    ("Bacteria — Coliform / E. coli (chlorinated)", "Bacteria", "Na2S2O3", "bacteria_thio"),
    ("Bacteria — Coliform / E. coli (non-chlorinated)", "Bacteria", "AS IS", "bacteria_asis"),
    ("Soil Volatiles (VOC, 8260 / 5035)", "Soil", "Methanol / DI Water", "soil_voa_vials"),
    ("Soil TPH-GRO / VPH (methanol VOA)", "Soil", "Methanol", "soil_voa_vials"),
    ("Soil Semi-Volatiles (SVOC, 8270)", "Soil", "AS IS", "soil_clear_jars"),
    ("Soil Pesticides / PCBs", "Soil", "AS IS", "soil_clear_jars"),
    ("Soil Herbicides", "Soil", "AS IS", "soil_clear_jars"),
    ("Soil Metals", "Soil", "AS IS", "soil_clear_jars"),
    ("Soil EPH / TPH", "Soil", "AS IS", "soil_clear_jars"),
    ("Soil EPH (Massachusetts)", "Soil", "AS IS", "soil_amber_jars"),
    ("Soil pH / Solids / General", "Soil", "AS IS", "soil_clear_jars"),
    ("TO-15 (VOCs in Air)", "Air", "None (Summa vacuum)", "summa_canister"),
    ("APH (Air-Phase Hydrocarbons)", "Air", "None (Summa vacuum)", "summa_canister"),
    ("TCLP Metals", "TCLP", "AS IS", "pl_asis_bottles"),
    ("TCLP Volatiles", "TCLP", "AS IS", "clear_voa_40ml"),
    ("TCLP Semi-Volatiles", "TCLP", "AS IS", "amber_glass_1l"),
    ("TCLP Pesticides", "TCLP", "AS IS", "amber_glass_1l"),
    ("TCLP Herbicides", "TCLP", "AS IS", "amber_glass_1l"),
    ("Odor", "Water", "AS IS", "pl_asis_bottles"),
    ("Turbidity", "Water", "AS IS", "pl_asis_bottles"),
    ("UV 254", "Water", "AS IS", "amber_boston_round"),
    ("Sulfide", "Water", "NaOH/Zinc Acetate", "pl_asis_bottles"),
    ("Sulfite", "Water", "AS IS", "pl_asis_bottles"),
    ("Ortho-Phosphate", "Water", "AS IS", "pl_asis_bottles"),
    ("Volatile Fatty Acids", "Water", "H2SO4", "pl_asis_bottles"),
    ("Dissolved / Settleable Solids", "Water", "AS IS", "pl_asis_bottles"),
    ("Soil Formaldehyde", "Soil", "AS IS", "soil_clear_jars"),
    ("Soil Age Dating (petroleum)", "Soil", "AS IS", "soil_clear_jars"),
]



# which containers each matrix actually uses (for same-matrix quiz distractors)
CONTAINERS_BY_MATRIX = {}
for _n, _mx, _p, _ck in ANALYSES:
    CONTAINERS_BY_MATRIX.setdefault(_mx, set()).add(_ck)

CANISTERS = [("6.0 L", (3.0, 3.3), "24 hr"), ("1.4 L", (70, 80), "15 min")]

COMPANIES = ["Acme Environmental Inc.", "Testco Labs LLC", "Sample Co. Consulting",
             "Placeholder Geosciences", "Example Site Services", "Fictional Drilling Co.",
             "Demo Environmental Group", "Anytown Testing LLC"]
SAMPLERS  = ["Jane Sampler", "John Doe", "Sam Placeholder", "Alex Example", "Pat Tester",
             "Chris Demo", "Jordan Sample", "Casey Fictional"]
PROJECTS  = ["Sample Project A", "Example Site 1", "Demo Parcel B", "Test Location 2",
             "Placeholder Redevelopment", "Fictional Brownfield", "Anytown Cleanup",
             "Example Landfill"]
CITIES    = ["100 Sample Rd, Anytown, ST 00000", "1 Example Ave, Testville, ST 00000",
             "250 Placeholder St, Demo City, ST 00000", "42 Fictional Ln, Sampleton, ST 00000",
             "500 Test Blvd, Exampleburg, ST 00000", "99 Demo Dr, Anytown, ST 00000",
             "12 Mock St, Placeholderville, ST 00000"]

PREFIX = {
    "Water":    ["MW-", "GW-", "B-", "TB-", "DUP-", "SW-", "TAP-"],
    "Soil":     ["SB-", "B-", "TP-", "SS-", "GP-"],
    "Bacteria": ["TAP-", "WELL-", "DW-", "KIT-"],
    "Air":      ["IA-", "SG-", "AA-", "SS-"],
    "TCLP":     ["W-", "SB-", "B-", "TCLP-"],
}
MATRICES = ["All", "Water", "Soil", "Bacteria", "TCLP", "Air"]


def _pick_analyses(matrix, n):
    def in_scope(a):
        return a[1] == matrix if matrix != "All" else a[1] != "Air"
    pool = [a for a in ANALYSES if in_scope(a)]
    random.shuffle(pool)
    rows = []
    while len(rows) < n:
        if not pool:
            pool = [a for a in ANALYSES if in_scope(a)]
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
    <div class="brand">PEL</div>
    <div><div class="title">CHAIN OF CUSTODY RECORD<small>{h['form']}</small></div></div>
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


# --- full CT/MA/RI form with the real bottle-quantity columns -------------- #
FULL_COLS = [
    ("amber_oz",  "GL Amber<br>( ) oz"),
    ("soil_voa",  "Soil VOA<br>Vials"),
    ("soil_a",    "GL Soil<br>container"),
    ("soil_b",    "GL Soil<br>container"),
    ("voa40",     "40 mL<br>VOA Vial"),
    ("amber1l",   "GL Amber<br>1000 mL"),
    ("pl_asis",   "PL<br>As is"),
    ("pl_h2so4",  "PL<br>H&#8322;SO&#8324;"),
    ("pl_hno3",   "PL<br>HNO&#8323;"),
    ("pl_naoh",   "PL<br>NaOH"),
    ("bact_thio", "Bact.<br>w/thio"),
    ("bact_asis", "Bact.<br>as is"),
]


def form_cell(row):
    """Return (column_id, preservative_note) for how a customer fills this line."""
    ck, pres = row["container_key"], row["preservative"]
    if ck == "amber_boston_round":
        note = pres if pres in ("H3PO4", "NAHSO4", "NH4CL") else pres
        return "amber_oz", note
    if ck == "soil_voa_vials":  return "soil_voa", "MeOH + H\u2082O"
    if ck == "soil_clear_jars": return "soil_a", ""
    if ck == "soil_amber_jars": return "soil_b", ""
    if ck == "clear_voa_40ml":  return "voa40", ("Na\u2082SO\u2083" if pres == "Na2S2O3" else "As is")
    if ck == "hcl_vials_40ml":  return "voa40", "HCL"
    if ck == "amber_glass_1l":  return "amber1l", (pres if pres in ("HCL", "H2SO4") else "As is")
    if ck == "pl_asis_bottles":
        return {"AS IS": "pl_asis", "H2SO4": "pl_h2so4",
                "HNO3": "pl_hno3", "NAOH": "pl_naoh",
                "NaOH/Zinc Acetate": "pl_naoh"}.get(pres, "pl_asis"), ""
    if ck == "bacteria_thio":   return "bact_thio", ""
    if ck == "bacteria_asis":   return "bact_asis", ""
    return None, ""


FULL_CSS = """
<style>
.fcoc{font-family:Georgia,'Times New Roman',serif;color:#14346b;background:#fffdf8;
      border:2px solid #5f1a1c;border-radius:4px;overflow:hidden;margin:4px 0 8px;}
.fcoc *{box-sizing:border-box;}
.fcoc .top{border-bottom:2px solid #5f1a1c;padding:8px 12px;display:flex;
           justify-content:space-between;align-items:flex-start;gap:8px;}
.fcoc .brand{font-size:20px;font-weight:700;color:#5f1a1c;}
.fcoc .title{text-align:center;color:#5f1a1c;font-weight:700;font-size:14px;letter-spacing:.5px;}
.fcoc .title small{display:block;font-size:10px;}
.fcoc .rt{font-size:10px;color:#5f1a1c;text-align:right;}
.fcoc .rt b{color:#14346b;}
.fcoc .info{display:grid;grid-template-columns:1fr 1fr 1fr;gap:2px 14px;padding:7px 12px;
            border-bottom:2px solid #5f1a1c;font-size:12px;}
.fcoc .lab{color:#5f1a1c;font-weight:700;}
.fcoc .val{color:#14346b;border-bottom:1px dotted #b9a;}
.fcoc .scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;}
.fcoc table{border-collapse:collapse;font-size:11px;min-width:900px;width:100%;}
.fcoc th,.fcoc td{border:1px solid #c9b7a8;padding:3px 4px;text-align:center;color:#5f1a1c;}
.fcoc thead th{background:#f3e9e3;border-color:#5f1a1c;font-size:10px;line-height:1.05;
               vertical-align:bottom;}
.fcoc th.lft,.fcoc td.lft{text-align:left;}
.fcoc td.ent{color:#14346b;font-weight:600;}
.fcoc td.bot{color:#14346b;font-weight:700;background:#fdf7ea;}
.fcoc td.bot small{display:block;font-weight:600;color:#8a5a1a;font-size:9px;}
.fcoc .foot{font-size:10px;color:#8a7f72;padding:6px 12px;border-top:1px solid #c9b7a8;
            font-family:Arial,sans-serif;}
</style>
"""


def render_full_coc_html(coc):
    h = coc["header"]
    head_bottle = "".join(f"<th>{lbl}</th>" for _, lbl in FULL_COLS)
    body = ""
    for r in coc["rows"]:
        colid, note = form_cell(r)
        cells = ""
        for cid, _ in FULL_COLS:
            if cid == colid:
                extra = f"<small>{note}</small>" if note else ""
                cells += f'<td class="bot">{r["qty"]}{extra}</td>'
            else:
                cells += "<td></td>"
        body += (f'<tr><td>{r["n"]}</td>'
                 f'<td class="lft ent">{r["sample_id"]}</td>'
                 f'<td>{r["matrix"]}</td>'
                 f'<td class="ent">{r["time"]}</td>'
                 f'<td class="lft ent">{r["analysis"]}</td>'
                 f'{cells}</tr>')
    return f"""{FULL_CSS}
<div class="fcoc">
  <div class="top">
    <div class="brand">PEL</div>
    <div><div class="title">CHAIN OF CUSTODY RECORD<small>CT / MA / RI</small></div></div>
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
  </div>
  <div class="scroll">
    <table>
      <thead><tr>
        <th>#</th><th class="lft">Client Sample ID</th><th>Matrix</th>
        <th>Time<br>Sampled</th><th class="lft">Analysis Request</th>{head_bottle}
      </tr></thead>
      <tbody>{body}</tbody>
    </table>
  </div>
  <div class="foot">Bottle quantities entered per line, the way the lab requires.
    Swipe the grid sideways to see all container columns.</div>
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


def make_options(correct_key, matrix):
    # prefer distractors from the SAME matrix so choices are all plausible
    same = [k for k in CONTAINERS_BY_MATRIX.get(matrix, set()) if k != correct_key]
    random.shuffle(same)
    distractors = same[:2]
    if len(distractors) < 2:  # matrices with few containers (bacteria, air) fill from the rest
        pool = [k for k in CONTAINERS if k != correct_key and k not in distractors]
        if matrix != "Air":
            pool = [k for k in pool if k != "summa_canister"]
        random.shuffle(pool)
        for k in pool:
            distractors.append(k)
            if len(distractors) == 2:
                break
    opts = [correct_key] + distractors
    random.shuffle(opts)
    return opts


def make_quiz_coc(scope, forced_idx):
    """A small CoC whose rows are real analyses, with `forced_idx` placed at a
    random row and flagged. Container/preservative columns are omitted so the
    form can't give away the answer."""
    pool = [i for i in scope_indices(scope) if i != forced_idx]
    random.shuffle(pool)
    others = pool[:random.randint(2, 3)]
    order = others + [forced_idx]
    random.shuffle(order)
    base_date = dt.date.today() - dt.timedelta(days=random.randint(0, 20))
    header = {
        "customer": random.choice(COMPANIES), "project": random.choice(PROJECTS),
        "sampled_by": random.choice(SAMPLERS), "date": base_date.strftime("%m/%d/%Y"),
        "po": f"PO-{random.randint(1000, 9999)}",
        "temp": f"{random.uniform(1.5, 5.9):.1f}", "cooler": random.choice(["Yes", "Yes", "No"]),
        "coolant": random.choice(["ICE", "IPK", "ICE"]),
    }
    rows, counts, check_n = [], {}, None
    for pos, ai in enumerate(order, start=1):
        aname, amx, apres, ackey = ANALYSES[ai]
        pfx = random.choice(PREFIX.get(amx, ["S-"]))
        counts[pfx] = counts.get(pfx, 0) + 1
        t = (dt.datetime.combine(base_date, dt.time(8, 0))
             + dt.timedelta(minutes=random.randint(0, 480)))
        rows.append({"n": pos, "sample_id": f"{pfx}{counts[pfx]:02d}", "matrix": amx,
                     "time": t.strftime("%H:%M"), "analysis": aname,
                     "preservative": apres, "container_key": ackey,
                     "qty": random.randint(1, 3), "checked": ai == forced_idx})
        if ai == forced_idx:
            check_n = pos
    return {"header": header, "rows": rows}, check_n


def render_quiz_full(coc, reveal=False):
    """Full CT/MA/RI form. Bottle columns are blank while answering; on reveal
    the checked line's correct bottle cell gets filled in."""
    h = coc["header"]
    head_bottle = "".join(f"<th>{lbl}</th>" for _, lbl in FULL_COLS)
    body = ""
    for r in coc["rows"]:
        hi = ' style="background:#fdf1c4"' if r["checked"] else ""
        chk = ("<span style='color:#2f6f44;font-weight:900'>&#10003;</span>"
               if r["checked"] else "")
        colid, note = form_cell(r)
        cells = ""
        for cid, _ in FULL_COLS:
            if reveal and r["checked"] and cid == colid:
                extra = f"<small>{note}</small>" if note else ""
                cells += f'<td class="bot">{r["qty"]}{extra}</td>'
            else:
                cells += "<td></td>"
        body += (f"<tr{hi}><td>{chk}</td><td>{r['n']}</td>"
                 f"<td class='lft ent'>{r['sample_id']}</td>"
                 f"<td>{r['matrix']}</td><td class='ent'>{r['time']}</td>"
                 f"<td class='lft ent'>{r['analysis']}</td>{cells}</tr>")
    foot = ("Here's how that line should look filled in \u2014 swipe to see the checked column."
            if reveal else
            "Grab the container for the &#10003; highlighted line. (Bottle columns blank on purpose.)")
    return f"""{FULL_CSS}
<div class="fcoc">
  <div class="top">
    <div class="brand">PEL</div>
    <div><div class="title">CHAIN OF CUSTODY RECORD<small>CT / MA / RI</small></div></div>
    <div class="rt">Page 1 of 1<br>Temp <b>{h['temp']} &deg;C</b><br>
      Cooler <b>{h['cooler']}</b> / <b>{h['coolant']}</b></div>
  </div>
  <div class="info">
    <div><span class="lab">Customer:</span> <span class="val">{h['customer']}</span></div>
    <div><span class="lab">Project:</span> <span class="val">{h['project']}</span></div>
    <div><span class="lab">Project P.O.:</span> <span class="val">{h['po']}</span></div>
    <div><span class="lab">Sampled by:</span> <span class="val">{h['sampled_by']}</span></div>
    <div><span class="lab">Date:</span> <span class="val">{h['date']}</span></div>
    <div></div>
  </div>
  <div class="scroll">
    <table>
      <thead><tr>
        <th>&#10003;</th><th>#</th><th class="lft">Client Sample ID</th><th>Matrix</th>
        <th>Time<br>Sampled</th><th class="lft">Analysis Request</th>{head_bottle}
      </tr></thead>
      <tbody>{body}</tbody>
    </table>
  </div>
  <div class="foot">{foot}</div>
</div>
"""


def new_question(scope):
    exclude = st.session_state.qcur["idx"] if st.session_state.qcur else None
    idx = pick_next(scope, exclude)
    matrix = ANALYSES[idx][1]
    coc, check_n = make_quiz_coc(scope, idx)
    st.session_state.qnum += 1
    st.session_state.qcur = {"idx": idx, "options": make_options(ANALYSES[idx][3], matrix),
                             "answered": False, "chosen": None, "nonce": st.session_state.qnum,
                             "coc": coc, "check_n": check_n}


# --------------------------------------------------------------------------- #
#  Streamlit UI                                                               #
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
#  Reference chart (verbatim from the Phoenix sampling guide)                 #
# --------------------------------------------------------------------------- #
CHART_SOIL = {
 "Soil \u2014 Inorganics": [
   ("28 days","Ammonia","4 oz. Glass jar"),
   ("28 days","Chloride","4 oz. Glass jar"),
   ("30 days","Chromium, (hexavalent)","4 oz. Glass jar"),
   ("28 days","COD","4 oz. Glass jar"),
   ("14 days","Cyanides","4 oz. Glass jar"),
   ("28 days","Flashpoint","4 oz. Glass jar"),
   ("6 months*","Metals, Total","4 oz. Glass jar"),
   ("48 hr","Nitrate","4 oz. Glass jar"),
   ("48 hr","Nitrite","4 oz. Glass jar"),
   ("28 days","Nitrogen Tot-TKN","4 oz. Glass jar"),
   ("28 days","Oil & Grease Or Petroleum HC","4 oz. Glass jar"),
   ("IMMED","Ph","4 oz. Glass jar"),
   ("28 days","Phenolics","4 oz. Glass jar"),
   ("28 days","Phosphate Or Phosphorus","4 oz. Glass jar"),
   ("7 days","Solids-Fixed","4 oz. Glass jar"),
   ("7 days","Solids-Total","4 oz. Glass jar"),
   ("7 days","Solids-Volatile","4 oz. Glass jar"),
   ("28 days","Sulfate","4 oz. Glass jar"),
   ("7 days","Sulfide","4 oz. Glass jar"),
   ("14 days","TOC","4 oz. Glass jar"),
   ("28 days","TOX Or EOX","4 oz. Glass jar"),
 ],
 "Soil \u2014 TCLP": [
   ("6 months*","Metals","4 oz. Glass jar"),
   ("14 (1)","Volatiles","25 gm ENCORE/4 oz. jar"),
   ("14 (1)","Pesticides","4 oz. Glass jar"),
   ("14 (1)","Semi Volatiles","4 oz. Glass jar"),
   ("14 (1)","Herbicides","4 oz. Glass jar"),
   ("as above","Full TCLP (Solid)","(1) 25 gm encore and (2) 8 oz. Glass jars"),
 ],
 "Soil \u2014 Petroleum": [
   ("N/A","Age Dating","4 Glass jar"),
   ("14 days","EPH","4 oz. Glass jar"),
   ("14 days","EPH-(MA)","4 oz. Amber glass jar"),
   ("14 days","ETPH","4 oz. Glass jar"),
   ("14 days","TPH DRO","4 oz. Glass jar"),
   ("14 days","TPH GRO","(2) 10mL methanol VOA"),
   ("28 days","VPH","(2) 15mL methanol VOA"),
 ],
 "Soil \u2014 Organics (Soils/Solids/Oil/Solvents)": [
   ("3 days","Formaldehyde","4 oz. Glass jar"),
   ("14 days","Herbicides/Pesticides","4 oz. Glass jar"),
   ("365 days","PCBs","4 oz. Glass jar"),
   ("14 days","Semi Volatiles","4 oz. Glass jar"),
   ("14 days","Volatiles","4 oz. Glass jar, (1) Methanol VOA, (2) DI water VOA **"),
 ],
}
CHART_WATER = {
 "Water \u2014 Inorganics": [
   ("14 days","Alkalinity","As Is","120 ml/plastic, no headspace"),
   ("28 days","Ammonia","H2SO4","250mL Plastic"),
   ("24 hours","Bacteria (DW)","As Is","120mL Sterile plastic"),
   ("6 hours","Bacteria (WW)","As Is","120mL Sterile plastic"),
   ("48 hour","BOD","As Is","500mL Plastic"),
   ("28 days","Bromide","As Is","100mL Plastic"),
   ("28 days","Chloride","As Is","250mL Plastic"),
   ("IMMED","Chlorine Residual","As Is","100mL Plastic"),
   ("24 hr","Chromium, Hexavalent","As Is","250mL Plastic"),
   ("28 days","COD","H2SO4","250mL Plastic"),
   ("24 hr","Color","As Is","250mL Plastic"),
   ("28 days","Conductance","As Is","100mL Plastic"),
   ("14 days","Cyanide","NaOH","250mL Plastic"),
   ("28 days","Flashpoint","As Is","250mL Plastic"),
   ("28 days","Fluoride (ww)","As Is","500mL Plastic"),
   ("6 months","Hardness","HNO3","100mL Plastic"),
   ("48 hr","MBAS","As Is","500mL Plastic"),
   ("28 days","Mercury","HNO3","250mL Plastic"),
   ("6 months*","Metals, Dissolved (Field Filter)","HNO3","250mL Plastic"),
   ("6 months*","Metals, Dissolved (Lab Filter)","As Is","250mL Plastic"),
   ("6 months*","Metals, Total","HNO3","250mL Plastic"),
   ("48 hr","Nitrate","As Is","250mL Plastic"),
   ("28 days","Nitrate/Nitrite Combined","H2SO4","250mL Plastic"),
   ("48 hr","Nitrite","As Is","250mL Plastic"),
   ("28 days","Nitrogen, TOT-TKN","H2SO4","250mL Plastic"),
   ("24 hr","Odor","As Is","100mL Plastic"),
   ("48 hr","Odor (NY)","As Is","250mL Plastic"),
   ("28 days","Oil & Grease","H2SO4","1000 ml/Amber"),
   ("IMMED","Oxygen, Dissolved","As Is","300 ml/DO plastic w/cap & stopper"),
   ("IMMED","Ph","As Is","100mL Plastic"),
   ("28 days","Phenolics","H2SO4","8 oz. Amber"),
   ("48 hr","Phosphate, Ortho","As Is","250mL Plastic"),
   ("28 days","Phosphate, Phosphorus","H2SO4","250mL Plastic"),
   ("7 days","Solids, Dissolved","As Is","100mL Plastic"),
   ("48 hr","Solids, Settleable","As Is","(2)-1000 ml/plastic"),
   ("7 days","Solids, Suspended","As Is","500mL Plastic"),
   ("7 days","Solids, Total","As Is","100mL Plastic"),
   ("7 days","Solids, Volatile","As Is","100mL Plastic"),
   ("28 days","Sulfate","As Is","250mL Plastic"),
   ("7 days","Sulfide","NaOH/Zinc Acetate","250mL Plastic"),
   ("IMMED","Sulfite","As Is","100mL Plastic"),
   ("28 days","TOC","H3PO4","8 oz. Amber Glass"),
   ("28 days","TOX","H2SO4","8 oz. Amber Glass"),
   ("48 hr","Turbidity","As Is","100mL Plastic"),
   ("48 hr","UV 254","As Is","8 oz. Amber Glass"),
   ("14 days","Volatile Fatty Acids","As Is or H2SO4","250mL Plastic or Glass"),
 ],
 "Water \u2014 TCLP": [
   ("6 months*","Metals","As Is","500mL Plastic"),
   ("14 days (1)","Volatiles","As Is","(4)-40mL VOA Vials"),
   ("7 days (2)","Semi Volatiles","As Is","(2) 1L Amber Glass"),
   ("7 days (2)","Pesticides","As Is","1L Amber Glass"),
   ("7 days (2)","Herbicides","As Is","1L Amber Glass"),
   ("as above","Full TCLP (Liquid)","As Is","(3) 1L Amber Glass, (1) 500mL plastic, (4) 40mL VOA Vials"),
 ],
 "Water \u2014 Petroleum": [
   ("14 days","EPH","HCL","(2) 1L Amber Glass"),
   ("7 days","ETPH","As Is","1L Amber Glass"),
   ("7 days","TPH DRO","As Is","1L Amber Glass"),
   ("14 days","TPH GRO","HCL","(2)-40mL VOA Vials"),
   ("14 days","VPH","HCL","(2)-40mL VOA Vials"),
 ],
 "Water \u2014 Organics (Liquids)": [
   ("14 days","1,4 Dioxane by method 8260","HCL","(3)-40mL VOA Vials"),
   ("28 days","1,4 Dioxane Low Level 8270 Or 522***","NAHSO4","8 oz. Amber Glass"),
   ("14 days","Alcohols","As Is","(2)-40mL VOA Vials"),
   ("14 days","EDB/DBCP","As Is","(2)-40mL VOA Vials"),
   ("3 days","Formaldehyde","As Is","8 oz. Amber Glass"),
   ("14 days","Glycols","As Is","(2)-40mL VOA Vials"),
   ("14 days","Haloacetic Acids (HAA5)","NH4CL","4 oz. Amber Glass"),
   ("7 days","Herbicides","As Is","1L Amber Glass"),
   ("14 days","Oxygenates","HCL","(3)-40mL VOA Vials"),
   ("365 days","PCBs","As Is","1L Amber Glass"),
   ("7 days","Pesticides","As Is","1L Amber Glass"),
   ("7 days","Semi Volatiles","As Is","(2) 1L Amber Glass"),
   ("14 days","THMs","Na2S2O3","(3)-40mL VOA Vials"),
   ("14 days","Volatiles","HCL","(3)-40mL VOA Vials"),
   ("14 days / 3 days","Volatiles (624) HCL / As is","HCL / As Is","(3)-40mL VOA Vials / (2)-40mL VOA Vials"),
 ],
}
CHART_FOOTNOTES = [
 "(1) 14-day hold for TCLP extraction",
 "(2) 7-day hold for TCLP extraction",
 "*** for Method 522, if chlorinated system the preservative includes Na2S2O3",
 "** submit to lab within 48 hours of collection, or freeze",
 "* 28 days for Mercury",
]
CHART_DOTS = {"HNO3": ("#d1202f", "#ffffff"), "H2SO4": ("#f2c200", "#333333"),
              "HCL": ("#8f7fd4", "#ffffff"), "NAOH": ("#1f2f6e", "#ffffff"),
              "NA2S2O3": ("#3aa0e0", "#ffffff")}


# plain-English "what it's testing for" for each analysis on the chart
_metals = ("Screens for metals such as lead, arsenic, and chromium. Many are toxic even at "
           "low levels and can come from pipes, industry, or natural soil. Water samples are "
           "acid-preserved so the metals stay dissolved until analysis.")
_voc = ("Screens for volatile organic compounds \u2014 solvents and fuel chemicals like benzene "
        "and TCE that evaporate easily. They're common near gas stations, dry cleaners, and "
        "spills, and many are harmful. Collected with no air bubble so they can't escape.")
_svoc = ("Screens for heavier organic pollutants that don't evaporate quickly, including PAHs "
         "and many industrial chemicals. It's a broad scan used at contaminated sites. Several "
         "of these compounds are toxic or cancer-causing.")
_pest = ("Tests for bug-killer residues, including older persistent ones like DDT and chlordane. "
         "They can wash off farmland or linger in soil for years. Many are toxic and tightly "
         "regulated.")
_herb = ("Tests for weed-killer residues such as 2,4-D. They come from farm and lawn runoff and "
         "can reach water supplies. Several are health concerns in drinking water.")
_pcb = ("Tests for PCBs \u2014 banned oily chemicals once used in electrical equipment. They "
        "persist in soil and sediment for decades and build up in the food chain. Regulated as "
        "probable carcinogens.")
_ogr = ("Measures the total amount of oily and greasy material in the sample. It flags "
        "contamination from petroleum, food processing, or industrial discharge. It doesn't "
        "identify the specific oil, just how much is there.")
_phen = ("Tests for phenol-type compounds, pollution indicators that often come from industrial "
         "or petroleum discharge. They can cause taste-and-odor problems and are toxic at higher "
         "levels.")
_toc = ("Total Organic Carbon measures how much carbon-based material is dissolved in the water. "
        "It's not a poison itself, but high TOC feeds bacteria and forms disinfection byproducts "
        "when chlorinated. A common drinking-water and process check.")
_tox = ("Measures total organic halogens \u2014 organic molecules carrying chlorine, bromine, or "
        "iodine. It's a broad flag for man-made chlorinated contamination. Higher numbers suggest "
        "industrial or solvent pollution.")
_cod = ("Chemical Oxygen Demand estimates how much oxygen it would take to chemically break down "
        "the organic matter in the sample. It's a fast gauge of how polluted wastewater is. "
        "Higher numbers mean more organic contamination.")
_ph = ("Measures how acidic or basic the sample is on the 0\u201314 scale. It affects corrosion, "
       "metal solubility, and whether a waste is 'corrosive.' It's measured immediately because "
       "it changes fast.")
_flash = ("Measures the lowest temperature at which the sample gives off enough vapor to ignite. "
          "It tells whether a waste is legally 'ignitable' and therefore hazardous. Common for "
          "drums, solvents, and oily waste.")
_cn = ("Tests for cyanide, a fast-acting poison that can come from metal plating, mining, or "
       "industrial waste. Even low levels are dangerous, so it's tightly regulated. Base-preserved "
       "to keep the cyanide stable.")
_sulfide = ("Tests for sulfide, the 'rotten egg' smell compound. It's toxic, corrosive, and common "
            "in wastewater and low-oxygen water. Preserved so the sulfide doesn't escape as gas.")
_sulfate = ("Measures dissolved sulfate, a common natural salt. High levels taste bitter and can "
            "have a laxative effect, and may indicate mining or industrial influence. A routine "
            "general-chemistry test.")
_ammonia = ("Measures ammonia-nitrogen, a form of nitrogen from sewage, fertilizer, or animal "
            "waste. High levels are toxic to fish and signal pollution. A common wastewater and "
            "surface-water check.")
_chloride = ("Measures dissolved chloride (a salt). It's used to judge water quality and spot "
             "road-salt, seawater, or wastewater influence. High chloride corrodes pipes and harms "
             "freshwater life.")
_cr6 = ("Tests for chromium-6, the toxic, cancer-causing form of chromium (the 'Erin Brockovich' "
        "contaminant). It usually comes from industrial plating or manufacturing. It's regulated "
        "far more strictly than ordinary chromium.")
_nitrate = ("Measures nitrate, a nitrogen form usually from fertilizer, manure, or septic systems. "
            "High nitrate in drinking water is dangerous for infants ('blue-baby syndrome'). Wells "
            "are routinely tested for it.")
_nitrite = ("Measures nitrite, a short-lived nitrogen form in the nitrogen cycle. It signals fresh "
            "contamination or incomplete treatment. Usually run alongside nitrate.")
_tkn = ("Total Kjeldahl Nitrogen measures organic nitrogen plus ammonia together. Combined with "
        "nitrate/nitrite it gives 'total nitrogen,' a key nutrient-pollution measure. High values "
        "point to sewage or fertilizer loading.")
_phos = ("Measures phosphorus, a nutrient that in excess triggers algae blooms in lakes and "
         "streams. It commonly comes from fertilizer, detergents, or wastewater. A core part of "
         "nutrient testing.")
_form = ("Tests for formaldehyde, an industrial chemical and preservative that irritates the lungs "
         "and is a probable carcinogen. It can show up around manufacturing or certain wastes.")
_eph = ("Extractable Petroleum Hydrocarbons measures the heavier, diesel-and-oil range of "
        "petroleum. It's used to find and quantify fuel/oil contamination. Often paired with VPH "
        "for the lighter range.")
_tphgro = ("Total Petroleum Hydrocarbons in the Gasoline Range \u2014 measures lighter, gasoline-type "
           "fuel. Because it's volatile, it's collected in sealed methanol/VOA vials. Common at gas "
           "stations and fuel spills.")
_vph = ("Volatile Petroleum Hydrocarbons \u2014 measures the lighter, gasoline-range petroleum "
        "vapors. It's collected volatile-style (methanol/VOA). Often paired with EPH to cover the "
        "full fuel range.")
_solids = ("Measures how much solid material is in the water. Different versions look at what's "
           "suspended, dissolved, or total. A basic water-quality and treatment measure.")
_fulltclp = ("The complete TCLP suite \u2014 a leaching test that simulates whether a waste will "
             "release metals and organic toxins into groundwater in a landfill. It bundles metals, "
             "volatiles, semi-volatiles, pesticides, and herbicides. Results decide if a waste is "
             "hazardous.")
_dioxane = ("Tests for 1,4-dioxane, an industrial solvent stabilizer and stubborn groundwater "
            "contaminant. It's a suspected carcinogen that's hard to remove with normal treatment.")

CHART_DESC = {
 # soil inorganics
 "Ammonia": _ammonia, "Chloride": _chloride, "Chromium, (hexavalent)": _cr6,
 "Chromium, Hexavalent": _cr6, "COD": _cod, "Cyanides": _cn, "Cyanide": _cn,
 "Flashpoint": _flash, "Metals, Total": _metals, "Metals": _metals,
 "Nitrate": _nitrate, "Nitrite": _nitrite, "Nitrogen Tot-TKN": _tkn, "Nitrogen, TOT-TKN": _tkn,
 "Oil & Grease Or Petroleum HC": _ogr, "Oil & Grease": _ogr, "Ph": _ph, "Phenolics": _phen,
 "Phosphate Or Phosphorus": _phos, "Phosphate, Phosphorus": _phos, "Phosphate, Ortho": _phos,
 "Solids-Fixed": _solids, "Solids-Total": _solids, "Solids-Volatile": _solids,
 "Sulfate": _sulfate, "Sulfide": _sulfide, "TOC": _toc, "TOX Or EOX": _tox, "TOX": _tox,
 # tclp + organics
 "Volatiles": _voc, "Pesticides": _pest, "Semi Volatiles": _svoc, "Herbicides": _herb,
 "Herbicides/Pesticides": _pest, "PCBs": _pcb, "Formaldehyde": _form,
 "Full TCLP (Solid)": _fulltclp, "Full TCLP (Liquid)": _fulltclp,
 # petroleum
 "Age Dating": ("A petroleum 'fingerprinting' analysis that estimates how long ago a fuel or oil "
                "release happened. Labs compare weathering patterns in the hydrocarbons. Used to "
                "sort out liability in spill cases."),
 "EPH": _eph, "EPH-(MA)": ("The Massachusetts version of the EPH petroleum test, run to that "
        "state's method. It measures diesel/oil-range petroleum. The soil version uses an amber jar "
        "to protect light-sensitive compounds."),
 "ETPH": ("Extractable Total Petroleum Hydrocarbons \u2014 Connecticut's measure for the diesel/oil "
          "range. It quantifies how much heavier petroleum is present. Common at CT tank and spill "
          "sites."),
 "TPH DRO": ("Total Petroleum Hydrocarbons in the Diesel Range \u2014 measures diesel, heating oil, "
             "and heavier fuel contamination. A standard cleanup-site measure. Paired with GRO to "
             "cover gasoline too."),
 "TPH GRO": _tphgro, "VPH": _vph,
 # water inorganics
 "Alkalinity": ("Measures the water's capacity to neutralize acid (mostly carbonates and "
                "bicarbonates). It buffers pH swings and affects corrosion and treatment. A routine "
                "general-chemistry parameter."),
 "Bacteria (DW)": ("Tests drinking water for coliform and E. coli \u2014 indicators of contamination "
                   "from human or animal waste. A positive result means the water may be unsafe. "
                   "Collected sterile, often with thiosulfate to remove chlorine."),
 "Bacteria (WW)": ("Tests wastewater for bacteria like coliforms to check treatment and "
                   "disinfection. It confirms discharged water meets health limits. The short hold "
                   "time means it must reach the lab fast."),
 "BOD": ("Biochemical Oxygen Demand measures how much oxygen microbes use to break down organic "
         "matter over 5 days. It shows how much organic pollution wastewater carries. A core "
         "treatment-plant measure."),
 "Bromide": ("Measures bromide, a natural salt ion. It matters because during disinfection it can "
             "form harmful brominated byproducts. Also used to trace seawater or industrial "
             "influence."),
 "Chlorine Residual": ("Measures leftover disinfecting chlorine in treated water. Enough must remain "
                       "to keep water safe through the pipes, but not so much it causes taste or "
                       "byproduct problems. Measured immediately since chlorine fades fast."),
 "Color": ("Measures the true color of the water, often from natural organics or industrial dyes. "
           "It's an aesthetic quality parameter and can hint at organic loading."),
 "Conductance": ("Measures how well the water carries electricity, which reflects dissolved-salt "
                 "content. It's a quick proxy for overall mineral levels. Handy for spotting "
                 "contamination or seawater intrusion."),
 "Fluoride (ww)": ("Measures fluoride, beneficial for teeth at low levels but harmful in excess. "
                   "Testing confirms it's within safe limits. Also relevant to some industrial "
                   "discharges."),
 "Hardness": ("Measures calcium and magnesium \u2014 the minerals that make water 'hard.' Hard water "
              "causes scale in pipes and affects soap use. Acid-preserved because it's measured with "
              "the metals."),
 "MBAS": ("Measures detergent-type foaming agents (surfactants). Their presence signals detergent "
          "or wastewater contamination. Often shows up as foaming in water."),
 "Mercury": ("Tests specifically for mercury, a highly toxic metal that builds up in fish and the "
             "food chain. It comes from industrial sources and some natural deposits. Regulated at "
             "very low limits."),
 "Metals, Dissolved (Field Filter)": ("Measures only the dissolved metals, with the sample filtered "
             "in the field before preserving. Field filtering captures the truly dissolved fraction "
             "before it changes. Used when the dissolved portion matters most."),
 "Metals, Dissolved (Lab Filter)": ("Measures dissolved metals, but the filtering is done at the lab "
             "instead of in the field. Same goal \u2014 the dissolved fraction \u2014 with a "
             "different filtering step."),
 "Nitrate/Nitrite Combined": ("Measures nitrate and nitrite together as total oxidized nitrogen. A "
             "common nutrient and drinking-water screen. High values point to fertilizer or septic "
             "influence."),
 "Odor": ("Measures the threshold at which the water has a detectable smell. An aesthetic "
          "drinking-water quality check. Odors can hint at organic or industrial contamination."),
 "Odor (NY)": ("Measures detectable odor in water using New York's method. It's an aesthetic quality "
               "check. Odors can point to organic or industrial contamination."),
 "Oxygen, Dissolved": ("Measures the oxygen dissolved in water, essential for fish and aquatic life. "
             "Low DO signals pollution or organic overloading. Measured immediately in a special "
             "stoppered bottle because it changes fast."),
 "Sulfite": ("Measures sulfite, often a leftover treatment chemical used to remove chlorine or "
             "oxygen. Checked to confirm dosing and protect equipment. Measured quickly because it "
             "reacts away."),
 "Turbidity": ("Measures how cloudy the water is from suspended particles. It affects disinfection "
               "and is a key drinking-water standard. Spikes can indicate contamination or treatment "
               "problems."),
 "UV 254": ("A quick optical test that shines UV light through the water to gauge dissolved organic "
            "material. It correlates with disinfection-byproduct potential. A fast surrogate for "
            "organic content."),
 "Volatile Fatty Acids": ("Measures short-chain fatty acids that build up in digesters and "
             "wastewater. They show how a biological or anaerobic treatment process is performing. "
             "Rising levels can signal an upset process."),
 "Solids, Dissolved": ("Measures the material dissolved in the water (salts and minerals that pass "
             "through a filter). It reflects overall mineral content and water quality."),
 "Solids, Settleable": ("Measures the portion of solids that settles to the bottom over time. Used "
             "to judge wastewater-treatment performance."),
 "Solids, Suspended": ("Measures the solid particles floating in the water (what a filter catches). "
             "High levels make water cloudy and can smother aquatic life. A standard "
             "wastewater-discharge measure."),
 "Solids, Total": _solids, "Solids, Volatile": ("Splits solids into the part that burns off "
             "(organic/volatile) versus the mineral part left behind. It shows how much of the "
             "solids are organic. Useful for wastewater and sludge."),
 # water organics
 "1,4 Dioxane by method 8260": _dioxane + " This version uses the volatile (8260) method in "
             "acid-preserved vials.",
 "1,4 Dioxane Low Level 8270 Or 522***": _dioxane + " This is the trace-level method, collected in "
             "a bisulfate-preserved amber bottle instead of a VOA vial.",
 "Alcohols": ("Screens for alcohol compounds (like methanol or isopropanol) in water. These can come "
              "from industrial processes or spills. Collected volatile-style since they evaporate."),
 "EDB/DBCP": ("Tests for two old soil fumigants (EDB and DBCP) once used on crops. They can persist "
              "in groundwater and are linked to cancer, so drinking water is screened for them."),
 "Glycols": ("Tests for glycols such as antifreeze (ethylene/propylene glycol). They can contaminate "
             "water from de-icing, spills, or industry. Collected volatile-style."),
 "Haloacetic Acids (HAA5)": ("A group of five disinfection byproducts formed when chlorine reacts "
             "with natural organic matter. They're regulated in drinking water because long-term "
             "exposure is a health concern."),
 "Oxygenates": ("Tests for fuel oxygenates like MTBE that were added to gasoline. They spread quickly "
                "in groundwater and cause taste-and-odor problems. Common at gas-station "
                "contamination sites."),
 "THMs": ("Trihalomethanes are disinfection byproducts formed when chlorine meets natural organics. "
          "They're regulated in drinking water due to long-term health risks. Samples are "
          "dechlorinated to stop further formation."),
 "Volatiles (624) HCL / As is": _voc + " This is the 624-method version; the preservative depends on "
             "the specific list being run.",
}



def _chart_pres(text):
    key = text.upper().replace(" ", "")
    if key in CHART_DOTS:
        bg, fg = CHART_DOTS[key]
        return f'<span class="cdot" style="background:{bg};color:{fg};border-color:{bg}">{text}</span>'
    return f'<span class="cplain">{text}</span>'


def render_chart_html():
    def soil_tbl(rows):
        trs = "".join(f"<tr><td class='ch'>{h}</td><td class='ca'>{a}</td>"
                      f"<td class='cc'>{c}</td>"
                      f"<td class='cd'>{CHART_DESC.get(a, '')}</td></tr>" for h, a, c in rows)
        return ("<table><thead><tr><th>Hold</th><th>Analysis</th>"
                "<th>Container</th><th>What it's for</th></tr></thead>"
                f"<tbody>{trs}</tbody></table>")

    def water_tbl(rows):
        trs = "".join(f"<tr><td class='ch'>{h}</td><td class='ca'>{a}</td>"
                      f"<td class='cp'>{_chart_pres(p)}</td><td class='cc'>{c}</td>"
                      f"<td class='cd'>{CHART_DESC.get(a, '')}</td></tr>"
                      for h, a, p, c in rows)
        return ("<table><thead><tr><th>Hold</th><th>Analysis</th>"
                "<th>Preserv.</th><th>Container</th><th>What it's for</th></tr></thead>"
                f"<tbody>{trs}</tbody></table>")

    body = "<div class='cgrp'>SOIL</div>"
    for title, rows in CHART_SOIL.items():
        body += f"<div class='csec'>{title}</div>" + soil_tbl(rows)
    body += "<div class='cgrp'>WATER</div>"
    for title, rows in CHART_WATER.items():
        body += f"<div class='csec'>{title}</div>" + water_tbl(rows)
    foot = "".join(f"<div>{f}</div>" for f in CHART_FOOTNOTES)
    keyline = " ".join(_chart_pres(x) for x in ("HNO3", "H2SO4", "HCL", "NaOH", "Na2S2O3"))
    return f"""
<style>
.pchart{{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;}}
.pchart .cgrp{{font-family:Georgia,serif;color:#fff;background:#5f1a1c;
   margin:16px 0 4px;font-size:16px;padding:5px 10px;border-radius:4px;letter-spacing:.5px;}}
.pchart .csec{{font-family:Georgia,serif;color:#e8c9a0;font-weight:700;margin:12px 0 4px;font-size:14px;
   border-bottom:1.5px solid #7a5a48;padding-bottom:2px;}}
.pchart table{{width:100%;border-collapse:collapse;background:#fffdf8;margin-bottom:6px;
   border:1px solid #c8b89a;font-size:12.5px;}}
.pchart th{{background:#f3e9e3;color:#5f1a1c;text-align:left;padding:5px 7px;font-size:11px;
   border:1px solid #c8b89a;}}
.pchart td{{padding:5px 7px;border:1px solid #e6dcc8;vertical-align:middle;color:#211d18;}}
.pchart td.ch{{color:#8a7f72;white-space:nowrap;font-size:11px;}}
.pchart td.ca{{font-weight:600;color:#14346b;}}
.pchart td.cc{{color:#5f1a1c;}}
.pchart td.cd{{color:#4a4238;font-size:11px;line-height:1.35;width:44%;}}
.pchart th:last-child{{width:44%;}}
.pchart .cdot{{display:inline-block;padding:1px 8px;border-radius:10px;border:1.5px solid;
   font-size:11px;font-weight:700;white-space:nowrap;}}
.pchart .cplain{{display:inline-block;padding:1px 8px;border-radius:3px;border:1px solid #cbb;
   background:#fff;color:#5f4a44;font-size:11px;font-weight:600;white-space:nowrap;}}
.pchart .ckey{{background:#fffdf8;border:1px solid #c8b89a;border-radius:6px;padding:8px 12px;
   margin-top:10px;font-size:11px;color:#4a4238;}}
.pchart .cfn{{background:#fffdf8;border:1px solid #c8b89a;border-radius:6px;padding:8px 12px;
   margin-top:10px;font-size:11px;color:#6a6055;line-height:1.6;}}
</style>
<div class="pchart">{body}
<div class="ckey"><b>Label colors:</b> {keyline} &mdash; everything else is a plain printed label.</div>
<div class="cfn">{foot}</div></div>
"""



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
mode = st.radio("Mode", ["🎲 CoC Generator", "🎯 Quiz", "📋 Chart"], horizontal=True,
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

    if coc["matrix"] == "Air":
        st.markdown(render_coc_html(coc), unsafe_allow_html=True)
    else:
        st.markdown(render_full_coc_html(coc), unsafe_allow_html=True)
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
elif mode == "🎯 Quiz":
    scope = st.session_state.get("qscope", "All")
    idxs = scope_indices(scope)
    stats = st.session_state.qstats
    score = st.session_state.qscore

    # make sure there's a question in the current scope
    if st.session_state.qcur is None or st.session_state.qcur["idx"] not in idxs:
        new_question(scope)
    q = st.session_state.qcur
    name, amx, pres, correct_key = ANALYSES[q["idx"]]

    # a real CoC with one line checked off (answer columns hidden)
    st.markdown(render_quiz_full(q["coc"], reveal=q["answered"]), unsafe_allow_html=True)
    st.markdown(f"#### Which container for the ✓ line — **{name}** _({amx})_?")

    if not q["answered"]:
        cols = st.columns(len(q["options"]))
        for i, (col, ckey) in enumerate(zip(cols, q["options"])):
            with col:
                p = img_path(ckey)
                if p:
                    st.image(p, use_container_width=True)
                else:
                    st.markdown(
                        "<div style='height:150px;display:flex;align-items:center;"
                        "justify-content:center;border:1px solid #e4ddce;border-radius:8px;"
                        "background:#faf6ee;font-size:40px'>🛢️</div>",
                        unsafe_allow_html=True)
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
        # plain-English "what this test is and why they run it"
        st.markdown(
            f"<div style='background:#eef2f8;border-left:4px solid #14346b;"
            f"border-radius:6px;padding:10px 12px;margin:6px 0;font-size:14px;"
            f"color:#14346b !important'>"
            f"<b style='color:#0e2550'>{name} —</b> "
            f"<span style='color:#22314d'>{ANALYSIS_INFO.get(name, '')}</span></div>",
            unsafe_allow_html=True)
        cname, cfn, cdesc = CONTAINERS[correct_key]
        st.markdown(f"**Answer: {cname}**")
        st.markdown("Preservative: " + dot_html(pres), unsafe_allow_html=True)
        p = img_path(correct_key)
        if p:
            st.image(p, use_container_width=True)
        else:
            st.info("📷 No photo on file — " + cdesc)
        # plain-English "what usually goes in this container"
        st.markdown(
            f"<div style='background:#eef5ee;border-left:4px solid #2f6f44;"
            f"border-radius:6px;padding:10px 12px;margin-top:6px;font-size:14px;"
            f"color:#1f3a28 !important'>"
            f"<b style='color:#1d5c33'>What usually goes in it:</b> "
            f"<span style='color:#25402e'>{CONTAINER_CONTENTS[correct_key]}</span></div>",
            unsafe_allow_html=True)
        if st.button("Next question →", use_container_width=True, type="primary"):
            new_question(scope)
            st.rerun()

    st.divider()
    b1, b2 = st.columns([1, 1])
    with b1:
        st.selectbox("Drill (matrix)", MATRICES, key="qscope")
    with b2:
        st.write("")
        st.button("↺ Reset score & progress", on_click=reset_quiz,
                  use_container_width=True)

# ============================== CHART MODE ================================== #
else:
    st.caption("Full Phoenix reference — exact wording from the sampling guide. "
               "Colored dots are the five label colors you'll see in the binder.")
    st.markdown(render_chart_html(), unsafe_allow_html=True)

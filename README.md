# Phoenix CoC & Bottle Trainer  📱

A little Streamlit app that generates a random Phoenix Environmental Labs
Chain of Custody (CoC) and shows the sample container(s) you'd grab to fill it,
using real photos from the container reference binder. Built to be used on a
phone.

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Controls sit at the top: pick a **Matrix** (Water / Soil / Bacteria / Air / All)
and number of sample lines, tap **Generate new CoC**. Flip **Quiz me** on to hide
the photos and guess the container first. On a narrow screen the CoC table folds
into stacked cards so you don't have to pinch-zoom.

## Put it on your phone

**Easiest — free hosting (recommended):**
1. Put this folder in a GitHub repo (`app.py`, `images/`, `requirements.txt`).
2. Go to https://share.streamlit.io, sign in with GitHub, click **New app**,
   pick the repo and `app.py`, deploy.
3. Open the app URL on your phone and **Add to Home Screen** — it behaves like
   an app.

**On the same Wi-Fi (no hosting):**
```bash
streamlit run app.py --server.address 0.0.0.0
```
Find your computer's local IP (e.g. 192.168.1.50) and open
`http://192.168.1.50:8501` on your phone.

## Quiz mode

Switch the toggle at the top to **🎯 Quiz**. You get a CoC line (an analysis) and
tap which container you'd grab from 4 choices. It tracks:

- **Score** (correct / total) and running **accuracy %**
- **Streak** (current + best)
- **Coverage** — how many of the pairings you've seen, with a progress bar
  (there are 29 total; pick a **Drill** matrix to focus on Water/Soil/etc.)

Unseen pairings are shown first so you cover the whole set, then the ones you
miss come back ~10x more often until they stick. **Reset score & progress**
clears everything.

## How the matching works

Each analysis maps to a preservative and a container, taken from your Phoenix
label/container binder: 504→AS IS, 524→HCl, 525→AA/K-Citrate/EDTA, 531→C6H7KO7,
547/548/549→Na2S2O3, HAA5→NH4CL, TOC→H3PO4, Phenol/TOX→H2SO4, 1,4-Dioxane→NAHSO4,
plus standard practice for metals (HNO3), cyanide (NaOH), nutrients (H2SO4),
VOCs (HCl vials) and bacteria (thio vs as-is). Preservative "dots" use the same
colors as the label sheet (HNO3 red, H2SO4 yellow, HCl purple, NaOH navy,
Na2S2O3 blue). Air samples generate 6.0 L / 24-hr and 1.4 L / 15-min canister
configs like the Air Analyses CoCs.

## Make it yours

- **Edit pairings / add analyses:** change the `ANALYSES` list in `app.py`.
- **Swap in a better photo:** drop a PNG into `images/` with the same filename.
- **Add a canister photo:** save `images/summa_canister.png` and set it as the
  second field of `CONTAINERS["summa_canister"]` so Air samples show a picture.

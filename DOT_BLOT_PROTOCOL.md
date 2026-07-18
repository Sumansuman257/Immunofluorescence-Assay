# Dot Blot Protocol (Protein Immunodetection)

A dot blot is a simplified, rapid technique for detecting a target **protein** (antigen)
in a sample by applying it directly as a "dot" onto a membrane and probing it with
antibodies. Unlike a Western blot, samples are **not** separated by size on a gel, so a
dot blot confirms the *presence/relative amount* of an antigen, not its molecular weight.

---

## 1. Overview

| Property | Detail |
|---|---|
| Purpose | Detect/semi-quantify a protein antigen; screen antibodies; check antibody titer |
| Membrane | Nitrocellulose (0.45 or 0.2 µm) or PVDF |
| Detection | Primary + enzyme-conjugated (HRP/AP) secondary antibody, or direct-conjugated primary |
| Readout | Chemiluminescence (ECL), colorimetric substrate, or fluorescence |
| Typical time | ~3–4 hours (plus optional overnight primary incubation) |

---

## 2. Materials & Reagents

**Equipment**
- Nitrocellulose or PVDF membrane
- Fine-tip pipette (1–2 µL)
- Forceps (flat/blunt) and clean tray/dish
- Rocking platform / orbital shaker
- Imaging system (chemiluminescence imager) or scanner for colorimetric blots

**Buffers & solutions**
- **TBS (10×):** 24 g Tris base + 88 g NaCl in 900 mL H₂O, pH to 7.6, bring to 1 L.
- **TBST (wash buffer):** 1× TBS + 0.1% Tween-20.
- **Blocking buffer:** 5% (w/v) non-fat dry milk **or** 3–5% BSA in TBST.
  *(Use BSA, not milk, when detecting phospho-proteins or using biotin/streptavidin.)*
- **Primary antibody:** diluted in blocking buffer (typical 1:500–1:5000; follow datasheet).
- **Secondary antibody:** HRP- or AP-conjugated anti-(host IgG), diluted per datasheet
  (typical 1:5000–1:20000).
- **Detection substrate:** ECL reagent (HRP) or BCIP/NBT (AP colorimetric).
- **Methanol** (only if using PVDF — for membrane activation).

> Safety: wear gloves and handle membranes only with forceps to avoid contaminating
> proteins/oils from skin. Work in a clean area; handle ECL and antibody stocks per SDS.

---

## 3. Procedure

### Step 1 — Prepare the membrane
- **PVDF:** activate by soaking in **100% methanol for 30 seconds**, then rinse in TBS.
- **Nitrocellulose:** no activation needed; equilibrate briefly in TBS.
- Optionally lightly pencil-mark a grid to guide spotting (do not touch the spotting area).

### Step 2 — Spot the samples
- Apply **1–2 µL** of each sample slowly to the center of a grid square.
- Keep the spot small (~3–5 mm); apply in fractions if loading larger volumes,
  letting each application dry before adding more.
- Include controls on every membrane:
  - **Positive control** (known antigen)
  - **Negative control** (buffer only / non-expressing lysate)
  - Optional dilution series for semi-quantitation.

### Step 3 — Dry / fix
- Let the membrane air-dry **5–15 minutes** until spots are fully absorbed.
  Drying helps immobilize the protein on the membrane.

### Step 4 — Block
- Incubate the membrane in **blocking buffer for 1 hour at room temperature**
  with gentle rocking (or overnight at 4 °C).

### Step 5 — Primary antibody
- Discard blocking buffer. Add diluted **primary antibody**.
- Incubate **1 hour at room temperature** (or **overnight at 4 °C** for weak signals),
  with gentle rocking.

### Step 6 — Wash
- Wash **3 × 5 minutes** with TBST, rocking.

### Step 7 — Secondary antibody
- Add diluted **enzyme-conjugated secondary antibody**.
- Incubate **1 hour at room temperature** with gentle rocking.
  *(Skip this step if using a directly conjugated primary antibody.)*

### Step 8 — Wash
- Wash **3 × 5 minutes** with TBST, then a final **1 × 5 minutes** with TBS
  (removes Tween before detection).

### Step 9 — Detect
- **Chemiluminescence (HRP):** cover membrane with ECL substrate for ~1–5 minutes,
  drain excess, and image.
- **Colorimetric (AP):** add BCIP/NBT; a purple dot develops within minutes.
  Stop by rinsing in water once bands appear.

### Step 10 — Analyze
- A visible dot = antigen present. Compare intensity against the dilution series or
  positive control for semi-quantitative assessment (e.g. by densitometry).

---

## 4. Quick Reference Timeline

| # | Step | Time |
|---|------|------|
| 1 | Membrane prep (PVDF activation) | 0.5 min + rinse |
| 2 | Spot samples | ~5–10 min |
| 3 | Air-dry | 5–15 min |
| 4 | Block | 60 min |
| 5 | Primary antibody | 60 min (or overnight 4 °C) |
| 6 | Wash | 3 × 5 min |
| 7 | Secondary antibody | 60 min |
| 8 | Wash | 3 × 5 min + 1 × 5 min TBS |
| 9 | Detect | 1–5 min |
| 10 | Analyze | — |

---

## 5. Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| No signal | Too little antigen; antibody too dilute; wrong secondary | Increase sample; optimize antibody dilution; confirm species match |
| High background | Insufficient blocking; antibody too concentrated; poor washing | Extend blocking; dilute antibody; add wash steps / more Tween |
| Diffuse/large spots | Volume applied too fast/too large | Apply smaller volumes in fractions, let dry between |
| Uneven dots | Membrane touched/contaminated | Use forceps; handle by edges only |
| Speckled background (milk) | Phospho-target with milk block | Switch to BSA blocking buffer |

---

## 6. Notes

- Dot blot shows presence/abundance only — **it cannot confirm protein size**; use a
  Western blot when specificity or molecular weight verification is required.
- For **nucleic acid** dot blots the workflow differs (denaturation, UV/heat crosslinking,
  labeled probe hybridization) and is not covered here.
- Always follow the antibody manufacturer's recommended dilutions and incubation times.

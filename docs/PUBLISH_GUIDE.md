# Publishing guide

*Plain-language summary: step-by-step instructions to put the panel on GitHub and get three DOIs from Zenodo. You verified v0.1.0 on 2026-11-04 and the draft stamps are off. Nothing has been uploaded yet. No upload tokens were supplied in the build session, so these steps are yours, or Claude can do them for you if you supply tokens (Option A).*

## Copy-ready text

**Repository name:** `perinatal-bh-panel`

**Repository description:** Open county-level panel of perinatal mental health and substance use need beside treatment capacity, for every U.S. county, with rural and frontier flags.

**Author (exactly as in AUTHORS.json):** Emesobum, Munachimso A. | ORCID 0009-0002-7506-2153 | Independent Researcher, Nevada, USA

**Keywords:** perinatal mental health; maternal mental health; postpartum; substance use treatment; county health data; rural health; frontier; health workforce; open data

**License:** Creative Commons Attribution 4.0 International (data); MIT (code)

**Titles and descriptions:** in `dist/release1_need_zenodo_metadata.json`, `dist/release2_capacity_zenodo_metadata.json`, and `dist/release3_gap_zenodo_metadata.json`. Rewrite each description in your own words first (Checklist Part 5).

## Your plan: three records, released in order

| Release | Zip to upload | Target month |
|---|---|---|
| 1. Need measures | `dist/release1_need_v0.1.0.zip` | February 2027, or earlier once verified |
| 2. Capacity inventory | `dist/release2_capacity_v0.1.0.zip` | March 2027 |
| 3. Gap scores | `dist/release3_gap_v0.1.0.zip` | April 2027 |

Release 2 should link to Release 1's DOI, and Release 3 to both, as related works.

## Before any upload (5 min)

1. Done: v0.1.0 is already built without draft stamps.
2. Run `python3 tools/publish_gate.py dist/release1_need --allow-draft-in code tools`. It must print `gate: clear`. (The Zenodo upload script `tools/zenodo_deposit.py` also runs this gate on the zip and its metadata by itself and refuses to upload if it fails.) (The scripts in `code/` and `tools/` contain the draft switch and the gate's own search patterns, so they are exempt; every data file and document is still checked.) Repeat for the release you are about to upload.

## Option A: Claude uploads for you (10 min of your time)

1. **GitHub token.** Go to https://github.com/settings/tokens/new. Note: "panel upload". Expiration: 7 days. Tick the **repo** box. Click **Generate token**. Copy it (starts with `ghp_`).
2. **Zenodo token.** Go to https://zenodo.org/account/settings/applications/tokens/new/. Name: "panel upload". Tick **deposit:write** and **deposit:actions**. Click **Create**. Copy it.
3. In a new Claude session with this project, say: "Publish Release 1. Here are my tokens." Paste them when asked. Claude stores them only for that session, tests on the Zenodo sandbox first, shows you the practice record, and publishes only after you say yes.
4. Afterward, delete both tokens: GitHub https://github.com/settings/tokens and Zenodo https://zenodo.org/account/settings/applications/. A token is a temporary password; deleting it ends Claude's access.

## Option B: you upload (about 30 min the first time)

### GitHub

1. Go to https://github.com/new. Repository name: `perinatal-bh-panel`. Public. Do **not** add a README (the project has one). Click **Create repository**.
2. Unzip `perinatal-bh-panel_v0.1.0.zip`. The folder is already a Git repository with one commit ("Release v0.1.0") and a `v0.1.0` tag, under your name and email. In a terminal inside the `perinatal-bh-panel` folder, paste:
   ```
   git remote add origin https://github.com/memesobum/perinatal-bh-panel.git
   git push -u origin main --tags
   ```
   When asked for a password, paste a GitHub token (Option A, step 1), not your account password. Refresh https://github.com/memesobum/perinatal-bh-panel: it should show your README.
3. Optional: on GitHub click **Releases**, then **Draft a new release**, choose tag `v0.1.0`, title "v0.1.0", and click **Publish release**.

### Zenodo (repeat for each release)

1. Log in at https://zenodo.org with **Log in with ORCID**.
2. Click **New upload** (top right).
3. Drag in the release zip from `dist/`.
4. **Resource type:** Dataset.
5. **Title** and **Description:** paste from that release's `_zenodo_metadata.json` (your rewritten version).
6. **Creators:** Emesobum, Munachimso A.; ORCID 0009-0002-7506-2153; affiliation Independent Researcher, Nevada, USA.
7. **License:** Creative Commons Attribution 4.0 International.
8. **Keywords:** paste the list above. **Version:** 0.1.0.
9. **Related works:** add your GitHub repository URL as "Is supplemented by". For Release 2 and 3, add the earlier releases' DOIs as "References".
10. Click **Preview** and read it once. Then **Publish**. The screen shows a DOI like `10.5281/zenodo.1234567`.

## The same day you publish (5 min)

1. Put the DOI in `CITATION.cff` (add a line `doi: "10.5281/zenodo.NUMBER"`) and in the README status line. Add the DOI next to "Released v0.1.0".
2. Save a PDF of the Zenodo page (browser Print, then Save as PDF).
3. Add a row to your evidence log:
   `2027-MM-DD,Perinatal BH Panel Release 1 v0.1.0,dataset,Zenodo + GitHub,DOI,live,,0 downloads at release,zenodo_record.pdf,Verified per checklist on DATE`
   Publications not logged the day they happen are the ones that go missing later.

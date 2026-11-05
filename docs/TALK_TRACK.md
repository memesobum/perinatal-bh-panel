# Talking about the U.S. County Perinatal Behavioral Health Need and Capacity Panel

*Plain-language summary: what to say when someone asks about this project. Numbers match `report/stats.json` for v0.1.0 and must be re-checked after your verification and any change to the decisions.*

## 60-second version

**The problem:** Mental health conditions are a leading cause of pregnancy-related death. CDC's review of 2020 deaths in 38 states attributed 115 of 511 pregnancy-related deaths with a known cause to them. Agencies deciding where to add screening and treatment for pregnant and postpartum women have had no open, county-by-county picture of where need outruns services.

**What I built:** An open national panel with a row for every one of the 3,144 U.S. counties. It sets measures of need beside treatment capacity: substance use programs for pregnant and postpartum women, community health center sites, and obstetric and behavioral health clinicians. Rural and frontier counties are flagged. It uses only free federal data, and every number traces to a logged source file.

**What it shows:** 57% of counties, holding about one in eight U.S. births, have no substance use treatment program listed for pregnant or postpartum women. That rises to 87% of frontier counties. It also identifies 107 counties where need ranks in the top quarter and capacity in the bottom quarter, most of them rural.

**Who can use it:** state Medicaid and public health agencies, maternal mortality review committees, rural health offices, researchers, and grant writers.

**Where it is:** https://github.com/memesobum/perinatal-bh-panel, with a permanent Zenodo DOI for each release.

## Two-sentence version

I built the first open, county-level panel for every U.S. county that sets perinatal mental health and substance use need beside the treatment available to pregnant and postpartum women, with rural and frontier counties flagged. It grew out of my Nevada county mapping for the Larson Institute and shows that most rural and frontier counties have no listed substance use program for pregnant or postpartum women.

## Questions you may be asked

1. **Where does the data come from?** Only free federal sources: HRSA's Area Health Resources Files and health center sites, Census population estimates, CDC PLACES and the Social Vulnerability Index, USDA rural codes, SAMHSA's FindTreatment.gov directory, and the CMS clinician registry. Each file's address, date, and fingerprint is logged.
2. **What are its limits?** Need uses adult depression and social vulnerability as stand-ins, because no open source measures perinatal depression in every county. The pregnant/postpartum flag exists only for substance use programs. Clinician counts are registrations, not proof of available appointments. Very small counties are unstable and flagged.
3. **Why does this matter for the United States?** Mental health is among the leading causes of pregnancy-related death, and many rural counties have no specialized services. A shared, open, county-level evidence base lets agencies target scarce perinatal behavioral health resources where gaps are largest, and lets anyone check the work.

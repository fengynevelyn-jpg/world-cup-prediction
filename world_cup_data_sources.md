# World Cup Prediction Data Notes

This file is intentionally public-facing and conservative.

## Recommended rule for this repo

Treat third-party data as **user-supplied local input**, not as repository content.

That means this repo should mainly publish:

- code
- schema
- templates
- tiny examples or synthetic demos

It should generally avoid publishing:

- raw third-party dumps
- large mirrored snapshots
- locally generated feature tables based on third-party data
- redistributed market-value tables unless you have confirmed the right to redistribute them

## Source categories used by the local workflow

### 1. StatsBomb open data

Primary source:

- [StatsBomb open-data repo](https://github.com/statsbomb/open-data)

Notes:

- StatsBomb explicitly says the data is made available for public use in research and football analytics.
- Their README also asks that published work attribute StatsBomb and use their logo when sharing research or analysis based on the data.
- Before redistributing derived tables, check the latest upstream terms and decide whether attribution-only is enough for your use case.

## 2. FIFA ranking inputs

Primary source:

- [FIFA men's ranking page](https://inside.fifa.com/en/fifa-world-ranking/men)

Notes:

- Rankings themselves are factual inputs, but the exact historical retrieval path matters.
- If you rely on archived or mirrored ranking pages, document that clearly.

### 3. Historical international results

Local workflow has used a public historical match-results dataset to compute Elo and recent-form features.

Notes:

- Keep the acquisition step separate from this repo when possible.
- Document the exact upstream source and terms before redistributing any processed extracts.

### 4. Squad-value inputs

Local workflow has used:

- World Cup squad pages
- a public Transfermarkt-derived player-value dataset

Conservative publishing guidance:

- treat squad-value features as optional
- do not assume redistribution of player-value tables is safe just because a public GitHub repo exists
- prefer shipping only the code path, and let users supply the local data themselves after reviewing upstream terms

## Practical publishing policy

For a low-risk public release, keep:

- `world_cup_prediction_schema.md`
- `world_cup_matches_template.csv`
- `world_cup_matches_example.csv`
- `world_cup_matches_demo.csv`
- feature-building and training scripts

Exclude from version control:

- raw data under `data/`
- downloaded HTML/ZIP assets
- locally generated feature tables
- experiment result tables
- internal working notes

## Attribution reminder

If you publish analysis or predictions generated from StatsBomb data, include source attribution as requested by StatsBomb:

- [StatsBomb open-data README](https://github.com/statsbomb/open-data)

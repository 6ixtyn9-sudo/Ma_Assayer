# Ma Assayer — Gold Universe Purity Engine

**"Testing the purity of predictions — separating Gold from Charcoal"**

This is the official purity engine for the Ma Golide Gold Universe.

## Architecture
- Satellites (league spreadsheets) → feed clean data to Assayer
- Assayer → produces `ASSAYER_EDGES` + `ASSAYER_LEAGUE_PURITY`
- Mothership → reads the purity contract to build accas

## How to use
1. Point the Assayer at any satellite spreadsheet ID
2. Run "🚀 Run Full Assay"
3. The two output sheets become the official contract for the Mothership

## Repository Structure
All 10 production modules are included.

Made with ❤️ for the Gold Universe.

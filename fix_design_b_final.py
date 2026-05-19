import os

# Fix MODULE 02
f2 = "docs/MODULE 02_Main_Orchestrator"
with open(f2, "r") as f:
    content2 = f.read()
content2 = content2.replace("'🚀 Run Full Assay (Side+Totals only)'", "'🚀 Run Full Assay (All Markets)'")
with open(f2, "w") as f:
    f.write(content2)

# Fix MODULE 07
f7 = "docs/MODULE 07_Parser_Data Parsing"
with open(f7, "r") as f:
    content7 = f.read()

old_vars = """    const allBets = [];
    const sheetSummaries = [];
    const skippedSheets = [];
    let totalSkippedRows = 0;"""

new_vars = """    const allBets = [];
    const sheetSummaries = [];
    const skippedSheets = [];
    let totalSkippedRows = 0;
    let womenIntakeCount = 0;
    let menIntakeCount = 0;"""
content7 = content7.replace(old_vars, new_vars)

old_quarter = """            // Quarter handling for Highest Quarter, etc. (we want it applied to full match = null)
            bet.quarter = null;"""

new_quarter = """            // Quarter handling for Highest Quarter, etc. (we want it applied to full match = null)
            bet.quarter = null;
            
            bet.isWomen = this.isWomenLeague(bet.league, bet.match);
            if (bet.isWomen) womenIntakeCount++;
            else menIntakeCount++;"""
content7 = content7.replace(old_quarter, new_quarter)

old_log = """    this.log.info(`Integrated Other markets into league purity: intakeSheets=${sheetSummaries.length} intakeBets=${allBets.length}`);
    Log_.sectionEnd("Parsing Intake Markets");"""

new_log = """    this.log.info(`Integrated Other markets into league purity: intakeSheets=${sheetSummaries.length} intakeBets=${allBets.length}`);
    this.log.info(`Intake gender classification: ${womenIntakeCount} Women, ${menIntakeCount} Men`);
    Log_.sectionEnd("Parsing Intake Markets");"""
content7 = content7.replace(old_log, new_log)

with open(f7, "w") as f:
    f.write(content7)


# Fix MODULE 08
f8 = "docs/MODULE 08_Stats_Stats Calculations"
with open(f8, "r") as f:
    content8 = f.read()

old_stats = """          if (distinctTypeKeys.length >= 2) {
            for (const tk of distinctTypeKeys) {
              const tkBets = byTypeKey[tk];
              if (!Array.isArray(tkBets) || tkBets.length < Config_.thresholds.minN) continue;

              processSlice(tkBets, league, source, gender, tier, tk);
            }
          }"""

new_stats = """          if (distinctTypeKeys.length >= 2 || source === "Other") {
            for (const tk of distinctTypeKeys) {
              const tkBets = byTypeKey[tk];
              const minNReq = source === "Other" ? 1 : Config_.thresholds.minN;
              if (!Array.isArray(tkBets) || tkBets.length < minNReq) continue;

              processSlice(tkBets, league, source, gender, tier, tk);
            }
          }"""
content8 = content8.replace(old_stats, new_stats)

with open(f8, "w") as f:
    f.write(content8)

print("Applied fixes")

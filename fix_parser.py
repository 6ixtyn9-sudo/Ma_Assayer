import re

file_path = "docs/MODULE 07_Parser_Data Parsing"

with open(file_path, "r") as f:
    content = f.read()

intake_function = """
  // =========================================================================
  // parseIntakeMarketSheets
  // =========================================================================
  parseIntakeMarketSheets(ss) {
    if (!this.log) this.init();
    Log_.section("Parsing Intake Markets");

    const intakeSheets = ss.getSheets().filter(sh => sh.getName().startsWith("INTAKE__"));
    
    if (intakeSheets.length === 0) {
      this.log.info("No INTAKE__ sheets found.");
      Log_.sectionEnd("Parsing Intake Markets");
      return { bets: [], sheetSummaries: [], skippedSheets: [], skippedRows: 0 };
    }

    ColResolver_.init();
    
    // Merge side + totals aliases
    const FLEET_ALIASES = {};
    for (const k in Config_.sideColumnAliases) {
      FLEET_ALIASES[k] = [...Config_.sideColumnAliases[k]];
    }
    for (const k in Config_.totalsColumnAliases) {
      if (FLEET_ALIASES[k]) {
        FLEET_ALIASES[k] = Array.from(new Set([...FLEET_ALIASES[k], ...Config_.totalsColumnAliases[k]]));
      } else {
        FLEET_ALIASES[k] = [...Config_.totalsColumnAliases[k]];
      }
    }
    
    // Intake aliases
    FLEET_ALIASES["market"] = FLEET_ALIASES["type"] || ["market", "type", "bet type"];
    FLEET_ALIASES["result"] = FLEET_ALIASES["outcome"] || ["result", "outcome"];
    
    const allBets = [];
    const sheetSummaries = [];
    const skippedSheets = [];
    let totalSkippedRows = 0;

    for (const sheet of intakeSheets) {
        const sheetName = sheet.getName();
        const data = sheet.getDataRange().getValues();
        if (data.length < 2) {
            skippedSheets.push(sheetName);
            continue;
        }

        const headers = data[0];
        const resolveResult = ColResolver_.resolve(headers, FLEET_ALIASES, sheetName);
        const resolved = resolveResult.resolved;

        const hasLeague = resolved['league'] !== undefined;
        const hasMarket = resolved['market'] !== undefined || resolved['type'] !== undefined;
        const hasOutcome = resolved['result'] !== undefined || resolved['outcome'] !== undefined;
        const hasMatch = resolved['match'] !== undefined || (resolved['home'] !== undefined && resolved['away'] !== undefined);

        if (!hasLeague || !hasMarket || !hasOutcome || !hasMatch) {
            const missing = [];
            if (!hasLeague) missing.push('league');
            if (!hasMarket) missing.push('market/type');
            if (!hasOutcome) missing.push('outcome/result');
            if (!hasMatch) missing.push('match OR (home+away)');

            this.log.warn(`Skipping sheet ${sheetName}: missing required columns: ${missing.join(', ')}`);
            this.log.warn(`Headers: [${headers.slice(0, 20).join(', ')}]`);
            skippedSheets.push(sheetName);
            continue;
        }

        let parsed = 0;
        let skipped = 0;

        for (let i = 1; i < data.length; i++) {
            const row = data[i];
            
            if (row.every(cell => cell === "" || cell === null || cell === undefined)) {
                skipped++;
                continue;
            }

            const leagueRaw = this.getValue(row, resolved, "league");
            if (!leagueRaw || String(leagueRaw).trim() === "") {
                skipped++;
                continue;
            }

            const rawMarket = String(this.getValue(row, resolved, "market") || this.getValue(row, resolved, "type") || "");
            const rawOutcome = this.getValue(row, resolved, "result") || this.getValue(row, resolved, "outcome");

            const bet = {};
            bet.league = String(leagueRaw).trim().toUpperCase();
            
            // typeKey
            const sanitizedMarket = (rawMarket || "UNKNOWN")
                .replace(/[^a-z0-9]/gi, '_')
                .replace(/_+/g, '_')
                .toUpperCase()
                .slice(0, 20);
            bet.typeKey = sanitizedMarket;
            bet.type = rawMarket;
            
            bet.tier = this.parseTier(this.getValue(row, resolved, "tier"));
            bet.result = this.parseOutcome(rawOutcome);
            bet.source = "Other";

            bet.match = this.getValue(row, resolved, "match");
            bet.home = this.getValue(row, resolved, "home");
            bet.away = this.getValue(row, resolved, "away");
            bet.date = this.getValue(row, resolved, "date");
            bet.time = this.getValue(row, resolved, "time");
            
            bet.pick = this.getValue(row, resolved, "pick");
            bet.line = this.getValue(row, resolved, "line");
            bet.direction = this.parseDirection(this.getValue(row, resolved, "direction"));
            
            // Quarter handling for Highest Quarter, etc. (we want it applied to full match = null)
            bet.quarter = null;
            
            bet.confidence = this.parseConfidence(this.getValue(row, resolved, "confidence"));
            bet.odds = this.parseOdds(this.getValue(row, resolved, "odds"));
            bet.units = this.getValue(row, resolved, "units");
            bet.ev = this.getValue(row, resolved, "ev");
            bet.notes = this.getValue(row, resolved, "notes");
            
            if (bet.result === 1) bet.win = 1;
            else if (bet.result === 0) bet.loss = 1;
            else if (bet.result === -1) bet.push = 1;

            allBets.push(bet);
            parsed++;
        }
        
        sheetSummaries.push({ sheetName, rowsRead: data.length - 1, rowsParsed: parsed, rowsSkipped: skipped });
        totalSkippedRows += skipped;
        this.log.info(`Parsed ${sheetName}: ${parsed} bets, ${skipped} skipped`);
    }

    this.log.info(`Integrated Other markets into league purity: intakeSheets=${sheetSummaries.length} intakeBets=${allBets.length}`);
    Log_.sectionEnd("Parsing Intake Markets");
    
    return { bets: allBets, sheetSummaries, skippedSheets, skippedRows: totalSkippedRows };
  }
};
"""

target = "return mismatches;\n}"
replacement = f"return mismatches;\n  }},\n{intake_function}"

if "parseIntakeMarketSheets(ss)" not in content:
    # Check if the file ends with "return mismatches;\n}"
    # The file might have "return mismatches;\n};"
    if "return mismatches;\n};" in content:
        content = content.replace("return mismatches;\n};", f"return mismatches;\n  }},\n{intake_function}")
    else:
        content = content.replace(target, replacement)
        
    with open(file_path, "w") as f:
        f.write(content)
        
print("Updated Parser")

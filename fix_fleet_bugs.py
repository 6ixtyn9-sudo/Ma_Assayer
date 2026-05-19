import re

file_path = "docs/MODULE 11_FleetImport_Fleet Accuracy Report Ingestion"

with open(file_path, "r") as f:
    content = f.read()

# 1) nextRowStringCount & mergedHeader
content = content.replace("log.info(`Chosen header row index (1-based) = ${bestRowIdx + (nextRowStringCount > 5 ? 0 : 1)}`);", "log.info(`Chosen header row index (1-based) = ${bestRowIdx + (mergedHeader ? 0 : 1)}`);")

content = content.replace("let finalHeaders = data[bestRowIdx].map(h => String(h || '').trim());", "let finalHeaders = data[bestRowIdx].map(h => String(h || '').trim());\n    let mergedHeader = false;")
content = content.replace("bestRowIdx++; \n      }", "bestRowIdx++; \n          mergedHeader = true;\n      }")


# 2) Token hits logic
old_token_logic = "if (tokens.some(t => cLower.includes(t) || t.includes(cLower))) {"
new_token_logic = "if (tokens.some(t => cLower.includes(t) || (cLower.length >= 3 && t.includes(cLower)))) {"
content = content.replace(old_token_logic, new_token_logic)


# 3) Robust Side/Totals flush
old_flush_check = """      const currentHeaders = sheet.getRange(1, 1, 1, sheet.getLastColumn() || 1).getValues()[0];
      if (tabName === Config_.sheets.side || tabName === Config_.sheets.totals) {
         if (currentHeaders.join(',') !== headers.join(',')) {
             log.error(`STOP: ${tabName} schema mismatch! Expected [${headers.join(',')}] but got [${currentHeaders.join(',')}]`);
             runReport.errors.push({ reason: `${tabName}_SCHEMA_MISMATCH`, expected: headers, actual: currentHeaders });
             continue; 
         }
      }"""

new_flush_check = """      // Force Side and Totals header row 1 when we clearBeforeImport
      // Here we just ensure row 1 matches exactly.
      if (tabName === Config_.sheets.side || tabName === Config_.sheets.totals) {
         sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
         sheet.setFrozenRows(1);
         sheet.getRange(1, 1, 1, headers.length)
            .setFontWeight('bold')
            .setBackground(Config_.colors.header)
            .setFontColor(Config_.colors.headerText);
      }"""
content = content.replace(old_flush_check, new_flush_check)


# 4) Minimum viable schema (hasDate)
old_has_date = "const hasDate = resolved['date'] !== undefined || resolved['time'] !== undefined;"
new_has_date = "const hasDate = resolved['date'] !== undefined;"
content = content.replace(old_has_date, new_has_date)

with open(file_path, "w") as f:
    f.write(content)

print("Applied fixes")

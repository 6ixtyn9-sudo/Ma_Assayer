import re

file_path = "docs/MODULE 11_FleetImport_Fleet Accuracy Report Ingestion"

with open(file_path, "r") as f:
    content = f.read()

# 1) Column alias merge in importAccuracyReports_
old_resolver = """        ColResolver_.init();
        const resolveResult = ColResolver_.resolve(
          headers, Config_.sideColumnAliases, `AR_${sat.id.slice(0,8)}`
        );"""

new_resolver = """        ColResolver_.init();
        
        // Merge Side + Totals aliases
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

        const resolveResult = ColResolver_.resolve(
          headers, FLEET_ALIASES, `AR_${sat.id.slice(0,8)}`
        );"""

content = content.replace(old_resolver, new_resolver)

# 2) 2-row header merge logic
old_merge_logic = """    let finalHeaders = data[bestRowIdx].map(h => String(h || '').trim());
    let mergedHeader = false;
    
    if (bestRowIdx + 1 < data.length) {
      let nextRowStringCount = 0;
      const nextRow = data[bestRowIdx + 1];
      for (const cell of nextRow) {
          if (cell !== '' && typeof cell === 'string' && isNaN(cell)) {
              nextRowStringCount++;
          }
      }
      if (nextRowStringCount > 5) { 
          for (let i = 0; i < finalHeaders.length; i++) {
              const subH = String(nextRow[i] || '').trim();
              if (subH) finalHeaders[i] = finalHeaders[i] ? finalHeaders[i] + ' ' + subH : subH;
          }
          bestRowIdx++; 
          mergedHeader = true;
      }
    }
    
    log.info(`Chosen header row index (1-based) = ${bestRowIdx + (mergedHeader ? 0 : 1)}`);"""

new_merge_logic = """    let finalHeaders = data[bestRowIdx].map(h => String(h || '').trim());
    let mergedHeader = false;
    let mergeReason = 'None';
    
    if (bestRowIdx + 1 < data.length) {
      const nextRow = data[bestRowIdx + 1];
      const mergeCheck = this.shouldMergeHeader_(data[bestRowIdx], nextRow, tokens, bestTokensHit);
      
      if (mergeCheck.merge) { 
          for (let i = 0; i < finalHeaders.length; i++) {
              const subH = String(nextRow[i] || '').trim();
              if (subH) finalHeaders[i] = finalHeaders[i] ? finalHeaders[i] + ' ' + subH : subH;
          }
          bestRowIdx++; 
          mergedHeader = true;
      }
      mergeReason = mergeCheck.reason;
    }
    
    log.info(`HeaderMerge: merged=${mergedHeader} (reason: ${mergeReason})`);
    log.info(`Chosen header row index (1-based) = ${bestRowIdx + (mergedHeader ? 0 : 1)}`);"""

content = content.replace(old_merge_logic, new_merge_logic)

# 3) Add shouldMergeHeader_ helper right after readAccuracyReport_
old_helper_anchor = """  // ─── Market routing ───────────────────────────────────────────────────────"""

new_helper = """  shouldMergeHeader_(headerRow, nextRow, tokens, headerRowTokenHits) {
    if (headerRowTokenHits < 3) return { merge: false, reason: 'Header tokenHits < 3' };
    
    let numericLikeCount = 0;
    let nextRowTokenHits = 0;
    let blankInHeaderCount = 0;
    let filledByNextRowCount = 0;
    
    const maxLen = Math.max(headerRow.length, nextRow.length);
    for (let i = 0; i < maxLen; i++) {
        const hCell = String(headerRow[i] || '').trim();
        const nCell = String(nextRow[i] || '').trim();
        
        if (!hCell) {
            blankInHeaderCount++;
            if (nCell) filledByNextRowCount++;
        }
    }
    
    for (const cell of nextRow) {
        if (cell === '' || cell === null || cell === undefined) continue;
        const sCell = String(cell).trim();
        const cLower = sCell.toLowerCase();
        
        let isNumLike = false;
        if (!isNaN(sCell)) isNumLike = true; 
        else if (/^[-+]?\\d+$/.test(sCell)) isNumLike = true; 
        else if (/\\d{1,2}[-/]\\d{1,2}/.test(sCell)) isNumLike = true; 
        else if (/\\d{1,2}:\\d{2}/.test(sCell)) isNumLike = true; 
        
        if (isNumLike) {
            numericLikeCount++;
        } else if (tokens.some(t => cLower.includes(t) || (cLower.length >= 3 && t.includes(cLower)))) {
            nextRowTokenHits++;
        }
    }
    
    if (numericLikeCount > 2) return { merge: false, reason: `numericLikeCount=${numericLikeCount} > 2` };
    if (nextRowTokenHits < 2) return { merge: false, reason: `nextRowTokenHits=${nextRowTokenHits} < 2` };
    if (blankInHeaderCount < 3) return { merge: false, reason: `blankInHeaderCount=${blankInHeaderCount} < 3` };
    if (filledByNextRowCount < 2) return { merge: false, reason: `filledByNextRowCount=${filledByNextRowCount} < 2` };
    
    return { merge: true, reason: 'Met all criteria' };
  },

  // ─── Market routing ───────────────────────────────────────────────────────"""

content = content.replace(old_helper_anchor, new_helper)

with open(file_path, "w") as f:
    f.write(content)

print("Applied fixes")

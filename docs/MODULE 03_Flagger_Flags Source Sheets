/******************************************************************************
 * MA ASSAYER — Complete Production Module
 * 
 * "Testing the purity of predictions - separating Gold from Charcoal"
 * 
 * COMPLETE ROBUST IMPLEMENTATION
 * 
 * ARCHITECTURE:
 * ├── M1_Output_          Sheet Writers
 * ├── M2_Main_            Controller/Orchestrator
 * ├── M3_Flagger_         Apply Flags to Source
 * ├── M4_Discovery_       Edge Discovery Engine
 * ├── M5_Config_          Configuration & Constants
 * ├── M6_ColResolver_     Fuzzy Column Matching (case-insensitive)
 * ├── M7_Parser_          Data Parsing
 * ├── M8_Stats_           Statistical Calculations
 * ├── M9_Utils_           Utility Functions
 * └── M10_Log_            Logging System
 ******************************************************************************/
 
// ============================================================================
// MODULE: Flagger_ — Apply Flags to Source Sheets
// ============================================================================

const Flagger_ = {
  log: null,

  GRADE_ORDER: ["CHARCOAL", "ROCK", "BRONZE", "SILVER", "GOLD", "PLATINUM"],

  init() {
    this.log = Log_.module("FLAGGER");
  },

  applyFlags(ss, edges, leagueAssay, teamAssay, matchupAssay) {
    if (leagueAssay === undefined) leagueAssay = {};
    if (teamAssay === undefined) teamAssay = {};
    if (matchupAssay === undefined) matchupAssay = {};
    if (!this.log) this.init();
    Log_.section("Applying Flags");

    const sideEdges = edges.filter(e => e.source === "Side");
    const totalsEdges = edges.filter(e => e.source === "Totals");

    this.log.info(`Processing ${sideEdges.length} side edges, ${totalsEdges.length} totals edges`);

    const sideResult = this.flagSheet(ss, Config_.sheets.side, sideEdges, leagueAssay, "side", teamAssay, matchupAssay);
    const totalsResult = this.flagSheet(ss, Config_.sheets.totals, totalsEdges, leagueAssay, "totals", teamAssay, matchupAssay);

    const summary = {
      side: sideResult,
      totals: totalsResult,
      totalFlagged: (sideResult ? sideResult.flagged : 0) + (totalsResult ? totalsResult.flagged : 0),
      totalRows: (sideResult ? sideResult.total : 0) + (totalsResult ? totalsResult.total : 0)
    };

    this.log.success(`Flagging complete: ${summary.totalFlagged}/${summary.totalRows} rows flagged`);
    Log_.sectionEnd("Applying Flags");

    return summary;
  },

  _buildEdgeIndex(edges) {
    const index = new Map();

    for (const edge of edges) {
      if (!edge.criteria || typeof edge.criteria !== "object") continue;

      const keys = Object.keys(edge.criteria);
      if (keys.length === 0) continue;

      const firstKey = keys.sort()[0];
      const firstVal = edge.criteria[firstKey];
      const indexKey = `${firstKey}:${firstVal}`;

      if (!index.has(indexKey)) {
        index.set(indexKey, []);
      }
      index.get(indexKey).push(edge);
    }

    return index;
  },

  flagSheet(ss, sheetName, edges, leagueAssay, type, teamAssay, matchupAssay) {
    if (teamAssay === undefined) teamAssay = {};
    if (matchupAssay === undefined) matchupAssay = {};
    if (!this.log) this.init();

    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      this.log.warn(`Sheet not found: ${sheetName}`);
      return { success: false, error: "Sheet not found" };
    }

    const data = sheet.getDataRange().getValues();
    if (data.length < 2) {
      this.log.warn(`No data in sheet: ${sheetName}`);
      return { success: false, error: "No data", total: 0, flagged: 0 };
    }

    const headers = data[0];

    const flagCol = this.findOrCreateColumn(sheet, headers,
      ["ma_edgeflags", "maassayer", "ma flag", "edge flag", "flags"], "MA_EdgeFlags");
    const gradeCol = this.findOrCreateColumn(sheet, headers,
      ["ma_grade", "purity", "purity grade"], "MA_Grade");
    const statusCol = this.findOrCreateColumn(sheet, headers,
      ["ma_status", "edge status"], "MA_Status");

    const aliases = type === "side" ? Config_.sideColumnAliases : Config_.totalsColumnAliases;
    ColResolver_.init();
    const { resolved } = ColResolver_.resolve(headers, aliases, sheetName);

    const edgeIndex = this._buildEdgeIndex(edges);

    const outFlags = [];
    const outGrades = [];
    const outStatuses = [];

    let flaggedCount = 0;
    let toxicCount = 0;
    let highQualityCount = 0;

    const PROGRESS_CHUNK = 500;
    const processingStartTime = Date.now();
    const MAX_PROCESSING_MS = 5 * 60 * 1000;
    let timeoutReached = false;

    for (let i = 1; i < data.length; i++) {
      if ((i - 1) % PROGRESS_CHUNK === 0 && i > 1) {
        const elapsed = Date.now() - processingStartTime;
        this.log.info(`${sheetName}: Processed ${i - 1}/${data.length - 1} rows (${elapsed}ms)`);

        if (elapsed > MAX_PROCESSING_MS) {
          this.log.warn(`${sheetName}: Timeout approaching after ${i - 1} rows, completing early`);
          timeoutReached = true;
          break;
        }
      }

      const row = data[i];

      const bet = this.parseRowForMatching(row, resolved, type);

      const result = this.evaluateRow(bet, edges, leagueAssay, edgeIndex, teamAssay, matchupAssay);

      if (result.matchedEdges.length > 0) flaggedCount++;
      if (result.isToxic) toxicCount++;
      if (result.bestGrade === "GOLD" || result.bestGrade === "PLATINUM") highQualityCount++;

      outFlags.push([result.matchedEdges.join(" | ") || ""]);
      outGrades.push([this.formatGrade(result.bestGrade)]);
      outStatuses.push([result.status]);
    }

    if (outFlags.length > 0) {
      sheet.getRange(2, flagCol, outFlags.length, 1).setValues(outFlags);
      sheet.getRange(2, gradeCol, outGrades.length, 1).setValues(outGrades);
      sheet.getRange(2, statusCol, outStatuses.length, 1).setValues(outStatuses);
    }

    const resultMsg = timeoutReached ? " (truncated due to timeout)" : "";
    this.log.success(`${sheetName}: ${flaggedCount}/${outFlags.length} flagged, ` +
                     `${toxicCount} toxic, ${highQualityCount} high-quality${resultMsg}`);

    return {
      success: true,
      total: outFlags.length,
      flagged: flaggedCount,
      toxic: toxicCount,
      highQuality: highQualityCount,
      truncated: timeoutReached
    };
  },

  evaluateRow(bet, edges, leagueAssay, edgeIndex, teamAssay, matchupAssay) {
    if (edgeIndex === undefined || edgeIndex === null) edgeIndex = null;
    if (teamAssay === undefined || teamAssay === null) teamAssay = null;
    if (matchupAssay === undefined || matchupAssay === null) matchupAssay = null;

    const matchedEdges = [];
    let bestGrade = "CHARCOAL";
    let status = "—";
    let isToxic = false;
    let bestEdge = null;

    const league = (bet && bet.league) ? String(bet.league).trim().toUpperCase() : "";
    const betSource = (bet && bet.source) ? bet.source : ((bet && bet.side) ? "Side" : ((bet && bet.direction) ? "Totals" : null));
    const gender = (bet && bet.isWomen) ? "W" : "M";
    const tier = (bet && bet.tier) ? String(bet.tier).trim().toUpperCase() : "UNKNOWN";
    const quarterVal = (bet && typeof bet.quarter === "number" && isFinite(bet.quarter)) ? bet.quarter : null;

      const tryAssayKeys = () => {
    if (!league || !betSource) return null;

    const keys = [];

    // v4.3.0: derive typeKey for Totals bets
    let betTypeKey = "";
    if (betSource === "Totals" && bet) {
      if (bet.typeKey) {
        betTypeKey = bet.typeKey;
      } else if (typeof Discovery_ !== "undefined" && Discovery_._getTotalsTypeKey) {
        betTypeKey = Discovery_._getTotalsTypeKey(bet);
      } else if (typeof Parser_ !== "undefined" && Parser_._deriveTotalsTypeKey) {
        betTypeKey = Parser_._deriveTotalsTypeKey(bet);
      }
    }

    // v4.3.0: typeKey-specific keys first (Totals only, most precise)
    if (betTypeKey) {
      if (quarterVal != null) keys.push(`${league}_Q${quarterVal}_${betSource}_${gender}_${tier}_${betTypeKey}`);
      keys.push(`${league}_${betSource}_${gender}_${tier}_${betTypeKey}`);
    }

    // Existing keys (aggregate, backward-compatible)
    if (quarterVal != null) keys.push(`${league}_Q${quarterVal}_${betSource}_${gender}_${tier}`);
    keys.push(`${league}_${betSource}_${gender}_${tier}`);

    if (quarterVal != null) keys.push(`${league}_Q${quarterVal}_${betSource}_${gender}_UNKNOWN`);
    keys.push(`${league}_${betSource}_${gender}_UNKNOWN`);

    if (quarterVal != null) keys.push(`${league}_Q${quarterVal}_${betSource}`);
    keys.push(`${league}_${betSource}`);

    for (const k of keys) {
      if (leagueAssay && leagueAssay[k]) return leagueAssay[k];
    }

    const entries = Object.values(leagueAssay || {}).filter(l => l && l.league === league);
    if (entries.length === 0) return null;

    const best =
      entries.find(l => l.source === betSource && l.quarter === quarterVal && l.gender === gender && l.tier === tier && l.typeKey === betTypeKey) ||
      entries.find(l => l.source === betSource && l.quarter === quarterVal && l.gender === gender && l.tier === tier) ||
      entries.find(l => l.source === betSource && l.quarter == null && l.gender === gender && l.tier === tier) ||
      entries.find(l => l.source === betSource && l.quarter === quarterVal) ||
      entries.find(l => l.source === betSource && l.quarter == null) ||
      entries.find(l => l.source === betSource) ||
      entries[0];

    return best || null;
  };

    const leagueInfo = league ? tryAssayKeys() : null;

    const isKnownToxicLeague =
      league && Array.isArray(Config_.toxicLeagues) ? Config_.toxicLeagues.includes(league) : false;

    const isAssayToxicLeague =
      !!(leagueInfo && (leagueInfo.isToxic || leagueInfo.grade === "CHARCOAL"));

    const leagueBlocks = isKnownToxicLeague || isAssayToxicLeague;

    const backedTeam = (bet && bet.backedTeam) ? String(bet.backedTeam).trim().toUpperCase() : null;
    const matchupKey = (bet && bet.matchupKey) ? String(bet.matchupKey).trim().toUpperCase() : null;

    const teamKeyFn = (team, q) => (q == null ? team : `${team}__Q${q}`);
    const matchupKeyQFn = (mk, q) => (q == null ? mk : `${mk}__Q${q}`);

    let teamInfo = null;
    if (betSource === "Side" && backedTeam && teamAssay) {
      if (quarterVal != null && teamAssay[teamKeyFn(backedTeam, quarterVal)]) {
        teamInfo = teamAssay[teamKeyFn(backedTeam, quarterVal)];
      } else if (teamAssay[teamKeyFn(backedTeam, null)]) {
        teamInfo = teamAssay[teamKeyFn(backedTeam, null)];
      }
    }

    let matchupInfo = null;
    if (betSource === "Side" && matchupKey && matchupAssay) {
      if (quarterVal != null && matchupAssay[matchupKeyQFn(matchupKey, quarterVal)]) {
        matchupInfo = matchupAssay[matchupKeyQFn(matchupKey, quarterVal)];
      } else if (matchupAssay[matchupKeyQFn(matchupKey, null)]) {
        matchupInfo = matchupAssay[matchupKeyQFn(matchupKey, null)];
      }
    }

    const teamBlocks = !!(teamInfo && (teamInfo.isToxic || teamInfo.grade === "CHARCOAL"));
    const teamOverridesLeague = !!(teamInfo && (teamInfo.isElite || teamInfo.grade === "GOLD" || teamInfo.grade === "PLATINUM"));

    const matchupBlocks = !!(matchupInfo && (matchupInfo.isToxic || matchupInfo.grade === "CHARCOAL"));
    const matchupOverridesLeague = !!(matchupInfo && (matchupInfo.isElite || matchupInfo.grade === "GOLD" || matchupInfo.grade === "PLATINUM"));

    if (matchupBlocks) {
      matchedEdges.push("⛔TOXIC_MATCHUP");
      bestGrade = "CHARCOAL";
      isToxic = true;
      const qLab = (matchupInfo && matchupInfo.quarterLabel) ? ` (${matchupInfo.quarterLabel})` : "";
      const mBacked = (matchupInfo && matchupInfo.backedTeam) ? matchupInfo.backedTeam : (backedTeam || "?");
      const mOpp = (matchupInfo && matchupInfo.opponentTeam) ? matchupInfo.opponentTeam : ((bet && bet.opponentTeam) ? bet.opponentTeam : "?");
      status = `⛔ Toxic Matchup: ${mBacked} vs ${mOpp}${qLab}`;

    } else if (teamBlocks) {
      matchedEdges.push("⛔TOXIC_TEAM");
      bestGrade = "CHARCOAL";
      isToxic = true;
      const tqLab = (teamInfo && teamInfo.quarterLabel) ? ` (${teamInfo.quarterLabel})` : "";
      status = `⛔ Toxic Team: ${backedTeam}${tqLab}`;

    } else if (leagueBlocks && !(teamOverridesLeague || matchupOverridesLeague)) {
      matchedEdges.push("⛔TOXIC_LEAGUE");
      bestGrade = "CHARCOAL";
      isToxic = true;
      const qPart = quarterVal == null ? "" : (quarterVal === 0 ? " Full" : ` Q${quarterVal}`);
      status = `⛔ Toxic (${betSource || "?"} ${gender} ${tier}${qPart})`;

    } else {
      if (leagueBlocks && (teamOverridesLeague || matchupOverridesLeague)) {
        matchedEdges.push("⚠️TOXIC_LEAGUE_OVERRIDDEN");
      }

      if (matchupInfo && matchupOverridesLeague) {
        matchedEdges.push(`💠MATCHUP_${matchupInfo.grade}`);

        if (this.GRADE_ORDER.indexOf(matchupInfo.grade) > this.GRADE_ORDER.indexOf(bestGrade)) {
          bestGrade = matchupInfo.grade;
        }

        const mSym = matchupInfo.gradeSymbol || matchupInfo.grade;
        const mBacked2 = matchupInfo.backedTeam || backedTeam || "?";
        const mOpp2 = matchupInfo.opponentTeam || ((bet && bet.opponentTeam) ? bet.opponentTeam : "?");
        const mQLab = matchupInfo.quarterLabel || "All";
        status = `💠 ${mSym} ${mBacked2} vs ${mOpp2} (${mQLab})`;

      } else if (teamInfo && teamOverridesLeague) {
        matchedEdges.push(`💎TEAM_${teamInfo.grade}`);

        if (this.GRADE_ORDER.indexOf(teamInfo.grade) > this.GRADE_ORDER.indexOf(bestGrade)) {
          bestGrade = teamInfo.grade;
        }

        const tSym = teamInfo.gradeSymbol || teamInfo.grade;
        const tQLab = teamInfo.quarterLabel || "All";
        status = `💎 ${tSym} ${backedTeam} (${tQLab})`;

      } else if (leagueInfo && (leagueInfo.grade === "GOLD" || leagueInfo.grade === "PLATINUM")) {
        const symbol = leagueInfo.gradeSymbol || leagueInfo.grade;
        const qLabel = leagueInfo.quarter == null ? "All" : (leagueInfo.quarter === 0 ? "Full" : `Q${leagueInfo.quarter}`);
        status = `🏆 ${symbol} ${leagueInfo.source || betSource} ${leagueInfo.gender || gender} ${leagueInfo.tier || tier} ${qLabel}`;
      }
    }

    if (!isToxic) {
      let candidateEdges = edges;

      if (edgeIndex && edgeIndex.size > 0) {
        const candidateSet = new Set();
        const betEntries = Object.entries(bet || {});
        for (let ei = 0; ei < betEntries.length; ei++) {
          const bKey = betEntries[ei][0];
          const bVal = betEntries[ei][1];
          if (bVal == null) continue;
          const indexed = edgeIndex.get(`${bKey}:${bVal}`);
          if (indexed) {
            for (let ix = 0; ix < indexed.length; ix++) {
              candidateSet.add(indexed[ix]);
            }
          }
        }
        if (candidateSet.size > 0) candidateEdges = Array.from(candidateSet);
      }

      for (let ce = 0; ce < candidateEdges.length; ce++) {
        const edge = candidateEdges[ce];
        if (this.matchesCriteria(bet, edge.criteria)) {
          matchedEdges.push(edge.id);

          if (this.GRADE_ORDER.indexOf(edge.grade) > this.GRADE_ORDER.indexOf(bestGrade)) {
            bestGrade = edge.grade;
            bestEdge = edge;
          }

          const symbol = edge.gradeSymbol || edge.grade;
          if (edge.grade === "PLATINUM" || edge.grade === "GOLD") {
            status = `✨ ${symbol} ${this.truncate(edge.name, 20)}`;
          } else if (edge.grade === "SILVER" && status.indexOf("✨") === -1) {
            status = `🥈 ${this.truncate(edge.name, 20)}`;
          }
        }
      }

      if (matchedEdges.length > 0 && status === "—") {
        status = `${matchedEdges.length} edge(s) matched`;
      }
    }

    const isSystemMarker = (x) => /^⛔|^⚠️|^💎|^💠/.test(String(x || ""));
    const edgeCount = matchedEdges.filter(e => !isSystemMarker(e)).length;

    return {
      matchedEdges: matchedEdges,
      bestGrade: bestGrade,
      bestEdge: bestEdge,
      status: status,
      isToxic: isToxic,
      edgeCount: edgeCount
    };
  },

  // =========================================================================
  // v4.3.0 PATCH: typeKey fallback for when Discovery_ is unavailable
  // =========================================================================

  _getTotalsTypeKeyFallback(bet) {
    if (!bet) return "UNKNOWN";
    if (bet.typeKey) return bet.typeKey;

    const raw = String(bet.type || "").trim().toUpperCase().replace(/\s+/g, " ");
    if (!raw) return "UNKNOWN";

    const hasSniper = raw.indexOf("SNIPER") !== -1;
    const hasOU = raw.indexOf("O/U") !== -1 ||
                  raw.indexOf("OU") !== -1 ||
                  raw.indexOf("OVER/UNDER") !== -1 ||
                  raw.indexOf("OVER UNDER") !== -1 ||
                  raw.indexOf("TOTAL") !== -1;

    if (hasSniper && hasOU) {
      if (raw.indexOf("DIR") !== -1) return "SNIPER_OU_DIR";
      if (raw.indexOf("STAR") !== -1) return "SNIPER_OU_STAR";
      return "SNIPER_OU";
    }

    if (hasOU) {
      if (raw.indexOf("DIR") !== -1) return "OU_DIR";
      if (raw.indexOf("STAR") !== -1) return "OU_STAR";
      return "OU";
    }

    return "OTHER";
  },

  // =========================================================================
  // v4.3.0 PATCH: matchesCriteria auto-derives typeKey
  // =========================================================================

    matchesCriteria(bet, criteria) {
    if (!criteria || typeof criteria !== "object" || Object.keys(criteria).length === 0) return false;
    if (!bet || typeof bet !== "object") return false;

    var norm = function(x) {
      if (x === null || x === undefined) return x;
      if (typeof x === "boolean") return x;
      if (typeof x === "number") return isFinite(x) ? x : null;

      var s = String(x).trim();
      if (s === "") return "";

      if (/^[+-]?\d+(\.\d+)?$/.test(s)) {
        var n = parseFloat(s);
        return isFinite(n) ? n : null;
      }
      return s.toUpperCase();
    };

    var criteriaEntries = Object.entries(criteria);
    for (var i = 0; i < criteriaEntries.length; i++) {
      var key = criteriaEntries[i][0];
      var expected = criteriaEntries[i][1];
      var actual = bet[key];

      // v4.3.0: auto-derive typeKey if missing on the bet
      if (key === "typeKey" && (actual === undefined || actual === null)) {
        if (typeof Discovery_ !== "undefined" && Discovery_._getTotalsTypeKey) {
          actual = Discovery_._getTotalsTypeKey(bet);
        } else {
          actual = this._getTotalsTypeKeyFallback(bet);
        }
      }

      if (actual === undefined || actual === null) return false;
      if (norm(actual) !== norm(expected)) return false;
    }

    return true;
  },

    flagBet(bet, edges, leagueAssay, teamAssay, matchupAssay) {
    var safeEdges = Array.isArray(edges) ? edges : [];
    var edgeIndex = this._buildEdgeIndex(safeEdges);

    return this.evaluateRow(
      bet,
      safeEdges,
      leagueAssay || {},
      edgeIndex,
      teamAssay || null,
      matchupAssay || null
    );
  },

  // =========================================================================
  // v4.3.0 PATCH: parseRowForMatching adds source + type + typeKey for totals
  // =========================================================================

  parseRowForMatching(row, resolved, type) {
    const self = this;

    const getValue = (key, defaultVal) => {
      if (defaultVal === undefined) defaultVal = "";
      if (typeof Parser_ !== "undefined" && Parser_.getValue) {
        return Parser_.getValue(row, resolved, key, defaultVal);
      }
      const idx = resolved[key];
      return (idx !== undefined && idx >= 0 && idx < row.length) ? row[idx] : defaultVal;
    };

    const pick = getValue("pick", "");
    const league = String(getValue("league", "")).trim().toUpperCase();
    const match = String(getValue("match", ""));
    const confRaw = getValue("confidence");

    const conf = (typeof Parser_ !== "undefined" && Parser_.parseConfidence)
      ? Parser_.parseConfidence(confRaw)
      : self._parseConfidenceFallback(confRaw);

    const tierRaw = getValue("tier");
    const tier = (typeof Parser_ !== "undefined" && Parser_.parseTier)
      ? Parser_.parseTier(tierRaw)
      : self._parseTierFallback(tierRaw);

    const quarterRaw = getValue("quarter");
    const quarter = (typeof Parser_ !== "undefined" && Parser_.parseQuarter)
      ? Parser_.parseQuarter(quarterRaw)
      : self._parseQuarterFallback(quarterRaw);

    const isWomen = (typeof Parser_ !== "undefined" && Parser_.isWomenLeague)
      ? Parser_.isWomenLeague(league, match)
      : self._isWomenFallback(league, match);

    const confBucket = (typeof Parser_ !== "undefined" && Parser_.getConfBucket)
      ? Parser_.getConfBucket(conf)
      : self._getConfBucketFallback(conf);

    // v4.3.0: include source so evaluateRow can derive betSource
    const base = {
      source: type === "side" ? "Side" : "Totals",
      league: league,
      isWomen: isWomen,
      confBucket: confBucket,
      tier: tier,
      quarter: quarter
    };

    if (type === "side") {
      const spread = (typeof Parser_ !== "undefined" && Parser_.parseSpread)
        ? Parser_.parseSpread(pick)
        : self._parseSpreadFallback(pick);

      const side = (typeof Parser_ !== "undefined" && Parser_.parseSide)
        ? Parser_.parseSide(pick, getValue("side"))
        : self._parseSideFallback(pick, getValue("side"));

      const spreadBucket = (typeof Parser_ !== "undefined" && Parser_.getSpreadBucket)
        ? Parser_.getSpreadBucket(spread)
        : self._getSpreadBucketFallback(spread);

      base.side = side;
      base.spreadBucket = spreadBucket;

      const norm = (s) => {
        if (typeof Parser_ !== "undefined" && Parser_.normalizeTeamName) {
          return Parser_.normalizeTeamName(s);
        }
        return s ? String(s).trim().toUpperCase() : null;
      };

      let home = norm(getValue("home", ""));
      let away = norm(getValue("away", ""));

      if ((!home || !away) && (typeof Parser_ !== "undefined" && Parser_.extractTeamsFromMatch)) {
        const parsed = Parser_.extractTeamsFromMatch(match);
        home = home || parsed.home;
        away = away || parsed.away;
      }

      let backedTeam = null;
      if (typeof Parser_ !== "undefined" && Parser_.deriveBackedTeam) {
        backedTeam = Parser_.deriveBackedTeam({ side: side, home: home, away: away, pick: pick, match: match });
      } else {
        backedTeam = (side === "H") ? home : ((side === "A") ? away : null);
      }

      let opponentTeam = null;
      if (backedTeam && home && away) {
        opponentTeam = (backedTeam === home) ? away : ((backedTeam === away) ? home : null);
      }

      const matchupKey = (backedTeam && opponentTeam) ? `${backedTeam}__VS__${opponentTeam}` : null;

      base.backedTeam = backedTeam || null;
      base.opponentTeam = opponentTeam || null;
      base.matchupKey = matchupKey || null;

    } else {
      // totals
      const lineRaw = getValue("line");
      const line = (typeof Parser_ !== "undefined" && Parser_.parseLine)
        ? Parser_.parseLine(lineRaw)
        : self._parseLineFallback(lineRaw);

      const direction = (typeof Parser_ !== "undefined" && Parser_.parseDirection)
        ? Parser_.parseDirection(getValue("direction"))
        : self._parseDirectionFallback(getValue("direction"));

      const lineBucket = (typeof Parser_ !== "undefined" && Parser_.getLineBucket)
        ? Parser_.getLineBucket(line)
        : self._getLineBucketFallback(line);

      base.direction = direction;
      base.lineBucket = lineBucket;

      // v4.3.0: read raw type and derive canonical typeKey
      const typeRaw = getValue("type", "");
      base.type = String(typeRaw || "");

      if (typeof Discovery_ !== "undefined" && Discovery_._getTotalsTypeKey) {
        base.typeKey = Discovery_._getTotalsTypeKey(base);
      } else if (typeof Parser_ !== "undefined" && Parser_._deriveTotalsTypeKey) {
        base.typeKey = Parser_._deriveTotalsTypeKey(base);
      } else {
        base.typeKey = self._getTotalsTypeKeyFallback(base);
      }
    }

    return base;
  },

  findOrCreateColumn(sheet, headers, aliases, defaultName) {
    const normalizedAliases = aliases.map(a => a.toLowerCase().replace(/[^a-z0-9]/g, ""));

    for (let i = 0; i < headers.length; i++) {
      const h = String(headers[i]).toLowerCase().replace(/[^a-z0-9]/g, "");
      if (normalizedAliases.some(a => h.includes(a) || a.includes(h))) {
        return i + 1;
      }
    }

    const newCol = headers.length + 1;
    sheet.getRange(1, newCol).setValue(defaultName).setFontWeight("bold");
    return newCol;
  },

  formatGrade(grade) {
    const symbols = {
      PLATINUM: "💎",
      GOLD: "🥇",
      SILVER: "🥈",
      BRONZE: "🥉",
      ROCK: "🪨",
      CHARCOAL: "💩"
    };

    const symbol = symbols[grade] || "";
    return `${symbol} ${grade}`;
  },

  truncate(str, maxLen) {
    if (!str || str.length <= maxLen) return str;
    return str.substring(0, maxLen - 1) + "…";
  },

  // =========================================================================
  // FALLBACK PARSERS
  // =========================================================================

  _parseConfidenceFallback(val) {
    if (val === null || val === undefined) return null;
    const str = String(val).replace("%", "").trim();
    const num = parseFloat(str);
    return isNaN(num) ? null : (num > 1 ? num / 100 : num);
  },

  _parseTierFallback(val) {
    if (!val) return null;
    const upper = String(val).toUpperCase().trim();
    if (upper.includes("STRONG") || upper === "S") return "STRONG";
    if (upper.includes("MED") || upper === "M") return "MEDIUM";
    if (upper.includes("WEAK") || upper === "W") return "WEAK";
    return null;
  },

  _parseQuarterFallback(val) {
    if (val === null || val === undefined) return null;
    const str = String(val).replace(/[Qq]/g, "").trim();
    const num = parseInt(str, 10);
    return (num >= 1 && num <= 4) ? num : null;
  },

  _isWomenFallback(league, match) {
    const combined = `${league} ${match}`.toUpperCase();
    return /\bW\b|WOMEN|WBB|WNBA|WCBB/.test(combined);
  },

  _getConfBucketFallback(conf) {
    if (conf === null || conf === undefined) return null;
    const buckets = Config_.confBuckets || [
      { name: "ELITE", min: 0.70, max: 1.00 },
      { name: "HIGH", min: 0.60, max: 0.70 },
      { name: "MEDIUM", min: 0.55, max: 0.60 },
      { name: "LOW", min: 0, max: 0.55 }
    ];
    for (const b of buckets) {
      if (conf >= b.min && conf < b.max) return b.name;
    }
    return buckets[buckets.length - 1] ? buckets[buckets.length - 1].name : null;
  },

  _parseSpreadFallback(pick) {
    if (!pick) return null;
    const m = String(pick).match(/[+-]?\d+\.?\d*/);
    return m ? parseFloat(m[0]) : null;
  },

  _parseSideFallback(pick, sideCol) {
    const pickStr = String(pick).toUpperCase();
    if (pickStr.includes("HOME") || pickStr.startsWith("H")) return "H";
    if (pickStr.includes("AWAY") || pickStr.startsWith("A")) return "A";

    if (sideCol) {
      const sideStr = String(sideCol).toUpperCase().trim();
      if (sideStr.includes("HOME") || sideStr === "H") return "H";
      if (sideStr.includes("AWAY") || sideStr === "A") return "A";
    }
    return null;
  },

  _getSpreadBucketFallback(spread) {
    if (spread === null || spread === undefined) return null;
    const abs = Math.abs(spread);
    const buckets = Config_.spreadBuckets || [
      { name: "TINY", min: 0, max: 3.5 },
      { name: "SMALL", min: 3.5, max: 7.5 },
      { name: "MEDIUM", min: 7.5, max: 12.5 },
      { name: "LARGE", min: 12.5, max: 999 }
    ];
    for (const b of buckets) {
      if (abs >= b.min && abs < b.max) return b.name;
    }
    return null;
  },

  _parseLineFallback(val) {
    if (val === null || val === undefined) return null;
    const num = parseFloat(String(val).replace(/[^\d.]/g, ""));
    return isNaN(num) ? null : num;
  },

  _parseDirectionFallback(val) {
    if (!val) return null;
    const str = String(val).toLowerCase().trim();
    if (str.includes("over") || str === "o") return "Over";
    if (str.includes("under") || str === "u") return "Under";
    return null;
  },

  _getLineBucketFallback(line) {
    if (line === null || line === undefined) return null;
    const buckets = Config_.lineBuckets || [
      { name: "LOW", min: 0, max: 140 },
      { name: "MEDIUM", min: 140, max: 160 },
      { name: "HIGH", min: 160, max: 999 }
    ];
    for (const b of buckets) {
      if (line >= b.min && line < b.max) return b.name;
    }
    return null;
  },

  // =========================================================================
  // UTILITY METHODS
  // =========================================================================

  previewFlags(ss, sheetName, edges, leagueAssay, type) {
    if (!this.log) this.init();

    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) return { error: "Sheet not found" };

    const data = sheet.getDataRange().getValues();
    if (data.length < 2) return { error: "No data", total: 0 };

    const headers = data[0];
    const aliases = type === "side" ? Config_.sideColumnAliases : Config_.totalsColumnAliases;
    ColResolver_.init();
    const { resolved } = ColResolver_.resolve(headers, aliases, sheetName);

    const edgeIndex = this._buildEdgeIndex(edges);

    const gradeCount = {};
    let flagged = 0;
    let toxic = 0;

    for (let i = 1; i < data.length; i++) {
      const bet = this.parseRowForMatching(data[i], resolved, type);
      const result = this.evaluateRow(bet, edges, leagueAssay, edgeIndex);

      if (result.matchedEdges.length > 0) flagged++;
      if (result.isToxic) toxic++;

      gradeCount[result.bestGrade] = (gradeCount[result.bestGrade] || 0) + 1;
    }

    return {
      total: data.length - 1,
      flagged: flagged,
      toxic: toxic,
      byGrade: gradeCount
    };
  },

  clearFlags(ss, sheetName) {
    if (!this.log) this.init();

    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) return;

    const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    const flagCols = ["ma_edgeflags", "ma_grade", "ma_status"];

    for (let i = 0; i < headers.length; i++) {
      const h = String(headers[i]).toLowerCase().replace(/[^a-z0-9]/g, "");
      if (flagCols.some(f => h.includes(f.replace(/_/g, "")))) {
        const lastRow = sheet.getLastRow();
        if (lastRow > 1) {
          sheet.getRange(2, i + 1, lastRow - 1, 1).clearContent();
        }
      }
    }

    this.log.info(`Cleared flags from ${sheetName}`);
  },

  getRowsMatchingEdge(ss, sheetName, edge, type) {
    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) return [];

    const data = sheet.getDataRange().getValues();
    if (data.length < 2) return [];

    const headers = data[0];
    const aliases = type === "side" ? Config_.sideColumnAliases : Config_.totalsColumnAliases;
    ColResolver_.init();
    const { resolved } = ColResolver_.resolve(headers, aliases, sheetName);

    const matches = [];
    for (let i = 1; i < data.length; i++) {
      const bet = this.parseRowForMatching(data[i], resolved, type);
      if (this.matchesCriteria(bet, edge.criteria)) {
        matches.push(i + 1);
      }
    }

    return matches;
  }
};

// ============================================================================
// MODULE: Discovery_ — Edge Discovery Engine (v4.3.0 — Type-Segmented Totals
//                       + Contextual Baselines)
//
// WHAT CHANGED (v4.3.0):
//   1. _normalizeType / _getTotalsTypeKey — canonical derivation-type field
//   2. Totals discovery loops nest INSIDE typeKey so every Totals edge carries
//      criteria.typeKey.  This prevents DIR edges from blessing STAR bets.
//   3. Baselines are CONTEXTUAL: deeper scans compare against their parent
//      slice, not the global pool.  Prevents "fake lift" from riding a
//      strong parent category.
//   4. Filter gate: Totals edges without criteria.typeKey are dropped.
//   5. matchesCriteria auto-computes typeKey on untagged bets (safety net
//      for Flagger_ callers that haven't run through Discovery first).
//   6. Side discovery baselines also made contextual at depth ≥ 2.
// ============================================================================

const Discovery_ = {
  log: null,

  init() {
    this.log = Log_.module("DISCOVERY");
  },

  // ---------------------------------------------------------------------------
  // Internal helpers
  // ---------------------------------------------------------------------------

  _clone(obj) {
    if (typeof Utils_ !== "undefined" && Utils_.deepClone) {
      return Utils_.deepClone(obj);
    }
    return JSON.parse(JSON.stringify(obj));
  },

  /**
   * ◆ PATCH: Normalise a raw type string to upper-case, single-spaced.
   */
  _normalizeType(raw) {
    return String(raw || "").trim().toUpperCase().replace(/\s+/g, " ");
  },

  /**
   * ◆ PATCH: Derive a canonical, stable typeKey for any totals bet.
   *
   * Maps the messy universe of type strings to a small canonical set:
   *   SNIPER_OU  |  SNIPER_OU_DIR  |  SNIPER_OU_STAR
   *   OU         |  OU_DIR         |  OU_STAR
   *   OTHER      |  UNKNOWN
   *
   * This is the field that goes into edge criteria and prevents
   * cross-derivation leakage.
   */
  _getTotalsTypeKey(bet) {
    if (!bet) return "UNKNOWN";
    if (bet.typeKey) return bet.typeKey;          // already computed

    const t = this._normalizeType(bet.type);
    if (!t) return "UNKNOWN";

    // Detect "Sniper O/U" family
    const hasSniper = t.includes("SNIPER");
    const hasOU     = t.includes("O/U")  || t.includes("OU")  ||
                      t.includes("OVER/UNDER") || t.includes("OVER UNDER") ||
                      t.includes("TOTAL");

    if (hasSniper && hasOU) {
      if (t.includes("DIR"))  return "SNIPER_OU_DIR";
      if (t.includes("STAR")) return "SNIPER_OU_STAR";
      return "SNIPER_OU";
    }

    if (hasOU) {
      if (t.includes("DIR"))  return "OU_DIR";
      if (t.includes("STAR")) return "OU_STAR";
      return "OU";
    }

    return "OTHER";
  },

  // ---------------------------------------------------------------------------
  // Edge creation
  // ---------------------------------------------------------------------------

  createEdge(source, id, name, bets, stats, baseline, criteria = {}) {
    const lowerBound = Stats_.wilsonLowerBound(stats.wins, stats.decisive);
    const upperBound = Stats_.wilsonUpperBound(stats.wins, stats.decisive);
    const lift       = stats.winRate - baseline.winRate;
    const liftPct    = baseline.winRate > 0 ? (lift / baseline.winRate) * 100 : 0;
    const gradeInfo  = Stats_.getGradeInfo(stats.winRate, stats.decisive);

    return {
      id: id.replace(/\s+/g, "_").replace(/[^A-Z0-9_]/gi, "").toUpperCase(),
      source,
      name,
      description: `${name} (${source})`,
      criteria: this._clone(criteria),
      n: stats.decisive,
      wins: stats.wins,
      losses: stats.losses,
      winRate: stats.winRate,
      winRatePct: Stats_.pct(stats.winRate),
      lift,
      liftPct,
      liftDisplay: Stats_.lift(lift),
      lowerBound,
      upperBound,
      confidenceInterval: `${Stats_.pct(lowerBound)} - ${Stats_.pct(upperBound)}`,
      grade: gradeInfo.grade,
      gradeSymbol: gradeInfo.symbol,
      gradeName: gradeInfo.name,
      reliable: stats.decisive >= Config_.thresholds.minNReliable,
      sampleSize: stats.decisive >= Config_.thresholds.minNPlatinum ? "Large" :
                  stats.decisive >= Config_.thresholds.minNReliable ? "Medium" : "Small",
      autoDiscovered: true,
      discoveredAt: new Date().toISOString()
    };
  },

  // ---------------------------------------------------------------------------
  // Attribute scanner (unchanged API — baseline meaning is now contextual)
  // ---------------------------------------------------------------------------

  scanAttribute(bets, source, attrName, values, getter, baseline, parentCriteria = {}) {
    const edges = [];
    const t = Config_.thresholds;

    for (const val of values) {
      if (val === null || val === undefined) continue;

      const filtered = bets.filter(b => getter(b) === val);
      if (filtered.length < t.minN) continue;

      const stats = Stats_.calcBasic(filtered);
      if (stats.decisive < t.minN) continue;

      const lift = stats.winRate - baseline.winRate;

      if (lift >= t.liftThreshold) {
        const criteria  = { ...parentCriteria, [attrName]: val };
        const sortedKeys = Object.keys(criteria).sort();
        const idParts   = [source];
        const nameParts = [];
        for (const k of sortedKeys) {
          const v = criteria[k];
          idParts.push(`${k}_${String(v).replace(/[^A-Z0-9]/gi, "")}`);
          nameParts.push(`${k}=${v}`);
        }

        edges.push(this.createEdge(
          source,
          idParts.join("_"),
          nameParts.join(" + "),
          filtered,
          stats,
          baseline,
          criteria
        ));
      }
    }

    return edges;
  },

  // ---------------------------------------------------------------------------
  // Main discovery orchestrator
  // ---------------------------------------------------------------------------

  discoverAll(sideBets, totalsBets, globalStats = null) {
    if (!this.log) this.init();
    Log_.section("Discovering Edges");

    const discovered = [];
    const t = Config_.thresholds;

    const discoveryStartTime = Date.now();
    const MAX_DISCOVERY_MS   = 5 * 60 * 1000;
    let   timeoutWarningLogged = false;

    const isApproachingTimeout = () => {
      if (Date.now() - discoveryStartTime > MAX_DISCOVERY_MS) {
        if (!timeoutWarningLogged) {
          this.log.warn("Approaching execution time limit, completing discovery early");
          timeoutWarningLogged = true;
        }
        return true;
      }
      return false;
    };

    // ========================================================================
    //  SIDE DISCOVERY  (contextual baselines at depth ≥ 2)
    // ========================================================================
    if (sideBets.length > 0 && !isApproachingTimeout()) {
      this.log.info(`Scanning ${sideBets.length} side bets for edges`);
      const sideBaseline = Stats_.calcBasic(sideBets);

      const quarterValues      = [1, 2, 3, 4];
      const sideValues         = ["H", "A"];
      const tierValues         = ["STRONG", "MEDIUM", "WEAK"];
      const spreadBucketValues = Config_.spreadBuckets.map(b => b.name);
      const confBucketValues   = Config_.confBuckets.map(b => b.name);
      const boolValues         = [true, false];

      // Pre-build maps
      const sideByQuarter = new Map();
      for (let q = 1; q <= 4; q++) {
        sideByQuarter.set(q, sideBets.filter(b => b.quarter === q));
      }

      const sideByQuarterSide = new Map();
      for (let q = 1; q <= 4; q++) {
        for (const side of sideValues) {
          sideByQuarterSide.set(`${q}_${side}`,
            sideBets.filter(b => b.quarter === q && b.side === side));
        }
      }

      // ---- Single Attribute (global baseline) ----
      discovered.push(...this.scanAttribute(
        sideBets, "Side", "quarter", quarterValues, b => b.quarter, sideBaseline));
      discovered.push(...this.scanAttribute(
        sideBets, "Side", "side", sideValues, b => b.side, sideBaseline));
      discovered.push(...this.scanAttribute(
        sideBets, "Side", "tier", tierValues, b => b.tier, sideBaseline));
      discovered.push(...this.scanAttribute(
        sideBets, "Side", "spreadBucket", spreadBucketValues, b => b.spreadBucket, sideBaseline));
      discovered.push(...this.scanAttribute(
        sideBets, "Side", "confBucket", confBucketValues, b => b.confBucket, sideBaseline));
      discovered.push(...this.scanAttribute(
        sideBets, "Side", "isWomen", boolValues, b => b.isWomen, sideBaseline));

      // Matchup-based (Side only)
      const minNMatchup = t.minNMatchup ?? 20;
      const highVolumeMatchups = [...new Set(sideBets.map(b => b.matchupKey).filter(Boolean))]
        .filter(mk => sideBets.filter(b => b.matchupKey === mk).length >= minNMatchup);
      discovered.push(...this.scanAttribute(
        sideBets, "Side", "matchupKey", highVolumeMatchups, b => b.matchupKey, sideBaseline));

      // ---- Two-Attribute: Quarter + X  ◆ PATCH: contextual baseline ----
      for (let q = 1; q <= 4; q++) {
        if (isApproachingTimeout()) break;

        const qBets = sideByQuarter.get(q);
        if (!qBets || qBets.length < t.minN) continue;

        const qBaseline = Stats_.calcBasic(qBets);        // ◆ contextual
        const qCriteria = { quarter: q };

        discovered.push(...this.scanAttribute(
          qBets, "Side", "side", sideValues, b => b.side, qBaseline, qCriteria));
        discovered.push(...this.scanAttribute(
          qBets, "Side", "spreadBucket", spreadBucketValues, b => b.spreadBucket, qBaseline, qCriteria));
        discovered.push(...this.scanAttribute(
          qBets, "Side", "tier", ["STRONG", "MEDIUM"], b => b.tier, qBaseline, qCriteria));
        discovered.push(...this.scanAttribute(
          qBets, "Side", "confBucket", confBucketValues, b => b.confBucket, qBaseline, qCriteria));
        discovered.push(...this.scanAttribute(
          qBets, "Side", "isWomen", boolValues, b => b.isWomen, qBaseline, qCriteria));
      }

      // ---- Three-Attribute: Q + Side + X  ◆ PATCH: contextual baseline ----
      for (let q = 1; q <= 4; q++) {
        if (isApproachingTimeout()) break;

        for (const side of sideValues) {
          if (isApproachingTimeout()) break;

          const key     = `${q}_${side}`;
          const qsBets  = sideByQuarterSide.get(key);
          if (!qsBets || qsBets.length < t.minN) continue;

          const qsBaseline = Stats_.calcBasic(qsBets);    // ◆ contextual
          const criteria   = { quarter: q, side: side };

          discovered.push(...this.scanAttribute(
            qsBets, "Side", "spreadBucket", spreadBucketValues,
            b => b.spreadBucket, qsBaseline, criteria));
          discovered.push(...this.scanAttribute(
            qsBets, "Side", "isWomen", boolValues,
            b => b.isWomen, qsBaseline, criteria));
          discovered.push(...this.scanAttribute(
            qsBets, "Side", "confBucket", confBucketValues,
            b => b.confBucket, qsBaseline, criteria));
          discovered.push(...this.scanAttribute(
            qsBets, "Side", "tier", tierValues,
            b => b.tier, qsBaseline, criteria));
        }
      }

      this.log.info(`Side discovery found ${discovered.length} raw edges`);
    }

    // ========================================================================
    //  TOTALS DISCOVERY  ◆ PATCH: TYPE-SEGMENTED + CONTEXTUAL BASELINES
    // ========================================================================
    const totalsStartIdx = discovered.length;

    if (totalsBets.length > 0 && !isApproachingTimeout()) {
      this.log.info(`Scanning ${totalsBets.length} totals bets for edges`);

      // ----- Step 1: stamp canonical typeKey on every totals bet -----
      for (const b of totalsBets) {
        b.typeKey = this._getTotalsTypeKey(b);
      }

      const totalsBaseline = Stats_.calcBasic(totalsBets);

      const quarterValues    = [1, 2, 3, 4];
      const directionValues  = ["Over", "Under"];
      const tierValues       = ["STRONG", "MEDIUM", "WEAK"];
      const lineBucketValues = Config_.lineBuckets.map(b => b.name);
      const confBucketValues = Config_.confBuckets.map(b => b.name);
      const boolValues       = [true, false];

      // ----- Step 2: build typeValues (types with ≥ minN samples) -----
      const typeCounts = {};
      for (const b of totalsBets) {
        typeCounts[b.typeKey] = (typeCounts[b.typeKey] || 0) + 1;
      }
      const typeValues = Object.keys(typeCounts).filter(k => typeCounts[k] >= t.minN);

      this.log.info(`Totals type distribution: ${JSON.stringify(typeCounts)}`);
      this.log.info(`Types with sufficient samples (>=${t.minN}): ${typeValues.join(", ") || "none"}`);

      // ----- Step 3: typeKey-only scan (global baseline) -----
      // Finds which derivation types are overall better / worse than the pool
      discovered.push(...this.scanAttribute(
        totalsBets, "Totals", "typeKey", typeValues,
        b => b.typeKey, totalsBaseline
      ));

      // ----- Step 4: type-segmented discovery -----
      for (const typ of typeValues) {
        if (isApproachingTimeout()) break;

        const typedBets = totalsBets.filter(b => b.typeKey === typ);
        if (typedBets.length < t.minN) continue;

        const typeBaseline = Stats_.calcBasic(typedBets);
        const typeCriteria = { typeKey: typ };

        // ---- 2-attr: TypeKey + X  (baseline = type slice) ----
        discovered.push(...this.scanAttribute(
          typedBets, "Totals", "quarter", quarterValues,
          b => b.quarter, typeBaseline, typeCriteria));
        discovered.push(...this.scanAttribute(
          typedBets, "Totals", "direction", directionValues,
          b => b.direction, typeBaseline, typeCriteria));
        discovered.push(...this.scanAttribute(
          typedBets, "Totals", "tier", tierValues,
          b => b.tier, typeBaseline, typeCriteria));
        discovered.push(...this.scanAttribute(
          typedBets, "Totals", "lineBucket", lineBucketValues,
          b => b.lineBucket, typeBaseline, typeCriteria));
        discovered.push(...this.scanAttribute(
          typedBets, "Totals", "confBucket", confBucketValues,
          b => b.confBucket, typeBaseline, typeCriteria));
        discovered.push(...this.scanAttribute(
          typedBets, "Totals", "isWomen", boolValues,
          b => b.isWomen, typeBaseline, typeCriteria));

        // ---- 3-attr: TypeKey + Quarter + X ----
        for (let q = 1; q <= 4; q++) {
          if (isApproachingTimeout()) break;

          const tqBets = typedBets.filter(b => b.quarter === q);
          if (tqBets.length < t.minN) continue;

          const tqBaseline = Stats_.calcBasic(tqBets);     // ◆ contextual
          const tqCriteria = { typeKey: typ, quarter: q };

          discovered.push(...this.scanAttribute(
            tqBets, "Totals", "direction", directionValues,
            b => b.direction, tqBaseline, tqCriteria));
          discovered.push(...this.scanAttribute(
            tqBets, "Totals", "lineBucket", lineBucketValues,
            b => b.lineBucket, tqBaseline, tqCriteria));
          discovered.push(...this.scanAttribute(
            tqBets, "Totals", "tier", tierValues,
            b => b.tier, tqBaseline, tqCriteria));
          discovered.push(...this.scanAttribute(
            tqBets, "Totals", "confBucket", confBucketValues,
            b => b.confBucket, tqBaseline, tqCriteria));
          discovered.push(...this.scanAttribute(
            tqBets, "Totals", "isWomen", boolValues,
            b => b.isWomen, tqBaseline, tqCriteria));
        }

        // ---- 4-attr: TypeKey + Quarter + Direction + X ----
        for (let q = 1; q <= 4; q++) {
          if (isApproachingTimeout()) break;

          for (const dir of directionValues) {
            if (isApproachingTimeout()) break;

            const tqdBets = typedBets.filter(b => b.quarter === q && b.direction === dir);
            if (tqdBets.length < t.minN) continue;

            const tqdBaseline = Stats_.calcBasic(tqdBets); // ◆ contextual
            const tqdCriteria = { typeKey: typ, quarter: q, direction: dir };

            discovered.push(...this.scanAttribute(
              tqdBets, "Totals", "lineBucket", lineBucketValues,
              b => b.lineBucket, tqdBaseline, tqdCriteria));
            discovered.push(...this.scanAttribute(
              tqdBets, "Totals", "isWomen", boolValues,
              b => b.isWomen, tqdBaseline, tqdCriteria));
            discovered.push(...this.scanAttribute(
              tqdBets, "Totals", "confBucket", confBucketValues,
              b => b.confBucket, tqdBaseline, tqdCriteria));
            discovered.push(...this.scanAttribute(
              tqdBets, "Totals", "tier", tierValues,
              b => b.tier, tqdBaseline, tqdCriteria));
          }
        }
      }

      this.log.info(`Totals discovery found ${discovered.length - totalsStartIdx} raw edges`);
    }

    // ========================================================================
    //  FILTER & DEDUPLICATE  ◆ PATCH: typeKey gate + Wilson gate
    // ========================================================================
    const maxLift   = t.maxEdgeLift || 0.25;
    const wilsonGate = t.wilsonLowerBoundGate || 0;

    const filtered = discovered.filter(e =>
      e.n >= t.minN &&
      e.lift >= t.liftThreshold &&
      e.lift <= maxLift &&
      e.lowerBound >= wilsonGate &&                                // ◆ PATCH
      (e.source !== "Totals" || (e.criteria && e.criteria.typeKey)) // ◆ PATCH
    );

    // Deduplicate by ID (keep largest sample)
    const uniqueMap = {};
    filtered.forEach(e => {
      if (!uniqueMap[e.id] || e.n > uniqueMap[e.id].n) {
        uniqueMap[e.id] = e;
      }
    });

    const unique = Object.values(uniqueMap);

    // Sort: grade descending, then lift descending
    const gradeOrder = {
      PLATINUM: 6, GOLD: 5, SILVER: 4, BRONZE: 3, ROCK: 2, CHARCOAL: 1
    };

    unique.sort((a, b) => {
      const gradeCompare = (gradeOrder[b.grade] || 0) - (gradeOrder[a.grade] || 0);
      if (gradeCompare !== 0) return gradeCompare;
      return b.lift - a.lift;
    });

    // ---- Logging ----
    const elapsedMs = Date.now() - discoveryStartTime;
    this.log.info(
      `Discovery complete: ${unique.length} unique edges from ${discovered.length} raw (${elapsedMs}ms)`
    );

    const gradeCounts = {};
    unique.forEach(e => { gradeCounts[e.grade] = (gradeCounts[e.grade] || 0) + 1; });
    this.log.info("Edge grade distribution:", gradeCounts);

    // ◆ PATCH: log type-segmented Totals breakdown
    const totalsByType = {};
    unique.filter(e => e.source === "Totals").forEach(e => {
      const tk = (e.criteria && e.criteria.typeKey) || "NONE";
      totalsByType[tk] = (totalsByType[tk] || 0) + 1;
    });
    if (Object.keys(totalsByType).length > 0) {
      this.log.info("Totals edges by typeKey:", totalsByType);
    }

    const topTier = unique.filter(e => e.grade === "GOLD" || e.grade === "PLATINUM");
    this.log.info(`Gold/Platinum edges: ${topTier.length}`);

    if (timeoutWarningLogged) {
      this.log.warn("Discovery was truncated due to time constraints — results may be incomplete");
    }

    Log_.sectionEnd("Discovering Edges");

    return unique;
  },

  // ---------------------------------------------------------------------------
  // Edge matching (used by Flagger_)
  // ---------------------------------------------------------------------------

  /**
   * ◆ PATCH: auto-computes typeKey on the fly for Totals bets that don't
   * have it yet (safety net for callers outside the discovery pipeline).
   */
    matchesCriteria(bet, edge) {
    if (!edge || !edge.criteria || typeof edge.criteria !== "object" || Object.keys(edge.criteria).length === 0) {
      return false;
    }
    if (!bet || typeof bet !== "object") {
      return false;
    }

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

    var criteriaEntries = Object.entries(edge.criteria);
    for (var i = 0; i < criteriaEntries.length; i++) {
      var key = criteriaEntries[i][0];
      var expected = criteriaEntries[i][1];
      var actual = bet[key];

      // Auto-derive typeKey for untagged Totals bets
      if (key === "typeKey" && (actual === undefined || actual === null)) {
        actual = this._getTotalsTypeKey(bet);
      }

      if (actual === undefined || actual === null) return false;
      if (norm(actual) !== norm(expected)) return false;
    }

    return true;
  },

  /**
   * ◆ PATCH: pre-compute typeKey once before iterating edges for efficiency.
   */
  findMatchingEdges(bet, edges) {
    // Stamp typeKey if needed so matchesCriteria doesn't recompute per-edge
    if (bet.source === "Totals" && !bet.typeKey) {
      bet.typeKey = this._getTotalsTypeKey(bet);
    }

    const matches = edges.filter(e =>
      e.source === bet.source && this.matchesCriteria(bet, e)
    );

    const gradeOrder = {
      PLATINUM: 6, GOLD: 5, SILVER: 4, BRONZE: 3, ROCK: 2, CHARCOAL: 1
    };
    matches.sort((a, b) => (gradeOrder[b.grade] || 0) - (gradeOrder[a.grade] || 0));

    return matches;
  },

  getBestEdge(bet, edges) {
    const matches = this.findMatchingEdges(bet, edges);
    return matches.length > 0 ? matches[0] : null;
  },

  // ---------------------------------------------------------------------------
  // Query helpers (unchanged)
  // ---------------------------------------------------------------------------

  getTopEdges(edges, grade = null, limit = 10) {
    let filtered = edges;

    if (grade) {
      if (Array.isArray(grade)) {
        filtered = edges.filter(e => grade.includes(e.grade));
      } else {
        filtered = edges.filter(e => e.grade === grade);
      }
    }

    return filtered.slice(0, limit);
  },

  getEdgesBySource(edges, source) {
    return edges.filter(e => e.source === source);
  },

  groupByGrade(edges) {
    const groups = {
      PLATINUM: [], GOLD: [], SILVER: [], BRONZE: [], ROCK: [], CHARCOAL: []
    };

    edges.forEach(e => {
      if (groups[e.grade]) {
        groups[e.grade].push(e);
      }
    });

    return groups;
  },

  getSummary(edges) {
    const byGrade  = this.groupByGrade(edges);
    const bySource = {
      Side:   edges.filter(e => e.source === "Side").length,
      Totals: edges.filter(e => e.source === "Totals").length
    };

    const avgLift = edges.length > 0
      ? edges.reduce((sum, e) => sum + e.lift, 0) / edges.length
      : 0;

    const avgN = edges.length > 0
      ? edges.reduce((sum, e) => sum + e.n, 0) / edges.length
      : 0;

    return {
      total: edges.length,
      byGrade: {
        PLATINUM:  byGrade.PLATINUM.length,
        GOLD:      byGrade.GOLD.length,
        SILVER:    byGrade.SILVER.length,
        BRONZE:    byGrade.BRONZE.length,
        ROCK:      byGrade.ROCK.length,
        CHARCOAL:  byGrade.CHARCOAL.length
      },
      bySource,
      avgLift: Math.round(avgLift * 10000) / 10000,
      avgN:    Math.round(avgN)
    };
  }
};

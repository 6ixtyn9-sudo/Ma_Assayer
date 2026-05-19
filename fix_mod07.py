import sys

file_path = "docs/MODULE 07_Parser_Data Parsing"

with open(file_path, "r") as f:
    text = f.read()

# We need to extract the `parseIntakeMarketSheets` block, which currently starts at line 1255.
# Let's find the start string.
start_marker = "  // =========================================================================\n  // parseIntakeMarketSheets"

if start_marker not in text:
    print("Could not find start marker")
    sys.exit(1)

parts = text.split(start_marker)
before_intake = parts[0]
intake_block = start_marker + parts[1]

# `before_intake` ends with:
# "  return mismatches;\n  },\n\n"
# We need to change it to:
# "  return mismatches;\n}\n\n"
if "return mismatches;\n  },\n\n" in before_intake:
    before_intake = before_intake.replace("return mismatches;\n  },\n\n", "return mismatches;\n}\n\n")
else:
    # Just replace "return mismatches;\n  }," if it matches
    before_intake = before_intake.replace("return mismatches;\n  },", "return mismatches;\n}")

# Now we need to insert `intake_block` into `before_intake` before `};` at the end of Parser_.
# But wait, `intake_block` already has `};` at the end, from our earlier script.
# Let's remove `};\n` from the end of `intake_block` if it exists.
if intake_block.endswith("};\n"):
    intake_block = intake_block[:-3]
if intake_block.endswith("};\n\n"):
    intake_block = intake_block[:-4]

# Also let's clean up the end of `intake_block`.
intake_block = intake_block.rstrip() + "\n"

# Now find `};` in `before_intake` which marks the end of Parser_.
# It should be around:
# "    return { bets: bets, columns: resolved, errors: parseErrors, stats: stats };\n  }\n};\n\nfunction auditSideOutcomes() {"
parser_end_marker = "    return { bets: bets, columns: resolved, errors: parseErrors, stats: stats };\n  }\n};\n"

if parser_end_marker in before_intake:
    # we replace `};\n` with `},\n\n` + intake_block + `};\n`
    replacement = "    return { bets: bets, columns: resolved, errors: parseErrors, stats: stats };\n  },\n\n" + intake_block + "};\n"
    before_intake = before_intake.replace(parser_end_marker, replacement)
else:
    print("Could not find parser end marker")
    sys.exit(1)

# Write back
with open(file_path, "w") as f:
    f.write(before_intake)

print("Fixed syntax in MODULE 07")

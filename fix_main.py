import re

file_path = "docs/MODULE 02_Main_Orchestrator"
with open(file_path, "r") as f:
    content = f.read()

# Replace runAssay()
old_runassay_parse = """    const sideData = Parser_.parseSideSheet(ss);
    const totalsData = Parser_.parseTotalsSheet(ss);
    
    const allBets = [...sideData.bets, ...totalsData.bets];"""
    
new_runassay_parse = """    const sideData = Parser_.parseSideSheet(ss);
    const totalsData = Parser_.parseTotalsSheet(ss);
    const intakeData = Parser_.parseIntakeMarketSheets(ss);
    
    const allBets = [...sideData.bets, ...totalsData.bets, ...(intakeData ? intakeData.bets : [])];"""

content = content.replace(old_runassay_parse, new_runassay_parse)

# Replace runFlaggerOnly()
old_flagger_parse = """     const sideData = Parser_.parseSideSheet(ss);
     const totalsData = Parser_.parseTotalsSheet(ss);
     const allBets = [...sideData.bets, ...totalsData.bets];"""
     
new_flagger_parse = """     const sideData = Parser_.parseSideSheet(ss);
     const totalsData = Parser_.parseTotalsSheet(ss);
     const intakeData = Parser_.parseIntakeMarketSheets(ss);
     const allBets = [...sideData.bets, ...totalsData.bets, ...(intakeData ? intakeData.bets : [])];"""

content = content.replace(old_flagger_parse, new_flagger_parse)

with open(file_path, "w") as f:
    f.write(content)
print("Updated Main_Orchestrator")

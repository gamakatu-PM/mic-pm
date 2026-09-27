import openpyxl,sys
wb=openpyxl.load_workbook(sys.argv[1],data_only=True)
def dump(n,rng):
    ws=wb[n]; print("==",n)
    for row in ws[rng]:
        vals=[c.value for c in row]
        if any(v not in (None,"") for v in vals): print([v for v in vals])
dump("0.자가진단","A4:D13")
dump("설정","A4:D15")
dump("2.현장","A2:Z9")
dump("3.설계사","A2:R9")
dump("5.이번주_갈곳","A1:I8")
dump("6.본전계산","A4:D22")
dump("7.문안","A5:B14")

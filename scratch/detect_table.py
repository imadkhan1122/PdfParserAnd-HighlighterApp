import camelot
file = "../data/sample_prospectus/BLI.pdf"


tables = camelot.read_pdf(file, pages='74')
print(tables.n)
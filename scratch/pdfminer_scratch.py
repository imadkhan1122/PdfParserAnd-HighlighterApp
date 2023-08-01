import itertools
from typing import Generator, Any

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LAParams, LTFigure, LTTextBoxHorizontal, LTTextLineHorizontal, LTChar, \
    LTTextBoxVertical

pages=extract_pages("../data/sample_kids/fid_kid.pdf")
for page in pages:
    for element in page:
            if isinstance(element, LTTextBoxHorizontal):
                print(element.get_text())
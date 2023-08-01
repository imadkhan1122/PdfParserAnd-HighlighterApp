from operator import itemgetter
import fitz
import math
import numpy as np
from collections import Counter
from typing import List, Tuple

"""
utilities extending PyMuPDF
"""


def span_font_info(s, granularity=True):

    styles = {}
    if granularity:
        identifier = "{0}_{1}_{2}_{3}".format(round(s['size'], 0), s['flags'], s['font'],
                                              s['color'])
        styles[identifier] = {'size': round(s['size'], 0), 'flags': s['flags'], 'font': s['font'],
                              'color': s['color'],
                              'italic' : True if "italic" in str(s['font'].lower()) else False,
                              'bold': True if "bold" in str(s['font'].lower()) else False,
                              }
        font_stats = {'size': s['size'], 'flags': s['flags'], 'font': s['font'],
                              'color': s['color'],
                              'italic' : True if "italic" in str(s['font'].lower()) else False,
                              'bold': True if "bold" in str(s['font'].lower()) else False,
                                }


    else:
        identifier = "{0}".format(round(s['size']))
        styles[identifier] = {'size': round(s['size']), 'font': s['font']}
    #TODO: Implement font_counts, font_stats

    return {'font_counts': [],
            'styles' :styles,
            'font_stats': font_stats,
            'bbox'      : s['bbox']
            }




def doc_font_info(doc, granularity=True):
    """Extracts fonts and their usage in PDF documents.
    :param doc: fitz.doc to iterate through
    :type doc: <class 'fitz.fitz.Document'>
    :param granularity: also use 'font', 'flags' and 'color' to discriminate text
    :type granularity: bool
    :rtype: [(font_size, count), (font_size, count}], dict
    :return: most used fonts sorted by count, font style information
    """
    styles = {}
    font_counts = {}
    sizes = []
    colors = []
    fonts = []
    doc_bbox = []
    for page in doc:
        h, w = page.rect.height, page.rect.width
        rect = fitz.Rect(0, 10, w, h - 20)
        blocks = page.get_text("dict", sort=True, clip=rect)["blocks"]
        for b in blocks:  # iterate through the text blocks
            if b['type'] == 0:  # block contains text
                for l in b["lines"]:  # iterate through the text lines
                    for s in l["spans"]:  # iterate through the text spans
                        if granularity:
                            identifier = "{0}_{1}_{2}_{3}".format(round(s['size'], 0), s['flags'], s['font'],
                                                                  s['color'])
                            styles[identifier] = {'size': round(s['size'], 0), 'flags': s['flags'], 'font': s['font'],
                                                  'color': s['color']}
                            doc_bbox.append((s['bbox'], s['bbox'][2]-s['bbox'][0]))
                        else:
                            identifier = "{0}".format(round(s['size']))
                            styles[identifier] = {'size': round(s['size']), 'font': s['font']}
                            doc_bbox.append((s['bbox'], s['bbox'][2]-s['bbox'][0]))
                        sizes.append(s['size'])
                        colors.append(s['color'])
                        fonts.append(s['font'])
                        font_counts[identifier] = font_counts.get(identifier, 0) + 1  # count the fonts usage


    size_counts = Counter(sizes)
    common_size = size_counts.most_common(1)[0][0]
    #
    fonts_counts = Counter(fonts)
    common_font = fonts_counts.most_common(1)[0][0]
    #
    color_counts = Counter(colors)
    common_color = color_counts.most_common(1)[0][0]
    
    
    sizes = list(set(sizes))
    font_counts = sorted(font_counts.items(), key=itemgetter(1), reverse=True)
    

    if len(font_counts) < 1:
        raise ValueError("Zero discriminating fonts found!")
    for s, v in font_counts:
        styles[s]['count'] = v
        
    maxx = 0
    bbox = (0,0,0,0)
    for box, value in doc_bbox:
        if value > maxx:
            maxx = value
            bbox = box


    #TODO: add additional
    font_stats = {
        'max_font'     : max(sizes),
        'min_font'     : min(sizes),
        'common_color' : common_color,
        'common_font'  : common_font,
        'common_size'  : common_size,
    }

    return {'font_counts':font_counts, 'styles':styles, 'font_stats':font_stats, 'bbox': bbox, 'page_w':w, 'page_h':h}


def block_font_info(block, granularity=True):
    """Extracts fonts and their usage in PDF documents.
    :param Block: source.Element object

    :param granularity: also use 'font', 'flags' and 'color' to discriminate text
    :type granularity: bool
    :rtype: [(font_size, count), (font_size, count}], dict
    :return: most used fonts sorted by count, font style information
    """
    styles = {}
    font_counts = {}
    sizes = []
    colors = []
    fonts = []
    lines_info={}
    Widths = []
    if block['type'] == 0:  # block contains text
        for i,l in enumerate(block['lines']):  # iterate through the text lines
            lines_info[i]={}
            lines_info[i]['text']=""
            lines_info[i]['style']=[]

            for s in l["spans"]:  # iterate through the text spans
                if granularity:
                    identifier = "{0}_{1}_{2}_{3}".format(round(s['size'], 0), s['flags'], s['font'],
                                                          s['color'])
                    styles[identifier] = {'size': round(s['size'], 0), 'flags': s['flags'], 'font': s['font'],
                                          'color': s['color']}
                    Widths.append(s['bbox'][2]-s['bbox'][0])
                else:
                    identifier = "{0}".format(round(s['size']))
                    styles[identifier] = {'size': round(s['size']), 'font': s['font']}
                    Widths.append(s['bbox'][2]-s['bbox'][0])
                sizes.append(s['size'])
                colors.append(s['color'])
                fonts.append(s['font'])
                font_counts[identifier] = font_counts.get(identifier, 0) + 1  # count the fonts usage

                lines_info[i]['text']+=s['text']
                lines_info[i]['style'].append((round(s['size']),s['font'],s['color']))
                lines_info[i]['unique_font'] = len(lines_info[i]['style']) == 1
            lines_info[i]['bbox'] = l['bbox']

        size_counts = Counter(sizes)
        common_size = size_counts.most_common(1)[0][0]
        #
        fonts_counts = Counter(fonts)
        common_font = fonts_counts.most_common(1)[0][0]
        #
        color_counts = Counter(colors)
        common_color = color_counts.most_common(1)[0][0]
        sizes = list(set(sizes))
        font_counts = sorted(font_counts.items(), key=itemgetter(1), reverse=True)
        
        if len(font_counts) < 1:
            raise ValueError("Zero discriminating fonts found!")
        for s, v in font_counts:
            styles[s]['count'] = v
    


        bold = True if "bold" in str(common_font.lower()) else False
        italic = True if "italic" in str(common_font.lower()) else False
        
        #TODO: add additional
        font_stats = {
            'bold': bold,
            'italic': italic,
            "font_name":common_font,
            'max_font'     : max(sizes),
            'min_font'     : min(sizes),
            'common_color' : common_color,
            'common_font'  : common_font,
            'common_size'  : common_size,
        }


        return {'font_counts': font_counts, 'styles': styles, 'font_stats': font_stats,'bbox':block['bbox']},lines_info

    else:
        pass




def list_text_blocks(document):
    """
    retrieves textblocks fitz.Document or Page
    document: fitz.Document or fitz.Page
    :return list of texts
    """

    if isinstance(document, fitz.fitz.Page):
        document = [document]
    elif not isinstance(document, fitz.fitz.Document):
        return "document needs to be fitz Document or Page"
    blocks = []
    for page in document:
        _blocks = page.get_text("dict")["blocks"]

        for _block in _blocks:
            _span = ""
            for spans in _block['lines']:
                _text = spans['spans'][0]['text']
                _span += _text
            blocks.append([_span])
    return blocks


def find_string_in_text(doc, stringTobeFound: str, n: int = 0, tokenType="word", ignore_case: bool = True):
    """
    find string in document of page
    :param doc: fitz.Document or fitz.Page or string
    :param stringTobeFound: string of text to be found

    :param n: number of words, sentences to return left and right from found string
    :tokenType: 'word','sentence': return n words or sentences left and right from found string
    :param ignore_case: ignore capitalisation
    :return: list of words, sentences found
    """

    text_blocks = list_text_blocks(doc)
    if type(doc) == str:
        text_blocks = [[doc]]

    matched_text = []  # list of matches

    for block in text_blocks:
        if tokenType == "sentence":  # split text into sentences
            tokens = block[0].split(". ")
        else:  # or words
            tokens = block[0].split(" ")

        idx = []
        for token in tokens:
            if ignore_case:
                stringTobeFound = stringTobeFound.lower()
                token = token.lower()

            if stringTobeFound in token:
                idx.append(1)
            else:
                idx.append(0)

        # check if we have found a match, take the position and retrieve text[position-n:position+n]
        if np.array(idx).max() == 1:
            matched_text.append(tokens[max(np.array(idx).argmax() - n, 0):np.array(idx).argmax() + n + 1])

    return matched_text if tokenType == "sentence" else [[" ".join(x for x in y)] for y in matched_text]




class PdfTextExtraction:
    """
    Pdf text extraction class containing function to extract different elements of pdf text

    """

    def __init__(self, doc):
        self.doc = doc

    def extract_page_numbers(self) -> List[Tuple[int, int]]:
        """
        Extract page number as displayed on pdf page and returns list of tuples containing
        original page index and page as per the pdf, like (original page index, page number displayed on pdf)
        """
        # TODO Add more rules and cleanup
        page_numbers = []
        for e, page in enumerate(self.doc):
            # print(page.get_label())
            blocks = page.get_text_blocks(sort=True) # Check last blocks to extract page number
            page_number = None
            for i in blocks:
                # Check 5th element of block as it contains block text
                word = i[4].replace('\n', '').replace('-', '').replace('.', '').strip().lower()
                if word:  # If word is not empty
                    if any(l.isdigit() for l in word):  # If word contains numeric digits
                        if len(word.split()) > 1:
                            # Check if 'page' in word as some pdfs have format like page 1, page 2 etc
                            if 'page' in word:
                                page_number = None
                                for j, l in enumerate(word.split()):
                                    # If 'page' found then set element next to it as page number
                                    # if it is a valid numeric digit
                                    if l.lower() == 'page':
                                        try:
                                            temp_page_number = word.split()[j + 1]
                                        except IndexError:
                                            continue
                                        if temp_page_number.isdigit():
                                            page_number = int(temp_page_number)
                                            break
                                if page_number:  # Break main loop if page number found
                                    break
                            else:  # Set last element of the block as page number if it is a numeric digit
                                temp_page_number = word.split()[-1]
                                if temp_page_number.isdigit():
                                    page_number = int(temp_page_number)
                                break
                        else:
                            # If block text is only one element then set it as page number
                            # if it is a valid numeric digit
                            if word.isdigit():
                                page_number = int(word)
                            break
            # Add tuple containing original index and page number to page_numbers list and
            # if page number not extracted successfully then add empty string instead of it
            page_numbers.append((e, page_number)) if page_number else page_numbers.append((e, ''))
        return page_numbers


class Whitespace:
    """util to check whitespace of a smaller element(span/line) to larger element of which it is part of (block/doc"""

    def __init__(self, bbox_large, bbox_small):
        self.bbox_large = bbox_large
        self.bbox_small = bbox_small

    @property
    def width_large(self):
        width = self.bbox_large[2] - self.bbox_large[0]
        return width

    @property
    def width_small(self):
        width = self.bbox_small[2] - self.bbox_small[0]
        return width

    @property
    def whitespace_ratio(self):
        if self.width_small and self.width_large:
            try:
                return round(abs(self.width_small / self.width_large-1)*100)
            except ZeroDivisionError:
                return 0

    @property
    def whitespace_left(self):
        #percentage of ws on the left vs width of bbox_large
        return round(abs(self.bbox_large[0] - self.bbox_small[0])*100 / self.width_large)
        
    @property
    def whitespace_right(self):
        # percentage of ws on the right vs width of bbox_large
        if self.width_large and (self.bbox_small[2] <= self.bbox_large[2]):
            return round(abs(self.bbox_large[2] - self.bbox_small[2])*100 / self.width_large )

    @property
    def midpoint_small(self):
        return (self.bbox_small[2] + self.bbox_small[0]) / 2

    @property
    def midpoint_large(self):
        return(self.bbox_large[2] + self.bbox_large[0]) / 2


    @property
    def center_deviation(self):
        "percentage of mid away from center"
        try:
            return round(abs(self.midpoint_small / self.midpoint_large - 1) * 100)
        except ZeroDivisionError:
            return 0

    def is_centered(self, threshold=10):
        try:
            return abs(self.midpoint_small / self.midpoint_large - 1) * 100 < threshold
        except ZeroDivisionError:
            return True

    @property
    def one_span(self):
        return (self.width_large / self.width_small) > 0.99



if __name__ == "__main__":
    #path = 'data/sample_prospectus/ab.pdf'
    path = 'data/sample_prospectus/AQR.pdf'
    doc = fitz.open(path)

    # # MuParser
    # # font information
    # font_info = doc_font_info(doc, granularity=True)
    # # # get text blocks
    # text_blocks = list_text_blocks(doc)
    # # # find string in doc
    # matched_string = find_string_in_text(doc, "marketing", n=3, tokenType="sentence", ignore_case=True)
    #res = PdfTextExtraction(doc).extract_page_numbers()
    # ws= Whitespace((320, 41, 390, 53.),(368.1099853515625, 42, 380, 50))
    # ws.whitespace_ratio()
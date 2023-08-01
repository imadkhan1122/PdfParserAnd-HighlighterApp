import statistics
from collections import Counter

from pdfminer.layout import LTTextBoxHorizontal, LTChar

from pdfstructure.analysis.sizemapper import SizeMapper
from pdfstructure.analysis.styledistribution import StyleDistribution
from pdfstructure.model.document import TextElement
from pdfstructure.model.style import Style, TextSize
from pdfstructure.utils import truncate


class StyleAnnotator:
    """
    creates a PdfElements from incoming pdf-paragraphs (raw LTTextContainer from pdfminer.six).
    - annotates paragraph with @Style(italic, bold, fontname, mapped_size, mean_size).
    - mapped_font_size: captures most dominant character size within paragraph & maps it to TextSize Enum.
      mapped Size is leveraged by the hierarchy detection algorithm.
    """

    def __init__(self, sizemapper: SizeMapper, style_info: StyleDistribution):
        self._sizeMapper = sizemapper
        self._styleInfo = style_info

    @staticmethod
    def __investigate_box_style(element):
        """returns font, counter & size for block"""
        fonts = Counter()
        sizes = []
        for line in element:
            for c in line:
                if isinstance(c, LTChar):
                    fonts.update([c.fontname])
                    sizes.append(c.size)
        return fonts, sizes

    def process(self, element_gen):
        """"
        annotate each element with fontsize
        """
        for element in element_gen:


            if isinstance(element.original_element, LTTextBoxHorizontal):   #+.original element

                fonts, sizes = self.__investigate_box_style(element.original_element)   #+.original_element
                if not fonts or not element.original_element.get_text().rstrip():  #+.original_element



                    continue

                # get the most common font_name
                font_name = fonts.most_common(1)[0][0]


                element.mean_size = truncate(statistics.mean(sizes), 1)
                element.max_size = max(sizes)
                # todo currently empty boxes are forwarded.. with holding only \n
                element.mapped_font_size = self._sizeMapper.translate(target_enum=TextSize,
                                                         value=element.max_size)
                s = Style(bold="bold" in str(font_name.lower()),
                          italic="italic" in font_name.lower(),
                          font_name=font_name,
                          mapped_font_size=element.mapped_font_size,
                          mean_size=element.mean_size, max_size=element.max_size)


                # mean size
                
                mean_size = truncate(statistics.mean(sizes), 1)
                # maximum size
                max_size = max(sizes)
                
                # todo currently empty boxes are forwarded.. with holding only \n
                # this variable return that the either the given element is xsmal, xlarge or middle
                mapped_size = self._sizeMapper.translate(target_enum=TextSize,
                                                         value=max_size)
                # font style analysis based on element font sty;e
                s = Style(bold="bold" in str(font_name.lower()),
                          italic="italic" in font_name.lower(),
                          font_name=font_name,
                          mapped_font_size=mapped_size,
                          mean_size=mean_size, max_size=max_size)

                # todo, split lines within LTTextBoxHorizontal
                #  split using style as differentiator
                #  e.g 1st is title with bold text
                #      2nd & 3rd line are introduction lines with body style
                #      -> forward 2 boxes (header, content)
                element.style = s
                element.structured_text_element = TextElement(text_container=element.original_element, style=s,   #replaced pdfs TextElement with ppp.element and attached TextElement as structured_text_element
                                  page=element.page if hasattr(element, "page") else None)
                yield element

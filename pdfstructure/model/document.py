from collections import defaultdict
from typing import List
from pdfstructure.analysis.styledistribution import StyleDistribution
from pdfstructure.model.style import Style
from mu_helper import block_font_info


class Element:
    """
    class representing an element with page,block, line, span information.
    """

    def __init__(
            self, page_number: int, original_block, original_page):
        self.page_number = page_number 
        self.block_number = original_block.get('number')
        self.type = original_block.get('type')
        self.lines = original_block.get('lines')
        self.block_styles, self.line_styles = block_font_info(original_block)
        self.page_info = original_page
        self.page_info.bbox = tuple(original_page.rect)
        self.span_styles = {}

    @property
    def block_text(self):

        _span = ""

        for line in self.lines:
            for spans in line['spans']:
                _text = spans['text']
                _span += _text
            _span += '\n'
        return _span




class TextElement:
    """
    Represents one single TextContainer like a line of words.
    """

    def __init__(self, block, style: Style, text=None, page=None):
        self._data = block
        self._text = text
        self.style = style
        self.page = page


    @property
    def text(self):
        if not self._data:
            return self._text
        else:
            return self._data.text.strip()

    @classmethod
    def from_json(cls, data: dict):
        """

        @param data:
        @return:
        """
        if data:
            return TextElement(block=None, style=Style.from_json(data["style"]),
                               text=data.text)
        return None

    def __str__(self):
        return self.text


class Section:
    """
    Represents a section with title, contents and children
    """
    #heading: Element

    def __init__(self, element, level=0):

        if element is not None:
            try:
                element.__dict__.pop('structured_text_element')
            except:
                pass
            self.__dict__.update(element.__dict__)
            
        
        self.children = []  # Section
        self.level = None
        self.set_level(level)

    def set_level(self, level):
        self.level = level

    def append_children(self, section):
        self.children.append(section)

    @property
    def full_content(self):
        """
        Returns merged full content of all nested children.
        @return:
        """
        contents = [self.heading_text] if self.heading_text else []

        def __traverse__(section: Section):
            child: Section
            for child in section.children:
                yield child
                yield from __traverse__(child)

        for child in __traverse__(self):
            if child.heading_text:
                contents.append(child.heading_text)
        return "\n".join(contents)

    @property
    def top_level_content(self):
        """
        Paragraphs that belong directly to section, nested children are skipped.
        Example:
            This is a Header
                paragraph 1
                paragraph 2
                This is a subheader
                    paragraph 3
        Returns:
            [paragraph 1, paragraph 2]

        @return: List[Section]
        """
        child: Section
        content = []
        for child in self.children:
            if child.children:
                continue
            content.append(child)
        return content

    @classmethod
    def from_json(cls, data: dict):
        children = list(map(Section.from_json, data.get("children")))
        heading = TextElement.from_json(data.get("heading"))
        element = cls(heading, data["level"])
        element.children = children
        return element

    @property
    def heading_text(self):
        try:
            # print(self.heading.text)
            return self.text
        except:
            return ""

    def __str__(self):
        
        return self.heading_text
        # return "{}\n{}".format(self.heading.text,
        #                       " ".join([str(child.heading.text) for child in self.children]))


class DanglingTextSection(Section):
    def __init__(self):
        super().__init__(element=None)

    def __str__(self):
        return "{}".format(" ".join([str(e) for e in self.content]))


class StructuredPdfDocument:
    """
    PDF document containing its natural order hierarchy, as detected by the HierarchyParser.
    """
    elements: List[Section]

    def __init__(self,uri: str, elements: [Section], style_info=None):
        self.metadata = defaultdict(str)
        self.uri = uri
        self.elements = elements
        self.metadata["style_distribution"] = style_info


    def update_metadata(self, key, value):
        self.metadata[key] = value

    @property
    def text(self):
        return "\n".join([item.full_content for item in self.elements])

    @property
    def title(self):
        return self.metadata.get("title")
    
    
    @property
    def style_distribution(self) -> StyleDistribution:
        return self.metadata.get("style_distribution")

    @classmethod
    def from_json(cls, data: dict):
        elements = list(map(Section.from_json, data["elements"]))
        pdf = cls(elements)
        pdf.metadata.update(data.get("metadata"))
        return pdf

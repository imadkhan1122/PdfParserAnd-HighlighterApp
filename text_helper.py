import logging
import os
import re
from collections import namedtuple, defaultdict
from typing import List, Tuple, NamedTuple, ValuesView
import fitz
import spacy
from thefuzz import fuzz

from pdfstructure.hierarchy.parser import HierarchyParser
from pdfstructure.source import FileSource
from py_pdf_parser import loaders

nlp = spacy.load("en_core_web_sm")

"""
utilities for already parsed text
generally text field uses text with whitespace
"""

regex_dict = \
    {
        'phone': r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]',
        'email': r'[\w.+-]+@[\w-]+\.[\w.-]+'
    }


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
            blocks = page.get_text_blocks()[:5]  # Check last blocks to extract page number
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


class TextParser:
    """generates tokens of parsed text + text manipulation/filtering tools"""

    def __init__(self, texts):
        self.texts = texts
        self._token_tuple = namedtuple('Token', ['index', 'token', 'line_number', 'line_text_count', 'text'])
        self._result_tuple = namedtuple('Result', ['index', 'matched_string', 'line_number', 'match_ratio', 'tokens'])
        self.tokens = self._get_token_tuples(texts)

    def _get_token_tuples(self, texts: str = None) -> List[NamedTuple]:
        """
        :param texts:
        :return: list of Token Namedtuple
        """
        texts = self.texts if texts is None else texts
        token_list = []
        i = 0
        l = 0
        for line in texts.splitlines():
            line_tokens = nlp(line)
            line_text_count = len(line_tokens)
            for token in line_tokens:
                token_list.append(self._token_tuple(index=i, line_number=l, line_text_count=line_text_count,
                                                    token=token, text=token.text_with_ws))

                i += 1
            l += 1
        return token_list

    def get_sentence_tuples(self) -> List[Tuple]:
        """
        break text into sentences
        :return: [(idx, spacy token),(...)]
        """
        texts = self.texts.replace('\n', '').strip()
        nlp_text = nlp(texts)
        return [(i, s) for i, s in enumerate(nlp_text.sents)]

    def get_text_for_line(self, line_number):
        line_tokens = [(t.token.text_with_ws) for t in self.tokens if t.line_number == line_number]
        return ''.join(line_tokens)

    def get_tokens_between_indices(self, tokens: List[NamedTuple] = None, start: int = None,
                                   end: int = None) -> List[NamedTuple]:
        tokens = self.tokens if tokens is None else tokens
        start = max(0, start)  # To avoid indexing by negative value
        return tokens[start:end]

    def get_text_between_indices(self, tokens: List[NamedTuple] = None, start: int = None, end: int = None) -> str:
        tokens = self.tokens if tokens is None else tokens
        _tokens = self.get_tokens_between_indices(tokens, start, end)
        return "".join([t.token.text_with_ws for t in _tokens])

    def find_string_match(self, string_to_find: str, matches_to_return: int = 5, n_left: int = 0, n_right: int = 0,
                          delta_threshold: float = 100, ignore_case: bool = False) -> List[NamedTuple]:
        """
        params:
        texts: text to search for matching strings
        string_to_find: string to find matches for
        matches_to_return: number of matches to return
        delta_threshold: to only consider match if delta is above or equal to this value
        ignore_case: if True then ignore case while matching by making texts and string_to_find lowercase
            else don't change case

        return:
        list of tuples containing matched string and delta score
        """
        if ignore_case:
            string_to_find = string_to_find.lower()
        matches = []
        string_to_find_len = len(self._get_token_tuples(string_to_find))
        _score = 0  # storing the score

        for idx, token in enumerate(tokens):
            try:
                _tokens_slice = self.get_tokens_between_indices(tokens=self.tokens, start=idx,
                                                                end=idx + string_to_find_len)

                tokens_slice_text = "".join([t.text for t in _tokens_slice]).strip()

                tokens_slice_text = tokens_slice_text.lower() if ignore_case else tokens_slice_text
                fuzz_ratio = fuzz.ratio(string_to_find, tokens_slice_text)

                if fuzz_ratio >= delta_threshold:  # first time it finds string that matches
                    start = idx - n_left
                    end = idx + string_to_find_len + n_right
                    result = self._result_tuple(matched_string=self.get_text_between_indices(start=start, end=end),
                                                match_ratio=fuzz_ratio,
                                                index=idx, line_number=self.tokens[idx].line_number,
                                                tokens=self.tokens[start:end])
                    if fuzz_ratio > _score > 0:
                        matches.pop(-1)  # pop last match if better match found
                    matches.append(result)

                    _score = fuzz_ratio  # set _score to  fuzz_ratio in case we find a better occurrence

                else:  # drops below threshold
                    _score = 0
            except Exception as e:
                logging.exception(e)
                break

        return sorted([m for m in matches if m.match_ratio >= delta_threshold], key=lambda x: x.match_ratio,
                      reverse=True)[:matches_to_return]

    def find_value_for_match(self, string_to_find: str, regex_str: str = '',
                             matches_to_return: int = 1, n_left: int = 0, n_right: int = 10,
                             delta_threshold: float = 100):

        """
        find keyword and return the following n tokens (value)
        args: string_to_find: the string to be found
        regex_str: optional: either key from regex_dict or regex_str
        delta_threshold: similarity ratio
        """
        matches = self.find_string_match(string_to_find, matches_to_return=matches_to_return, n_left=n_left,
                                         n_right=n_right, delta_threshold=delta_threshold, ignore_case=True)
        if not matches:
            return

        result = []

        for match in matches:
            if regex_str != "":  # if regex defined filter regex match from matched string
                if any(ele in regex_str for ele in ['[', ']', '+', '?', '{', '}']):  # if regex str passed directly
                    value = re.search(regex_str, match.matched_string)
                else:  # regex from dict
                    value = re.search(regex_dict.get(regex_str), match.matched_string)
                if value:
                    result.append(value.group())

            else:  # use the following n_tokens after ':' or ','
                token_list = []
                for token in match.tokens[
                             len(self._get_token_tuples(string_to_find)):]:  # exclude the string_to_find
                    if token.text.strip() not in [':', ',']:  # remove if : or , is a token
                        token_list.append(token.token.text_with_ws)
                result.append(''.join(token_list[:n_right]))

        return result

    def regex_match_group(self, pattern, group, flags=0):
        reg = re.compile(pattern=pattern, flags=flags)
        _iter = reg.finditer(self.texts)
        return [m.group(group) for m in _iter]

    def regex_match_find_all(self, pattern, flags=0):
        return re.findall(pattern=pattern, string=self.texts, flags=flags)


class Section:
    """
    A continuous group of elements within a document.
    A section is intended to label a group of elements. Said elements must be continuous
    in the document.

    Args:
        document (Parsed PDFDocument): A reference to the TextParser class.
        name (str): The name of the section.
        unique_name (str): Multiple sections can have the same name, but a unique name
            will be generated by the Sectioning class.
        start_element: The first element in the section.
        end_element: The last element in the section.
    """

    document: TextParser
    name: str
    unique_name: str
    start_element: int
    end_element: int

    def __init__(
            self,
            document: TextParser,
            name: str,
            unique_name: str,
            start_element: int,
            end_element: int,
    ):
        if start_element > end_element:
            raise InvalidSectionError("end_element must come after start_element")
        self.document = document
        self.name = name
        self.unique_name = unique_name
        self.start_element = start_element
        self.end_element = end_element

    def __contains__(self, element) -> bool:
        return element in self.elements

    @property
    def elements(self) -> list:
        """
        All the elements in the section.

        Returns:
            ElementList: All the elements in the section.
        """
        return self.document.tokens[self.start_element:self.end_element]

    def text(self):
        return self.document.get_text_between_indices(self.document.tokens, self.start_element, self.end_element)

    def __eq__(self, other: object) -> bool:
        """
        Returns True if the two sections have the same unique name and are from the
        same document
        """
        if not isinstance(other, Section):
            raise NotImplementedError(f"Can't compare Section with {type(other)}")
        return all(
            [
                self.document == other.document,
                self.unique_name == other.unique_name,
                self.start_element == other.start_element,
                self.end_element == other.end_element,
                self.__class__ == other.__class__,
            ]
        )

    def __len__(self) -> int:
        """
        Returns the number of elements in the section.
        """
        return len(self.elements)

    def __repr__(self) -> str:
        return (
            f"<Section name: '{self.name}', unique_name: '{self.unique_name}', "
            f"number of elements: {len(self)}>"
        )


class Sectioning:
    """
     Creates a new section with the specified name.
     Creates a new section with the specified name, starting at `start_element` and
     ending at `end_element` (inclusive). The unique name will be set to name_<idx>
     where <idx> is the number of existing sections with that name.
     Args:
         name (str): The name of the new section.
         start_element: The first element in the section.
         end_element: The last element in the section.
         include_last_element (bool): Whether the end_element should be included in
             the section, or only the elements which are strictly before the end
             element. Default: True (i.e. include end_element).
     Returns:
         Section: The created section.
     Raises:
         InvalidSectionError: If a the created section would be invalid. This is
             usually because the end_element comes after the start element.
     """

    document: TextParser

    def __init__(self, document: TextParser):
        self.sections_dict = {}
        self.name_counts = defaultdict(int)
        self.document = document

    def create_section(
            self,
            name: str,
            start_element: int,
            end_element: int,
            include_last_element: bool = True,
    ) -> Section:

        current_count = self.name_counts[name]
        unique_name = f"{name}_{current_count}"
        self.name_counts[name] += 1

        if not include_last_element:
            if end_element <= 0:
                raise InvalidSectionError(
                    "Section would contain no elements as end_element is the first "
                    "element in the document and include_last_element is False"
                )
        section = Section(self.document, name, unique_name, start_element, end_element)
        self.sections_dict[unique_name] = section
        return section

    def get_sections_with_name(self, name: str) -> List[Section]:
        """
        Returns a list of all sections with the given name.
        """
        return [self.sections_dict[f"{name}_{idx}"] for idx in range(self.name_counts[name])]

    def get_section(self, unique_name: str) -> Section:
        """
        Returns the section with the given unique name.
        Raises:
            SectionNotFoundError: If there is no section with the given unique_name.
        """
        try:
            return self.sections_dict[unique_name]
        except KeyError as err:
            raise SectionNotFoundError(
                f"Could not find section with name {unique_name}"
            ) from err

    @property
    def sections(self) -> ValuesView[Section]:
        """
        Returns the list of all created Sections.
        """
        return self.sections_dict.values()


class InvalidSectionError(Exception):
    """Raise exception for invalid section"""


class SectionNotFoundError(Exception):
    """Raise exception if section not found"""


def main():
    path_kid = './data/sample_kids/cp_kid.pdf'
    path_TOC = './data/sample_TOC/Xtracker pg 4.pdf'

    doc = loaders.load_file(path_kid)
    texts = ''
    for p in doc.pages:
        for e in p.elements:
            texts += f'{e.text()}'

    print(texts)
    return
    # contents = re.findall('(.*?)[\W]+(\d+)(?=\n|$)', texts, flags=re.M)

    contents = re.findall(r'^\d+(?:\.\d+)* .*(?:\r?\n(?!\d+(?:\.\d+)* ).*)*', texts, flags=re.M)
    print(contents)
    return
    texts = "".join(element.text() for element in doc.elements)
    print(texts)

    # prospectr
    # toc_doc = loaders.load_file(path_TOC)
    # texts = " ".join(element.text() for element in toc_doc.elements)

    doc = fitz.open(path_TOC)
    page = doc.load_page(0)
    texts = page.get_text("text")

    # kid_doc = loaders.load_file(path_kid)
    # texts = "".join(element.text() for element in path_kid.elements)

    tp = TextParser(texts)

    # get sentences from text
    sents = tp.get_sentence_tuples()

    # get tokens
    tokens = tp._get_token_tuples(texts)

    # get tokens for line
    tfl = tp.get_text_for_line(3)

    # get tokens between indices
    tbi = tp.get_tokens_between_indices(start=10, end=20)

    # get text between indices
    txtbi = tp.get_text_between_indices(start=199, end=204)

    # #TextParser.find_string_match
    match = tp.find_string_match(string_to_find='and regulated by', n_left=0, n_right=3,
                                 matches_to_return=10, delta_threshold=80, ignore_case=True)

    # #find value for match
    values = tp.find_value_for_match(string_to_find='Recommended holding period', regex_str='', n_left=0, n_right=5,
                                     matches_to_return=10)

    # find group with regex
    search_string = 'regulated'
    pattern = r'(?i)(.+?){}\s+(.+?)\.'.format(search_string)
    group = 2
    res = tp.regex_match_group(pattern=pattern, group=group, flags=re.DOTALL)
    print(res)

    res = tp.regex_match_find_all(pattern=pattern, flags=re.DOTALL)
    print(res)

    # sectioning = Sectioning(document=tp)
    # sectioning.create_section(name='section1', start_element=2, end_element=10)
    # sectioning.create_section(name='section2', start_element=12, end_element=25)
    # section1 = sectioning.get_sections_with_name(name='section1')[0]
    # section2 = sectioning.get_sections_with_name(name='section2')[0]
    # print(section2.text())
    # print(section1.__contains__(section2.elements[0]))


def test():
    pdf_dir = 'data/sample_prospectus'
    for p in os.listdir(pdf_dir):  # Loop over to test each pdf file in pdf dir
        file = pdf_dir + '/' + p
        print(file)
        doc = fitz.open(file)
        pte = PdfTextExtraction(doc)
        print(pte.extract_page_numbers())

    exit()

    parser = HierarchyParser()

    path_kid = './data/sample_kids/cp_kid.pdf'
    path_TOC = './data/sample_TOC/Xtracker pg 4.pdf'

    # specify source (that implements source.read())
    source = FileSource(path_kid)
    source.load()

    # analyse document and parse as nested data structure
    document = parser.structure_document(source)
    texts = ''.join([e.full_content for e in document.elements])
    # Find phone numbers
    matches = re.findall(r'[\+\(]?[1-9][0-9 .\-\(\)]{9,}[0-9]', texts, re.M)
    print(matches)

    # Find titles
    matches = re.findall(r'\w{2},(.*),\d{4}', texts, re.M)
    print(matches)


if __name__ == "__main__":
    test()

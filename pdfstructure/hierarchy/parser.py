from pathlib import Path
from typing import List, Generator
from pdfstructure.hierarchy.headercompare import get_default_sub_header_conditions
from pdfstructure.model.document import TextElement, Section, StructuredPdfDocument, DanglingTextSection
from pdfstructure.source import Source
from mu_helper import Whitespace


class HierarchyParser:

    def __init__(self, header_conditions_cls, sub_header_conditions=get_default_sub_header_conditions()):
        self._isSubHeader = sub_header_conditions
        self.header_conditions_cls = header_conditions_cls

    def structure_document(self, source: Source) -> StructuredPdfDocument:
        """
        Analyses and parses a PDF document from a given @Source containing its natural hierarchy.
        @param source:
        @return:
        """
        structured_elements = self.create_hierarchy(source)
        
        # create wrapped document and capture some metadata
        structured_document = StructuredPdfDocument(uri=source.uri, elements=structured_elements, style_info=source.font_info)
        
        return structured_document

    def create_hierarchy(self, source) -> List[Section]:
        """
        Takes incoming flat list of paragraphs and creates nested natural order hierarchy.

        Example Structure:
        ==================
        Document.pdf
        <<
            1.  H1 Chapter Header
            content
                1.2     H2 Section Header
                content
                1.3     H2 Section Header
                content
                    1.3.1   H3 Subsection Header
                    content
            2.  H1 Chapter Header
            content
        >>

        @param block_gen:
        @return:
        """

        structured = []
        level_stack = []
        all_elements=[]
        element_gen = source.read_blocks()
        doc_style = source.font_info
        

        for element in element_gen:
            #for info only when debugging
            
            element.page_w = doc_style['page_w']
            element.page_h = doc_style['page_h']
            
            if self.header_conditions_cls(element,doc_style).check_condition_pipeline():
                element.label = 'heading' 
                child = Section(element)
                header_size = element.span_styles['font_stats']['size']
               
                # print(element.text)
                # initial state - push and continue with next block
                if not level_stack:
                    self.__push_to_stack(child, level_stack, structured)
                    continue

                stack_peek_size = level_stack[-1].span_styles['font_stats']['size']
        
                if stack_peek_size > header_size:
                    # append block as children
                    self.__push_to_stack(child, level_stack, structured)
        
                else:
                    # go up in hierarchy and insert block (as children) on its level
                    self.__pop_stack_until_match(level_stack, header_size, child)
                    self.__push_to_stack(child, level_stack, structured)
        
            else:
                # no header found, add paragraph as a content block to previous node
                # - content is on same level as its corresponding header
                element.label = ''
                content_node = Section(element, level=len(level_stack))
                if level_stack:
                    level_stack[-1].append_children(content_node)
                else:
                    # if last block in output structure has also no header, merge
                    if structured and isinstance(structured[-1], DanglingTextSection):
                        structured[-1].append_children(content_node)
                    else:
                        # # add dangling content as section
                        dangling_content = DanglingTextSection()
                        dangling_content.append_children(content_node)
                        dangling_content.set_level(len(level_stack))
                        structured.append(dangling_content)
            all_elements.append(element)
        return structured #, all_elements

    def __pop_stack_until_match(self, stack, headerSize, header):
        # if top level is smaller than current header to test, pop it
        # repeat until top level is bigger or same

        while self.__top_has_no_header(stack) or self.__should_pop_higher_level(stack, header):
            poped = stack.pop()
            # header on higher level in stack has sime FontSize
            # -> check additional sub-header conditions like regexes, enumeration etc.
            if poped.span_styles['font_stats']['size'] == headerSize:
                # check if header_to_check is sub-header of poped element within stack
                if self._isSubHeader.test(poped, header):
                    stack.append(poped)
                    return

    @staticmethod
    def __push_to_stack(child, stack, output):
        """
        insert incoming paragraph (child) in level(hierarchy) stack.
        @param child: next incoming paragraph
        @param stack: hierarchy-detect helper stack
        @param output: exporting list of elements (contains complete structure in the end)
        @return:
        """
        if stack:
            child.set_level(len(stack))
            stack[-1].children.append(child)
        else:
            # append as highest order element
            output.append(child)
        stack.append(child)

    @staticmethod
    def __should_pop_higher_level(stack: [Section], header_to_test: Section):
        """
        helper method for __pop_stack_until_match: check if last element in stack is smaller then new header-paragraph.
        @type header_to_test: object

        """
        if not stack:
            return False
        return stack[-1].span_styles['font_stats']['size'] <= header_to_test.span_styles['font_stats']['size']

    @staticmethod
    def __top_has_no_header(stack: [Section]):
        """
        helper method for @__pop_stack_until_match
        @param stack:
        @return:
        """
        if not stack:
            return False
        return len(stack[-1].text) == 0



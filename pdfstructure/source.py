import fitz
from typing import Generator, Any
from mu_helper import doc_font_info, span_font_info, block_font_info
from pdfstructure.model.document import Element



class Source:
    """
    Abstract interface to read a PDF from somewhere.
    """
    def __init__(self, uri=None):
        """
        @param uri: points to pdf that should be read
        """
        self.uri = uri

    def config(self):
        """
        get source configuration
        @return:
        """
        pass

    def read(self, *args, **kwargs) -> Generator:
        """
        yields flat list of paragraphs within a document.
        @param args:
        @param kwargs:
        @return:
        """
        pass




class FileSource(Source):
    def __init__(self, file_path: str, page_numbers=None,
                 **kwargs):
        super().__init__(uri=file_path)
        self.load()
        self.page_numbers = page_numbers
        self.params = kwargs
        self.font_info = doc_font_info(self.doc)

    def load(self,**kwargs):
        self.doc = fitz.open(self.uri, **kwargs)

    def config(self):
        return self.__dict__


    def read_blocks(self) -> Generator:
        #generate stream of spans
        pNumber = 0
        for page in self.doc:
            _blocks = page.get_text("dict", sort=True)["blocks"]
            for _block in _blocks:
                if _block['type'] == 0:
                    block = Element(pNumber, original_block=_block, original_page=page)
                    for line in block.lines:
                        for span in line['spans']:
                            block.span_styles = span_font_info(span)
                            block.text = span['text']
                            
                            yield block
            pNumber += 1




    
# if __name__ == "__main__":
#     source = PMPFileSource('data/sample_kids/fid_kid.pdf')
#     source.load()

#     block_gen = source.read_blocks()

#     block_gen.__next__().text
    
#     for block in block_gen:
#         print(block.lines)

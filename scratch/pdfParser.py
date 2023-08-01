import fitz
import re
from collections import Counter


path = '../data/sample_kids/ab_kid.pdf'

doc = fitz.open(path)

keys = ['Key Information Document', 'Product', 'What is this product?', 'What are the risks and what could I get in return?'
        , 'Performance Scenarios', 'What happens if AllianceBernstein (Luxembourg) S.à r.l. is unable to pay out?',
        'What are the costs?', 'How long should I hold it and can I take money out early?', 'How can I complain?',
        'Other relevant information']

def font_info(doc):
    All_Pages = []
    SIZE = []
    FONT = []
    COLOR = []
    for page in doc:
        h, w = page.rect.height, page.rect.width
        rect = fitz.Rect(0, 10, w, h-20)
        blocks = page.get_text("dict", sort=True, clip=rect)["blocks"]
        # blocks = [x[4] for x in  doc[0].text("blocks", sort=True)]
        Blocks = []
        for block in blocks:
            Block = []
            txt = ''
            try:
                for spans in block['lines']:
                    size = spans['spans'][0]['size']
                    SIZE.append(size)
                    font = spans['spans'][0]['font']
                    FONT.append(font)
                    text = spans['spans'][0]['text']
                    color = spans['spans'][0]['color']
                    COLOR.append(color)
                    txt+=text
                    Block.append({'size':size, 'style':font, 'color':color,'text':text})
            except:
                pass
            Blocks.append(Block)
        All_Pages.append(Blocks)

    return All_Pages, SIZE, FONT, COLOR
#
All_Pages_Blocks, size, font, color = font_info(doc)

#
uni_sizes = list(set(size))
uni_sizes.sort(reverse=True)
#
size_counts = Counter(size)
most_common_size = size_counts.most_common(1)[0][0]
#
fonts_counts = Counter(font)
most_common_font = fonts_counts.most_common(1)[0][0]
#
color_counts = Counter(color)
most_common_color = color_counts.most_common(1)[0][0]

headings = []
for page in All_Pages_Blocks:
    for block in page:
        if block != []:
            for line in block:
                # if 'bold' in line['style'] or 'Bold' in line['style'] and line['size'] != most_common_size:
                #     headings.append(line['text'])
                # elif line['style'] != most_common_font:
                #     headings.append(line['text'])
                if line['size'] == uni_sizes[3]:
                    print(line['text'])
            

        
        
if __name__ == "__main__":
    fi = font_info(doc)
        
        
        
        
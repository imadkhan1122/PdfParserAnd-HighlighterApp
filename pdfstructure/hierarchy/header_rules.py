from string import printable
from pdfstructure.utils import word_generator

from mu_helper import Whitespace

# INDIVIDUAL CONDITIONS TO ANALYSE HEADER. HAVE TO RETURN TRUE TO PASS HEADER TEST
#######################################################################################################################
# TODO: ADD MORE RULES TO DETERMINE IF HEADER OR NOT LIKE:
# DOES LINE START WITH NUMBER, ROMAN NUMBER....


def min_length(element, min_letters=3):
    """
    min letters: int
    :return: bool
    """
    return len(element.text) >= min_letters


def span_size_larger_than_common(element, doc_font):
    """ font size differs from common font"""
    return element.span_styles['font_stats']['size'] > doc_font['font_stats']['common_size']


def span_color_differ_than_common(element, doc_font):
    """ font color differs from common font"""
    return element.span_styles['font_stats']['color'] != doc_font['font_stats']['common_color']


def span_style_differ_than_common(element, doc_font)->bool:
    """ font name differs from common font"""
    return element.span_styles['font_stats']['font'] != doc_font['font_stats']['common_font']


def min_alpha(element)->bool:
    """
    fr a paragraph to be treated as a header, it has to contain at least 2 letters.
    @param element:
    @return:
    """
    alpha_count = 0
    numeric_count = 0
    for word in word_generator(element):
        for c in word:
            if c.isalpha():
                alpha_count += 1
            if c.isnumeric():
                numeric_count += 1

            if alpha_count >= 2:
                return True
    return False


def check_special_char(element)->bool:
    if set(element.text).difference(printable):
        return False
    else:
        return True

def no_dot_at_end(element)->bool:
    # checks if text doesn't end with a dot
    return not '.' in element.text[-2:]

def is_title(element)->bool:
    if check_bold(element) == False and check_italic(element) == False:
        cond = 0
        s = element.text.split(' ')
        if cond == 0:
            if any(word[0].isupper() == False for word in s if word):
                cond = 0
            else:
                cond = 1
                    
        elif cond == 0:
            if any(word.isupper() == False for word in s if word):
                cond = 0
            else:
                cond = 1
                
        if cond == 1:
            return True
        else:
            return False
    else:
        return True

def check_digit(element)->bool:
    ele = element.text
    try:
        first_alph = ele.find(next(filter(str.isalpha, ele)))
    except:
        first_alph = 0
    if any(i.isnumeric() for i in ele[first_alph:]):
        return False
    else:
        return True


def check_bold(element)->bool:
    #checks if bold in font name
    return element.span_styles['font_stats']['bold']


def check_italic(element)->bool:
    # checks if italic in font name
    return element.span_styles['font_stats']['italic']


def string_validity(element)->bool:
    ele = element.text
    try:
        first_alph = ele.find(next(filter(str.isalpha, ele)))
    except:
        first_alph = 0
    check = []
    if first_alph < 3 and ele[first_alph].isupper() == True:
        for e in ele[first_alph:].replace(' ', ''):
            if e.isalpha() == True or e == ':' or e == '?':
                check.append(True)
            else:
                check.append(False)
        if any(char is False for char in check):
            return False
        else:
            return True

def centered(element, threshold=10)->bool:
    """
    check if element is centered on page vs block or page if span == block
    :param element:
    :param threshold: percentage how much center can deviate from mid to still be centered (10 = 10% of mid vs width
    :return:
    """
    ws = Whitespace(element.block_styles['bbox'], element.span_styles['bbox'])

    return ws.is_centered(threshold) if not ws.one_span else Whitespace(element.page_info.bbox, element.span_styles['bbox'])



def lSpaces(element, min_space=10)->bool:
    """
    check if element has whitespace on left vs block or page if span == block
    :param element:
    :param threshold: percentage how much left space (10 = 10% of ls vs width)
    :return:
    """

    ws = Whitespace(element.block_styles['bbox'], element.span_styles['bbox'])

    return ws.whitespace_left > min_space if not ws.one_span else Whitespace(element.page_info.bbox,
                                                            element.span_styles['bbox']).whitespace_left > min_space


def rSpaces(element, min_space=20)->bool:
    """
     check if element has whitespace on right vs block or page if span == block
     :param element:
     :param threshold: percentage how much right space (10 = 10% of ls vs width)
     :return: bool
     """

    ws = Whitespace(element.block_styles['bbox'], element.span_styles['bbox'])

    return ws.whitespace_right > min_space if not ws.one_span else Whitespace(element.page_info.bbox,
                                                            element.span_styles['bbox']).whitespace_right > min_space

def whitespace_ratio(element, min_ratio=20) ->bool:
    """
      check how much whitespace there is vs block width or page width if span == block
      :param element:
      :param threshold: percentage how much right space (10 = 10% of ls vs width)
      :return: bool ie ws > threshold
      """
    ws = Whitespace(element.block_styles['bbox'], element.span_styles['bbox'])

    return ws.whitespace_ratio > min_ratio if not ws.one_span else Whitespace(element.page_info.bbox,
                                                            element.span_styles['bbox']).whitespace_ratio > min_ratio

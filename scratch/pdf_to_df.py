import fitz
import pandas as pd
from io import StringIO
import nltk

def pos_tag(text):

    try:
        pos = nltk.pos_tag(nltk.word_tokenize(text))
        counter = []
        sorter = {}
        for k in pos:
            if k[1] == "NN" or k[1] == "NNP" or k[1] == "NNS":
                tag = "NN"
                counter.append(tag)
            else:
                counter.append(k[1])

        for v in list(set(counter)):
            sorter[v] = counter.count(v)

        ratio = pd.Series(sorter).sort_values(ascending=True).iloc[0] / len(counter)

    except:
        ratio = 0

    return ratio

def header_rules(df):

    font_style_ts = []
    max_len = 6
    pos_ratio = 0.6
    ending_flag = "?"
    font_change = "Y"
    dict = {}

    for k,v in df.iterrows():
        score = 0
        if len(nltk.word_tokenize(v["text"])) <= max_len:
            score += 0.25

        if pos_tag(v["text"]) >= pos_ratio:
            score += 0.25

        if v["text"].endswith(ending_flag) is True:
            score += 0.25

        font_style = f"{v['size']}/{v['flags']}/{v['font']}/{v['color']}"
        if k == 0:
            font_style_ts.append(font_style)
        else:
            if font_style != font_style_ts[-1]:
                score += 0.25
                font_style_ts.append(font_style)
            else:
                font_style_ts.append(font_style)

        dict[v["text"]] = "H" if score >= 0.5 else "P"
    return dict


def create_agg_df(dict):
    """

    :param dict: dictionary of list, each list contains a block line associated by font
    :return: Adobe-like dataframe with columns, size/font/flag/color/text
    """

    df = pd.DataFrame()
    for k in dict.keys():
        for v in dict[k]:
            for y in v.values():
                ser = pd.Series(y)
                df = pd.concat([df, ser], axis=1)

    return df

def analyse_block(block):

    """

    :param block: retrieve from fun create block, an identified pdf block with single or multiple spans
    :return: Combines spans into single string based on font features
    """

    fonts = {}
    reduced_df = {}
    for k in range(len(list(block.keys()))):

        font_feat_i = f"{block[k].get('size')}_{block[k].get('flags')}_{block[k].get('font')}_{block[k].get('color')}"
        text_i = block[k].get("text")
        if font_feat_i not in list(fonts.keys()):
            fonts[font_feat_i] = text_i
        else:
            fonts[font_feat_i] += f" {text_i}"

    starter = 0
    for k in fonts.keys():

        items = k.split("_")

        reduced_df[starter] = {"size": items[0], "flags": items[1], "font": items[2], "color": items[3],
                               "text": fonts[k]}
        starter += 1

    return reduced_df


def create_block(block, page):

    df_lst = []
    df_subref = {}
    params = ["size", "flags", "font", "color", "text"]
    block_sub_ref = 0

    try:

        for l in block["lines"]:
            df_item = {}
            str = ""
            for k in l["spans"]:
                for x, y in k.items():
                    df_item["page"] = page
                    if x in params:
                        if x == "text":
                            str += y
                            df_item[x] = y
                        else:
                            df_item[x] = y

                    df_item["text"] = str.replace(u'\xa0', u' ')

            df_subref[block_sub_ref] = df_item
            block_sub_ref += 1

        x = analyse_block(df_subref)
        df_lst.append(x)
        #df_subref[block_sub_ref] = x

    except:
        pass

    #return df_subref
    return df_lst


def PdfToDf(file):

    """

    :param file: .pdf file
    :return: dataframe
    """

    doc = fitz.open(file)
    df_blocks = {}
    ref = 0
    for page in doc.pages():
        try:
            content = pd.read_json(page.text(option ="json"))
        except:
            content = pd.read_json(StringIO(page.text(option ="json")))

        for k in content["blocks"]:
            df = create_block(k, page = page)
            df_blocks[ref] = df
            ref += 1

    df = create_agg_df(df_blocks).transpose().reset_index()
    tags = header_rules(df)
    return df
    #return pd.DataFrame(df_blocks).transpose()


if __name__ == "__main__":

    x = PdfToDf("./data/sample_kids/fid_kid.pdf")
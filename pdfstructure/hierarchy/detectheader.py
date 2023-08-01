from pdfstructure.hierarchy.header_rules import *


class DetectHeaderBase:
    """
Base class handling the header conditions
block : mu_helper.Block
doc_styles: source.font_info
conditions_pipeline: all conditions in this list need to be true to return true
conditions_OR: dict of group of conditions. for each group at least 1 condition needs to be true for that group to return true
            each group of OR conditions needs to be added to the condition_pipeline to check whether all elements in there are true
    """

    def __init__(self, element, doc_styles):
        self.element = element
        self.doc_styles = doc_styles
        self.conditions_pipeline = []   #list of booleans that all need to be true to return true.
        self.conditions_OR = {}     #dict of group of conditions where only 1 condition in a group needs to be true for the group to return true


    def add_condition_to_pipeline(self, label, condition):
        self.conditions_pipeline.append((label, condition))


    def add_condition_to_OR_group(self, label, condition):

        """
        :param group: name of the group that contains the conditions where 1 needs to be true to return true
        :param condition: conditon method
        :return: {group1:[condition1, condition2...],  ->if cond1 or cond2 == True -> group1 is True
                  group2:[condition3, conditions4...]  ->if cond3 or cond4 == True -> group2 is True
                 }
        """
        if label in self.conditions_OR.keys():  #append condition to existing group
            self.conditions_OR[label].append((label, condition))
        else:
            self.conditions_OR[label] = [(label, condition)]  #greate group as key and put condition in list


    def add_OR_group_to_condition_pipeline(self, label):
        "checks if any condition in a group is True"
        if label in self.conditions_OR.keys():
            cond_bool = any(condition for label, condition in self.conditions_OR[label])
            self.add_condition_to_pipeline(label, cond_bool)


    def check_condition_pipeline(self):
        "checks if ALL conditions in conditions_all are true"
        bool_cond_list = [b for l,b in self.conditions_pipeline]
        return all(bool_cond_list)


#SET OF RULES CLASS FOR KID DOCUMENTS
class DetectHeaderKID(DetectHeaderBase):
    """
DetectHeader class optimised for KID documents
    """

    def __init__(self, element, doc_styles):
        super().__init__(element, doc_styles)
        #must haves:
        self.add_condition_to_pipeline('min_alpha',min_alpha(self.element))
        self.add_condition_to_pipeline('min_length', min_length(self.element, 4))
        self.add_condition_to_pipeline('no_dot_at_end', no_dot_at_end(self.element))
        self.add_condition_to_pipeline('digit', check_digit(self.element))
        self.add_condition_to_OR_group('larger_common', span_size_larger_than_common(self.element, self.doc_styles))
        self.add_condition_to_OR_group('color_diff_common', span_color_differ_than_common(self.element, self.doc_styles))
        self.add_condition_to_OR_group('style_diff_common', span_style_differ_than_common(self.element, self.doc_styles))
        self.add_condition_to_pipeline('special_char', check_special_char(self.element))
        self.add_condition_to_pipeline('digit', check_digit(self.element))
        self.add_condition_to_pipeline('string', string_validity(self.element))
        self.add_condition_to_OR_group('bold', check_bold(self.element))
        self.add_condition_to_OR_group('italic', check_italic(self.element))
        self.add_condition_to_pipeline('whitespace', whitespace_ratio(self.element, 20))


        #one needs to be true for OR1:
        self.add_condition_to_OR_group('OR1', lSpaces(self.element, 0.1))
        self.add_condition_to_OR_group('OR1', rSpaces(self.element, 0.25))
        self.add_condition_to_OR_group('OR1', centered(self.element))
        self.add_condition_to_OR_group('OR1', is_title(self.element))
        self.add_OR_group_to_condition_pipeline('OR1')



#SET OF RULES CLASS FOR PROSPECTUS DOCUMENTS
class DetectHeaderProspectus(DetectHeaderBase):
    """
    DetectHeader optimised for Prospectus
    """

    def __init__(self, element, doc_styles):
        super().__init__(element, doc_styles)


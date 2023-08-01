import pdf2image
import numpy as np
import layoutparser as lp
import torchvision


"""
https://layout-parser.readthedocs.io/en/latest/example/parse_ocr/index.html
pip install "detectron2@git+https://github.com/facebookresearch/detectron2.git@v0.5#egg=detectron2"
"""
pdf_file= './data/sample_kids/fid_kid.pdf' # Adjust the filepath of your input image accordingly
img = np.asarray(pdf2image.convert_from_path(pdf_file)[1])

model = lp.Detectron2LayoutModel('lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config',
                                 extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
                                 label_map={0: "Text", 1: "Title", 2: "List", 3:"Table", 4:"Figure"})
layout_result = model.detect(img)

lp.draw_box(img, layout_result,  box_width=5, box_alpha=0.2, show_element_type=True).show()
import shutil
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ppstructure.recovery.recovery_to_doc import sorted_layout_boxes, convert_info_docx



from flask import Flask, request, jsonify
import os
import cv2
import numpy as np
from pdf2image import convert_from_path
from werkzeug.utils import secure_filename
from collections import OrderedDict
import pandas as pd
import json

from word2json import process_word_document
from ppstructure.utility import parse_args
from ppstructure.predict_system import StructureSystem  # 根据你的实际路径修改

ORDERED_KEYS = [
    '病案标识', '住院号',
    '主诉', '现病史', '既往史', '个人史', '婚姻史', '家族史',
    '入院情况', '入院诊断', '诊疗经过', '病程记录',
    '手术名称', '手术经过', '术中诊断',
    '影像学意见', '超声提示', '超声印象',
    '出院诊断'
]

app = Flask(__name__)
UPLOAD_DIR = 'Uploads'
OUTPUT_DIR = 'output/structure'
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

#Step 1：加载模型，只执行一次
args = parse_args()
args.det_model_dir = 'inference/ch_PP-OCRv4_det_server_infer'
args.rec_model_dir = 'inference/ch_PP-OCRv4_rec_server_infer'
args.rec_char_dict_path = '../ppocr/utils/ppocr_keys_v1.txt'

args.layout_model_dir = 'inference/picodet_lcnet_x1_0_fgd_layout_infer'
args.layout_dict_path = '../ppocr/utils/dict/layout_dict/layout_publaynet_dict.txt'

args.vis_font_path = '../doc/fonts/simfang.ttf'

args.recovery = True
args.table = False
args.layout = True
args.output = OUTPUT_DIR

ocr_engine = StructureSystem(args)

def pdf_to_images(pdf_path):
    return convert_from_path(pdf_path, dpi=300)


def modify_diagnoses(data):
    try:
        admission_diagnoses = data['data']['content'].get('入院诊断', '')
        discharge_diagnoses = data['data']['content'].get('出院诊断', '')

        def reformat(diag_text):
            count = 1
            new_list = []
            for item in diag_text.split(' '):
                if item.strip():
                    if item[0].isdigit() and '.' in item:
                        diagnoses = item.split('.', 1)[1].strip()
                        for diag in diagnoses.split(' '):
                            if diag.strip():
                                new_list.append(f"{count}. {diag.strip()}")
                                count += 1
                    else:
                        new_list.append(f"{count}. {item.strip()}")
                        count += 1
            return ' '.join(new_list)

        if admission_diagnoses:
            data['data']['content']['入院诊断'] = reformat(admission_diagnoses)
        if discharge_diagnoses:
            data['data']['content']['出院诊断'] = reformat(discharge_diagnoses)

        return data
    except Exception as e:
        print(f"Error modifying diagnoses: {str(e)}")
        return data


def export_to_excel(data, output_path):
    try:
        rows = [{'字段': key, '值': value} for key, value in data['data']['content'].items()]
        df = pd.DataFrame(rows)
        excel_path = os.path.join(output_path, 'output.xlsx')
        df.to_excel(excel_path, index=False, sheet_name='Medical Record', engine='openpyxl')
        print(f"Excel file saved to {excel_path}")
    except Exception as e:
        print(f"Error exporting to Excel: {str(e)}")


@app.route('/ocr', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file or not file.filename.endswith('.pdf'):
        return jsonify({'error': '请上传 PDF 文件'}), 400

    filename = secure_filename(file.filename)
    pdf_path = os.path.join(UPLOAD_DIR, filename)
    file.save(pdf_path)

    # 清空旧输出目录
    if os.path.exists(OUTPUT_DIR):
        for f in os.listdir(OUTPUT_DIR):
            path = os.path.join(OUTPUT_DIR, f)
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)

    try:
        # Step 2：PDF 转图片并结构分析
        images = pdf_to_images(pdf_path)
        all_res = []
        for idx, img in enumerate(images):
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            res, _ = ocr_engine(img_cv, img_idx=idx)
            h, w, _ = img_cv.shape

            from ppstructure.recovery.recovery_to_doc import sorted_layout_boxes
            sorted_res = sorted_layout_boxes(res, w)
            all_res += sorted_res

        # Step 2.5：恢复为 Word 文档
        from ppstructure.recovery.recovery_to_doc import convert_info_docx
        img_name = os.path.splitext(filename)[0]
        convert_info_docx(img_cv, all_res, OUTPUT_DIR, img_name)

        # Step 3：从生成的 Word 文件中提取字段
        word_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.docx')]
        if not word_files:
            return jsonify({'error': '未生成 Word 文件'}), 500

        raw = process_word_document(os.path.join(OUTPUT_DIR, word_files[0])) or {}
        ordered = OrderedDict((k, raw.get(k, '')) for k in ORDERED_KEYS)
        response_data = {'data': {'content': ordered}}

        # Step 4：格式化诊断字段
        response_data = modify_diagnoses(response_data)

        # Step 5：保存 JSON 和 Excel
        with open(os.path.join(OUTPUT_DIR, 'output.json'), 'w', encoding='utf-8') as f:
            json.dump(response_data, f, ensure_ascii=False, indent=2)

        export_to_excel(response_data, OUTPUT_DIR)

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': f'OCR 处理失败: {str(e)}'}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

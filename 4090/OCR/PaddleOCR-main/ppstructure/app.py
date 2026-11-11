from flask import Flask, request, jsonify
import os
import subprocess
import shutil
from werkzeug.utils import secure_filename
from word2json import process_word_document
import json
from collections import OrderedDict
import pandas as pd

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


def modify_diagnoses(data):
    """
    Modifies the admission and discharge diagnoses in the data dictionary by reformatting
    numbered diagnosis items into individual numbered entries.
    """
    try:
        # Get admission and discharge diagnoses
        admission_diagnoses = data['data']['content'].get('入院诊断', '')
        discharge_diagnoses = data['data']['content'].get('出院诊断', '')

        # Modify admission diagnoses
        if admission_diagnoses:
            admission_list = admission_diagnoses.split(' ')
            new_admission = []
            count = 1
            for item in admission_list:
                if item.strip():
                    # Handle numbered diagnosis items
                    if item[0].isdigit() and '.' in item:
                        diagnoses = item.split('.', 1)[1].strip()
                        for diag in diagnoses.split(' '):
                            if diag.strip():
                                new_admission.append(f"{count}. {diag.strip()}")
                                count += 1
                    else:
                        new_admission.append(f"{count}. {item.strip()}")
                        count += 1
            data['data']['content']['入院诊断'] = ' '.join(new_admission)

        # Modify discharge diagnoses
        if discharge_diagnoses:
            discharge_list = discharge_diagnoses.split(' ')
            new_discharge = []
            count = 1
            for item in discharge_list:
                if item.strip():
                    # Handle numbered diagnosis items
                    if item[0].isdigit() and '.' in item:
                        diagnoses = item.split('.', 1)[1].strip()
                        for diag in diagnoses.split(' '):
                            if diag.strip():
                                new_discharge.append(f"{count}. {diag.strip()}")
                                count += 1
                    else:
                        new_discharge.append(f"{count}. {item.strip()}")
                        count += 1
            data['data']['content']['出院诊断'] = ' '.join(new_discharge)

        return data
    except Exception as e:
        print(f"Error modifying diagnoses: {str(e)}")
        return data


def export_to_excel(data, output_path):
    """
    Exports the JSON data to an Excel file with fields and values as rows.
    """
    try:
        # Prepare data for Excel
        rows = [{'字段': key, '值': value} for key, value in data['data']['content'].items()]
        df = pd.DataFrame(rows)

        # Save to Excel
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

    # 保存 PDF
    pdf_path = os.path.join(UPLOAD_DIR, secure_filename(file.filename))
    file.save(pdf_path)

    # 清理旧输出
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 调用 OCR 脚本
    try:
        cmd = ['bash', 'pdf_word.sh', pdf_path, 'output']
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        return jsonify({'error': 'OCR 处理失败'}), 500

    # 找 Word 文件
    word_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.docx')]
    if not word_files:
        return jsonify({'error': '未生成 Word 文件'}), 500

    # 提取字段
    raw = process_word_document(os.path.join(OUTPUT_DIR, word_files[0])) or {}

    # 按固定顺序构造结果
    ordered = OrderedDict((k, raw.get(k, '')) for k in ORDERED_KEYS)
    # ordered = OrderedDict((k, 'aaa') for k in ORDERED_KEYS)

    # 构造 JSON 数据
    response_data = {'data': {'content': ordered}}

    # 修改诊断内容
    response_data = modify_diagnoses(response_data)

    # 保存 JSON 到文件
    json_path = os.path.join(OUTPUT_DIR, 'output.json')
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error writing JSON file: {str(e)}")
        return jsonify({'error': '保存 JSON 文件失败'}), 500

    # 导出到 Excel
    export_to_excel(response_data, OUTPUT_DIR)

    # 返回响应
    return jsonify(response_data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
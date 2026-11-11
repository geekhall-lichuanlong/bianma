import shutil, sys, os, uuid, time
from flask import Flask, request, jsonify
import cv2, numpy as np
from pdf2image import convert_from_path
from werkzeug.utils import secure_filename
from collections import OrderedDict
import pandas as pd
import json
from concurrent.futures import ThreadPoolExecutor  # 改成线程池
import os

# -------------------
# PaddleOCR 相关
# -------------------
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ppstructure.recovery.recovery_to_doc import sorted_layout_boxes, convert_info_docx
from word2json import process_word_document
from ppstructure.utility import parse_args
from ppstructure.predict_system import StructureSystem

# -------------------
# 进度管理（线程安全字典）
# -------------------
progress_dict = {}
ORDERED_KEYS = [
    '病案标识','住院号','主诉','现病史','既往史','个人史','婚姻史','家族史',
    '入院情况','入院诊断','诊疗经过','病程记录','手术名称','手术经过','术中诊断',
    '影像学意见','超声提示','超声印象','出院诊断'
]

def init_progress(task_id, total):
    progress_dict[task_id] = {'total': total, 'done': 0}

def update_progress(task_id):
    if task_id in progress_dict:
        progress_dict[task_id]['done'] += 1

def get_progress(task_id):
    return progress_dict.get(task_id, None)

def print_progress(done, total, task_id):
    percent = done / total * 100
    bar = '=' * int(percent/5) + '-' * (20 - int(percent/5))
    sys.stdout.write(f"\r任务 {task_id[:8]} [{bar}] {done}/{total} ({percent:.2f}%)")
    sys.stdout.flush()

# -------------------
# Flask & 文件夹
# -------------------
app = Flask(__name__)
UPLOAD_DIR = 'Uploads'
OUTPUT_DIR = 'output/structure'
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=10)  # 改成线程池


def process_pdf(file_path, task_id):
    # 取文件名（不带路径、不带后缀）
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    save_dir = os.path.join("results", base_name)

    os.makedirs(save_dir, exist_ok=True)

    for i in range(10):
        time.sleep(1)  # 模拟处理
        progress_dict[task_id] = f"{(i + 1) * 10}%"

    # 假设保存 OCR 结果
    with open(os.path.join(save_dir, "ocr.txt"), "w", encoding="utf-8") as f:
        f.write(f"OCR result for {file_path}\n")
# -------------------
# 工具函数
# -------------------
def pdf_to_images(pdf_path):
    return convert_from_path(pdf_path, dpi=300)

def modify_diagnoses(data):
    try:
        for key in ['入院诊断','出院诊断']:
            diag_text = data['data']['content'].get(key,'')
            if diag_text:
                count = 1
                new_list = []
                for item in diag_text.split(' '):
                    if item.strip():
                        if item[0].isdigit() and '.' in item:
                            diag_content = item.split('.',1)[1].strip()
                            for d in diag_content.split(' '):
                                if d.strip():
                                    new_list.append(f"{count}. {d.strip()}")
                                    count += 1
                        else:
                            new_list.append(f"{count}. {item.strip()}")
                            count += 1
                data['data']['content'][key] = ' '.join(new_list)
        return data
    except Exception as e:
        print(f"Error modifying diagnoses: {e}")
        return data

def export_to_excel(data, output_path, filename):
    rows = [{'字段': k, '值': v} for k,v in data['data']['content'].items()]
    df = pd.DataFrame(rows)
    excel_path = os.path.join(output_path, f"{filename}.xlsx")
    df.to_excel(excel_path,index=False,sheet_name='Medical Record',engine='openpyxl')
    print(f"\nExcel saved: {excel_path}")

# -------------------
# 核心 OCR 处理
# -------------------
def process_pdf_task(pdf_path, task_id, output_dir):
    start = time.time()

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
    args.output = output_dir
    ocr_engine = StructureSystem(args)

    # 取 PDF 文件名（无后缀）
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    # 结果保存到 output/structure/<文件名>/
    task_output_dir = os.path.join(output_dir, base_name)
    os.makedirs(task_output_dir, exist_ok=True)

    images = pdf_to_images(pdf_path)
    total_pages = len(images)
    init_progress(task_id, total_pages)
    all_res = []

    for idx, img in enumerate(images):
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        res, _ = ocr_engine(img_cv, img_idx=idx)
        h, w, _ = img_cv.shape
        sorted_res = sorted_layout_boxes(res, w)
        all_res += sorted_res
        update_progress(task_id)
        print_progress(progress_dict[task_id]['done'], total_pages, task_id)

    # 输出文件名
    img_name = base_name
    convert_info_docx(img_cv, all_res, task_output_dir, img_name)
    word_files = [f for f in os.listdir(task_output_dir) if f.endswith('.docx')]
    raw = process_word_document(os.path.join(task_output_dir, word_files[0])) or {}
    ordered = OrderedDict((k, raw.get(k, '')) for k in ORDERED_KEYS)
    response_data = {'data': {'content': ordered}}
    response_data = modify_diagnoses(response_data)

    with open(os.path.join(task_output_dir, f"{img_name}.json"), "w", encoding="utf-8") as f:
        json.dump(response_data, f, ensure_ascii=False, indent=2)
    export_to_excel(response_data, task_output_dir, img_name)

    elapsed = time.time() - start
    print(f"\n任务 {task_id[:8]} 完成, 耗时 {elapsed:.2f} 秒")
    print(response_data)

    progress_dict.pop(task_id, None)
    return response_data


# -------------------
# 异步上传接口
# -------------------
@app.route('/upload_async',methods=['POST'])
def upload_async():
    file = request.files.get('file')
    if not file or not file.filename.endswith('.pdf'):
        return jsonify({'error':'请上传 PDF 文件'}),400

    filename = secure_filename(file.filename)
    pdf_path = os.path.join(UPLOAD_DIR, filename)
    file.save(pdf_path)

    task_id = str(uuid.uuid4())
    executor.submit(process_pdf_task,pdf_path,task_id,OUTPUT_DIR)

    return jsonify({'msg':'任务已提交','filename':filename,'task_id':task_id})

# -------------------
# 进度查询
# -------------------
@app.route('/progress/<task_id>',methods=['GET'])
def progress(task_id):
    prog = get_progress(task_id)
    print(prog)
    if prog is None:
        return jsonify({'msg':'任务不存在或已完成'}),203
    return jsonify(prog)

# -------------------
# 批量异步上传接口
# -------------------
@app.route('/upload_batch_async', methods=['POST'])
def upload_batch_async():
    # 支持多文件上传
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': '请上传至少一个 PDF 文件'}), 400

    task_list = []

    for file in files:
        if not file.filename.endswith('.pdf'):
            continue  # 跳过非PDF

        filename = secure_filename(file.filename)
        pdf_path = os.path.join(UPLOAD_DIR, filename)
        file.save(pdf_path)

        task_id = str(uuid.uuid4())
        executor.submit(process_pdf_task, pdf_path, task_id, OUTPUT_DIR)

        task_list.append({'filename': filename, 'task_id': task_id})

    if not task_list:
        return jsonify({'error': '没有有效的 PDF 文件'}), 400

    return jsonify({'msg': '批量任务已提交', 'tasks': task_list})



# -------------------
# 启动
# -------------------
if __name__=='__main__':
    app.run(host='0.0.0.0',port=5000)

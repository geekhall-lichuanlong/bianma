#!/bin/bash
PDF=$1
OUT=$2
python3 predict_system.py \
  --image_dir "$PDF" \
  --det_model_dir inference/ch_PP-OCRv4_det_server_infer \
  --rec_model_dir inference/ch_PP-OCRv4_rec_server_infer \
  --rec_char_dict_path ../ppocr/utils/ppocr_keys_v1.txt \
  --layout_model_dir inference/picodet_lcnet_x1_0_fgd_layout_infer \
  --layout_dict_path ../ppocr/utils/dict/layout_dict/layout_publaynet_dict.txt \
  --vis_font_path ../doc/fonts/simfang.ttf \
  --recovery True \
  --output "$OUT" \
  --table false \
  --layout true
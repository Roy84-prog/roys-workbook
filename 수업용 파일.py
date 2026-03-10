import json
import re
import os


# ==========================================
# [Core Logic] HTML 생성 로직
# ==========================================

def generate_step2_html_logic(json_data):
    """
    JSON 데이터를 받아 HTML 코드를 생성하는 함수
    [v22.2 Update]
    1. 선택지 폰트 크기 축소:
       - .option-item font-size: 16px -> 15px
    2. 이전 기능 완벽 유지:
       - 단어 뜻(빨간색): context_meaning 사용
       - 태그 처리: [ ] 및 《 》 모두 제거
    """

    # --- 1. Helper Functions ---

    def get_clean_meaning_for_highlight(meaning_str):
        return meaning_str.strip()

    def format_table_meaning(meaning_str):
        if '②' in meaning_str:
            parts = meaning_str.split('②')
            return f"{parts[0]}<span class='context-mean'>②{parts[1]}</span>"
        return meaning_str

    def remove_tags_keep_content(text):
        """
        [ ] 태그와 《 》 태그를 모두 제거하고 내용만 남김
        """
        if not text: return ""
        text = re.sub(r'\[/?[^\]]+\]', '', text)
        text = re.sub(r'《/?[^》]+》', '', text)
        return text

    def clean_header(text):
        return re.sub(r'^Q\.?\s*\d*\.?\s*', '', text).strip()

    def convert_blank_tags(text, css_class="flow-fill-blank"):
        if not text: return ""
        pattern = re.compile(
            r'(?:\[|《)\s*(BLANK|fill|blank)\s*(?:\]|》)(.*?)(?:\[|《)\s*/\s*(BLANK|fill|blank)\s*(?:\]|》)', re.IGNORECASE)
        return pattern.sub(rf'<span class="{css_class}"></span>', text)

    def process_flow_content(text):
        if not text: return ""
        text = convert_blank_tags(text, "flow-fill-blank")
        text = remove_tags_keep_content(text)
        return text

    def create_flexible_pattern(word):
        if len(word) > 3 and word.endswith('e'):
            root = word[:-1]
        elif len(word) > 3 and word.endswith('y'):
            root = word[:-1]
        else:
            root = word
        chars = [re.escape(c) for c in root]
        interleaved = r'[\-\s]*'.join(chars)
        return r'\b' + interleaved + r'[a-z]*\b'

    def process_visual_text(text, context_vocab_map):
        text = convert_blank_tags(text, "visual-blank")
        text = remove_tags_keep_content(text)

        sorted_words = sorted(context_vocab_map.keys(), key=len, reverse=True)

        for word in sorted_words:
            mean = context_vocab_map[word]
            regex_pattern = create_flexible_pattern(word)
            pattern = re.compile(regex_pattern, re.IGNORECASE)
            text = pattern.sub(rf'<span class="vocab">\g<0><span class="mean">{mean}</span></span>', text)

        text = re.sub(r'([❶-❿])', r'<span class="num-char">\1</span>', text)
        return text

    # --- 2. Data Parsing & Processing ---

    # [Context Meaning Parsing]
    context_vocab_map = {}
    sentence_analysis = json_data.get('sentence_analysis', [])

    for sent in sentence_analysis:
        raw_context = sent.get('context_meaning', '')
        if raw_context:
            items = raw_context.split(',')
            for item in items:
                if ':' in item:
                    parts = item.split(':', 1)
                    word_key = parts[0].strip()
                    word_mean = parts[1].strip()
                    if word_key:
                        context_vocab_map[word_key] = word_mean

    # (1) Page 1 Data processing
    raw_text = json_data.get('visual_data', {}).get('question_text_visual', '')
    processed_text = process_visual_text(raw_text, context_vocab_map)
    visual_lines = processed_text.split('\n')

    page1_lines_html = ""
    for i, line in enumerate(visual_lines):
        content = line if line.strip() else "&nbsp;"
        is_last_line = (i == len(visual_lines) - 1)
        line_class = "line last" if is_last_line else "line"
        page1_lines_html += f'<div class="{line_class}">{content}</div>'

    options_html = ""
    for opt in json_data.get('visual_data', {}).get('options_visual', []):
        clean_opt = remove_tags_keep_content(opt)
        options_html += f'<div class="option-item">{clean_opt}</div>'

    # (2) Page 2: Flow Chart
    flow_data = json_data.get('three_stage_flow', [])
    flow_items_html = []

    if not flow_data:
        for _ in range(3): flow_items_html.append('<div class="flow-box">&nbsp;</div>')
    else:
        for item in flow_data:
            range_txt = item.get('range', '')
            title_txt = remove_tags_keep_content(item.get('title', ''))
            content_txt = process_flow_content(item.get('content', ''))

            flow_items_html.append(f"""
            <div class="flow-box">
                <div class="flow-header">
                    <div class="flow-title">{title_txt}</div>
                    <div class="flow-range">{range_txt}</div>
                </div>
                <div class="flow-content">{content_txt}</div>
            </div>""")

    flow_chart_html = '<div class="flow-arrow">→</div>'.join(flow_items_html)

    # (3) Page 2: Analysis Boxes
    analysis_boxes_html = ""
    key_sentences = json_data.get('key_sentences', [])

    topic_item = next((item for item in key_sentences if "주제" in item.get('type', '')), None)
    if topic_item:
        clean_en = remove_tags_keep_content(topic_item['sentence']).replace("/", '<span class="slash">/</span>')
        clean_kr = remove_tags_keep_content(topic_item['translation'])
        clean_reason = remove_tags_keep_content(topic_item.get('reason', ''))

        analysis_boxes_html += f"""
        <div class="analysis-box">
            <div class="box-header">❶ TOPIC SENTENCE & MEANING</div>
            <div class="en-sentence">{clean_en}</div>
            <div class="kr-trans">{clean_kr}</div>
            <div class="point-box"><span class="point-label">Point</span> {clean_reason}</div>
        </div>"""

    syntax_item = next((item for item in key_sentences if "핵심" in item.get('type', '') and item != topic_item), None)
    if syntax_item:
        clean_en = remove_tags_keep_content(syntax_item['sentence']).replace("/", '<span class="slash">/</span>')
        clean_kr = remove_tags_keep_content(syntax_item['translation'])

        raw_reason = syntax_item.get('reason', '')
        clean_reason = remove_tags_keep_content(raw_reason)
        grammar_points = clean_reason.split('\n')

        grammar_html = ""
        for i, point in enumerate(grammar_points):
            if not point.strip(): continue
            label = f"Grammar {i + 1}" if len(grammar_points) > 1 else "Grammar"
            grammar_html += f'<div class="point-row"><span class="point-label">{label}</span> {point}</div>'

        analysis_boxes_html += f"""
        <div class="analysis-box">
            <div class="box-header">❷ KEY SYNTAX (핵심 구문)</div>
            <div class="en-sentence">{clean_en}</div>
            <div class="kr-trans">{clean_kr}</div>
            <div class="point-box">{grammar_html}</div>
        </div>"""

    # (4) Page 2: Vocab Table
    vocab_list = json_data.get('vocab_list', [])

    def create_table_rows(v_list):
        rows = ""
        for v in v_list:
            chunk_content = v.get('chunck_example') or v.get('chunk_example') or ""
            chunk_trans = v.get('chunk_meaning') or v.get('chunk_translation') or ""

            if not chunk_content:
                chunk_content = f"example of <b>{v['word']}</b>"
            if "<b>" not in chunk_content:
                pattern = re.compile(r'\b' + re.escape(v['word']) + r'\b', re.IGNORECASE)
                chunk_content = pattern.sub(f"<b>{v['word']}</b>", chunk_content)

            formatted_meaning = format_table_meaning(v['meaning'])

            chunk_html = f"{chunk_content}"
            if chunk_trans:
                chunk_html += f"<div class='chunk-trans'>{chunk_trans}</div>"

            rows += f"""
            <tr>
                <td class="col-word">{v['word']}</td>
                <td class="col-mean">{formatted_meaning}</td>
                <td class="col-chunk">{chunk_html}</td>
            </tr>"""
        return rows

    mid_idx = (len(vocab_list) + 1) // 2
    left_rows = create_table_rows(vocab_list[:mid_idx])
    right_rows = create_table_rows(vocab_list[mid_idx:])

    vocab_section_html = f"""
    <div class="vocab-container-2col">
        <table class="vocab-table">
            <thead>
                <tr><th width="22%">Word</th><th width="33%">Meaning</th><th width="45%">Chunk</th></tr>
            </thead>
            <tbody>{left_rows}</tbody>
        </table>
        <table class="vocab-table">
            <thead>
                <tr><th width="22%">Word</th><th width="33%">Meaning</th><th width="45%">Chunk</th></tr>
            </thead>
            <tbody>{right_rows}</tbody>
        </table>
    </div>
    """

    meta = json_data.get('meta_info', {})
    topic = json_data.get('topic_data', {})
    q_header = clean_header(meta.get('question_header', ''))
    q_origin = remove_tags_keep_content(meta.get('source_origin', ''))
    q_subject = remove_tags_keep_content(topic.get('keywords', ''))

    # --- 3. HTML Assembly ---
    html_fragment = f"""
    <div class="page-container">
        <div class="left-col">
            <div class="header-info">{q_origin}</div>
            <div class="question-stem">{q_header}</div>
            <div class="line-wrapper">{page1_lines_html}</div>
            <div class="options-area">{options_html}</div>
        </div>
        <div class="right-col">
             <div class="tip-card">
                <div class="tip-header"><div class="tip-bar"></div><div class="tip-title">Focus Tip</div></div>
             </div>
        </div>
    </div>

    <div class="page-container analysis-page">
        <div class="subject-box"><div class="subject-title">📌 Subject : {q_subject}</div></div>

        <div class="flow-chart-wrapper">
             {flow_chart_html}
        </div>

        <div class="section-title">SENTENCE ANALYSIS (구문 분석)</div>
        {analysis_boxes_html}

        <div class="section-title">VOCABULARY & CHUNK (10 Words)</div>
        {vocab_section_html}
    </div>
    """
    return html_fragment


# ==========================================
# [Main Execution] Merge Files Logic
# ==========================================

def merge_files_to_single_html():
    # 1. CSS & Header Template
    html_header = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>Merged Study Material</title>
<style>
    /* Reset & Base */
    * { box-sizing: border-box; }
    body { margin: 0; padding: 40px; background-color: #525659; font-family: 'Apple SD Gothic Neo', sans-serif; color: #333; }

    @page { size: A4; margin: 0; }

    .page-container { 
        width: 210mm; min-height: 297mm; 
        background: white; 
        margin: 0 auto 50px auto; 
        padding: 10mm; 
        display: flex; 
        page-break-after: always;
    }
    .page-container:last-child { page-break-after: auto; }

    /* Layout */
    .left-col { width: 60%; padding-right: 25px; border-right: 1.5px dashed #aaa; }
    .right-col { width: 40%; padding-left: 25px; }
    .analysis-page { display: block !important; }

    .header-info { font-size: 12px; border: 1px solid #999; padding: 2px 6px; margin-bottom: 10px; color: #555; display: inline-block; }
    .question-stem { font-weight: bold; font-size: 16px; margin-bottom: 20px; line-height: 1.4; }

    /* Line System */
    .line-wrapper { display: flex; flex-direction: column; gap: 12px; font-family: 'Times New Roman', serif; font-size: 17px; margin-bottom: 30px; }
    .line { display: block; width: 100%; text-align: justify; text-align-last: justify; word-spacing: -0.5px; line-height: 1.2; }
    .line.last { text-align-last: left; }

    /* Vocab Highlight */
    .vocab { position: relative; display: inline-block; border-bottom: 1px dotted #999; font-weight: bold; cursor: pointer; }
    .mean { display: block; position: absolute; top: 110%; left: 50%; transform: translateX(-50%); font-size: 9px; color: #ff0000; font-weight: 800; white-space: nowrap; font-family: 'Apple SD Gothic Neo', sans-serif; letter-spacing: -0.5px; }
    .num-char { font-size: 0.85em; vertical-align: 1px; margin-right: 1px; }
    .visual-blank { display: inline-block; width: 100px; border-bottom: 1.5px solid #000; vertical-align: -2px; margin: 0 4px; }

    /* Components */
    .tip-card { border: 1px solid #ddd; border-radius: 8px; height: 300px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .tip-header { padding: 10px 15px; border-bottom: 1px solid #eee; display: flex; align-items: center; gap: 8px; }
    .tip-bar { width: 4px; height: 20px; background-color: #8e44ad; }
    .tip-title { font-weight: bold; color: #8e44ad; }

    .subject-box { border-left: 5px solid #27ae60; padding: 10px 15px; margin-bottom: 15px; background: #fff; border: 1px solid #eee; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .subject-title { font-weight: bold; color: #27ae60; font-size: 14px; }

    .section-title { font-size: 18px; font-weight: 800; color: #333; border-bottom: 2px solid #333; padding-bottom: 8px; margin-bottom: 20px; margin-top: 30px; }
    .section-title:first-of-type { margin-top: 0; }

    /* [Compressed Sentence Analysis] */
    .analysis-box { 
        background-color: #fff; border: 1px solid #ddd; 
        border-radius: 8px; 
        padding: 10px; 
        margin-bottom: 15px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.02); 
    }
    .box-header { font-weight: 800; color: #d35400; margin-bottom: 8px; font-size: 14px; display: flex; align-items: center; gap: 5px; }
    .en-sentence { 
        font-family: 'Times New Roman', serif; font-weight: bold; color: #333; 
        margin-bottom: 6px; 
        line-height: 1.4; 
        font-size: 15px; 
    }
    .kr-trans { 
        font-size: 12px; 
        color: #666; margin-bottom: 10px; line-height: 1.4; 
    }

    .point-box { background: #fdfdfd; border: 1px dotted #999; border-radius: 4px; padding: 8px; font-size: 12px; color: #555; }
    .point-row { margin-bottom: 4px; }
    .point-label { font-weight: bold; background: #eee; padding: 2px 6px; border-radius: 3px; margin-right: 6px; font-size: 11px; color: #333; }

    /* Flow Chart */
    .flow-chart-wrapper { display: flex; justify-content: space-between; align-items: stretch; margin-bottom: 15px; gap: 15px; }
    .flow-box { flex: 1; background-color: #fff; border: 1px solid #e0e0e0; border-top: 4px solid #2980b9; border-radius: 8px; padding: 12px; min-height: 110px; display:flex; flex-direction:column; gap:8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .flow-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; border-bottom: 1px dashed #eee; padding-bottom: 6px; }
    .flow-title { font-weight: 800; font-size: 13px; color: #2c3e50; line-height: 1.3; flex: 1; }
    .flow-range { font-size: 10px; color: #888; background: #f1f1f1; padding: 2px 5px; border-radius: 3px; white-space: nowrap; flex-shrink: 0; }
    .flow-content { font-size: 12px; color: #555; line-height: 1.6; word-break: keep-all; flex-grow: 1; }
    .flow-fill-blank { display: inline-block; width: 70px; border-bottom: 1.5px solid #333; vertical-align: bottom; margin: 0 3px; transform: translateY(-3px); }
    .flow-arrow { color: #ccc; font-size: 20px; font-weight: bold; align-self: center; }

    /* [Compressed Vocab Table] */
    .vocab-container-2col { display: flex; gap: 15px; margin-top: 10px; }
    .vocab-table { flex: 1; border-collapse: collapse; border-top: 2px solid #333; border-bottom: 1px solid #333; }
    .vocab-table th { 
        background: #f8f9fa; padding: 4px; 
        border-bottom: 1px solid #ccc; font-weight: bold; font-size: 11px; color: #333; 
    }
    .vocab-table td { 
        padding: 4px 6px; 
        border-bottom: 1px solid #eee; vertical-align: middle; 
    }

    .col-word { 
        font-family: 'Georgia', 'Times New Roman', serif; font-weight: bold; color: #2c3e50; 
        font-size: 12.5px; 
    }
    .col-mean { 
        font-size: 10.5px; 
        color: #555; letter-spacing: -0.3px; line-height: 1.2; 
    }
    .context-mean { color: #2980b9; font-weight: 800; }
    .col-chunk { font-style: italic; color: #777; font-size: 10.5px; }
    .col-chunk b { color: #d35400; font-weight: bold; }
    .chunk-trans { font-size: 9px; color: #aaa; margin-top: 2px; font-weight: normal; font-style: normal; }

    /* [Options Area Font] */
    .options-area { 
        margin-top: 20px; 
        border-top: 1px dashed #ccc; 
        padding-top: 20px; 
        /* 나눔명조, 바탕, 세리프 순 */
        font-family: 'Nanum Myeongjo', 'Batang', 'Times New Roman', serif; 
    }
    .option-item { margin-bottom: 12px; line-height: 1.7; font-size: 15px; } /* 16px -> 15px */

    @media print { body { padding: 0; background: none; } .page-container { margin: 0; border: none; box-shadow: none; } }
</style>
</head>
<body>
"""

    html_footer = """
</body>
</html>
"""

    # 2. Main Logic
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    target_folder = os.path.join(desktop_path, "4")
    output_filename = "merged_study_material_v22.html"
    output_path = os.path.join(target_folder, output_filename)

    if not os.path.exists(target_folder):
        print(f"⚠️ 폴더 없음: {target_folder}")
        return

    files = sorted([f for f in os.listdir(target_folder) if f.endswith('.txt')])

    if not files:
        print(f"⚠️ 처리할 파일 없음")
        return

    print(f"📂 총 {len(files)}개의 파일을 병합합니다...")

    all_body_content = ""

    for file_name in files:
        file_path = os.path.join(target_folder, file_name)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_str = f.read()
                data = json.loads(json_str)
                fragment = generate_step2_html_logic(data)
                all_body_content += fragment
                print(f"  - 처리 완료: {file_name}")
        except Exception as e:
            print(f"  ❌ 오류 발생 ({file_name}): {e}")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_header + all_body_content + html_footer)

    print("=" * 60)
    print(f"🎉 병합 완료! 파일 생성됨: {output_path}")


if __name__ == "__main__":
    merge_files_to_single_html()
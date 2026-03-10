import json
import re
import os

# ==========================================
# [설정 영역]
# ==========================================
OUTPUT_FILENAME = "Roy_English_Material_Final_v59.html"

# ==========================================
# [HTML/CSS 템플릿]
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>영어 지문 분석 학습지</title>
<style>
:root {{
    --bg-color: #f9f9f9;
    --font-eng: 'Times New Roman', serif;
    --font-kor: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;

    /* 문장 성분 색상 */
    --c-S: #1565c0; /* 주어: 파랑 */
    --c-V: #c62828; /* 동사: 빨강 */
    --c-O: #d35400; /* 목적어: 오렌지 브라운 */
    --c-C: #2e7d32; /* 보어: 초록 */
    --c-M: #757575; /* 수식어: 회색 */
    --c-con: #8e24aa; /* 접속사: 보라 */
}}

body {{ font-family: var(--font-kor); font-size: 15px; color: #333; margin: 20px; line-height: 1.6; background: var(--bg-color); }}
.container {{ display: flex; gap: 30px; background: #fff; padding: 40px; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); min-width: 1000px; max-width: 1600px; margin: 0 auto; }}

/* [LEFT COLUMN] */
.english-col {{ flex: 40; display: flex; flex-direction: column; border-right: 1px dashed #ddd; padding-right: 25px; }}
.topic-box {{ background-color: #e8f5e9; border-left: 5px solid #4caf50; padding: 12px 15px; margin-bottom: 25px; font-size: 13.5px; color: #1b5e20; border-radius: 4px; }}
.question-header {{ font-weight: 800; font-size: 17px; color: #222; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid #222; }}
.source-tag {{ font-size: 11px; color: #fff; background-color: #555; padding: 2px 7px; border-radius: 12px; margin-left: 8px; vertical-align: middle; font-weight: normal; }}

/* [지문 텍스트] */
.source-text {{ 
    font-family: var(--font-eng); 
    font-size: 20px; 
    line-height: 2.5; 
    white-space: pre-wrap; 
    text-align: justify; 
    margin-bottom: 30px; 
    color: #111; 
}}

/* [Highlights - Full Area & Clone] */
span[class^="highlight-"] {{
    border-radius: 4px; 
    padding: 2px 4px; 
    margin: 0 1px;
    -webkit-box-decoration-break: clone;
    box-decoration-break: clone;
    position: relative;
}}
span[class^="highlight-"]::before {{
    font-size: 9px; position: absolute; top: -11px; left: 0;
    font-weight: normal; font-family: sans-serif; line-height: 1; white-space: nowrap;
}}
.highlight-subject {{ background-color: #fff9c4; border-bottom: 2px solid #fbc02d; }}
.highlight-subject::before {{ content: 'Key'; color: #f9a825; font-weight:bold; }}
.highlight-feature {{ background-color: #fff9c4; border-bottom: 2px solid #fbc02d; }}
.highlight-feature::before {{ content: 'Feature'; color: #f9a825; font-weight:bold; }}
.highlight-clue {{ background-color: #e3f2fd; border-bottom: 2px solid #64b5f6; }}
.highlight-clue::before {{ content: 'Clue'; color: #1976d2; font-weight:bold; }}

/* [Badges] */
.badge-them {{ display: inline-block; font-size: 11px; background-color: #7e57c2; color: #fff; padding: 2px 6px; border-radius: 4px; margin-right: 6px; font-weight: bold; vertical-align: 2px; font-family: var(--font-kor); }}
.badge-key {{ display: inline-block; font-size: 11px; background-color: #0277bd; color: #fff; padding: 2px 6px; border-radius: 4px; margin-right: 6px; font-weight: bold; vertical-align: 2px; font-family: var(--font-kor); }}

/* [Header Badges] */
.header-badge-them {{ font-size: 12px; background-color: #ffebee; color: #c62828; border: 1px solid #ef9a9a; padding: 2px 8px; border-radius: 12px; margin-left: 8px; vertical-align: middle; font-weight: bold; }}
.header-badge-key {{ font-size: 12px; background-color: #fffde7; color: #f57f17; border: 1px solid #fff59d; padding: 2px 8px; border-radius: 12px; margin-left: 5px; vertical-align: middle; font-weight: bold; }}

/* [Interlinear Vocab] */
.vocab-container {{ display: inline-block; position: relative; text-indent: 0; vertical-align: baseline; line-height: 1.0; }}
.vocab-text {{ font-weight: normal; color: inherit; border-bottom: 1px dotted #bbb; position: relative; z-index: 1; }}
.vocab-sub {{ position: absolute; bottom: 100%; left: 50%; transform: translateX(-50%); width: max-content; margin-bottom: -3px; font-size: 11px; color: #d32f2f; background-color: transparent; text-shadow: 1px 1px 0 #eeeeee, -1px -1px 0 #eeeeee, 1px -1px 0 #eeeeee, -1px 1px 0 #eeeeee; padding: 0 1px; font-weight: normal; font-family: var(--font-kor); z-index: 10; line-height: 1.1; pointer-events: none; }}

/* [Syntax Parsing] */
.syntax-box {{ display: inline; border-bottom: 2px solid; position: relative; padding-bottom: 1px; margin-right: 2px; -webkit-box-decoration-break: clone; box-decoration-break: clone; }}
.syntax-box::before {{ position: absolute; top: 24px; left: 0; font-size: 10px; font-weight: 900; font-family: sans-serif; line-height: 1; }}

/* 성분별 색상 + 볼드체(S,V,O,C) 적용 */
.S-box {{ border-bottom-color: var(--c-S); font-weight: 900; }} .S-box::before {{ content: 'S'; color: var(--c-S); }}
.V-box {{ border-bottom-color: var(--c-V); font-weight: 900; }} .V-box::before {{ content: 'V'; color: var(--c-V); }}
.O-box {{ border-bottom-color: var(--c-O); font-weight: 900; }} .O-box::before {{ content: 'O'; color: var(--c-O); }}
.C-box {{ border-bottom-color: var(--c-C); font-weight: 900; }} .C-box::before {{ content: 'C'; color: var(--c-C); }}
.M-box {{ border-bottom-color: var(--c-M); font-weight: normal; }} .M-box::before {{ content: 'M'; color: var(--c-M); }}
.con-box {{ border-bottom-color: var(--c-con); font-weight: normal; }} .con-box::before {{ content: 'Conn'; color: var(--c-con); }}

/* [Grammar Text Styling] */
.S-text {{ color: var(--c-S); font-weight: 900; }}
.V-text {{ color: var(--c-V); font-weight: 900; }}
.O-text {{ color: var(--c-O); font-weight: 900; }}
.C-text {{ color: var(--c-C); font-weight: 900; }}
.M-text {{ color: var(--c-M); font-weight: normal; }}
.con-text {{ color: var(--c-con); font-weight: normal; }}

/* [Vocab Table] */
table.vocab-table {{ width: 100%; border-collapse: collapse; margin-bottom: 25px; font-size: 13px; table-layout: fixed; border: 1px solid #ddd; }}
table.vocab-table th {{ background: #f1f3f5; padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold; color: #444; font-size: 13px; }}
table.vocab-table td {{ padding: 8px; border: 1px solid #ddd; vertical-align: middle; word-wrap: break-word; background: #fff; text-align: center; }}
table.vocab-table td:nth-child(3) {{ text-align: left; }} 
table.vocab-table col:nth-child(1) {{ width: 20%; }} 
table.vocab-table col:nth-child(2) {{ width: 15%; }} 
table.vocab-table col:nth-child(3) {{ width: 30%; }} 
table.vocab-table col:nth-child(4) {{ width: 17%; }} 
table.vocab-table col:nth-child(5) {{ width: 18%; }} 
.vocab-word-bold {{ font-weight: bold; font-family: var(--font-eng); color: #000; font-size: 14px; }}
.vocab-pron {{ color: #555; font-size: 12px; }}

/* [Options - Compact] */
.options-box {{ margin-top: 20px; padding: 10px; border-top: 2px solid #333; background: #fff; }}
.option-item {{ margin-bottom: 8px; border: 1px solid #eee; border-radius: 6px; padding: 10px; background-color: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }}
.opt-header {{ margin-bottom: 3px; line-height: 1.3; }}
.opt-text {{ font-family: var(--font-eng); font-weight: bold; font-size: 16px; color: #000; }}
.opt-trans {{ font-size: 12.5px; color: #777; margin-bottom: 6px; display: block; line-height: 1.3; }}
.opt-analysis {{ background-color: #f9f9f9; padding: 6px 10px; border-radius: 4px; font-size: 13px; color: #444; border-left: 3px solid #ddd; line-height: 1.4; }}
.err-badge-wrong {{ font-size: 11px; background-color: #fff3e0; color: #ef6c00; padding: 1px 5px; border-radius: 3px; border: 1px solid #ffe0b2; margin-right: 5px; font-weight: bold; }}
.err-badge-correct {{ font-size: 11px; background-color: #e8f5e9; color: #2e7d32; padding: 1px 5px; border-radius: 3px; border: 1px solid #a5d6a7; margin-right: 5px; font-weight: bold; }}

/* [RIGHT COLUMN] */
.korean-col {{ flex: 60; display: flex; flex-direction: column; padding-left: 10px; }}

/* [Right Header - Card Style] */
.right-info-box {{ display: flex; flex-direction: column; gap: 10px; margin-bottom: 25px; }}
.right-info-item {{ background-color: #fff; border: 1px solid #eee; border-left-width: 4px; border-radius: 6px; padding: 12px 15px; font-size: 13.5px; line-height: 1.5; color: #444; box-shadow: 0 2px 4px rgba(0,0,0,0.03); }}
.ri-material {{ border-left-color: #4caf50; }}
.ri-guide {{ border-left-color: #ff9800; }}
.ri-tip {{ border-left-color: #9c27b0; }}
.ri-label {{ font-weight: 800; margin-bottom: 4px; color: #222; font-size: 14px; display: block; }}
.ri-content {{ display: block; }}

/* [Analysis Card] */
.analysis-card {{ margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px dashed #ddd; background-color: #fff; padding: 10px; border-radius: 4px; }}
.analysis-card.card-them {{ background-color: #fff; border: 2px solid #e53935; border-left: 6px solid #e53935; border-bottom: 2px solid #e53935; box-shadow: 0 2px 8px rgba(229, 57, 53, 0.1); }}
.analysis-card.card-key {{ background-color: #fff; border: 2px solid #fbc02d; border-left: 6px solid #fbc02d; border-bottom: 2px solid #fbc02d; box-shadow: 0 2px 8px rgba(251, 192, 45, 0.1); }}

/* [English Sentence Box - Reduced Padding] */
.eng-sent {{ 
    font-family: var(--font-eng); 
    font-size: 18px; 
    background-color: #f4f4f4; 

    /* [수정됨] 내부 여백 축소 */
    padding: 15px 15px; 

    border-left: 4px solid var(--c-S); 
    border-radius: 6px;
    position: relative;

    /* [수정됨] 외부 여백 축소 */
    margin-top: 15px; 
    margin-bottom: 12px; 

    line-height: 2.6; 
    color: #222; 
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}}

.kor-sent {{ font-size: 14px; color: #444; padding-left: 5px; margin-bottom: 8px; line-height: 1.6; word-break: keep-all; }}

/* [Summary Badge] */
.summary-badge {{ position: absolute; top: -13px; left: 0; display: inline-block; font-family: var(--font-kor); font-size: 13px; color: #e65100; background-color: #fff3e0; border: 1px solid #ffe0b2; padding: 0px 6px; border-radius: 8px; font-weight: 800; line-height: 1.6; z-index: 5; }}

.syntax-tip {{ display: block; width: fit-content; max-width: 100%; margin-top: 6px; padding: 5px 10px; border: 1px solid #333; background-color: #fff; border-radius: 4px; font-size: 12.5px; color: #000; line-height: 1.4; box-shadow: 2px 2px 0px rgba(0,0,0,0.1); }}
.syntax-label {{ display: inline-block; background-color: #333; color: #fff; padding: 1px 6px; border-radius: 3px; margin-right: 6px; font-size: 11px; font-weight: bold; vertical-align: 1px; }}

.answer-box {{ background-color: #e1f5fe; border: 1px solid #81d4fa; border-radius: 8px; padding: 20px; margin-bottom: 25px; }}
.ans-header {{ font-weight: bold; color: #0277bd; font-size: 16px; margin-bottom: 12px; border-bottom: 1px solid #b3e5fc; padding-bottom: 8px; }}
.ans-content {{ font-size: 13.5px; color: #37474f; line-height: 1.6; }}
.logic-box {{ background-color: #f5f5f5; border: 1px solid #e0e0e0; padding: 15px; border-radius: 8px; font-family: 'D2Coding', monospace; font-size: 12.5px; margin-bottom: 25px; line-height: 1.7; color: #333; }}

/* [Left Scenario Box] */
.scenario-box {{ background-color: #fff3e0; border: 1px solid #ffe0b2; border-radius: 8px; padding: 15px; margin-top: 20px; }}
.scene-header {{ font-size: 15px; font-weight: 900; color: #e65100; margin-bottom: 12px; border-bottom: 2px solid #ffe0b2; padding-bottom: 6px; }}
.scene-content {{ font-size: 13px; color: #444; line-height: 1.5; background:#fff; padding:10px; border-radius:4px; border-left:4px solid #ff9800; }}

.blank-box {{ display: inline-block; width: 60px; height: 20px; border: 1px solid #000; vertical-align: middle; margin: 0 3px; background: #fff; }}
.star-red {{ color: #e53935; text-shadow: 1px 1px 0px #b71c1c; font-size: 1.1em; margin-right: 5px; vertical-align: -1px; }}
.star-yellow {{ color: #fbc02d; text-shadow: 1px 1px 0px #f57f17; font-size: 1.1em; margin-right: 5px; vertical-align: -1px; }}
</style>
</head>
<body>
<div class="container">
    <div class="english-col">
        <div class="topic-box">
            <strong style="font-size:14px;">📌 Topic & Summary</strong><br>
            <div style="margin-top:6px;">{topic_keywords}<br>{topic_summary}</div>
        </div>

        <div class="answer-box">
            <div class="ans-header">✅ 정답: {correct_choice}</div>
            <div class="ans-content">
                <strong>[해설 요약]</strong><br>{explanation_summary}<br><br>
                <strong>[논리적 근거]</strong><br>
                <ul style="margin:5px 0 0 20px; padding:0; list-style-type:circle;">{clue_targets_html}</ul><br>
                <strong>[논리 연결]</strong><br>{clue_logic}
            </div>
        </div>

        <div class="options-box">
            <strong style="font-size:14px; display:block; margin-bottom:15px; border-bottom:1px solid #ddd; padding-bottom:5px;">🧐 선택지 분석 (Why & Why not?)</strong>
            {options_html}
        </div>

        <div class="logic-box"><strong style="font-size:14px; color:#000;">📊 Logic Flow</strong><br><br>{logic_map_text}</div>

        <div class="scenario-box">
            <div class="scene-header">🎯 지문 마킹 시뮬레이션</div>
            <div class="scene-content">{scenario_sim}</div>
        </div>
    </div>

    <div class="korean-col">
        <div class="right-info-box">
            <div class="right-info-item ri-material">
                <span class="ri-label">📌 소재</span>
                <span class="ri-content">{clue_material} {header_badges}</span>
            </div>
            <div class="right-info-item ri-guide">
                <span class="ri-label">🗣️ 수업 가이드</span>
                <span class="ri-content">{scenario_guide}</span>
            </div>
            <div class="right-info-item ri-tip">
                <span class="ri-label">💡 집중 Tip</span>
                <span class="ri-content">{scenario_tip}</span>
            </div>
        </div>

        {sentence_analysis_html}

        <div class="question-header" style="margin-top: 30px;">{question_header} <span class="source-tag">{source_origin}</span></div>
        <div class="source-text">{visual_passage}</div>

        <span class="table-label">📚 Vocabulary</span>
        <table class="vocab-table">
            <colgroup><col><col><col><col><col></colgroup>
            <thead><tr><th>Word</th><th>Pronunciation</th><th>Meaning</th><th>Synonym</th><th>Confusing</th></tr></thead>
            <tbody>{vocab_table_rows}</tbody>
        </table>

        <span class="table-label">📌 Key Sentences Analysis</span>
        <table class="analysis-table">
            <colgroup><col width="12%"> <col width="10%"> <col width="35%"> <col width="25%"> <col width="18%"></colgroup>
            <thead><tr><th>출처</th><th>종류</th><th>영어 문장</th><th>한글 해석</th><th>선정 사유</th></tr></thead>
            <tbody>{key_sentence_rows}</tbody>
        </table>
    </div>
</div>
</body>
</html>
"""


# ==========================================
# [함수 정의]
# ==========================================

def clean_json_input(text):
    text = re.sub(r'^```json', '', text.strip(), flags=re.MULTILINE)
    text = re.sub(r'^```', '', text.strip(), flags=re.MULTILINE)
    return text.strip().rstrip('`')


def apply_vocab_style(text, vocab_list_dicts):
    if not vocab_list_dicts: return text
    sorted_vocab = sorted(vocab_list_dicts, key=lambda x: len(x.get('word', '').split('[')[0].strip()), reverse=True)
    for v in sorted_vocab:
        raw_word = v.get('word', '').split('[')[0].strip()
        meaning = v.get('meaning', '').replace('①', '').replace('②', ',').strip()
        if not raw_word: continue
        try:
            pattern = re.compile(rf'\b({re.escape(raw_word)})\b', re.IGNORECASE)
            replacement = rf'<span class="vocab-container"><span class="vocab-sub">{meaning}</span><span class="vocab-text">\g<1></span></span>'
            text = pattern.sub(replacement, text)
        except:
            pass
    return text


def parse_local_vocab(word_str):
    if not word_str: return []
    result = []
    items = word_str.split(',')
    for item in items:
        if ':' in item:
            parts = item.split(':', 1)
            w = parts[0].strip()
            m = parts[1].strip()
            result.append({'word': w, 'meaning': m})
    return result


def convert_common_tags(text):
    text = re.sub(r'\[Them sentence\](.*?)\[/Them sentence\]', r'<span class="star-red">★</span>\1', text,
                  flags=re.DOTALL)
    text = re.sub(r'\[Key sentence\](.*?)\[/Key sentence\]', r'<span class="star-yellow">★</span>\1', text,
                  flags=re.DOTALL)
    text = re.sub(r'\[Key sentence \](.*?)\[/Key sentence \]', r'<span class="star-yellow">★</span>\1', text,
                  flags=re.DOTALL)

    text = re.sub(r'\[subject\](.*?)\[/subject\]', r'<span class="highlight-subject">\1</span>', text, flags=re.DOTALL)
    text = re.sub(r'\[keyword\](.*?)\[/keyword\]', r'<span class="highlight-subject">\1</span>', text, flags=re.DOTALL)
    text = re.sub(r'\[feature\](.*?)\[/feature\]', r'<span class="highlight-feature">\1</span>', text, flags=re.DOTALL)
    text = re.sub(r'\[clue\](.*?)\[/clue\]', r'<span class="highlight-clue">\1</span>', text, flags=re.DOTALL)
    text = re.sub(r'\[clue1\](.*?)\[/clue1\]', r'<span class="highlight-clue">\1</span>', text, flags=re.DOTALL)
    text = re.sub(r'\[clue2\](.*?)\[/clue2\]', r'<span class="highlight-clue">\1</span>', text, flags=re.DOTALL)

    text = text.replace('[BLANK]', '<span class="blank-box"></span>')
    text = text.replace(' / ', ' <span class="slash">/</span> ')
    return text


def convert_eng_tags(text):
    text = convert_common_tags(text)
    tags = {'S': 'S', 'V': 'V', 'O': 'O', 'C': 'C', 'OC': 'C', 'M': 'M', 'con': 'con'}
    for _ in range(3):
        for tag, cls_prefix in tags.items():
            pattern = re.compile(rf'\[{tag}\](.*?)\[/{tag}\]', re.IGNORECASE | re.DOTALL)
            text = pattern.sub(rf'<span class="syntax-box {cls_prefix}-box">\1</span>', text)
    return text


def convert_kor_tags(text):
    text = convert_common_tags(text)
    tags = {'S': 'S', 'V': 'V', 'O': 'O', 'C': 'C', 'OC': 'C', 'M': 'M', 'con': 'con'}
    for _ in range(3):
        for tag, cls_prefix in tags.items():
            pattern = re.compile(rf'\[{tag}\](.*?)\[/{tag}\]', re.IGNORECASE | re.DOTALL)
            text = pattern.sub(rf'<span class="{cls_prefix}-text">\1</span>', text)
    return text


def generate_html_from_json(json_str):
    try:
        data = json.loads(clean_json_input(json_str), strict=False)

        meta = data.get('meta_info', {})
        visual = data.get('visual_data', {})
        topic = data.get('topic_data', {})
        vocab = data.get('vocab_list', [])
        keys = data.get('key_sentences', [])
        sentences = data.get('sentence_analysis', [])
        ans = data.get('answer_data', {})
        wrong = data.get('wrong_answer_analysis', [])
        if not wrong: wrong = data.get('options_analysis', [])
        scene = data.get('class_scenario', {})

        raw_logic = data.get('logic_map', [])
        if isinstance(raw_logic, list):
            logic_map_text = "<br>".join(raw_logic)
        else:
            logic_map_text = str(raw_logic).replace('\n', '<br>').replace('\\n', '<br>')

        them_list = []
        key_list = []
        for s in sentences:
            eng_txt = s.get('eng_analyzed', '')
            num = s.get('num', '')
            if '[Them sentence]' in eng_txt:
                them_list.append(f"S{num}")
            if '[Key sentence]' in eng_txt or '[Key sentence ]' in eng_txt:
                key_list.append(f"S{num}")

        header_badges = ""
        if them_list:
            header_badges += f"<span class='header-badge-them'>★주제문: {', '.join(them_list)}</span>"
        if key_list:
            header_badges += f"<span class='header-badge-key'>★재진술: {', '.join(key_list)}</span>"

        all_sentence_words = []
        for s in sentences:
            all_sentence_words.extend(parse_local_vocab(s.get('word', '')))

        raw_passage = visual.get('question_text_visual', '')
        passage_with_vocab = apply_vocab_style(raw_passage, all_sentence_words)
        processed_passage = convert_eng_tags(passage_with_vocab)

        options_html = ""
        vis_opts = visual.get('options_visual', [])

        for i, opt_text in enumerate(vis_opts):
            analysis_item = None
            for w in wrong:
                if w.get('choice', '')[:1] in opt_text:
                    analysis_item = w
                    break

            if analysis_item:
                err_type = analysis_item.get('error_type', '')
                reason = analysis_item.get('reason', '')
                trans = analysis_item.get('trans', '')
                is_correct = "정답" in err_type

                badge_class = "err-badge-correct" if is_correct else "err-badge-wrong"
                badge_html = f"<span class='{badge_class}'>{err_type}</span>"

                analysis_html = f"<div class='opt-analysis'>{badge_html} {reason}</div>"
                trans_html = f"<span class='opt-trans'>{trans}</span>"
            else:
                analysis_html = ""
                trans_html = ""

            options_html += f"""
            <div class='option-item'>
                <div class='opt-header'><span class='opt-text'>{opt_text}</span></div>
                {trans_html}
                {analysis_html}
            </div>"""

        vocab_rows = ""
        for v in vocab:
            word = v.get('word', '')
            pron = v.get('pronunciation', '')
            meaning = v.get('meaning', '').replace('①', '').replace('②', ', ').strip()
            if meaning.startswith(','): meaning = meaning[1:].strip()

            vocab_rows += f"""
            <tr>
                <td class='vocab-word-bold'>{word}</td>
                <td class='vocab-pron'>{pron}</td>
                <td style='text-align:left;'>{meaning}</td>
                <td>{v.get('synonym', '-')}</td>
                <td>{v.get('confusing', '-')}</td>
            </tr>"""

        key_rows = ""
        for k in keys:
            full_sentence = k.get('sentence', '')
            source_match = re.search(r'\[(.*?)\]$', full_sentence)
            source_text = f"[{source_match.group(1)}]" if source_match else "-"
            clean_sentence = full_sentence.replace(source_text, "").strip() if source_match else full_sentence

            key_rows += f"""
            <tr>
                <td style='text-align:center; color:#555;'>{source_text}</td>
                <td style='text-align:center; font-weight:bold; color:#0d47a1;'>{k.get('type', '')}</td>
                <td style='font-family:Times New Roman; font-size:14px; text-align:left;'>{clean_sentence}</td>
                <td style='font-size:13px; text-align:left;'>{k.get('translation', '')}</td>
                <td style='font-size:12px; color:#555; text-align:left;'>{k.get('reason', '')}</td>
            </tr>"""

        sentence_analysis_html = ""
        for s in sentences:
            local_vocab_list = parse_local_vocab(s.get('word', ''))

            raw_eng = s.get('eng_analyzed', '')
            eng_with_vocab = apply_vocab_style(raw_eng, local_vocab_list)
            eng = convert_eng_tags(eng_with_vocab)
            kor = convert_kor_tags(s.get('kor_translation', ''))
            tip = s.get('syntax_tip', '')

            summary = s.get('summary_mark', '')
            summary_html = f"<span class='summary-badge'>{summary}</span>" if summary else ""

            num_icon = ""
            for n in ["❶", "❷", "❸", "❹", "❺", "❻", "❼", "❽"]:
                if n in eng: num_icon = n + " "; break
            eng_clean = re.sub(r'[❶❷❸❹❺❻❼❽]', '', eng)

            card_class = "analysis-card"
            if '[Them sentence]' in s.get('eng_analyzed', ''):
                card_class += " card-them"
            elif '[Key sentence]' in s.get('eng_analyzed', '') or '[Key sentence ]' in s.get('eng_analyzed', ''):
                card_class += " card-key"

            sentence_analysis_html += f"""
            <div class="{card_class}">
                <div class="eng-sent">
                    {summary_html} 
                    <span style="font-weight:bold; margin-right:5px; color:#000;">{num_icon}</span>{eng_clean}
                </div>
                <div class="kor-sent">{kor}</div>
                <div class="syntax-tip"><span class="syntax-label">구문팁</span>{tip}</div>
            </div>"""

        targets_html = "<br>".join(
            [f"<li>{convert_common_tags(t)}</li>" for t in ans.get('clues', {}).get('target_sentences', [])])

        final_html = HTML_TEMPLATE.format(
            topic_keywords=topic.get('keywords', ''),
            topic_summary=topic.get('summary', ''),
            question_header=meta.get('question_header', ''),
            source_origin=meta.get('source_origin', ''),
            visual_passage=processed_passage,
            options_html=options_html,
            vocab_table_rows=vocab_rows,
            key_sentence_rows=key_rows,
            sentence_analysis_html=sentence_analysis_html,
            correct_choice=ans.get('correct_choice', ''),
            explanation_summary=ans.get('explanation_summary', ''),
            clue_targets_html=targets_html,
            clue_material=convert_common_tags(ans.get('clues', {}).get('material', '')),
            clue_logic=convert_common_tags(ans.get('clues', {}).get('logic_flow', '')),
            logic_map_text=logic_map_text,
            scenario_sim=convert_common_tags(scene.get('simulation_text', '')),
            scenario_guide=scene.get('guide_ment', ''),
            scenario_tip=scene.get('tip_ment', ''),
            header_badges=header_badges
        )

        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        final_save_path = os.path.join(desktop_path, OUTPUT_FILENAME)

        with open(final_save_path, 'w', encoding='utf-8') as f:
            f.write(final_html)

        print("\n" + "=" * 40)
        print(f"✅ [성공] Final_v59 (Gray Box Padding Reduced) 완료!")
        print(f"📂 저장 위치: {final_save_path}")
        print("=" * 40 + "\n")

    except Exception as e:
        print(f"❌ 오류: {e}")


# ==========================================
# [실행 영역]
# ==========================================
if __name__ == "__main__":
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    input_filename = "input.txt"
    input_file_path = os.path.join(desktop_path, input_filename)

    print(f"🔍 '{input_filename}' 파일을 찾는 중... ({input_file_path})")

    if os.path.exists(input_file_path):
        try:
            with open(input_file_path, 'r', encoding='utf-8') as f:
                json_data = f.read()
            print(f"📂 파일을 읽어 변환합니다...")
            generate_html_from_json(json_data)
        except Exception as e:
            print(f"❌ 오류 발생:\n{e}")
    else:
        print("=" * 60)
        print(f"⚠️ 바탕화면에 '{input_filename}' 파일이 없습니다.")
        print("=" * 60)
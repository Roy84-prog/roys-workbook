import json
import re
import os
import random
from playwright.sync_api import sync_playwright

# ========================================================
# [설정 영역: 시험지 기본 정보 및 문항 수 조절]
# ========================================================
CONFIG_TARGET_FOLDER = "00"  # 바탕화면에 있는 텍스트 파일 폴더명
CONFIG_ACADEMY_NAME = "With ROY"
CONFIG_CLASS_NAME = "고1 심화반"  # 반명 조절 매개변수

# 문항 수 설정 (보유한 단어 수보다 크게 설정하면, 가능한 최대치까지만 출제됩니다)
COUNT_STEP1 = 20  # STEP 1: 단어 뜻 적기 문항 수
COUNT_STEP2 = 10  # STEP 2: 유의어 연결 문항 수
COUNT_STEP3 = 10  # STEP 3: 문맥 속 빈칸 채우기 문항 수

# ========================================================
# [HTML/CSS 템플릿: 세로형(Portrait) Review Test 전용]
# ========================================================
TEST_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>Cumulative Review Test</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');
    @import url('https://cdn.jsdelivr.net/gh/moonspam/NanumSquare@1.0/nanumsquareround.css');
    @import url('https://cdn.jsdelivr.net/npm/font-kopub@1.0/kopubbatang.min.css');

    @media print {
        body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
        .page-break { page-break-after: always; }
        .page-container { margin: 0 !important; border: none !important; box-shadow: none !important; width: 210mm !important; height: 297mm !important; }
        @page { size: A4 portrait; margin: 0; }
    }

    :root {
        --c-brand: #003b6f; --c-accent: #00897b; --c-text: #263238; 
    }

    body { margin: 0; padding: 0; background-color: #e0e0e0; font-family: 'Noto Sans KR', sans-serif; color: var(--c-text); }

    /* 세로형 A4 사이즈 (210mm x 297mm) */
    .page-container {
        width: 210mm; height: 297mm; background-color: white;
        margin: 0 auto; padding: 0; box-sizing: border-box; 
        box-shadow: 0 10px 30px rgba(0,0,0,0.1); position: relative;
        display: flex; flex-direction: column; overflow: hidden;
    }

    /* Header & Footer */
    .page-header { height: 10mm; min-height: 10mm; border-top: 5px solid var(--c-brand); border-bottom: 2px solid #b0bec5; display: flex; justify-content: space-between; align-items: center; padding: 0 10mm; box-sizing: border-box; }
    .ph-left { display: flex; align-items: center; font-family: 'Montserrat', 'Noto Sans KR', sans-serif; }
    .ph-title-main { font-weight: 800; color: var(--c-text); font-size: 14px; letter-spacing: -0.5px; }
    .ph-right { font-family: 'Noto Sans KR', sans-serif; font-size: 13px; font-weight: 700; color: #455a64; letter-spacing: 0.5px; }

    .page-footer { margin-top: auto; height: 8mm; min-height: 8mm; display: flex; justify-content: center; align-items: flex-start; padding-top: 1mm; font-family: 'Montserrat', sans-serif; font-size: 11px; color: #78909c; font-weight: 800; }

    /* Review Test Body */
    .p2-voca-body { flex: 1; padding: 5mm 10mm 5mm 10mm; display: flex; flex-direction: column; gap: 15px; background: #fff; box-sizing: border-box; overflow: hidden; }

    .test-section-card { background: #fff; border-radius: 8px; border: 1px solid #cfd8dc; overflow: hidden; display: flex; flex-direction: column; }
    .test-sec-title { background: #f8fafd; padding: 8px 12px; border-bottom: 1px solid #eceff1; font-size: 13px; font-weight: 800; color: #37474f; font-family: 'NanumSquareRound', sans-serif; display: flex; align-items: center; gap: 8px; }
    .icon-v { background: #5c6bc0; width:18px; height:18px; color:white; font-size:12px; display:flex; justify-content:center; align-items:center; border-radius:4px; font-family: 'Montserrat', sans-serif; font-weight: 900;} 

    /* STEP 1. Table */
    .step1-container { display: flex; gap: 0; width: 100%; }
    .step1-table { width: 50%; border-collapse: collapse; font-family: 'Noto Sans KR', sans-serif; table-layout: fixed; }
    .step1-table:first-child { border-right: 1px solid #eceff1; }
    /* 표 머리말 아래 굵은 선 (2px solid #78909c) 적용 */
    .step1-table th { background: #ffffff; color: #78909c; padding: 6px; font-size: 10px; border-bottom: 2px solid #78909c; font-family: 'Montserrat', sans-serif; text-transform: uppercase; }
    .step1-table td { padding: 4px 8px; border-bottom: 1px solid #b0bec5; vertical-align: middle; height: 26px; overflow: hidden; }

    .q-num { flex-shrink: 0; width: 22px; color: #90a4ae; font-size: 10.5px; font-weight: 800; font-family: 'Montserrat', sans-serif; display: inline-block; }
    /* 영어 표제어 굵기 조정: 800 -> 700 */
    .tt-word { font-family: 'Montserrat', sans-serif; font-weight: 700; color: var(--c-brand); font-size: 12.5px; }
    .tt-mean-p1 { font-weight: 800; color: #d32f2f; line-height: 1.2; font-family: 'NanumSquareRound', sans-serif; }

    /* STEP 2. Table */
    .step2-container { padding: 10px 15px; background: #fafafa; display: flex; gap: 15px;}
    .step2-box { flex: 1; background: #fff; border: 1px solid #eceff1; border-radius: 6px; padding: 6px 10px; }
    .step2-subtable { width: 100%; border-collapse: collapse; font-family: 'Noto Sans KR', sans-serif; table-layout: fixed; }
    .step2-subtable td { border-bottom: 1px dashed #b0bec5; vertical-align: middle; padding: 0; }
    .step2-subtable tr:last-child td { border-bottom: none; }

    /* STEP 3. Table */
    .step3-card { flex: 1; min-height: 0; }
    .step3-table-container { flex: 1; display: flex; overflow: hidden; }
    .step3-table { width: 100%; border-collapse: collapse; font-family: 'Noto Sans KR', sans-serif; table-layout: fixed; }
    /* 표 머리말 아래 굵은 선 (2px solid #78909c) 적용 */
    .step3-table th { background: #ffffff; color: #78909c; padding: 6px; font-size: 10px; border-bottom: 2px solid #78909c; font-family: 'Montserrat', sans-serif; text-transform: uppercase; }
    .step3-table td { padding: 6px 10px; vertical-align: middle; border-bottom: 1px solid #b0bec5; }

    .step3-ko-text { color:#1565c0; font-weight: 800; font-size: 12px; font-family: 'NanumSquareRound', sans-serif; letter-spacing: -0.3px; line-height: 1.3; }
    .step3-chunk-text { color:#37474f; line-height:1.5; font-size: 12.5px; font-family: 'Montserrat', 'KoPub Batang', serif; letter-spacing: -0.2px; }
    .chunk-hl { font-weight: 800; color: #d32f2f; text-decoration: underline; } 
    .chunk-hint { font-weight: 700; color: #d84315; font-family: 'Montserrat', monospace; letter-spacing: 1px;}

    .tt-empty-box { height: 18px; } 
</style>
</head>
<body>
    <div class="page-container">
        <div class="page-header">
            <div class="ph-left">
                <span class="ph-title-main">___CLASS_NAME___ Vocabulary Test</span>
                <span style="font-size:11px; color:#90a4ae; font-weight:700; margin-left:8px; font-family:'Montserrat';">[범위: ___TEST_RANGE______IS_ANSWER___]</span>
            </div>
            <div class="ph-right">이름 : ____________________ &nbsp;&nbsp;&nbsp; 점수 : &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; / ___TOTAL_SCORE___</div>
        </div>

        <div class="p2-voca-body">
            <div class="test-section-card">
                <div class="test-sec-title"><div class="icon-v">V</div>STEP 1. Speed Check (단어 뜻 적기)</div>
                <div class="step1-container">
                    <table class="step1-table">
                        <colgroup><col width="45%"><col width="55%"></colgroup>
                        <thead><tr><th>Word</th><th>Meaning</th></tr></thead>
                        <tbody>___STEP1_LEFT___</tbody>
                    </table>
                    <table class="step1-table">
                        <colgroup><col width="45%"><col width="55%"></colgroup>
                        <thead><tr><th>Word</th><th>Meaning</th></tr></thead>
                        <tbody>___STEP1_RIGHT___</tbody>
                    </table>
                </div>
            </div>

            <div class="test-section-card">
                <div class="test-sec-title"><div class="icon-v">V</div>STEP 2. Match Synonyms (유의어 연결)</div>
                <div class="step2-container">
                    ___STEP2_CONTENT___
                </div>
            </div>

            <div class="test-section-card step3-card">
                <div class="test-sec-title"><div class="icon-v">V</div>STEP 3. Chunk Context (첫 알파벳 힌트를 보고 빈칸 채우기)</div>
                <div class="step3-table-container">
                    <table class="step3-table">
                        <colgroup><col width="40%"><col width="60%"></colgroup>
                        <thead><tr><th>Korean Translation</th><th>English Chunk (Fill in the blank)</th></tr></thead>
                        <tbody>___STEP3_ROWS___</tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="page-footer">___CONFIG_ACADEMY_NAME___</div>
    </div>
</body>
</html>
"""

# ==============================================================================
# 유틸리티 함수
# ==============================================================================
def get_shrink_style(text, max_len=20, base_size=11.5):
    t_len = sum(1.8 if ord('가') <= ord(c) <= ord('힣') else 1.0 for c in text)
    style = "white-space: nowrap; overflow: visible; "
    diff = t_len - max_len

    if diff >= 20:
        style += f"font-size: {max(7.0, base_size - 3.0)}px; letter-spacing: -0.6px;"
    elif diff >= 14:
        style += f"font-size: {max(8.0, base_size - 2.0)}px; letter-spacing: -0.4px;"
    elif diff >= 8:
        style += f"font-size: {max(9.0, base_size - 1.5)}px; letter-spacing: -0.3px;"
    elif diff >= 4:
        style += f"font-size: {max(10.0, base_size - 1.0)}px; letter-spacing: -0.2px;"
    elif diff > 0:
        style += f"font-size: {max(10.5, base_size - 0.5)}px; letter-spacing: -0.1px;"
    else:
        style += f"font-size: {base_size}px;"
    return style

def is_valid_synonym(syn):
    if not syn: return False
    clean = syn.strip().upper()
    if clean in ['', '-', 'N', 'A', 'N/A', 'NONE', 'X']: return False
    return True

# ==============================================================================
# PDF 자동 저장 함수 (Playwright 활용)
# ==============================================================================
def save_html_to_pdf(html_content, output_pdf_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html_content)
        page.evaluate("document.fonts.ready")
        page.pdf(
            path=output_pdf_path,
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
        )
        browser.close()

# ==============================================================================
# 시험지 생성 코어 로직
# ==============================================================================
def generate_global_review_test(all_vocab_list, is_teacher, test_range_text):
    if not all_vocab_list: return ""

    unique_vocab = []
    seen = set()
    for v in all_vocab_list:
        word = v.get('word', '').strip().lower()
        if word and word not in seen:
            seen.add(word)
            unique_vocab.append(v)

    random.shuffle(unique_vocab)

    s1_count = min(COUNT_STEP1, len(unique_vocab))
    step1_pool = unique_vocab[:s1_count]

    valid_s2_pool = [v for v in unique_vocab if is_valid_synonym(v.get('synonym', ''))]
    s2_count = min(COUNT_STEP2, len(valid_s2_pool))
    step2_pool = random.sample(valid_s2_pool, s2_count)

    s3_candidates = [v for v in unique_vocab if v not in step1_pool]
    s3_count = min(COUNT_STEP3, len(unique_vocab))

    if len(s3_candidates) < s3_count:
        shortage = s3_count - len(s3_candidates)
        extra = [v for v in step1_pool]
        random.shuffle(extra)
        s3_candidates.extend(extra[:shortage])

    step3_pool = random.sample(s3_candidates, s3_count)

    total_score = s1_count + s2_count + s3_count

    # ---------------------------------------------------------
    # [STEP 1 렌더링]
    # ---------------------------------------------------------
    list_for_left = step1_pool[:len(step1_pool) // 2 + (len(step1_pool) % 2)]
    list_for_right = step1_pool[len(list_for_left):]

    step1_left, step1_right = "", ""

    def render_step1_row(index, v):
        ans_word = v.get("word", "")
        raw_mean = v.get('meaning', '')
        clean_mean = re.sub(r'[①-⑳]', '|', raw_mean)
        clean_mean = re.sub(r'\(.*?\)', '', clean_mean).strip()
        final_mean = ", ".join([p.strip() for p in clean_mean.split('|') if p.strip()])
        m_style = get_shrink_style(final_mean, 22, 11)

        if is_teacher:
            return f"""<tr>
                <td class="tt-word"><span class="q-num">{index}.</span> {ans_word}</td>
                <td style="text-align:center;"><div class="tt-mean-p1" style="{m_style}">{final_mean}</div></td>
            </tr>"""
        else:
            return f"""<tr>
                <td class="tt-word"><span class="q-num">{index}.</span> {ans_word}</td>
                <td><div class="tt-empty-box"></div></td>
            </tr>"""

    for i, v in enumerate(list_for_left):
        step1_left += render_step1_row(i + 1, v)
    for i, v in enumerate(list_for_right):
        step1_right += render_step1_row(i + 1 + len(list_for_left), v)

    # ---------------------------------------------------------
    # [STEP 2 렌더링]
    # ---------------------------------------------------------
    group_a = step2_pool[:len(step2_pool) // 2 + (len(step2_pool) % 2)]
    group_b = step2_pool[len(group_a):]

    def generate_matching_rows(group, num_offset):
        if not group: return ""
        rows_html, svg_lines = "", ""
        syn_pool = []

        row_height = 38

        for i, v in enumerate(group):
            syn = v.get('synonym', '')
            clean_syn = syn.replace('/', ',').replace('(', '').replace(')', '')
            final_syn = ", ".join([s.strip() for s in clean_syn.split(',')])
            syn_pool.append({'syn': final_syn, 'id': i})

        random.shuffle(syn_pool)

        if is_teacher:
            for row_idx_left, v in enumerate(group):
                row_idx_right = next(idx for idx, s in enumerate(syn_pool) if s['id'] == row_idx_left)
                y1 = row_idx_left * row_height + (row_height / 2)
                y2 = row_idx_right * row_height + (row_height / 2)
                svg_lines += f'<line x1="5" y1="{y1}" x2="95" y2="{y2}" stroke="#e65100" stroke-width="1.5" opacity="0.6" />'

        for i, v in enumerate(group):
            shuffled_syn = syn_pool[i]['syn'] if i < len(syn_pool) else ""
            s_style = get_shrink_style(shuffled_syn, 22, 12)

            rows_html += f"""
            <tr style="height: {row_height}px;">
                <td class="tt-word" style="width:38%;">
                    <span class="q-num">{num_offset + i}.</span> {v.get("word", "")}
                </td>
                <td style="text-align:center; width:24%;">
                    <div style="display:flex; justify-content:space-between; color:#b0bec5; font-size:10px;">
                        <span>●</span><span>●</span>
                    </div>
                </td>
                <td class="tt-mean-p1" style="text-align:right; width:38%; color:#455a64; {s_style}">{shuffled_syn}</td>
            </tr>"""

        return f"""
        <div class="step2-box">
            <div style="position:relative; width:100%;">
                <svg style="position:absolute; left:38%; top:0; width:24%; height:100%; overflow:visible; z-index:5;" viewBox="0 0 100 {len(group) * row_height}" preserveAspectRatio="none">
                    {svg_lines}
                </svg>
                <table class="step2-subtable" style="position:relative; z-index:10;">
                    <colgroup><col width="38%"><col width="24%"><col width="38%"></colgroup>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>
        </div>
        """

    step2_html = generate_matching_rows(group_a, s1_count + 1)
    if group_b:
        step2_html += generate_matching_rows(group_b, s1_count + 1 + len(group_a))

    # ---------------------------------------------------------
    # [STEP 3 렌더링 (첫 알파벳 힌트)]
    # ---------------------------------------------------------
    step3_rows = ""
    for i, v in enumerate(step3_pool):
        chunk_raw = v.get('chunk_example', '')
        chunk_ko = v.get('chunk_translation', '')
        word_raw = v.get('word', '').split('(')[0].strip()

        clean_word = re.sub(r'\(.*?\)', '', word_raw.lower().strip()).strip()
        base = clean_word
        if len(base) > 3:
            if base.endswith('y') or base.endswith('e') or base.endswith('s'):
                base = base[:-1]

        pattern = r'\b' + re.escape(base) + r'[a-z]*'

        if is_teacher:
            try:
                chunk_step3 = re.sub(pattern, lambda m: f'<span class="chunk-hl">{m.group()}</span>', chunk_raw,
                                     flags=re.IGNORECASE)
            except:
                chunk_step3 = chunk_raw
        else:
            def hint_replacer(m):
                matched = m.group()
                if not matched: return ""
                first_char = matched[0]
                underscores = "_" * 12
                return f'<span class="chunk-hint">{first_char}{underscores}</span>'

            try:
                chunk_step3 = re.sub(pattern, hint_replacer, chunk_raw, flags=re.IGNORECASE)
            except:
                chunk_step3 = chunk_raw

        step3_rows += f"""<tr>
            <td class="step3-ko-text"><span class="q-num">{s1_count + s2_count + 1 + i}.</span> {chunk_ko}</td>
            <td class="step3-chunk-text">{chunk_step3}</td>
        </tr>"""

    final_html = TEST_TEMPLATE.replace("___TOTAL_SCORE___", str(total_score)) \
        .replace("___CLASS_NAME___", CONFIG_CLASS_NAME) \
        .replace("___TEST_RANGE___", test_range_text) \
        .replace("___IS_ANSWER___", " (ANS)" if is_teacher else "") \
        .replace("___CONFIG_ACADEMY_NAME___", CONFIG_ACADEMY_NAME) \
        .replace("___STEP1_LEFT___", step1_left) \
        .replace("___STEP1_RIGHT___", step1_right) \
        .replace("___STEP2_CONTENT___", step2_html) \
        .replace("___STEP3_ROWS___", step3_rows)

    return final_html

if __name__ == "__main__":
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    target_folder = os.path.join(desktop_path, CONFIG_TARGET_FOLDER)

    if not os.path.exists(target_folder):
        print("=" * 60)
        print(f"⚠️ 바탕화면에 '{CONFIG_TARGET_FOLDER}' 폴더가 없습니다.")
        print("=" * 60)
        exit()

    files = [f for f in os.listdir(target_folder) if f.endswith('.txt')]

    global_vocab_list = []
    source_origins = set()

    print(f"📂 총 {len(files)}개의 파일에서 단어와 범위를 수집합니다...")

    for file_name in files:
        try:
            with open(os.path.join(target_folder, file_name), 'r', encoding='utf-8') as f:
                data = json.loads(f.read())
                global_vocab_list.extend(data.get('vocab_list', []))
                source = data.get('meta_info', {}).get('source_origin', '').strip()
                if source:
                    source_origins.add(source)

        except Exception as e:
            print(f"   ❌ Error reading {file_name}: {e}")

    if not global_vocab_list:
        print("⚠️ 추출된 단어가 없습니다. 프로그램을 종료합니다.")
        exit()

    sorted_sources = sorted(list(source_origins))
    if len(sorted_sources) > 1:
        test_range_text = f"{sorted_sources[0]} ~ {sorted_sources[-1]}"
    elif len(sorted_sources) == 1:
        test_range_text = sorted_sources[0]
    else:
        test_range_text = "All Units"

    # ==============================================================================
    # [수정된 부분] 랜덤 시드를 고정하여 학생용과 교사용이 동일한 단어를 추출하도록 합니다.
    # ==============================================================================
    test_seed = random.randint(1, 999999)

    random.seed(test_seed)
    student_html = generate_global_review_test(global_vocab_list, is_teacher=False, test_range_text=test_range_text)

    random.seed(test_seed)
    teacher_html = generate_global_review_test(global_vocab_list, is_teacher=True, test_range_text=test_range_text)
    # ==============================================================================

    # 1. HTML 파일 저장 (웹 브라우저 확인용)
    student_html_path = os.path.join(target_folder, "Global_Review_Test_Student.html")
    teacher_html_path = os.path.join(target_folder, "Global_Review_Test_Teacher.html")
    with open(student_html_path, 'w', encoding='utf-8') as f:
        f.write(student_html)
    with open(teacher_html_path, 'w', encoding='utf-8') as f:
        f.write(teacher_html)

    # 2. PDF 자동 변환 및 저장 (Playwright 사용)
    student_pdf_path = os.path.join(target_folder, "Global_Review_Test_Student.pdf")
    teacher_pdf_path = os.path.join(target_folder, "Global_Review_Test_Teacher.pdf")

    print("📄 백그라운드에서 PDF를 생성 중입니다. 잠시만 기다려주세요...")
    try:
        save_html_to_pdf(student_html, student_pdf_path)
        save_html_to_pdf(teacher_html, teacher_pdf_path)
        pdf_success = True
    except Exception as e:
        print(f"⚠️ PDF 변환 중 오류가 발생했습니다: {e}")
        pdf_success = False

    print("=" * 60)
    print(f"🎉 '{CONFIG_CLASS_NAME}' 누적 단어 시험지 생성이 완료되었습니다!")
    print(f"   📌 시험 범위: {test_range_text}")
    print(f"   📘 학생용 HTML: {os.path.basename(student_html_path)}")
    print(f"   📕 교사용 HTML: {os.path.basename(teacher_html_path)}")
    if pdf_success:
        print(f"   📄 학생용 PDF: {os.path.basename(student_pdf_path)}")
        print(f"   📄 교사용 PDF: {os.path.basename(teacher_pdf_path)}")
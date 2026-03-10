import os
import json
import random
import re


# ==========================================
# 1. 헬퍼 함수
# ==========================================
def get_choseong(text):
    choseong_list = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    result = []
    for char in text:
        if '가' <= char <= '힣':
            result.append(choseong_list[(ord(char) - 44032) // 588])
        elif char == ' ':
            result.append(' ')
        else:
            result.append(char)
    return "".join(result)


# [스마트 단어 찾기 함수] (구동사 분리형 + 활용형 완벽 지원)
def smart_replace(text, word, replacement_format):
    """
    text: 전체 문장
    word: 찾을 단어 (예: tuck in, carry out)
    replacement_format: 바꿀 형식
    """
    # 1. 구동사(두 단어 이상)인 경우 처리
    if ' ' in word:
        parts = word.split()
        verb = parts[0]
        particle = " ".join(parts[1:])

        roots = [verb]
        if len(verb) > 3: roots.append(verb[:-1])
        if len(verb) > 4: roots.append(verb[:-2])

        for root in roots:
            pattern_str = r"\b" + re.escape(root) + r"\w*\s+(?:[\w']+\s+){0,4}" + re.escape(particle) + r"\b"
            pattern = re.compile(pattern_str, re.IGNORECASE)

            if pattern.search(text):
                return pattern.sub(lambda m: replacement_format.format(m.group()), text)

    # 2. 한 단어인 경우 처리
    else:
        roots = [word]
        if len(word) > 3: roots.append(word[:-1])
        if len(word) > 4: roots.append(word[:-2])

        for root in roots:
            pattern_str = r"\b" + re.escape(root) + r"\w*"
            pattern = re.compile(pattern_str, re.IGNORECASE)

            if pattern.search(text):
                return pattern.sub(lambda m: replacement_format.format(m.group()), text)

    return text


# ==========================================
# 2. 핵심 로직: 워크북 + 간단 해설지 동시 생성
# ==========================================
def generate_html_from_json(json_str, output_path):
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        print(f"❌ JSON 형식 오류")
        return

    grouped_data = {}
    for item in data:
        src = item.get('source', 'Unknown Source')
        if src not in grouped_data:
            grouped_data[src] = []
        grouped_data[src].append(item)

    # -----------------------------------------------------------
    # [스타일 정의]
    # -----------------------------------------------------------
    common_css = """
        body { font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; color: #333; }
        table { width: 100%; border-collapse: collapse; font-size: 0.9em; table-layout: fixed; }
        th, td { border: 1px solid #ccc; padding: 4px 6px; vertical-align: middle; word-wrap: break-word; }
        th { background-color: #f8f8f8; text-align: center; font-weight: bold; }
    """

    # 워크북용 CSS
    wb_css = common_css + """
        @page { size: A4; margin: 10mm; } 
        body { width: 190mm; margin: 0 auto; font-size: 10pt; }
        .page { page-break-after: always; position: relative; height: 275mm; display: flex; flex-direction: column; }
        .page:last-child { page-break-after: auto; }

        /* [수정됨] 페이지 번호 위치 조정 (bottom: -30px) */
        .page-footer {
            position: absolute;
            bottom: -30px; /* 더 아래로 내림 */
            width: 100%;
            text-align: center;
            font-size: 10pt;
            font-weight: bold;
            color: #777;
            letter-spacing: 2px;
        }

        h1 { text-align: center; font-size: 1.4em; margin: 0 0 10px 0; border-bottom: 2px solid #333; padding-bottom: 5px; letter-spacing: -1px; }
        h2 { font-size: 1.05em; background: #eee; padding: 4px 8px; margin: 12px 0 6px 0; border-left: 5px solid #333; }
        p { margin: 2px 0 6px 0; font-size: 0.85em; color: #666; }
        th { height: 22px; }
        .chunk-box { font-size: 0.9em; color: #444; margin-bottom: 2px; line-height: 1.2; }
        .chunk-kr { font-size: 0.75em; color: #888; display: block; }
        .write-box { height: 18px; border-bottom: 1px solid #ddd; }

        b { background-color: #e0f7fa; padding: 0 2px; border-radius: 2px; color: #000; }

        .match-section { display: flex; justify-content: space-between; gap: 20px; }
        .match-col { width: 49%; }
        .match-row { display: flex; align-items: center; height: 32px; border-bottom: 1px dashed #ddd; font-size: 0.95em; }
        .m-eng { flex: 0 0 35%; text-align: left; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }

        /* 점 간격 17px 유지 */
        .m-dot { flex: 0 0 20%; text-align: center; color: #bbb; font-size: 0.7em; letter-spacing: 17px; } 

        .m-kor { flex: 0 0 45%; text-align: right; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
        .quiz-box { border: 1px solid #ddd; padding: 10px 15px; border-radius: 6px; background: #fafafa; flex-grow: 1; }
        .quiz-item { margin-bottom: 6px; font-size: 0.95em; line-height: 1.4; display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 1px dotted #eee; padding-bottom: 2px; }
        .quiz-sent { width: 75%; }
        .quiz-hint { width: 23%; text-align: right; font-size: 0.8em; color: #888; font-style: italic; }
        .highlight { font-weight: bold; color: #0066cc; border-bottom: 1px solid #0066cc; }
    """

    # 해설지용 CSS
    ans_css = common_css + """
        @page { size: A4; margin: 10mm; }
        body { width: 190mm; margin: 0 auto; font-size: 10pt; }
        .ans-header { text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px; }
        .ans-block { border: 1px solid #ccc; padding: 15px; margin-bottom: 15px; border-radius: 5px; page-break-inside: avoid; }
        .ans-source { font-weight: bold; background: #333; color: #fff; padding: 5px 10px; display: inline-block; border-radius: 3px; margin-bottom: 10px; }
        .ans-flex { display: flex; gap: 20px; }
        .ans-section { flex: 1; }
        .ans-title { font-weight: bold; border-bottom: 1px solid #999; margin-bottom: 8px; padding-bottom: 2px; color: #0066cc; }
        .ans-item { font-size: 0.9em; border-bottom: 1px solid #eee; padding: 3px 0; display: flex; justify-content: space-between; }
        .ans-num { font-weight: bold; margin-right: 5px; color: #555; }
    """

    # HTML 초기화
    wb_html = f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>Workbook</title><style>{wb_css}</style></head><body>"
    ans_html = f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>Answer Key</title><style>{ans_css}</style></head><body>"
    ans_html += "<div class='ans-header'><h1>[해설지] 정답 및 어휘 목록</h1></div>"

    page_num = 1

    for source, items in grouped_data.items():
        # 데이터 셔플
        match_items = items[:]
        random.shuffle(match_items)
        quiz_items = items[:]
        random.shuffle(quiz_items)

        # ---------------------------------------------------------
        # 1. 워크북 (Workbook)
        # ---------------------------------------------------------
        wb_html += f"""
        <div class="page">
            <h1>📄 {source} Summary Workbook</h1>

            <h2>[Part A] 핵심 어휘 학습 및 스펠링 연습</h2>
            <p>단어와 문맥을 읽고, 스펠링을 칸에 맞춰 한 번씩 써보세요.</p>
            <table>
                <colgroup><col width="5%"> <col width="15%"> <col width="15%"> <col width="45%"> <col width="20%"></colgroup>
                <thead><tr><th>No</th> <th>Word</th> <th>Meaning</th> <th>Context Chunk</th> <th>Write</th></tr></thead>
                <tbody>
        """
        for i, item in enumerate(items, 1):
            w = item['word']
            # 스마트 찾기
            c_en = smart_replace(item['chunk_en'], w, "<b>{}</b>")
            wb_html += f"""
                <tr>
                    <td style="text-align:center;">{i}</td><td><strong>{w}</strong></td>
                    <td style="font-size:0.9em;">{item['meaning']}</td>
                    <td><div class="chunk-box">{c_en}</div><span class="chunk-kr">{item['chunk_kr']}</span></td>
                    <td><div class="write-box"></div></td>
                </tr>
            """
        wb_html += "</tbody></table>"

        # [Part B]
        wb_html += """<h2>[Part B] 의미 연결하기 (Matching)</h2><div class="match-section">"""
        labels = ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ']
        half = (len(match_items) + 1) // 2
        groups = [match_items[:half], match_items[half:]]

        for group in groups:
            wb_html += '<div class="match-col">'
            engs = [x['word'].capitalize() for x in group]
            kors = [x['meaning'] for x in group]
            shuffled_kors = kors[:]
            random.shuffle(shuffled_kors)

            for j in range(len(group)):
                curr_label = labels[j] if j < len(labels) else '?'
                wb_html += f"""
                <div class="match-row">
                    <span class="m-eng">{engs[j]}</span>
                    <span class="m-dot">● ●</span>
                    <span class="m-kor">{curr_label}. {shuffled_kors[j]}</span>
                </div>
                """
            wb_html += '</div>'
        wb_html += "</div>"

        # [Part C]
        wb_html += """<h2>[Part C] 문맥 초성 퀴즈 (Context Quiz)</h2>
                      <p>문맥에 알맞은 단어를 넣으세요. 힌트는 우측에 있습니다. (총 10문제)</p>
                      <div class="quiz-box">"""
        for i, item in enumerate(quiz_items, 1):
            w, m = item['word'], item['meaning']
            hint = get_choseong(m)
            # 스마트 찾기
            chunk_display = smart_replace(item['chunk_en'], w, "<span class='highlight'>{}</span>")

            wb_html += f"""
            <div class="quiz-item">
                <div class="quiz-sent">• {chunk_display}</div>
                <div class="quiz-hint">({hint})</div>
            </div>
            """

        # [페이지 번호] 바닥으로 내리기 (bottom: -30px)
        wb_html += f"""</div><div class="page-footer">- {page_num} -</div></div>"""
        page_num += 1

        # ---------------------------------------------------------
        # 2. 해설지 (Answer Key)
        # ---------------------------------------------------------
        ans_html += f"""
        <div class="ans-block">
            <div class="ans-source">{source}</div>
            <div class="ans-flex">
                <div class="ans-section">
                    <div class="ans-title">[Part A/B] 어휘 정답 목록</div>
        """
        for item in items:
            ans_html += f"<div class='ans-item'><span><b>{item['word']}</b></span> <span>{item['meaning']}</span></div>"

        ans_html += """
                </div>
                <div class="ans-section">
                    <div class="ans-title">[Part C] 퀴즈 정답 (랜덤 순서)</div>
        """
        for i, item in enumerate(quiz_items, 1):
            ans_html += f"<div class='ans-item'><span class='ans-num'>{i}.</span> <span><b>{item['word']}</b> ({item['meaning']})</span></div>"

        ans_html += """
                </div>
            </div>
        </div>
        """

    wb_html += "</body></html>"
    ans_html += "</body></html>"

    ans_output_path = output_path.replace(".html", "_해설.html")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(wb_html)
    with open(ans_output_path, 'w', encoding='utf-8') as f:
        f.write(ans_html)

    print(f"✅ 생성 완료: {os.path.basename(output_path)} (워크북)")
    print(f"✅ 생성 완료: {os.path.basename(ans_output_path)} (해설지)")


if __name__ == "__main__":
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    target_folder = os.path.join(desktop_path, "5")

    if not os.path.exists(target_folder):
        print(f"⚠️ '5' 폴더가 없습니다: {target_folder}")
    else:
        files = [f for f in os.listdir(target_folder) if f.endswith('.txt')]
        if not files:
            print("⚠️ 처리할 .txt 파일이 없습니다.")
        else:
            print(f"📂 총 {len(files)}개의 파일을 변환합니다...")
            for file_name in files:
                input_path = os.path.join(target_folder, file_name)
                output_name = file_name.replace('.txt', '.html')
                output_path = os.path.join(target_folder, output_name)

                with open(input_path, 'r', encoding='utf-8') as f:
                    generate_html_from_json(f.read(), output_path)
            print("🎉 모든 작업이 완료되었습니다!")

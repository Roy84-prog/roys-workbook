import json
import re
import os
import itertools

# [v184] HTML 태그 자동 닫힘 보정을 위한 라이브러리
# (터미널에서 pip install beautifulsoup4 설치 권장)
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
    print("Warning: beautifulsoup4 라이브러리가 없습니다. 'pip install beautifulsoup4'를 설치하면 밑줄 오류를 완벽히 해결할 수 있습니다.")

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
/* [인쇄 시 설정] */
@media print {{
    body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    .container {{ box-shadow: none; border: 1px solid #ddd; }}
    @page {{ margin: 10mm; size: A4; }}
    .page-break {{ page-break-before: always; }}
    .interactive-num {{ pointer-events: none; color: inherit; }} 
    .translation-bubble {{ display: none !important; }}
    /* 인쇄 시 버튼 및 모달 숨김 */
    .header-btn {{ display: none !important; }} 
    .custom-modal {{ display: none !important; }}
}}

:root {{
    --bg-color: #f9f9f9;
    --font-eng: 'Times New Roman', serif;
    --font-kor: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;

    /* 문장 성분 색상 변경 */
    --c-S: #0d47a1; /* 주어(S): 진한 파랑 */
    --c-V: #b71c1c; /* 동사(V): 진한 빨강 */
    --c-O: #7b1fa2; /* 목적어(O): 보라색 (수정됨) */
    --c-C: #1b5e20; /* 보어(C): 진한 초록 */
    --c-M: #9e9e9e; /* 수식어(M): 삭제 대상이므로 예비로만 남김 */
    --c-con: #8e24aa; /* 접속사: 기존 유지 */
}}

body {{ font-family: var(--font-kor); font-size: 15px; color: #333; margin: 20px; line-height: 1.6; background: var(--bg-color); }}

/* [v184] 안전한 밑줄 스타일 추가 */
.text-underline {{ 
    text-decoration: underline; 
    text-underline-position: under; 
    text-decoration-thickness: 1px;
}}

/* [Header Container: Page 1 Info] */
.header-container {{
    background: #fff;
    padding: 30px;
    border-radius: 12px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.08);
    min-width: 1000px;
    max-width: 1600px;
    margin: 0 auto 30px;
    display: block;
    position: relative; 
    min-height: 220px;
}}

/* [Header Buttons Common Style] */
.header-btn {{
    position: absolute;
    color: white;
    border: none;
    padding: 5px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    transition: background 0.3s, transform 0.1s;
    z-index: 100;
    width: 110px;
    text-align: center;
    letter-spacing: -0.5px;
}}
.header-btn:active {{ transform: translateY(1px); }}

/* --- Right Buttons (Translations) --- */
.btn-literal {{ top: 20px; right: 20px; background-color: #0277bd; }} 
.btn-literal:hover {{ background-color: #01579b; }}

.btn-liberal {{ top: 55px; right: 20px; background-color: #546e7a; }}
.btn-liberal:hover {{ background-color: #455a64; }}

.btn-tips {{ top: 90px; right: 20px; background-color: #7b1fa2; }} 
.btn-tips:hover {{ background-color: #4a148c; }}

.btn-logic {{ top: 125px; right: 20px; background-color: #00897b; }}
.btn-logic:hover {{ background-color: #00695c; }}

/* --- Left Buttons (English) --- */
.btn-eng-all {{ top: 20px; left: 20px; background-color: #3949ab; }}
.btn-eng-all:hover {{ background-color: #283593; }}

.btn-eng-pure {{ top: 55px; left: 20px; background-color: #00695c; }}
.btn-eng-pure:hover {{ background-color: #004d40; }}

.btn-vis-clean {{ top: 90px; left: 20px; background-color: #455a64; }} 
.btn-vis-clean:hover {{ background-color: #263238; }}

/* [v182] New Button for Learning Points */
.btn-learning {{ top: 125px; left: 20px; background-color: #d84315; }} 
.btn-learning:hover {{ background-color: #bf360c; }}

/* --- Center Buttons (Study Aids) --- */
.btn-vocab {{ top: 20px; left: 50%; margin-left: -55px; background-color: #ef6c00; }}
.btn-vocab:hover {{ background-color: #e65100; }}

.btn-keys {{ top: 55px; left: 50%; margin-left: -55px; background-color: #c62828; }}
.btn-keys:hover {{ background-color: #b71c1c; }}

.btn-ans {{ top: 90px; left: 50%; margin-left: -55px; background-color: #2e7d32; }}
.btn-ans:hover {{ background-color: #1b5e20; }}

.btn-opts {{ top: 125px; left: 50%; margin-left: -55px; background-color: #5d4037; }} 
.btn-opts:hover {{ background-color: #3e2723; }}

/* [New] Exam Prediction Button & Modal */
.btn-exam {{ top: 160px; left: 50%; margin-left: -55px; background-color: #d81b60; box-shadow: 0 0 8px rgba(216,27,96,0.5); }}
.btn-exam:hover {{ background-color: #ad1457; }}


/* [Modals (Bubbles)] */
.custom-modal {{
    display: none; 
    position: absolute;
    top: 60px; 
    width: 600px; 
    max-width: 48vw;
    background: #fff;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 15px 40px rgba(0,0,0,0.3);
    max-height: 80vh;
    overflow-y: auto;
    /* z-index handled by JS */
}}

/* Modal Positions & Borders */
/* Right Group */
.modal-literal {{ right: 20px; border: 3px solid #0277bd; top: 50px; }}
.modal-liberal {{ right: 20px; border: 3px solid #546e7a; top: 85px; }}
.modal-tips {{ right: 20px; border: 3px solid #7b1fa2; top: 120px; }}
.modal-logic {{ right: 20px; border: 3px solid #00897b; top: 155px; }}

/* Left Group */
.modal-eng-all {{ left: 20px; border: 3px solid #3949ab; top: 50px; }}
.modal-eng-pure {{ left: 20px; border: 3px solid #00695c; top: 85px; }}
.modal-vis-clean {{ left: 20px; border: 3px solid #455a64; top: 120px; width: 600px; }}
/* [v182] Learning Modal */
.modal-learning {{ left: 20px; border: 3px solid #d84315; top: 155px; width: 600px; }}
.modal-learning h3 {{ color: #d84315; }}

/* Center Group */
.modal-center {{ left: 50%; margin-left: -350px; width: 700px; }} 

.modal-vocab {{ left: 50%; margin-left: -350px; border: 3px solid #ef6c00; top: 50px; width: 700px; }}
.modal-keys {{ left: 50%; margin-left: -350px; border: 3px solid #c62828; top: 85px; width: 700px; }}
.modal-ans {{ left: 50%; margin-left: -350px; border: 3px solid #2e7d32; top: 120px; width: 700px; }}
.modal-opts {{ left: 50%; margin-left: -350px; border: 3px solid #5d4037; top: 155px; width: 700px; }}
.modal-exam {{ left: 50%; margin-left: -350px; border: 3px solid #d81b60; top: 190px; width: 700px; }}

.custom-modal h3 {{
    margin-top: 0;
    border-bottom: 2px solid #eee;
    padding-bottom: 8px;
    font-size: 15px;
    margin-bottom: 12px;
}}

/* Modal Text Colors */
.modal-liberal h3 {{ color: #546e7a; }}
.modal-literal h3 {{ color: #0277bd; }}
.modal-tips h3 {{ color: #7b1fa2; }}
.modal-logic h3 {{ color: #00897b; }}
.modal-eng-all h3 {{ color: #3949ab; }}
.modal-eng-pure h3 {{ color: #00695c; }}
.modal-vis-clean h3 {{ color: #455a64; }}
.modal-vocab h3 {{ color: #ef6c00; }}
.modal-keys h3 {{ color: #c62828; }}
.modal-ans h3 {{ color: #2e7d32; }}
.modal-opts h3 {{ color: #5d4037; }}
.modal-exam h3 {{ color: #d81b60; }}

.modal-content {{
    font-size: 14px;
    line-height: 1.7;
    color: #333;
}}

/* [Logic Sections inside Modals] */
.logic-section {{
    margin-bottom: 15px;
    padding: 12px;
    border-radius: 6px;
    border-left-width: 4px;
    border-left-style: solid;
}}
/* [v166] Pastel Colors */
.logic-section-intro {{ background-color: #f0f7ff; border-left-color: #1565c0; }}
.logic-section-body {{ background-color: #fffbf2; border-left-color: #ef6c00; }}
.logic-section-conc {{ background-color: #f3fcf5; border-left-color: #2e7d32; }}
.logic-section-none {{ background-color: #f5f5f5; border-left-color: #9e9e9e; }}

.logic-section-title {{
    display: block;
    font-weight: 800;
    font-size: 13px;
    margin-bottom: 8px;
    padding-bottom: 4px;
    border-bottom: 1px solid rgba(0,0,0,0.1);
}}
.logic-section-intro .logic-section-title {{ color: #1565c0; }}
.logic-section-body .logic-section-title {{ color: #ef6c00; }}
.logic-section-conc .logic-section-title {{ color: #2e7d32; }}

.trans-line, .eng-line {{
    margin-bottom: 10px;
    padding-left: 4px;
}}
.trans-line:last-child, .eng-line:last-child {{ margin-bottom: 0; }}

/* Font for English Modals */
.modal-eng-all .modal-content, 
.modal-eng-pure .modal-content,
.modal-vis-clean .modal-content {{
    font-family: var(--font-eng);
    font-size: 16px; 
}}

/* [Visual Source Specifics] */
.visual-source-text {{ 
    font-family: var(--font-eng); 
    font-size: 19px; 
    line-height: 2.2; 
}}

/* [Modal Internal Tags] */
.trans-num {{ font-weight: bold; margin-right: 5px; color: #546e7a; }}
.eng-num {{ font-weight: bold; margin-right: 5px; color: #3949ab; font-family: var(--font-kor); font-size:13px; }} 
.raw-num {{ font-weight: bold; margin-right: 5px; color: #00695c; font-family: var(--font-kor); font-size:13px; }}

.trans-summary {{
    display: inline-block;
    font-size: 11px;
    color: #555;
    background-color: #fff;
    padding: 1px 6px;
    border-radius: 4px;
    border: 1px solid #ccc;
    margin-left: 6px;
    vertical-align: 1px;
    font-weight: bold;
    font-family: var(--font-kor);
}}

.trans-logic {{
    display: inline-block;
    font-size: 11px;
    font-weight: 800;
    color: #1565c0; 
    background-color: #e3f2fd;
    padding: 1px 6px;
    border-radius: 4px;
    margin-left: 4px;
    vertical-align: 1px;
    font-family: var(--font-kor);
}}

/* [Top Container] */
.top-container {{ 
    background: #fff; 
    padding: 40px; 
    border-radius: 12px; 
    box-shadow: 0 5px 15px rgba(0,0,0,0.08); 
    min-width: 1000px; 
    max-width: 1600px; 
    margin: 0 auto 30px; 
    display: block; 
}}

/* [Bottom Container] */
.bottom-container {{ 
    display: flex; 
    gap: 40px;
    background: #fff; 
    padding: 40px; 
    border-radius: 12px; 
    box-shadow: 0 5px 15px rgba(0,0,0,0.08); 
    min-width: 1000px; 
    max-width: 1600px; 
    margin: 0 auto; 
    align-items: flex-start;
}}

.b-left {{ flex: 40; display: flex; flex-direction: column; gap: 25px; border-right: 1px dashed #ddd; padding-right: 30px; }}
.b-right {{ flex: 60; display: flex; flex-direction: column; }}

/* [Common Box Styles] */
.box-style {{
    background-color: #fff;
    border: 1px solid #eee;
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.03);
}}

/* [Info Items] */
.info-group {{ display: flex; flex-direction: column; gap: 10px; margin-top: 170px; }}
.ri-item {{ background-color: #fff; border: 1px solid #eee; border-left-width: 4px; border-left-style: solid; border-radius: 6px; padding: 12px 15px; font-size: 15px; line-height: 1.5; color: #444; box-shadow: 0 2px 4px rgba(0,0,0,0.03); }}
.ri-material {{ border-left-color: #4caf50; }}
.ri-guide {{ border-left-color: #ff9800; }}
.ri-tip {{ border-left-color: #9c27b0; }}
.ri-label {{ font-weight: 800; margin-bottom: 4px; color: #222; font-size: 15.5px; display: block; }}

/* [Topic Box] */
.topic-box {{ background-color: #e8f5e9; border-left: 5px solid #4caf50; padding: 12px 15px; font-size: 17.5px; color: #1b5e20; border-radius: 4px; }}

/* [Answer Box] */
.answer-box {{ background-color: #e1f5fe; border: 1px solid #81d4fa; border-radius: 8px; padding: 20px; }}
.ans-header {{ font-weight: bold; color: #0277bd; font-size: 16px; margin-bottom: 12px; border-bottom: 1px solid #b3e5fc; padding-bottom: 8px; }}
.ans-content {{ font-size: 13.5px; color: #37474f; line-height: 1.6; }}

/* [Options Box] */
.options-box {{ border-top: 2px solid #333; background: #fff; padding-top:10px; }}
.option-item {{ margin-bottom: 8px; border: 1px solid #eee; border-radius: 6px; padding: 10px; background-color: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }}
.opt-header {{ margin-bottom: 3px; line-height: 1.3; }}
.opt-text {{ font-family: var(--font-eng); font-weight: bold; font-size: 16px; color: #000; }}
.opt-trans {{ font-size: 12.5px; color: #777; margin-bottom: 6px; display: block; line-height: 1.3; }}
.opt-analysis {{ background-color: #f9f9f9; padding: 6px 10px; border-radius: 4px; font-size: 13px; color: #444; border-left: 3px solid #ddd; line-height: 1.4; }}
.err-badge-wrong {{ font-size: 11px; background-color: #fff3e0; color: #ef6c00; padding: 1px 5px; border-radius: 3px; border: 1px solid #ffe0b2; margin-right: 5px; font-weight: bold; }}
.err-badge-correct {{ font-size: 11px; background-color: #e8f5e9; color: #2e7d32; padding: 1px 5px; border-radius: 3px; border: 1px solid #a5d6a7; margin-right: 5px; font-weight: bold; }}

/* [Logic & Scenario] */
.logic-box {{ background-color: #f5f5f5; border: 1px solid #e0e0e0; padding: 15px; border-radius: 8px; font-family: 'D2Coding', monospace; font-size: 12.5px; line-height: 1.7; color: #333; }}
.logic-box strong {{ font-size: 14px; color: #000; margin-bottom: 10px; display: block; }}
.scenario-box {{ background-color: #fff3e0; border: 1px solid #ffe0b2; border-radius: 8px; padding: 15px; }}
.scene-header {{ font-size: 15px; font-weight: 900; color: #e65100; margin-bottom: 12px; border-bottom: 2px solid #ffe0b2; padding-bottom: 6px; }}
.scene-content {{ font-size: 13px; color: #444; line-height: 1.5; background:#fff; padding:10px; border-radius:4px; border-left:4px solid #ff9800; }}

/* [Learning Points Box] - [v171] */
.learning-box {{ margin-top: 20px; }}
.learning-item {{ margin-bottom: 12px; }}
.learning-label {{ display: inline-block; font-size: 11px; font-weight: bold; color: #fff; padding: 2px 6px; border-radius: 4px; margin-bottom: 4px; vertical-align: 1px; }}
.logic-label {{ background-color: #7e57c2; }}
.grammar-label {{ background-color: #00897b; }}
.learning-list {{ margin: 5px 0 0 15px; padding: 0; list-style-type: disc; font-size: 13.5px; color: #444; }}
.learning-list li {{ margin-bottom: 4px; line-height: 1.5; }}

/* [Difficulty Box] - [v175] */
.difficulty-box {{
    background-color: #f1f8e9; 
    border: 1px solid #c5e1a5; 
    border-radius: 6px; 
    padding: 6px 12px; 
    display: inline-flex; 
    align-items: center; 
    gap: 10px; 
    margin-bottom: 10px; 
    font-family: var(--font-eng);
}}
.diff-label {{ font-weight: 900; font-size: 14px; color: #558b2f; letter-spacing: 0.5px; }}
.diff-stars {{ font-size: 16px; color: #fdd835; letter-spacing: 1px; }}

/* [Visual Passage Styles for Restoration] - [v176] */
.visual-box-given {{
    border: 2px solid #333;
    padding: 15px;
    margin-bottom: 20px;
    background-color: #fff;
    border-radius: 4px;
}}
.visual-box-summary {{
    border: 2px solid #333;
    padding: 15px;
    margin-top: 20px;
    background-color: #fff;
    border-radius: 4px;
}}

/* [Visual Passage] */
.question-header {{ font-weight: 800; font-size: 18px; color: #222; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid #222; }}
.source-tag {{ font-size: 11px; color: #fff; background-color: #555; padding: 2px 7px; border-radius: 12px; margin-left: 8px; vertical-align: middle; font-weight: normal; }}

.source-text {{ 
    font-family: var(--font-eng); 
    font-size: 19px; 
    line-height: 3.4; 
    width: fit-content; 
    max-width: 100%; 
    margin: 0 0 30px 0; 
    color: #111; 
    display: block;
}}

.line-justify {{ display: block; text-align: justify; text-align-last: justify; word-break: keep-all; }}
.line-last {{ display: block; text-align: left; text-align-last: left; }}
.line-with-sub {{ display: block; text-align: left; text-align-last: left; word-break: keep-all; }}

/* [Interactive Numbering] */
.interactive-num {{
    cursor: pointer;
    position: relative;
    display: inline-block;
    transition: transform 0.2s ease;
    z-index: 10;
}}
.interactive-num:hover {{
    transform: scale(1.3);
    color: #1565c0;
}}
.translation-bubble {{
    visibility: hidden;
    width: 480px; 
    max-width: 90vw; 
    background-color: #ffffff;
    color: #333;
    text-align: left !important;
    text-align-last: left !important;
    white-space: normal;
    border-radius: 8px;
    padding: 15px;
    position: absolute;
    z-index: 1000;
    bottom: 140%; 
    left: 50%;
    transform: translateX(-50%) translateY(10px);
    opacity: 0;
    transition: opacity 0.3s, transform 0.3s;
    font-family: var(--font-kor);
    font-size: 14px;
    line-height: 1.6;
    box-shadow: 0 5px 25px rgba(0,0,0,0.15);
    border: 2px solid #333;
    font-weight: normal;
    pointer-events: none;
    word-break: keep-all;
}}
.translation-bubble::after {{
    content: "";
    position: absolute;
    top: 100%;
    left: 50%;
    margin-left: -8px;
    border-width: 8px;
    border-style: solid;
    border-color: #333 transparent transparent transparent;
}}
.interactive-num.active .translation-bubble {{
    visibility: visible;
    opacity: 1;
    transform: translateX(-50%) translateY(0);
    pointer-events: auto;
}}

/* Bubble Internal Layout */
.bubble-eng {{ font-family: var(--font-eng); font-size: 17px; margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px dashed #ccc; line-height: 1.5; }}
.bubble-kor {{ font-size: 14px; color: #444; margin-bottom: 10px; line-height: 1.5; }}
.bubble-easy, .bubble-tip {{ background: #f1f3f5; padding: 8px 10px; border-radius: 6px; font-size: 12.5px; margin-top: 6px; color: #444; display: flex; align-items: flex-start; gap: 8px; }}
.bubble-easy .easy-label, .bubble-tip .syntax-label {{ flex-shrink: 0; margin-right: 0; font-size: 11px; padding: 2px 6px; }}

/* [Highlights & Badges] */
span[class^="highlight-"] {{ 
    border-radius: 4px; padding: 2px 4px; margin: 0 1px; 
    -webkit-box-decoration-break: clone; box-decoration-break: clone; 
    position: relative; z-index: 1; 
}}
span[class^="highlight-"]::before {{ content: none; display: none; }}

.highlight-subject {{ background-color: #fff9c4; border-bottom: 2px solid #fbc02d; }}
.highlight-feature {{ background-color: #fff9c4; border-bottom: 2px solid #fbc02d; }}
.highlight-clue {{ background-color: #e3f2fd; border-bottom: 2px solid #64b5f6; }}

.fill-text {{ font-weight: 900; text-decoration: underline; text-decoration-thickness: 2px; }}

.badge-them {{ display: inline-block; font-size: 11px; background-color: #7e57c2; color: #fff; padding: 2px 6px; border-radius: 4px; margin-right: 6px; font-weight: bold; vertical-align: 2px; font-family: var(--font-kor); }}
.badge-key {{ display: inline-block; font-size: 11px; background-color: #0277bd; color: #fff; padding: 2px 6px; border-radius: 4px; margin-right: 6px; font-weight: bold; vertical-align: 2px; font-family: var(--font-kor); }}
.header-badge-them {{ font-size: 12px; background-color: #ffebee; color: #c62828; border: 1px solid #ef9a9a; padding: 2px 8px; border-radius: 12px; margin-left: 8px; vertical-align: middle; font-weight: bold; }}
.header-badge-key {{ font-size: 12px; background-color: #fffde7; color: #f57f17; border: 1px solid #fff59d; padding: 2px 8px; border-radius: 12px; margin-left: 5px; vertical-align: middle; font-weight: bold; }}

/* [Interlinear Vocab] */
.vocab-container {{ display: inline; position: relative; text-indent: 0; line-height: 1.0; }}
.vocab-text {{ color: inherit; border-bottom: 1px dotted #bbb; font-weight: inherit; }}
.vocab-sub {{ position: absolute; top: 100%; left: 50%; transform: translateX(-50%); width: max-content; margin-top: 1px; font-size: 9px; color: #d32f2f; background-color: transparent; text-shadow: 1px 1px 0 #eeeeee, -1px -1px 0 #eeeeee, 1px -1px 0 #eeeeee, -1px 1px 0 #eeeeee; padding: 0 1px; font-weight: bold; font-family: var(--font-kor); z-index: 10; line-height: 1.1; pointer-events: none; }}

/* [Syntax Parsing] */
.syntax-box {{ display: inline; position: relative; padding-bottom: 1px; margin-right: 1px; border-bottom: none; -webkit-box-decoration-break: clone; box-decoration-break: clone; }}
.syntax-box::before {{ position: absolute; top: -3px; left: 0; font-size: 6px; font-weight: normal; font-family: sans-serif; line-height: 1; }}

/* 영어 문장 성분: 색상 적용 & 볼드체 해제(normal) - 절대 방어 !important 추가 */
.S-box {{ color: var(--c-S) !important; font-weight: normal !important; }} .S-box::before {{ content: 'S'; color: var(--c-S); }}
.V-box {{ color: var(--c-V) !important; font-weight: normal !important; }} .V-box::before {{ content: 'V'; color: var(--c-V); }}
.O-box {{ color: var(--c-O) !important; font-weight: normal !important; }} .O-box::before {{ content: 'O'; color: var(--c-O); }}
.C-box {{ color: var(--c-C) !important; font-weight: normal !important; }} .C-box::before {{ content: 'C'; color: var(--c-C); }}
.M-box {{ color: var(--c-M) !important; font-weight: normal !important; }} .M-box::before {{ content: 'M'; color: var(--c-M); }}
.con-box {{ color: var(--c-con) !important; font-weight: normal !important; }} .con-box::before {{ content: "con"; color: var(--c-con); }}
.IO-box {{ color: var(--c-O) !important; font-weight: normal !important; }} .IO-box::before {{ content: 'IO'; color: var(--c-O); }}
.DO-box {{ color: var(--c-O) !important; font-weight: normal !important; }} .DO-box::before {{ content: 'DO'; color: var(--c-O); }}

/* 한글 문장 성분: 색상 적용 & 무조건 볼드체(900) 강제 적용 */
.S-text {{ color: var(--c-S) !important; font-weight: 900 !important; }}
.V-text {{ color: var(--c-V) !important; font-weight: 900 !important; }}
.O-text {{ color: var(--c-O) !important; font-weight: 900 !important; }}
.C-text {{ color: var(--c-C) !important; font-weight: 900 !important; }}
.M-text {{ color: var(--c-M) !important; font-weight: 900 !important; }}
.con-text {{ color: var(--c-con) !important; font-weight: 900 !important; }}
.IO-text {{ color: var(--c-O) !important; font-weight: 900 !important; }}
.DO-text {{ color: var(--c-O) !important; font-weight: 900 !important; }}

/* [Analysis Card] */
.analysis-card {{ margin-bottom: 10px; border-bottom: 1px dashed #ddd; background-color: #fff; padding: 8px; border-radius: 4px; break-inside: avoid; }}
.analysis-card.card-them {{ background-color: #fff; border: 2px solid #e53935; border-left: 6px solid #e53935; border-bottom: 2px solid #e53935; box-shadow: 0 2px 8px rgba(229, 57, 53, 0.1); }}
.analysis-card.card-key {{ background-color: #fff; border: 2px solid #fbc02d; border-left: 6px solid #fbc02d; border-bottom: 2px solid #fbc02d; box-shadow: 0 2px 8px rgba(251, 192, 45, 0.1); }}

.analysis-card.bg-intro {{ background-color: #f0f7ff; border: 1px solid #bbdefb; }}
.analysis-card.bg-body {{ background-color: #fffbf2; border: 1px solid #ffecb3; }}
.analysis-card.bg-conc {{ background-color: #f3fcf5; border: 1px solid #c8e6c9; }}

.analysis-card.card-them {{ border: 2px solid #e53935; border-left: 6px solid #e53935; border-bottom: 2px solid #e53935; }}
.analysis-card.card-key {{ border: 2px solid #fbc02d; border-left: 6px solid #fbc02d; border-bottom: 2px solid #fbc02d; }}

/* 1페이지 영어 문장 및 한글 해석 청크 단위 상하 배치 (Flex Column) 레이아웃 적용 */
.eng-sent {{ font-family: var(--font-eng); font-size: 22.5px; background-color: transparent; padding: 4px 12px; border-left: 4px solid var(--c-S); position: relative; margin-top: 15px; margin-bottom: 15px; line-height: 2.3; color: #5d4037; display: flex; flex-wrap: wrap; align-items: flex-start; }}
.chunk-pair {{ display: flex; flex-direction: column; vertical-align: top; margin-right: 6px; margin-bottom: 12px; max-width: 100%; }}
.eng-chunk {{ background-color: #f4f4f4; padding: 2px 8px; border-radius: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); border: 1px solid #e0e0e0; word-break: keep-all; mix-blend-mode: multiply; color: #5d4037; }}
.kor-chunk {{ font-family: var(--font-kor); font-size: 19px; color: #5d4037; font-weight: 900; padding-left: 4px; margin-top: 6px; line-height: 1.4; word-break: keep-all; letter-spacing: -0.5px; }}
.slash-divider {{ color: #ccc; font-weight: 300; margin: 0 4px; font-size: 24px; margin-top: 4px; display: flex; align-items: center; }}
.num-badge {{ display: inline-block; background-color: #333; color: #fff; border-radius: 50%; width: 22px; height: 22px; text-align: center; line-height: 22px; font-size: 13px; font-weight: bold; margin-right: 0px; vertical-align: 1px; box-shadow: 1px 1px 2px rgba(0,0,0,0.2); font-family: var(--font-kor); }}

/* 기존에 사용하던 통짜 1페이지 한글 해석 렌더링 스타일 (사용 안하지만 예비용으로 유지) */
.kor-sent, .kor-sent * {{ font-size: 19px; color: #5d4037; font-weight: 900 !important; line-height: 2.0; word-break: keep-all; }}
.kor-sent {{ padding-left: 5px; margin-bottom: 3px; display: none; }}

.analysis-footer {{ margin-top: 8px; font-size: 13px; line-height: 1.7; word-break: keep-all; }}

/* [Easy Explanation] */
.easy-exp-box {{ display: inline-block; position: relative; background: #f5f5f5; border: 2px solid #e0e0e0; border-radius: 12px; padding: 8px 12px; margin-top: 12px; margin-bottom: 5px; font-size: 14px; color: #424242; line-height: 1.5; font-weight: 500; }}
.easy-exp-box::after, .easy-exp-box::before {{ bottom: 100%; left: 20px; border: solid transparent; content: " "; height: 0; width: 0; position: absolute; pointer-events: none; }}
.easy-exp-box::after {{ border-color: rgba(245, 245, 245, 0); border-bottom-color: #f5f5f5; border-width: 8px; margin-left: -8px; }}
.easy-exp-box::before {{ border-color: rgba(224, 224, 224, 0); border-bottom-color: #e0e0e0; border-width: 11px; margin-left: -11px; }}
.easy-label {{ display: inline-block; background-color: #757575; color: #fff; padding: 0px 4px; border-radius: 3px; margin-right: 5px; font-weight: bold; vertical-align: 1px; font-size: 11px; }}

/* [Syntax Tip] */
.syntax-tip {{ display: block; width: fit-content; max-width: 100%; margin-top: 6px; padding: 4px 8px; border: 1px solid #333; background-color: #fff; border-radius: 4px; font-size: 13px; color: #000; line-height: 1.4; box-shadow: 2px 2px 0px rgba(0,0,0,0.1); }}
.syntax-label {{ display: inline-block; background-color: #333; color: #fff; padding: 0px 4px; border-radius: 2px; margin-right: 5px; font-weight: bold; vertical-align: 1px; font-size: 11px; }}

/* [Exam Prediction Specifics] */
.exam-point-box {{ margin-top: 8px; padding: 8px 12px; background-color: #fffaf0; border: 1px dashed #f48fb1; border-radius: 6px; font-size: 12.5px; line-height: 1.5; color: #333; }}
.exam-badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #fff; margin-right: 6px; vertical-align: 1px; font-family: var(--font-kor); }}
.exam-badge-blank {{ background-color: #4caf50; }} /* Green */
.exam-badge-implied {{ background-color: #9c27b0; }} /* Purple */
.exam-badge-grammar {{ background-color: #f44336; }} /* Red */
.exam-target {{ font-weight: bold; color: #c2185b; text-decoration: underline; }}

/* [Visual Passage & Analysis Exam Highlights] */
.visual-exam-target {{ position: relative; }}
.visual-exam-label {{ position: absolute; bottom: 100%; left: 0; margin-bottom: 2px; font-size: 11px; color: #fff; padding: 2px 6px; border-radius: 4px; font-family: var(--font-kor); font-weight: 900; letter-spacing: 0.5px; box-shadow: 1px 1px 2px rgba(0,0,0,0.2); white-space: nowrap; line-height: 1; z-index: 5; }}

/* [Inline Syntax Tips for Page 1] */
.inline-syntax-target {{ position: relative; border-bottom: 2px dotted #333; background-color: rgba(0, 0, 0, 0.05); }}
/* 구문팁 배지를 검정색(#333)으로 통일 및 타겟 아래 오른쪽에 위치 */
.inline-syntax-label {{ position: absolute; top: 100%; right: 0; margin-top: 2px; font-size: 11px; background-color: #333; color: #fff; padding: 2px 5px; border-radius: 4px; font-family: var(--font-kor); font-weight: 900; white-space: nowrap; line-height: 1; z-index: 4; box-shadow: 1px 1px 2px rgba(0,0,0,0.2); }}


/* [CSAT Summary Image-style CSS] */
.csat-container {{ background-color: #fcfaf2; border: 1px solid #e0dcd0; padding: 20px; border-radius: 8px; margin-top: 20px; }}
.csat-header {{ display: flex; justify-content: space-between; align-items: center; padding-bottom: 10px; margin-bottom: 15px; }}
.csat-title {{ font-family: var(--font-kor); font-size: 16px; font-weight: 900; color: #333; display: flex; align-items: center; gap: 6px; }}
.csat-badge {{ background-color: #546e7a; color: white; font-size: 12px; padding: 2px 6px; border-radius: 4px; }}
.csat-subtitle {{ font-family: var(--font-kor); font-size: 12px; color: #7b909a; font-weight: bold; }}
.csat-text {{ font-family: var(--font-eng); font-size: 17px; line-height: 1.8; color: #222; margin-bottom: 25px; text-align: justify; }}
.csat-blank-ans {{ display: inline-block; border-bottom: 1px solid #333; min-width: 80px; text-align: center; font-weight: bold; color: #d32f2f; padding: 0 5px; }}
.csat-trans-header {{ font-family: var(--font-kor); font-size: 14px; font-weight: bold; color: #e6a822; margin-bottom: 10px; }}
.csat-trans-text {{ font-family: var(--font-kor); font-size: 14.5px; line-height: 32px; color: #444; background-image: repeating-linear-gradient(transparent, transparent 31px, #b0bec5 31px, #b0bec5 32px); background-position: 0 6px; padding-bottom: 8px; }}

.summary-badge {{ display: inline-block; font-family: var(--font-kor); font-size: 11px; color: #fff; background-color: #78909c; padding: 1px 8px; border-radius: 10px; font-weight: bold; margin-left: 6px; vertical-align: 1px; position: static; }}

/* [Logic Flow Side Display] */
.sent-container {{ display: flex; gap: 15px; align-items: flex-start; margin-bottom: 20px; }}
.sent-logic-col {{ flex: 0 0 130px; display: flex; flex-direction: column; gap: 10px; }}
.sent-analysis-col {{ flex: 1; min-width: 0; }}
.logic-flow-card {{ border-radius: 8px; padding: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border: 1px solid #eee; font-size: 13px; }}
.logic-intro {{ background: #e3f2fd; border-color: #90caf9; color: #1565c0; }}
.logic-body {{ background: #fff8e1; border-color: #ffe082; color: #ef6c00; }}
.logic-conc {{ background: #e8f5e9; border-color: #a5d6a7; color: #2e7d32; }}
.logic-title {{ font-weight: bold; display: block; margin-bottom: 4px; font-size: 14px; }}
.logic-desc {{ line-height: 1.4; color: #333; }}

.flow-container {{ display: flex; justify-content: space-between; gap: 15px; margin-top: 15px; margin-bottom: 25px; }}
.flow-card {{ flex: 1; background: #fff; border-radius: 12px; padding: 0; box-shadow: 0 4px 12px rgba(0,0,0,0.08); overflow: hidden; position: relative; border: 1px solid #eee; }}
.flow-card.flow-intro .flow-header {{ background: #e3f2fd; color: #1565c0; border-bottom: 2px solid #90caf9; }} 
.flow-card.flow-body .flow-header {{ background: #fff8e1; color: #ef6c00; border-bottom: 2px solid #ffe082; }} 
.flow-card.flow-conc .flow-header {{ background: #e8f5e9; color: #2e7d32; border-bottom: 2px solid #a5d6a7; }}
.flow-header {{ padding: 12px 15px; text-align: left; position: relative; }}
.flow-title {{ font-weight: 800; font-size: 15px; display: block; margin-bottom: 2px; }}
.flow-num-badge {{ display: inline-block; background: rgba(0,0,0,0.1); color: inherit; border-radius: 12px; padding: 1px 8px; font-size: 12px; font-weight: bold; margin-top: 4px; }}
.flow-content {{ padding: 15px; font-size: 13.5px; color: #444; line-height: 1.5; text-align: left; }}
.flow-arrow {{ align-self: center; font-size: 24px; color: #bdbdbd; font-weight: bold; flex-basis: 20px; text-align: center; }}


/* ================= 3페이지 단어장(Vocab) Section CSS ================= */
.sec-vocab {{ flex: 1.25; display: flex; flex-direction: column; margin-top: 0px; border: 1px solid #cfd8dc; border-radius: 8px; overflow: hidden; }}
.v-header {{ display: flex; background: #37474f; color: white; font-family: var(--font-eng, 'Montserrat', sans-serif); font-size: 11px; font-weight: 700; padding: 6px 0; border-bottom: 1px solid #cfd8dc; }}
.v-list {{ flex: 1; display: flex; flex-direction: column; overflow-y: hidden; background: white; }}
.v-row {{ display: flex; align-items: stretch; border-bottom: 1px solid #eceff1; padding: 0; min-height: 32px; flex: 1; }}
.v-row:nth-child(even) {{ background-color: #fafafa; }} 

.cell {{ display: flex; align-items: center; padding: 1px 8px; box-sizing: border-box; overflow: hidden; }}
.cell.col-word, .cell.col-mean, .cell.col-context {{ border-right: 1px solid rgba(0,0,0,0.05); }}
.v-header .cell {{ justify-content: center; padding: 3px 8px; text-align: center; }}
.v-header .cell.col-word, .v-header .cell.col-mean, .v-header .cell.col-context {{ border-right: 1px solid rgba(255,255,255,0.2); }}
.cell:last-child {{ border-right: none; }}

/* 열 너비 조정 */
.col-chk {{ width: 30px; justify-content: center; flex-shrink: 0; }}
.col-word {{ width: 16%; flex-shrink: 0; flex-direction: column; align-items: flex-start; padding-top: 8px; padding-bottom: 8px; }}
.col-mean {{ width: 38%; flex-shrink: 0; flex-direction: column; align-items: flex-start; padding-top: 8px; padding-bottom: 8px; }}
.col-context {{ width: 14%; flex-shrink: 0; flex-direction: column; align-items: flex-start; padding-top: 8px; padding-bottom: 8px; }}
.col-chunk {{ flex: 1; flex-direction: column; align-items: flex-start; padding-top: 8px; padding-bottom: 8px; }}

.v-row .col-chk {{ padding-top: 8px; align-items: flex-start; }}

.chk-box {{ width: 10px; height: 10px; border: 1px solid var(--c-brand, #003b6f); border-radius: 2px; background: white; margin-top:4px; }}
.word-txt {{ font-family: var(--font-eng, 'Montserrat', sans-serif); font-weight: 900; color: var(--c-brand, #003b6f); font-size: 16px; word-break: break-word; line-height: 1.2; }} 
.word-pron {{ font-size: 12px; color: #616161; font-family: var(--font-eng); margin-top: 3px; }}

/* 2페이지 어원(Etymology) 렌더링을 위한 CSS */
.word-ety {{ font-size: 11px; color: #8d6e63; font-family: var(--font-kor); margin-top: 3px; font-weight: 600; letter-spacing: -0.5px; word-break: keep-all; line-height: 1.2; }}

.vm-kor {{ font-weight: 800; color: #212121; font-size: 13.5px; line-height: 1.3; font-family: 'NanumSquareRound', sans-serif; display: block; width: 100%; }}
.vm-context {{ font-size: 12.5px; color: #00695c; line-height: 1.4; font-weight: bold; white-space: normal; word-break: keep-all; display: block; width: 100%; }}

.vch-en {{ font-family: var(--font-eng, 'Montserrat', sans-serif); font-weight: 600; color: var(--c-chunk-text, #263238); font-size: 14.5px; line-height: 1.3; margin-bottom: 3px; }}
.vch-ko {{ font-size: 13.5px; color: #78909c; line-height: 1.2; font-family: 'NanumSquareRound', sans-serif; }}
.c-hl {{ color: var(--c-chunk-hl, #d84315); font-weight: 900; }} 

/* 유의어, 반의어, 혼동어휘 뱃지 시스템 */
.rel-box {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; width: 100%; }}
.rel-item {{ display: inline-flex; align-items: center; font-size: 13.5px; font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; background: #f5f5f5; padding: 3px 6px; border-radius: 4px; line-height: 1; }}
.item-syn {{ color: #1b5e20; font-weight: 900; }}
.item-ant {{ color: #d32f2f; font-weight: 600; }} 
.item-conf {{ color: #333; font-weight: 900; }} 
.rel-item span {{ margin-right: 4px; font-size: 12px; padding: 2px 4px; border-radius: 2px; color: white; font-family: var(--font-kor); font-weight: bold; }}

.bg-syn {{ background-color: #26a69a; }} 
.bg-ant {{ background-color: #ef5350; }} 
.bg-conf {{ background-color: #ffa726; }} 

/* [모달창 전용 Vocabulary Table] */
table.modal-table {{ width: 100%; border-collapse: collapse; font-size: 13px; table-layout: fixed; border: 1px solid #e0e0e0; }}
table.modal-table th {{ background: #eee; padding: 6px; border: 1px solid #ccc; text-align: center; font-family: var(--font-kor); color:#444; }}
table.modal-table td {{ padding: 6px; border: 1px solid #ccc; vertical-align: middle; word-wrap: break-word; background:#fff; text-align:center; }}
table.modal-table td:nth-child(6) {{ text-align: left; }} 
table.modal-table td:nth-child(7) {{ text-align: left; }} 
table.modal-table col:nth-child(1) {{ width: 12%; }} 
table.modal-table col:nth-child(2) {{ width: 12%; }} 
table.modal-table col:nth-child(3) {{ width: 12%; }} 
table.modal-table col:nth-child(4) {{ width: 12%; }} 
table.modal-table col:nth-child(5) {{ width: 8%; }}  
table.modal-table col:nth-child(6) {{ width: 20%; }} 
table.modal-table col:nth-child(7) {{ width: 24%; }} 
.vocab-word-bold {{ font-weight: 900; font-family: var(--font-eng); color: #000; font-size: 16px; }}
.vocab-pron {{ color: #555; font-size: 12px; }}

.analysis-table {{ width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13px; border: 1px solid #e0e0e0; }}
.analysis-table th {{ background: #546e7a; color: #fff; padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold; }}
.analysis-table td {{ padding: 8px; border: 1px solid #ddd; vertical-align: middle; background: #fff; text-align: left; }}

/* [Special Tags] */
.slash {{ font-weight: 900; color: #000; margin: 0 3px; font-size: 1.1em; }}
.blank-filled {{ border-bottom: 2px solid #000; font-weight: 900; color: #000; padding: 0 2px; }}
.blank-empty {{ display: inline-block; width: 40px; height: 18px; border-bottom: 1px solid #333; vertical-align: middle; margin: 0 2px; }}
.err-wrong {{ color: #d32f2f; text-decoration: line-through; margin-right: 3px; }}
.err-right {{ color: #1565c0; font-weight: 900; margin-left: 3px; }}
.err-arrow {{ color: #555; font-size: 0.9em; font-weight: bold; }}
.star-red {{ color: #e53935; text-shadow: 1px 1px 0px #b71c1c; font-size: 1.1em; margin-right: 5px; vertical-align: -1px; }}
.star-yellow {{ color: #fbc02d; text-shadow: 1px 1px 0px #f57f17; font-size: 1.1em; margin-right: 5px; vertical-align: -1px; }}
</style>
</head>
<body>

<div class="header-container">
    <button class="header-btn btn-literal" onclick="toggleModal('modalLiteral')">직독직해 (Literal)</button>
    <div class="custom-modal modal-right modal-literal" id="modalLiteral">
        <span class="close-modal-btn" onclick="toggleModal('modalLiteral')">&times;</span>
        <h3>🔍 직독직해 (Literal)</h3>
        <div class="modal-content">{literal_translation_text}</div>
    </div>

    <button class="header-btn btn-liberal" onclick="toggleModal('modalLiberal')">전체 해석 (의역)</button>
    <div class="custom-modal modal-right modal-liberal" id="modalLiberal">
        <span class="close-modal-btn" onclick="toggleModal('modalLiberal')">&times;</span>
        <h3>📜 전체 해석 (의역)</h3>
        <div class="modal-content">{full_translation_text}</div>
    </div>

    <button class="header-btn btn-tips" onclick="toggleModal('modalTips')">구문 팁 정리</button>
    <div class="custom-modal modal-right modal-tips" id="modalTips">
        <span class="close-modal-btn" onclick="toggleModal('modalTips')">&times;</span>
        <h3>💡 구문 팁 정리</h3>
        <div class="modal-content">{syntax_tips_text}</div>
    </div>

    <button class="header-btn btn-logic" onclick="toggleModal('modalLogic')">3단 논리 흐름</button>
    <div class="custom-modal modal-right modal-logic" id="modalLogic">
        <span class="close-modal-btn" onclick="toggleModal('modalLogic')">&times;</span>
        <h3>📉 3단 논리 흐름</h3>
        <div class="modal-content">{logic_modal_content}</div>
    </div>

    <button class="header-btn btn-eng-all" onclick="toggleModal('modalEngAll')">영어 문장 전체 보기</button>
    <div class="custom-modal modal-left modal-eng-all" id="modalEngAll">
        <span class="close-modal-btn" onclick="toggleModal('modalEngAll')">&times;</span>
        <h3>🇺🇸 영어 문장 전체 보기</h3>
        <div class="modal-content">{english_sentences_text}</div>
    </div>

    <button class="header-btn btn-eng-pure" onclick="toggleModal('modalEngPure')">지문 읽기 (Pure)</button>
    <div class="custom-modal modal-left modal-eng-pure" id="modalEngPure">
        <span class="close-modal-btn" onclick="toggleModal('modalEngPure')">&times;</span>
        <h3>📖 지문 읽기 (Pure English)</h3>
        <div class="modal-content">{raw_english_text}</div>
    </div>

    <button class="header-btn btn-vis-clean" onclick="toggleModal('modalVisClean')">지문 원문 (Clean)</button>
    <div class="custom-modal modal-left modal-vis-clean" id="modalVisClean">
        <span class="close-modal-btn" onclick="toggleModal('modalVisClean')">&times;</span>
        <h3>📄 지문 원문 (Clean)</h3>
        <div class="modal-content visual-source-text">{visual_clean_text}</div>
    </div>

    <button class="header-btn btn-learning" onclick="toggleModal('modalLearning')">📚 핵심 콕콕</button>
    <div class="custom-modal modal-left modal-learning" id="modalLearning">
        <span class="close-modal-btn" onclick="toggleModal('modalLearning')">&times;</span>
        <h3>📚 핵심 콕콕 (Logic & Grammar)</h3>
        <div class="modal-content">
            <div class="learning-item">
                <span class="learning-label logic-label">논리</span>
                <ul class="learning-list">{learning_logic_html}</ul>
            </div>
            <div class="learning-item">
                <span class="learning-label grammar-label">구문</span>
                <ul class="learning-list">{learning_grammar_html}</ul>
            </div>
        </div>
    </div>

    <button class="header-btn btn-vocab" onclick="toggleModal('modalVocab')">📚 핵심 어휘</button>
    <div class="custom-modal modal-center modal-vocab" id="modalVocab">
        <span class="close-modal-btn" onclick="toggleModal('modalVocab')">&times;</span>
        <h3>📚 핵심 어휘 10선</h3>
        <div class="modal-content">{vocab_modal_content}</div>
    </div>

    <button class="header-btn btn-keys" onclick="toggleModal('modalKeys')">🗝️ 핵심 문장</button>
    <div class="custom-modal modal-center modal-keys" id="modalKeys">
        <span class="close-modal-btn" onclick="toggleModal('modalKeys')">&times;</span>
        <h3>🗝️ 핵심 문장 3개</h3>
        <div class="modal-content">{key_sent_modal_content}</div>
    </div>

    <button class="header-btn btn-ans" onclick="toggleModal('modalAns')">✅ 정답 및 해설</button>
    <div class="custom-modal modal-center modal-ans" id="modalAns">
        <span class="close-modal-btn" onclick="toggleModal('modalAns')">&times;</span>
        <h3>✅ 정답 및 해설</h3>
        <div class="modal-content">{answer_modal_content}</div>
    </div>

    <button class="header-btn btn-opts" onclick="toggleModal('modalOpts')">선택지 분석</button>
    <div class="custom-modal modal-center modal-opts" id="modalOpts">
        <span class="close-modal-btn" onclick="toggleModal('modalOpts')">&times;</span>
        <h3>🧐 선택지 분석</h3>
        <div class="modal-content">{options_modal_content}</div>
    </div>

    <button class="header-btn btn-exam" onclick="toggleModal('modalExam')">🚨 내신 출제 포인트</button>
    <div class="custom-modal modal-center modal-exam" id="modalExam">
        <span class="close-modal-btn" onclick="toggleModal('modalExam')">&times;</span>
        <h3>🚨 내신 변형 문제 예측 5선</h3>
        <div class="modal-content">{exam_modal_content}</div>
    </div>

    <div class="info-group">
        {difficulty_html}

        <div class="ri-item ri-material">
            <span class="ri-label">📌 소재</span>
            {clue_material} {header_badges}
        </div>
        <div class="ri-item ri-guide">
            <span class="ri-label">🗣️ 수업 가이드</span>
            {scenario_guide}
        </div>
        <div class="ri-item ri-tip">
            <span class="ri-label">💡 집중 Tip</span>
            {scenario_tip}
        </div>
    </div>
    <div class="topic-box" style="margin-top: 15px;">
        <strong style="font-size:17.5px;">📌 Topic & Summary</strong><br>
        <div style="margin-top:6px;">{topic_summary}</div>
    </div>
</div>

<div class="top-container">
    {sentence_analysis_html}
</div>

<div class="bottom-container">
    <div class="b-left">
        <div class="info-group">
            <div class="ri-item ri-material">
                <span class="ri-label">📌 소재</span>
                {clue_material} {header_badges}
            </div>
            <div class="ri-item ri-guide">
                <span class="ri-label">🗣️ 수업 가이드</span>
                {scenario_guide}
            </div>
            <div class="ri-item ri-tip">
                <span class="ri-label">💡 집중 Tip</span>
                {scenario_tip}
            </div>
        </div>

        <div class="topic-box">
            <strong style="font-size:17.5px;">📌 Topic & Summary</strong><br>
            <div style="margin-top:6px;">{topic_summary}</div>
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

        <div class="box-style options-box">
            <strong style="font-size:14px; display:block; margin-bottom:15px; border-bottom:1px solid #ddd; padding-bottom:5px;">🧐 선택지 분석 (Why & Why not?)</strong>
            {options_html}
        </div>

        <div class="logic-box">
            <strong>🔗 문장별 논리 전개 (Micro Flow)</strong>
            {logic_map_text}
        </div>

        <div class="scenario-box">
            <div class="scene-header">🎯 지문 마킹 시뮬레이션</div>
            <div class="scene-content">{scenario_sim}</div>
        </div>

        <div class="box-style learning-box">
            <strong style="font-size:14px; display:block; margin-bottom:10px; border-bottom:1px solid #ddd; padding-bottom:5px;">🎯 Learning Points (핵심 콕콕)</strong>
            <div class="learning-item">
                <span class="learning-label logic-label">논리</span>
                <ul class="learning-list">{learning_logic_html}</ul>
            </div>
            <div class="learning-item">
                <span class="learning-label grammar-label">구문</span>
                <ul class="learning-list">{learning_grammar_html}</ul>
            </div>
        </div>

        {csat_summary_html}

    </div>

    <div class="b-right">
        <strong style="font-size:14px; display:block; margin-bottom:15px;">📈 글의 흐름 (3단 구조)</strong>
        <div class="flow-container">
            {three_stage_flow_html}
        </div>

        <div class="question-header" style="margin-top: 40px;">{question_header} <span class="source-tag">{source_origin}</span></div>
        <div class="source-text">{visual_passage}</div>

        <span class="table-label" style="display:block; margin-top:30px; margin-bottom:10px; font-weight:bold;">📚 Vocabulary</span>
        {vocab_block}

        <span class="table-label" style="display:block; margin-top:30px; margin-bottom:10px; font-weight:bold;">📌 Key Sentences Analysis</span>
        <table class="analysis-table">
            <colgroup><col width="12%"> <col width="10%"> <col width="35%"> <col width="25%"> <col width="18%"></colgroup>
            <thead><tr><th style="text-align:center;">출처</th><th style="text-align:center;">종류</th><th style="text-align:center;">영어 문장</th><th style="text-align:center;">한글 해석</th><th style="text-align:center;">선정 사유</th></tr></thead>
            <tbody>{key_sentence_rows}</tbody>
        </table>

        <span class="table-label" style="display:block; margin-top:30px; margin-bottom:10px; font-weight:bold;">📌 True / False 문제 분석</span>
        {true_false_html}

        <span class="table-label" style="display:block; margin-top:30px; margin-bottom:10px; font-weight:bold;">📌 영영 풀이 (English Definitions)</span>
        {eng_def_html}
    </div>
</div>

<script>
// [Interactive Numbering]
function toggleBubble(element) {{
    const all = document.querySelectorAll('.interactive-num');
    const wasActive = element.classList.contains('active');
    all.forEach(el => el.classList.remove('active'));
    if (!wasActive) {{
        element.classList.add('active');
    }}
}}

document.addEventListener('click', function(event) {{
    if (!event.target.closest('.interactive-num')) {{
        const all = document.querySelectorAll('.interactive-num');
        all.forEach(el => el.classList.remove('active'));
    }}
}});

// [Modal Logic with Z-Index]
let currentZIndex = 1000; 

function toggleModal(modalId) {{
    const modal = document.getElementById(modalId);
    if (modal.style.display === 'block') {{
        modal.style.display = 'none';
    }} else {{
        currentZIndex++; 
        modal.style.zIndex = currentZIndex;
        modal.style.display = 'block';
    }}
}}
</script>

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
            # HTML 태그 보호 (?![^<]*>) 유지하여 span이나 class 같은 명령어에 뜻이 달리는 것 방지
            pattern = re.compile(rf'\b({re.escape(raw_word)})\b(?![^<]*>)', re.IGNORECASE)
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


def strip_all_tags(text):
    text = re.sub(r'\[/?[^\]]+\]', '', text)
    text = re.sub(r'《/?[^》]+》', '', text)
    text = text.replace('/', '')
    text = text.replace('★', '')
    text = re.sub(r'[❶❷❸❹❺❻❼❽❾❿⓫⓬⓭⓮⓯⓰⓱⓲⓳⓴]', '', text)
    return ' '.join(text.split())


def preprocess_multiline_tags(text):
    highlight_tags = ['subject', 'keyword', 'feature', 'clue', 'clue1', 'clue2', 'INCORRECT', 'highlight', 'strike',
                      'delete', '무관한문장', 'irrelevant']
    icon_tags = ['Them sentence', 'Theme sentence', 'Key sentence', 'Key sentence ']

    all_tags = highlight_tags + icon_tags

    for tag in all_tags:
        clean_tag = tag.strip()
        pattern = re.compile(rf'(《{tag}》)(.*?)(《\/{clean_tag}》)', re.DOTALL)

        def replacer(match):
            open_t = match.group(1)
            content = match.group(2)
            close_t = match.group(3)

            if '\n' in content:
                parts = content.split('\n')

                if tag in icon_tags:
                    wrapped = []
                    wrapped.append(f"{open_t}{parts[0]}{close_t}")
                    for p in parts[1:]:
                        wrapped.append(p)
                    return '\n'.join(wrapped)
                else:
                    wrapped = [f"{open_t}{p}{close_t}" for p in parts]
                    return '\n'.join(wrapped)

            return match.group(0)

        text = pattern.sub(replacer, text)

    return text


def strip_syntax_tags(text):
    syntax_tags = ['S', 'V', 'O', 'C', 'OC', 'M', 'con', 'IO', 'DO']
    for tag in syntax_tags:
        pattern = re.compile(rf'\[\/?{tag}\]', re.IGNORECASE)
        text = pattern.sub('', text)
    return text


def convert_common_tags(text):
    text = text.replace('<u>', '<span class="text-underline">').replace('</u>', '</span>')
    text = text.replace(' / ', ' <span class="slash">/</span> ')
    text = text.replace(' /', ' <span class="slash">/</span>')

    text = re.sub(r'《Them sentence》(.*?)《/Them sentence》', r'__STAR_RED__\1', text, flags=re.DOTALL)
    text = re.sub(r'《Theme sentence》(.*?)《/Theme sentence》', r'__STAR_RED__\1', text, flags=re.DOTALL)
    text = re.sub(r'《Key sentence》(.*?)《/Key sentence》', r'__STAR_YELLOW__\1', text, flags=re.DOTALL)
    text = re.sub(r'《Key sentence 》(.*?)《/Key sentence 》', r'__STAR_YELLOW__\1', text, flags=re.DOTALL)

    text = re.sub(r'《subject》(.*?)《/subject》', r'<span class="highlight-subject">\1</span>', text, flags=re.DOTALL)
    text = re.sub(r'《keyword》(.*?)《/keyword》', r'<span class="highlight-subject">\1</span>', text, flags=re.DOTALL)
    text = re.sub(r'《feature》(.*?)《/feature》', r'<span class="highlight-feature">\1</span>', text, flags=re.DOTALL)
    text = re.sub(r'《clue》(.*?)《/clue》', r'<span class="highlight-clue">\1</span>', text, flags=re.DOTALL)
    text = re.sub(r'《clue1》(.*?)《/clue1》', r'<span class="highlight-clue">\1</span>', text, flags=re.DOTALL)
    text = re.sub(r'《clue2》(.*?)《/clue2》', r'<span class="highlight-clue">\1</span>', text, flags=re.DOTALL)

    text = re.sub(r'《BLANK》(.+?)《/BLANK》', r'<span class="blank-filled">\1</span>', text)
    text = re.sub(r'《BLANK》\s*《/BLANK》', '<span class="blank-empty"></span>', text)

    def replace_incorrect(m):
        wrong = m.group(1)
        correction_part = m.group(2)
        if correction_part:
            right = correction_part.replace(':', '').strip()
            if right:
                return f'<span class="err-wrong">{wrong}</span><span class="err-arrow">→</span><span class="err-right">{right}</span>'
        return f'<span class="err-wrong">{wrong}</span>'

    text = re.sub(r'《INCORRECT》(.*?)《/INCORRECT》(\s*:\s*[^《<\[\n]+)?', replace_incorrect, text)

    text = re.sub(r'《(?:strike|delete|무관한문장|irrelevant)》(.*?)《/(?:strike|delete|무관한문장|irrelevant)》',
                  r'<span class="err-wrong">\1</span>', text, flags=re.IGNORECASE)
    text = re.sub(r'<(?:s|strike)>(.*?)</(?:s|strike)>', r'<span class="err-wrong">\1</span>', text,
                  flags=re.IGNORECASE)

    text = re.sub(r'《fill》(.*?)《/fill》', r'<span class="fill-text">\1</span>', text, flags=re.DOTALL)

    text = text.replace('★', '<span class="star-yellow">★</span>')
    text = text.replace('__STAR_RED__', '<span class="star-red">★</span>')
    text = text.replace('__STAR_YELLOW__', '<span class="star-yellow">★</span>')

    return text


def convert_eng_tags(text):
    text = convert_common_tags(text)
    text = re.sub(r'\[/?M\]', '', text, flags=re.IGNORECASE)
    tags = {'S': 'S', 'V': 'V', 'O': 'O', 'C': 'C', 'OC': 'C', 'con': 'con', 'IO': 'IO', 'DO': 'DO'}
    for _ in range(3):
        for tag, cls_prefix in tags.items():
            pattern = re.compile(rf'\[{tag}\](.*?)\[/{tag}\]', re.IGNORECASE | re.DOTALL)
            text = pattern.sub(rf'<span class="syntax-box {cls_prefix}-box">\1</span>', text)
    return text


def convert_kor_tags(text):
    text = convert_common_tags(text)
    text = re.sub(r'\[/?M\]', '', text, flags=re.IGNORECASE)
    tags = {'S': 'S', 'V': 'V', 'O': 'O', 'C': 'C', 'OC': 'C', 'con': 'con', 'IO': 'IO', 'DO': 'DO'}
    for _ in range(3):
        for tag, cls_prefix in tags.items():
            pattern = re.compile(rf'\[{tag}\](.*?)\[/{tag}\]', re.IGNORECASE | re.DOTALL)
            text = pattern.sub(rf'<span class="{cls_prefix}-text">\1</span>', text)
    return text


def smart_replace(text, word, replacement_format):
    if ' ' in word:
        parts = word.split()
        verb = parts[0]
        particle = " ".join(parts[1:])
        roots = [verb]
        if len(verb) > 3: roots.append(verb[:-1])
        if len(verb) > 4: roots.append(verb[:-2])
        for root in roots:
            pattern_str = r"\b" + re.escape(root) + r"\w*\s+(?:[\w']+\s+){0,4}" + re.escape(particle) + r"\b(?![^<]*>)"
            pattern = re.compile(pattern_str, re.IGNORECASE)
            if pattern.search(text):
                return pattern.sub(lambda m: replacement_format.format(m.group()), text)
    else:
        roots = [word]
        if len(word) > 3: roots.append(word[:-1])
        if len(word) > 4: roots.append(word[:-2])
        for root in roots:
            pattern_str = r"\b" + re.escape(root) + r"\w*(?![^<]*>)"
            pattern = re.compile(pattern_str, re.IGNORECASE)
            if pattern.search(text):
                return pattern.sub(lambda m: replacement_format.format(m.group()), text)
    return text


def make_visual_interactive(text, sentences):
    num_map = {
        '❶': 1, '❷': 2, '❸': 3, '❹': 4, '❺': 5,
        '❻': 6, '❼': 7, '❽': 8, '❾': 9, '❿': 10,
        '⓫': 11, '⓬': 12, '⓭': 13, '⓮': 14, '⓯': 15,
        '⓰': 16, '⓱': 17, '⓲': 18, '⓳': 19, '⓴': 20
    }

    def get_bubble_html(n):
        for s in sentences:
            if str(s.get('num')) == str(n):
                raw_eng = s.get('eng_analyzed', '').replace('\\n', '\n')
                eng_html = convert_eng_tags(raw_eng)
                raw_kor = s.get('kor_translation', '').replace('\\n', '\n')
                kor_html = convert_kor_tags(raw_kor)
                summary = s.get('summary_mark', '')
                if summary:
                    kor_html += f" <span class='summary-badge'>{summary}</span>"
                easy = s.get('easy_exp', '')

                raw_tip = s.get('syntax_tip', '')
                if isinstance(raw_tip, list):
                    tip_lines = []
                    for tip_item in raw_tip:
                        if isinstance(tip_item, dict):
                            tag = tip_item.get('tag', '')
                            target = tip_item.get('target', '')
                            exp = tip_item.get('explanation', '')
                            tip_lines.append(f"{tag} <b>{target}</b>: {exp}")
                        else:
                            tip_lines.append(str(tip_item))
                    tip = "<br>".join(tip_lines)
                else:
                    tip = str(raw_tip).replace('\\n', '\n')

                bubble_content = f'<div class="bubble-eng">{eng_html}</div><div class="bubble-kor">{kor_html}</div>'
                if easy:
                    bubble_content += f'<div class="bubble-easy"><span class="easy-label">쉬운풀이</span><div>{easy}</div></div>'
                if tip:
                    bubble_content += f'<div class="bubble-tip"><span class="syntax-label">구문팁</span><div>{tip}</div></div>'

                return bubble_content
        return ""

    def replace_match(match):
        char = match.group(0)
        num = num_map.get(char)
        if not num: return char
        content = get_bubble_html(num)
        if not content: return char
        return f'<span class="interactive-num" onclick="toggleBubble(this)">{char}<span class="translation-bubble">{content}</span></span>'

    pattern = re.compile(r'[❶❷❸❹❺❻❼❽❾❿⓫⓬⓭⓮⓯⓰⓱⓲⓳⓴]')
    return pattern.sub(replace_match, text)


def repair_html_content(html_text):
    html_text = re.sub(r'《/?[^》]+》', '', html_text)
    html_text = re.sub(r'\[/?[A-Za-z0-9]+\]', '', html_text)

    if BeautifulSoup:
        soup = BeautifulSoup(html_text, 'html.parser')
        return str(soup)

    return html_text


def highlight_chunk_word(target_word, full_sentence):
    if not target_word or not full_sentence: return full_sentence

    clean_word = re.sub(r'\(.*?\)', '', str(target_word).lower().strip()).strip()
    base = clean_word

    if len(base) > 3:
        if base.endswith('y'):
            base = base[:-1]
        elif base.endswith('e'):
            base = base[:-1]
        elif base.endswith('s'):
            base = base[:-1]

    pattern = r'\b' + re.escape(base) + r'[a-z]*'

    try:
        return re.sub(pattern, lambda m: f'<span class="c-hl">{m.group()}</span>', full_sentence, flags=re.IGNORECASE)
    except:
        return full_sentence


def get_shrink_style(text, max_len=20, base_size=13.5):
    t_len = len(text)
    style = ""
    if t_len > 35:
        style += f"font-size: {max(9.0, base_size - 3.0)}px; letter-spacing: -0.5px;"
    elif t_len > 26:
        style += f"font-size: {max(10.0, base_size - 2.0)}px; letter-spacing: -0.3px;"
    elif t_len > max_len:
        style += f"font-size: {max(11.5, base_size - 1.0)}px; letter-spacing: -0.2px;"
    else:
        style += f"font-size: {base_size}px;"
    return style


def is_valid_synonym(syn):
    if not syn: return False
    clean = str(syn).strip().upper()
    if clean in ['', '-', 'N', 'A', 'N/A', 'NONE', 'X']: return False
    return True


def apply_exam_highlights(text, exam_items):
    if not exam_items: return text

    for item in exam_items:
        target = item.get('target', '').strip()
        e_type = item.get('type', '')
        if not target: continue

        if e_type in ["blank_inference", "빈칸 추론", "빈칸출제", "빈칸"]:
            border_color = "#4caf50"
            bg_color = "rgba(76, 175, 80, 0.15)"
            label = "빈칸출제"
        elif e_type in ["implied_meaning", "함축 의미", "함축의미", "함축"]:
            border_color = "#9c27b0"
            bg_color = "rgba(156, 39, 176, 0.15)"
            label = "함축의미"
        elif e_type in ["grammar_correction", "어법 대비", "어법주의", "어법"]:
            border_color = "#f44336"
            bg_color = "rgba(244, 67, 54, 0.15)"
            label = "어법주의"
        else:
            border_color = "#ff9800"
            bg_color = "rgba(255, 152, 0, 0.15)"
            label = "변형출제"

        target_words = [w for w in re.split(r'[^a-zA-Z0-9]+', target) if w]
        if not target_words: continue

        escaped_words = [re.escape(w) for w in target_words]
        join_pattern = r'(?:<[^>]+>|\[/?.*?\]|《/?.*?》|[^a-zA-Z0-9]+)+'
        pattern_str = join_pattern.join(escaped_words)

        try:
            replacement = rf'<span class="visual-exam-target" style="border-bottom: 2px dashed {border_color}; background-color: {bg_color};"><span class="visual-exam-label" style="background-color: {border_color};">{label}</span>\g<0></span>'
            pattern = re.compile(f'({pattern_str})(?![^<]*>)', re.IGNORECASE | re.DOTALL)
            text = pattern.sub(replacement, text, count=1)
        except:
            pass

    return text


def apply_inline_syntax_tips(text, tip_data):
    if not isinstance(tip_data, list):
        return text

    for tip in tip_data:
        if not isinstance(tip, dict): continue
        target = tip.get('target', '').strip()
        tag = "구문팁"
        if not target: continue

        target_parts = target.split('~')
        regex_parts = []
        join_pattern = r'(?:<[^>]+>|\[/?.*?\]|《/?.*?》|[^a-zA-Z0-9]+)+'
        for part in target_parts:
            words = [w for w in re.split(r'[^a-zA-Z0-9]+', part) if w]
            if not words: continue
            escaped_words = [re.escape(w) for w in words]
            regex_parts.append(join_pattern.join(escaped_words))

        if not regex_parts: continue

        pattern_str = r'.*?'.join(regex_parts)

        try:
            replacement = rf'<span class="inline-syntax-target"><span class="inline-syntax-label">{tag}</span>\g<0></span>'
            pattern = re.compile(f'({pattern_str})(?![^<]*>)', re.IGNORECASE | re.DOTALL)
            text = pattern.sub(replacement, text, count=1)
        except:
            pass

    return text


def count_words(text_line):
    clean_l = re.sub(r'<[^>]+>', ' ', text_line)
    clean_l = re.sub(r'\[/?[^\]]+\]', ' ', clean_l)
    clean_l = re.sub(r'《/?[^》]+》', ' ', clean_l)
    clean_l = clean_l.replace('/', ' ').replace('★', ' ')
    clean_l = re.sub(r'[❶❷❸❹❺❻❼❽❾❿⓫⓬⓭⓮⓯⓰⓱⓲⓳⓴]', ' ', clean_l)
    words = [w for w in clean_l.split() if re.search(r'[a-zA-Z0-9]', w)]
    return len(words)


def generate_html_from_json(json_str, output_path):
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
        three_stage = data.get('three_stage_flow', [])

        csat_data = data.get('csat_summary_problem', {})
        if not csat_data and 'csat_summary_problem' in topic:
            csat_data = topic.get('csat_summary_problem', {})

        exam_data = data.get('predicted_exam_data', [])
        learning_point = data.get('learning_point', {})

        tf_data = data.get('true_false_details', [])
        eng_def_data = data.get('english_definitions', [])

        diff_level = meta.get('difficulty_level', '0')
        try:
            level_int = int(diff_level)
        except:
            level_int = 0
        level_int = max(0, min(5, level_int))

        full_star = "★"
        empty_star = "☆"
        stars_html = (full_star * level_int) + (empty_star * (5 - level_int))

        difficulty_html = f"""
        <div class="difficulty-box">
            <span class="diff-label">DIFFICULTY</span>
            <span class="diff-stars">{stars_html}</span>
        </div>
        """

        csat_summary_html = ""
        if csat_data:
            s_text = csat_data.get('summary_text', '')
            s_ans = csat_data.get('answer', '')
            s_trans = csat_data.get('translation', '')

            ans_A = ""
            ans_B = ""
            if "(A)" in s_ans and "(B)" in s_ans:
                part_a = s_ans.split("(B)")[0].replace("(A)", "").strip(" ,;/")
                part_b = s_ans.split("(B)")[1].strip(" ,;/")
                ans_A = part_a
                ans_B = part_b

            if ans_A:
                s_text = re.sub(r'\([Aa]\)[_\s]*', f'(A) <span class="csat-blank-ans">{ans_A}</span> ', s_text)
            if ans_B:
                s_text = re.sub(r'\([Bb]\)[_\s]*', f'(B) <span class="csat-blank-ans">{ans_B}</span> ', s_text)

            csat_summary_html = f"""
            <div class="csat-container">
                <div class="csat-header">
                    <div class="csat-title"><span class="csat-badge">S</span> 요약문 빈칸 완성 & 해석</div>
                    <div class="csat-subtitle">* 정답이 채워진 요약문과 해석입니다.</div>
                </div>
                <div class="csat-text">{s_text}</div>
                <div class="csat-trans-header">▼ 해석 및 구문 분석 (Interpretation)</div>
                <div class="csat-trans-text">{s_trans}</div>
            </div>
            """

        exam_points_map = {}
        exam_modal_rows = ""
        if exam_data:
            for item in exam_data:
                s_no = str(item.get('sentence_no', ''))
                if s_no not in exam_points_map:
                    exam_points_map[s_no] = []
                exam_points_map[s_no].append(item)

                e_type = item.get('type', '')
                t_phrase = item.get('target', '')
                reason = item.get('reason', '')

                type_kor = ""
                strategy = ""
                if e_type in ["blank_inference", "빈칸 추론", "빈칸출제", "빈칸"]:
                    type_kor = "<span class='exam-badge exam-badge-blank'>빈칸</span>"
                    strategy = f"<strong>Paraphrase:</strong> {item.get('paraphrase', '')}"
                elif e_type in ["implied_meaning", "함축 의미", "함축의미", "함축"]:
                    type_kor = "<span class='exam-badge exam-badge-implied'>함축</span>"
                    strategy = f"<strong>Meaning:</strong> {item.get('meaning', '')}"
                elif e_type in ["grammar_correction", "어법 대비", "어법주의", "어법"]:
                    type_kor = "<span class='exam-badge exam-badge-grammar'>어법</span>"
                    strategy = f"<strong>Distractor:</strong> {item.get('distractor', '')}"

                exam_modal_rows += f"""
                <div style='margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid #eee;'>
                    <div style='margin-bottom:4px;'><strong>S{s_no}.</strong> {type_kor} <span class='exam-target'>{t_phrase}</span></div>
                    <div style='font-size:13px; color:#555; margin-bottom:2px;'>{strategy}</div>
                    <div style='font-size:13px; color:#444;'>💡 <strong>출제이유:</strong> {reason}</div>
                </div>
                """

        exam_modal_content = exam_modal_rows if exam_modal_rows else "내신 출제 포인트 데이터가 없습니다."

        learning_logic_html = "<li>데이터 없음</li>"
        learning_grammar_html = "<li>데이터 없음</li>"
        visual_clean_html = ""
        visual_passage_html = ""

        logic_pts = learning_point.get('logic', [])
        grammar_pts = learning_point.get('grammar', [])

        if logic_pts:
            learning_logic_html = ""
            for p in logic_pts:
                p = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', p)
                learning_logic_html += f"<li>{convert_common_tags(p)}</li>"

        if grammar_pts:
            learning_grammar_html = ""
            for p in grammar_pts:
                p = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', p)
                learning_grammar_html += f"<li>{convert_common_tags(p)}</li>"

        raw_logic = data.get('logic_map', [])
        micro_logic_map = {}
        if isinstance(raw_logic, list):
            logic_list = []
            for item in raw_logic:
                item_str = str(item).strip()
                if item_str and item_str != '↓':
                    match = re.match(r'^S?(\d+)(?:[~-]S?(\d+))?', item_str, re.IGNORECASE)
                    if match:
                        start_num = match.group(1)
                        micro_logic_map[str(start_num)] = item_str
                formatted_item = re.sub(r'^([A-Za-z0-9~\s-]+\(.*\))', r'<b>\1</b>', item_str)
                logic_list.append(formatted_item)
            logic_map_text = "<br>".join(logic_list)
        else:
            logic_map_text = str(raw_logic).replace('\n', '<br>')
            for item in str(raw_logic).split('\n'):
                item_str = item.strip()
                if item_str and item_str != '↓':
                    match = re.match(r'^S?(\d+)(?:[~-]S?(\d+))?', item_str, re.IGNORECASE)
                    if match:
                        start_num = match.group(1)
                        micro_logic_map[str(start_num)] = item_str

        them_list = []
        key_list = []
        for s in sentences:
            eng_txt = s.get('eng_analyzed', '')
            num = s.get('num', '')
            if '《Theme sentence》' in eng_txt or '《Them sentence》' in eng_txt:
                them_list.append(f"S{num}")
            if '《Key sentence》' in eng_txt or '《Key sentence 》' in eng_txt:
                key_list.append(f"S{num}")

        header_badges = ""
        if them_list:
            header_badges += f"<span class='header-badge-them'>★주제문: {', '.join(them_list)}</span>"
        if key_list:
            header_badges += f"<span class='header-badge-key'>★재진술: {', '.join(key_list)}</span>"

        all_sentence_words = []
        for s in sentences:
            all_sentence_words.extend(parse_local_vocab(s.get('context_meaning', '')))

        raw_passage = visual.get('question_text_visual', '')
        raw_passage = raw_passage.replace('\\n', '\n')

        # 2페이지 지문 원문에 잘못 혼입된 한글 해석, HTML 박스 원천 차단
        raw_passage = re.sub(r'<div class="easy-exp-box".*?</div>', '', raw_passage, flags=re.DOTALL | re.IGNORECASE)
        raw_passage = re.sub(r'<div class="syntax-tip".*?</div>', '', raw_passage, flags=re.DOTALL | re.IGNORECASE)
        raw_passage = re.sub(r'\[서술형\]', '', raw_passage)
        raw_passage = re.sub(r'《서술형》', '', raw_passage)

        cleaned_rp_lines = []
        for line in raw_passage.split('\n'):
            has_eng = bool(re.search(r'[a-zA-Z]', line))
            has_kor = bool(re.search(r'[가-힣]', line))
            if not has_eng and has_kor:
                continue  # 순수 한글 해석 줄 삭제
            cleaned_rp_lines.append(line)
        raw_passage = '\n'.join(cleaned_rp_lines)

        clean_passage = preprocess_multiline_tags(raw_passage)
        clean_passage = strip_syntax_tags(clean_passage)

        clean_passage_with_exam = apply_exam_highlights(clean_passage, exam_data)

        passage_with_vocab = apply_vocab_style(clean_passage_with_exam, all_sentence_words)

        q_type = str(meta.get('question_type', '1')).strip()
        if q_type == '3':
            passage_with_vocab = re.sub(r'《BLANK》.*?《/BLANK》', ' __________________ ', passage_with_vocab,
                                        flags=re.DOTALL)

        processed_full_text = convert_common_tags(passage_with_vocab)

        if q_type == '4':
            processed_full_text = processed_full_text.replace('(A)', '\n(A)').replace('(B)', '\n(B)').replace('(C)',
                                                                                                              '\n(C)')
            processed_full_text = processed_full_text.replace('[A]', '\n[A]').replace('[B]', '\n[B]').replace('[C]',
                                                                                                              '\n[C]')
            processed_full_text = '\n'.join([line.strip() for line in processed_full_text.split('\n') if line.strip()])

        num_map_rev = {
            '❶': 1, '❷': 2, '❸': 3, '❹': 4, '❺': 5,
            '❻': 6, '❼': 7, '❽': 8, '❾': 9, '❿': 10,
            '⓫': 11, '⓬': 12, '⓭': 13, '⓮': 14, '⓯': 15,
            '⓰': 16, '⓱': 17, '⓲': 18, '⓳': 19, '⓴': 20
        }

        raw_lines_list = processed_full_text.split('\n')
        lines_data = []
        for rl in raw_lines_list:
            w_cnt = count_words(rl)

            for char, n in num_map_rev.items():
                if char in rl:
                    num_str = str(n)
                    if num_str in micro_logic_map:
                        micro_text = micro_logic_map[num_str]
                        text_len = len(re.sub(r'<[^>]+>', '', micro_text))
                        if text_len > 40:
                            fs = "9.5px"
                            ls = "-0.8px"
                        elif text_len > 25:
                            fs = "10px"
                            ls = "-0.5px"
                        else:
                            fs = "11px"
                            ls = "-0.3px"

                        micro_text = re.sub(r'^([A-Za-z0-9~\s-]+\(.*\))', r'<b>\1</b>', micro_text)

                        logic_box = f"""<span style="position: absolute; right: 0; width: 26%; z-index: 10;">
                            <span class="logic-flow-card" style="display: block; background-color: #f5f5f5; border-color: #e0e0e0; color: #333; font-family: 'D2Coding', sans-serif; padding: 4px 6px; margin: 0; box-shadow: 0 1px 2px rgba(0,0,0,0.05); font-size: {fs}; letter-spacing: {ls}; border-radius: 6px; border-left: 3px solid #1565c0; word-break: keep-all; white-space: normal; text-align: left; line-height: 1.2; transform: translateY(-2px);">
                                <span class="logic-desc" style="font-weight: 800;">{convert_common_tags(micro_text)}</span>
                            </span>
                        </span>"""
                        rl = rl.replace(char, logic_box + char)

            interactive_l = make_visual_interactive(rl, sentences)
            lines_data.append({'html': interactive_l, 'word_count': w_cnt})

        def build_passage_row(line_dict, is_last=False):
            l_html = line_dict['html']
            w_cnt = line_dict['word_count']
            align_class = "line-last" if (w_cnt <= 4 or is_last) else "line-justify"
            return f'<div class="{align_class}" style="position: relative; padding-right: 28%; margin-bottom: 10px; width: 100%; box-sizing: border-box;">{l_html}</div>'

        if q_type == '5':
            split_idx = -1
            for idx, line_dict in enumerate(lines_data):
                if '❷' in line_dict['html']:
                    split_idx = idx
                    break

            if split_idx > 0:
                box_lines = lines_data[:split_idx]
                body_lines = lines_data[split_idx:]
            else:
                box_lines = lines_data[:1]
                body_lines = lines_data[1:]

            box_content = "".join([build_passage_row(l, False) for l in box_lines])
            visual_passage_html += f'<div class="visual-box-given" style="padding-bottom: 5px;">{box_content}</div>'
            for idx, line_dict in enumerate(body_lines):
                visual_passage_html += build_passage_row(line_dict, idx == len(body_lines) - 1)

        elif q_type == '4':
            split_idx = -1
            for idx, line_dict in enumerate(lines_data):
                clean_line = re.sub(r'<[^>]+>', '', line_dict['html']).strip()
                if clean_line.startswith('(A)') or clean_line.startswith('[A]'):
                    split_idx = idx
                    break

            if split_idx > 0:
                box_lines = lines_data[:split_idx]
                body_lines = lines_data[split_idx:]
                box_content = "".join([build_passage_row(l, False) for l in box_lines])
                visual_passage_html += f'<div class="visual-box-given" style="padding-bottom: 5px;">{box_content}</div>'
                for idx, line_dict in enumerate(body_lines):
                    visual_passage_html += build_passage_row(line_dict, idx == len(body_lines) - 1)
            else:
                if lines_data:
                    visual_passage_html += f'<div class="visual-box-given" style="padding-bottom: 5px;">{build_passage_row(lines_data[0], False)}</div>'
                    for idx, line_dict in enumerate(lines_data[1:]):
                        visual_passage_html += build_passage_row(line_dict, idx == len(lines_data[1:]) - 1)

        elif q_type == '6':
            if lines_data:
                for idx, line_dict in enumerate(lines_data[:-1]):
                    visual_passage_html += build_passage_row(line_dict, False)
                visual_passage_html += f'<div class="visual-box-summary" style="padding-bottom: 5px;">{build_passage_row(lines_data[-1], True)}</div>'
        else:
            for idx, line_dict in enumerate(lines_data):
                visual_passage_html += build_passage_row(line_dict, idx == len(lines_data) - 1)

        # 2페이지 Clean 버전 지문도 word count(4단어 이하 조건) 적용하여 렌더링
        visual_clean_html = ""
        clean_vis = preprocess_multiline_tags(raw_passage)
        clean_vis = strip_syntax_tags(clean_vis)

        if q_type == '3':
            clean_vis = re.sub(r'《BLANK》.*?《/BLANK》', ' __________________ ', clean_vis, flags=re.DOTALL)

        clean_vis = convert_common_tags(clean_vis)

        if q_type == '4':
            clean_vis = clean_vis.replace('(A)', '\n(A)').replace('(B)', '\n(B)').replace('(C)', '\n(C)')
            clean_vis = clean_vis.replace('[A]', '\n[A]').replace('[B]', '\n[B]').replace('[C]', '\n[C]')
            clean_vis = '\n'.join([line.strip() for line in clean_vis.split('\n') if line.strip()])

        clean_vis_raw_lines = clean_vis.split('\n')

        clean_lines_data = []
        for l in clean_vis_raw_lines:
            w_cnt = count_words(l)

            for char, n in num_map_rev.items():
                if char in l:
                    num_str = str(n)
                    if num_str in micro_logic_map:
                        micro_text = micro_logic_map[num_str]
                        text_len = len(re.sub(r'<[^>]+>', '', micro_text))
                        if text_len > 40:
                            fs = "9.5px"
                            ls = "-0.8px"
                        elif text_len > 25:
                            fs = "10px"
                            ls = "-0.5px"
                        else:
                            fs = "11px"
                            ls = "-0.3px"

                        micro_text = re.sub(r'^([A-Za-z0-9~\s-]+\(.*\))', r'<b>\1</b>', micro_text)

                        logic_box = f"""<span style="position: absolute; right: 0; width: 26%; z-index: 10;">
                            <span class="logic-flow-card" style="display: block; background-color: #f5f5f5; border-color: #e0e0e0; color: #333; font-family: 'D2Coding', sans-serif; padding: 4px 6px; margin: 0; box-shadow: 0 1px 2px rgba(0,0,0,0.05); font-size: {fs}; letter-spacing: {ls}; border-radius: 6px; border-left: 3px solid #1565c0; word-break: keep-all; white-space: normal; text-align: left; line-height: 1.2; transform: translateY(-2px);">
                                <span class="logic-desc" style="font-weight: 800;">{convert_common_tags(micro_text)}</span>
                            </span>
                        </span>"""
                        l = l.replace(char, logic_box + char)

            clean_lines_data.append({'text': l, 'word_count': w_cnt})

        def build_clean_row(c_dict, is_last=False):
            txt = c_dict['text']
            w_cnt = c_dict['word_count']
            align_class = "line-last" if (w_cnt <= 4 or is_last) else "line-justify"
            return f'<div class="{align_class}" style="position: relative; padding-right: 28%; margin-bottom: 10px; width: 100%; box-sizing: border-box;">{txt}</div>'

        if q_type == '5':
            c_split_idx = -1
            for idx, c_dict in enumerate(clean_lines_data):
                if '❷' in c_dict['text'] or '(B)' in c_dict['text']:
                    c_split_idx = idx
                    break

            if c_split_idx == -1: c_split_idx = 1

            c_box = clean_lines_data[:c_split_idx]
            c_body = clean_lines_data[c_split_idx:]
            box_html = "".join([build_clean_row(c, False) for c in c_box])
            visual_clean_html += f'<div class="visual-box-given">{box_html}</div>'
            for idx, c in enumerate(c_body):
                visual_clean_html += build_clean_row(c, idx == len(c_body) - 1)

        elif q_type == '4':
            c_split_idx = -1
            for idx, c_dict in enumerate(clean_lines_data):
                c_line = c_dict['text'].strip()
                if c_line.startswith('(A)') or c_line.startswith('[A]'):
                    c_split_idx = idx
                    break

            if c_split_idx > 0:
                c_box = clean_lines_data[:c_split_idx]
                c_body = clean_lines_data[c_split_idx:]
                box_html = "".join([build_clean_row(c, False) for c in c_box])
                visual_clean_html += f'<div class="visual-box-given">{box_html}</div>'
                for idx, c in enumerate(c_body):
                    visual_clean_html += build_clean_row(c, idx == len(c_body) - 1)
            else:
                if clean_lines_data:
                    visual_clean_html += f'<div class="visual-box-given">{build_clean_row(clean_lines_data[0], False)}</div>'
                    for idx, c in enumerate(clean_lines_data[1:]):
                        visual_clean_html += build_clean_row(c, idx == len(clean_lines_data[1:]) - 1)

        elif q_type == '6':
            if clean_lines_data:
                for idx, c in enumerate(clean_lines_data[:-1]):
                    visual_clean_html += build_clean_row(c, False)
                visual_clean_html += f'<div class="visual-box-summary">{build_clean_row(clean_lines_data[-1], True)}</div>'
        else:
            for idx, c in enumerate(clean_lines_data):
                visual_clean_html += build_clean_row(c, idx == len(clean_lines_data) - 1)

        options_html = ""
        vis_opts = visual.get('options_visual', [])

        for item in vis_opts:
            if isinstance(item, dict):
                sub_q = item.get('sub_question', '')
                if sub_q and str(sub_q).strip() != "" and str(sub_q).strip() != "None":
                    options_html += f"<div style='font-size:14px; font-weight:800; margin-top:8px; margin-bottom:6px; color:#1565c0; border-bottom:1px dashed #ccc; padding-bottom:4px;'>📌 {sub_q}</div>"
                current_opts = item.get('options', [])
            elif isinstance(item, str):
                current_opts = [item]
            else:
                current_opts = []

            for opt_text in current_opts:
                analysis_item = None
                for w in wrong:
                    if w.get('choice', '')[:1] in str(opt_text):
                        analysis_item = w
                        break

                if analysis_item:
                    err_type = analysis_item.get('error_type', '')
                    reason = analysis_item.get('reason', '')
                    trans = analysis_item.get('trans', '')
                    is_correct = "정답" in err_type
                    badge_class = "err-badge-correct" if is_correct else "err-badge-wrong"
                    badge_html = f"<span class='{badge_class}'>{err_type}</span>"
                    reason = convert_common_tags(reason)
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

        options_modal_content = options_html if options_html else "선택지 분석 데이터가 없습니다."

        vocab_modal_rows = ""
        for v in vocab:
            word = v.get('word', '')
            pron = v.get('pronunciation', '')
            meaning = v.get('meaning', '').replace('①', '').replace('②', ',').strip()
            if meaning.startswith(','): meaning = meaning[1:].strip()

            chunk_eng = v.get('chunk_example', '-')
            if word and chunk_eng != '-':
                clean_word = re.sub(r'\(.*?\)', '', word).strip()
                chunk_eng = smart_replace(chunk_eng, clean_word,
                                          "<span style='color:#e53935; font-weight:bold;'>{}</span>")

            chunk_kor = v.get('chunk_translation', '')
            chunk_html = f"<b>{chunk_eng}</b>"
            if chunk_kor:
                chunk_html += f"<br><span style='color:#777; font-size:11px;'>{chunk_kor}</span>"

            ety = v.get('etymology', '').strip()
            ety_html_modal = f"<br><span style='font-size:11px; color:#8d6e63; font-weight:bold; letter-spacing:-0.5px;'>{ety}</span>" if ety and ety != '-' else ""

            row_html = f"""<tr>
                <td class='vocab-word-bold'>{word}</td>
                <td>{v.get('synonym', '-')}</td>
                <td>{v.get('antonym', '-')}</td>
                <td>{v.get('confusing', '-')}</td>
                <td class='vocab-pron'>{pron}{ety_html_modal}</td>
                <td style='text-align:left;'>{meaning}</td>
                <td style='text-align:left;'>{chunk_html}</td>
            </tr>"""
            vocab_modal_rows += row_html

        vocab_modal_content = f"""
        <table class='vocab-table modal-table'>
            <colgroup><col width="12%"><col width="12%"><col width="12%"><col width="12%"><col width="8%"><col width="20%"><col width="24%"></colgroup>
            <thead><tr><th>Word</th><th>Synonym</th><th>Antonym</th><th>Confusing</th><th>Pronunciation</th><th>Meaning</th><th>Chunk</th></tr></thead>
            <tbody>{vocab_modal_rows}</tbody>
        </table>
        """

        vocab_rows_divs = ""
        vocab_subset = vocab[:10]
        for idx, v in enumerate(vocab_subset):
            chunk_en_hl = highlight_chunk_word(v.get('word', ''), v.get('chunk_example', ''))
            chunk_ko = v.get('chunk_translation', '')

            pron = str(v.get('pronunciation', '')).strip()
            pron = pron.replace('[', '').replace(']', '').strip()
            pron_html = f'<div class="word-pron">[{pron}]</div>' if pron and pron != '-' else ''

            ety = str(v.get('etymology', '')).strip()
            ety_html = f'<div class="word-ety">{ety}</div>' if ety and ety != '-' else ''

            syn = v.get('synonym', '')
            ant = v.get('antonym', '')
            conf = v.get('confusing', '')

            rel_html = '<div class="rel-box">'
            if is_valid_synonym(syn):
                rel_html += f'<div class="rel-item item-syn"><span class="bg-syn">유</span>{syn}</div>'
            if is_valid_synonym(ant):
                rel_html += f'<div class="rel-item item-ant"><span class="bg-ant">반</span>{ant}</div>'
            if is_valid_synonym(conf):
                rel_html += f'<div class="rel-item item-conf" style="width:100%; margin-top:2px;"><span class="bg-conf">혼</span>{conf}</div>'
            rel_html += '</div>'

            if not is_valid_synonym(syn) and not is_valid_synonym(ant) and not is_valid_synonym(conf):
                rel_html = ""

            raw_mean = str(v.get('meaning', ''))

            contexts = re.findall(r'\((.*?)\)', raw_mean)
            context_str = ", ".join(contexts) if contexts else ""

            clean_mean = re.sub(r'\(.*?\)', '', raw_mean)
            clean_mean = re.sub(r'[①-⑳]', '|', clean_mean).strip()
            parts = [p.strip() for p in clean_mean.split('|') if p.strip()]
            final_mean = ", ".join(parts)

            mean_style = get_shrink_style(final_mean, 20, 13.5)

            vocab_rows_divs += f"""
            <div class="v-row">
                <div class="cell col-chk"><div class="chk-box"></div></div>
                <div class="cell col-word"><span class="word-txt">{v.get("word", "")}</span>{pron_html}{ety_html}</div>
                <div class="cell col-mean"><span class="vm-kor" style="{mean_style}">{final_mean}</span>{rel_html}</div>
                <div class="cell col-context"><span class="vm-context">{context_str}</span></div>
                <div class="cell col-chunk"><span class="vch-en">{chunk_en_hl}</span><br><span class="vch-ko">{chunk_ko}</span></div>
            </div>
            """

        vocab_block = f"""
        <div class="sec-vocab">
            <div class="v-header">
                <div class="cell col-chk">Chk</div>
                <div class="cell col-word">Word</div>
                <div class="cell col-mean">Mean & Syn / Ant</div>
                <div class="cell col-context">Context</div>
                <div class="cell col-chunk">Chunk Example</div>
            </div>
            <div class="v-list">{vocab_rows_divs}</div>
        </div>
        """

        key_rows = ""
        key_modal_list = []
        for k in keys:
            full_sentence = k.get('sentence', '')
            source_match = re.search(r'\[(.*?)\]$', full_sentence)
            source_text = f"[{source_match.group(1)}]" if source_match else "-"
            clean_sentence = full_sentence.replace(source_text, "").strip() if source_match else full_sentence

            clean_sentence = re.sub(r'《([^》]*)》', r'<span style="color:#d32f2f; font-weight:bold;">\1</span>',
                                    clean_sentence)

            raw_reason = k.get('reason', '')
            reason_highlighted = re.sub(r'《([^》]*)》', r'<span style="color:#d32f2f; font-weight:bold;">\1</span>',
                                        raw_reason)
            reason_txt = convert_common_tags(reason_highlighted)

            key_rows += f"""<tr><td style='text-align:center; color:#555;'>{source_text}</td><td style='text-align:center; font-weight:bold; color:#0d47a1;'>{k.get('type', '')}</td><td style='font-family:Times New Roman; font-size:14px; text-align:left;'>{clean_sentence}</td><td style='font-size:13px; text-align:left;'>{k.get('translation', '')}</td><td style='font-size:12px; color:#555; text-align:left;'>{reason_txt}</td></tr>"""

            key_modal_list.append(f"""
            <div style="margin-bottom:15px; border-bottom:1px dashed #ddd; padding-bottom:10px;">
                <div style="font-weight:bold; color:#0d47a1; margin-bottom:4px;">{k.get('type', '')} <span style="font-size:11px; color:#666; font-weight:normal;">{source_text}</span></div>
                <div style="font-family:'Times New Roman'; font-size:15px; margin-bottom:4px;">{clean_sentence}</div>
                <div style="font-size:13px; color:#333; margin-bottom:4px;">{k.get('translation', '')}</div>
                <div style="font-size:12px; color:#555; background:#f9f9f9; padding:4px;">💡 {reason_txt}</div>
            </div>
            """)

        key_sent_modal_content = "".join(key_modal_list) if key_modal_list else "핵심 문장 데이터가 없습니다."

        targets_html = ""
        if 'clues' in ans and 'target_sentences' in ans['clues']:
            targets_html = "<br>".join([f"<li>{convert_common_tags(t)}</li>" for t in ans['clues']['target_sentences']])

        answer_modal_content = f"""
        <div style="font-size:16px; font-weight:bold; color:#0277bd; margin-bottom:15px;">정답: {ans.get('correct_choice', '')}</div>
        <div style="margin-bottom:15px;"><strong>[해설 요약]</strong><br>{convert_common_tags(ans.get('explanation_summary', ''))}</div>
        <div style="margin-bottom:15px;"><strong>[논리적 근거]</strong><br><ul style="padding-left:20px;">{targets_html}</ul></div>
        <div><strong>[논리 연결]</strong><br>{convert_common_tags(ans.get('clues', {}).get('logic_flow', ''))}</div>
        """

        sentence_analysis_html = ""

        sent_bg_map = {}
        sent_stage_map = {}
        logic_flow_map = {}

        bg_classes = ['bg-intro', 'bg-body', 'bg-conc']
        card_classes = ['logic-intro', 'logic-body', 'logic-conc']
        flow_classes = ['flow-intro', 'flow-body', 'flow-conc']

        for idx, flow in enumerate(three_stage):
            range_str = flow.get('range', '').strip()

            target_nums = []
            parts = range_str.split(',')
            for part in parts:
                nums_in_part = re.findall(r'\d+', part)
                if not nums_in_part: continue
                nums = [int(n) for n in nums_in_part]

                if '~' in part or '-' in part:
                    if len(nums) >= 2:
                        n1, n2 = nums[0], nums[-1]
                        if n1 <= n2:
                            target_nums.extend(range(n1, n2 + 1))
                        else:
                            target_nums.extend([n1, n2])
                    elif len(nums) == 1:
                        target_nums.append(nums[0])
                else:
                    target_nums.extend(nums)

            if not target_nums: continue

            bg_cls = bg_classes[idx % 3]
            logic_cls = card_classes[idx % 3]

            for n in target_nums:
                sent_bg_map[str(n)] = bg_cls
                sent_stage_map[str(n)] = {'title': flow.get('title', ''), 'class': logic_cls}

            end_num = max(target_nums)
            logic_flow_map[str(end_num)] = {
                'title': flow.get('title', ''),
                'content': flow.get('content', ''),
                'class': card_classes[idx % 3],
                'range': range_str
            }

        eng_map = {}
        kor_map = {}
        raw_eng_map = {}
        literal_map = {}
        tips_map = {}
        summary_map = {}

        for s in sentences:
            n = s.get('num')
            local_vocab_list = parse_local_vocab(s.get('context_meaning', ''))
            raw_eng = s.get('eng_analyzed', '').replace('\\n', '\n')
            eng_with_vocab = apply_vocab_style(raw_eng, local_vocab_list)
            eng_map[n] = convert_eng_tags(eng_with_vocab)

            clean_text = strip_all_tags(raw_eng)
            raw_eng_map[n] = clean_text

            raw_liberal = s.get('kor_liberal_translation', '').strip().replace('\\n', '\n')
            kor_map[n] = convert_kor_tags(raw_liberal) if raw_liberal else ""

            raw_literal = s.get('kor_translation', '').strip().replace('\\n', '\n')
            literal_map[n] = convert_kor_tags(raw_literal) if raw_literal else ""

            raw_tip_data = s.get('syntax_tip', '')
            if isinstance(raw_tip_data, list):
                tip_lines = []
                for tip_item in raw_tip_data:
                    if isinstance(tip_item, dict):
                        tag = "[구문팁]"
                        target = tip_item.get('target', '')
                        exp = tip_item.get('explanation', '')
                        tip_lines.append(f"{tag} <b>{target}</b>: {exp}")
                    else:
                        tip_lines.append(str(tip_item))
                raw_tip = "<br>".join(tip_lines)
            else:
                raw_tip = str(raw_tip_data).strip().replace('\\n', '\n')

            tips_map[n] = convert_common_tags(raw_tip) if raw_tip else ""

            summary_map[n] = s.get('summary_mark', '')

        logic_modal_blocks = []
        for i, flow in enumerate(three_stage):
            card_cls = flow_classes[i % 3]
            flow_content = convert_common_tags(flow.get('content', ''))

            logic_modal_blocks.append(f"""
            <div style='margin-bottom:15px;'>
                <div class='flow-card {card_cls}'>
                    <div class='flow-header'>
                        <span class='flow-title'>{flow.get('title', '')}</span>
                        <span class='flow-num-badge'>{flow.get('range', '')}</span>
                    </div>
                    <div class='flow-content'>{flow_content}</div>
                </div>
            </div>
            """)
        logic_modal_content = "".join(logic_modal_blocks)

        def build_sequential_content(content_map, mode='eng'):
            html = ""
            current_stage_title = None

            for s in sentences:
                n = str(s.get('num'))
                try:
                    num_key = int(n)
                except:
                    continue

                line_content = content_map.get(num_key, "")

                if not line_content: continue

                stage_info = sent_stage_map.get(n, {'title': '기타', 'class': 'logic-section-none'})

                if stage_info['title'] != current_stage_title:
                    if current_stage_title is not None:
                        html += "</div>"

                    html += f"<div class='logic-section {stage_info['class']}'><span class='logic-section-title'>{stage_info['title']}</span>"
                    current_stage_title = stage_info['title']

                suffix = ""
                if mode in ['lit'] and summary_map.get(int(n)):
                    suffix = f"<span class='trans-summary'>{summary_map[int(n)]}</span>"

                cls = "eng-line"
                if mode in ['kor', 'lit', 'tip']: cls = "trans-line"

                num_cls = "eng-num"
                if mode in ['kor', 'lit', 'tip']:
                    num_cls = "trans-num"
                elif mode == 'raw':
                    num_cls = "raw-num"

                html += f"<div class='{cls}'><span class='{num_cls}'>{n}.</span>{line_content}{suffix}</div>"

            if current_stage_title is not None:
                html += "</div>"

            return html if html else "데이터 없음"

        english_sentences_text = build_sequential_content(eng_map, 'eng')
        full_translation_text = build_sequential_content(kor_map, 'kor')
        raw_english_text = build_sequential_content(raw_eng_map, 'raw')
        literal_translation_text = build_sequential_content(literal_map, 'lit')
        syntax_tips_text = build_sequential_content(tips_map, 'tip')

        for s in sentences:
            local_vocab_list = parse_local_vocab(s.get('context_meaning', ''))
            raw_eng = s.get('eng_analyzed', '').replace('\\n', '\n')

            num_val = str(s.get('num', ''))
            exam_items_for_this = exam_points_map.get(num_val, [])

            eng_with_exam = apply_exam_highlights(raw_eng, exam_items_for_this)

            # 1.5순위: 구문팁 밑줄 및 배지 적용
            eng_with_tips = apply_inline_syntax_tips(eng_with_exam, s.get('syntax_tip', ''))

            # 2순위: 어휘 태그 적용
            eng_with_vocab = apply_vocab_style(eng_with_tips, local_vocab_list)

            # 3순위: 구문 분석 태그(S, V, O) 색상 적용 (수식어 [M] 태그는 렌더링에서 제거됨)
            eng = convert_eng_tags(eng_with_vocab)
            kor = convert_kor_tags(s.get('kor_translation', ''))

            # 요약 배지 생성
            summary = s.get('summary_mark', '')
            summary_badge_span = f" <span style='display: inline-block; vertical-align: middle; margin-left: 6px;'><span class='summary-badge' style='margin: 0;'>{summary}</span></span>" if summary else ""

            # 1페이지 영어 & 한글 문장 청크(/) 단위 분리 및 상하 배치 (flex-column)
            eng_chunks = re.split(r'\s*<span class="slash">.*?</span>\s*', eng)
            kor_chunks = re.split(r'\s*<span class="slash">.*?</span>\s*', kor)

            zipped_chunks = list(itertools.zip_longest(eng_chunks, kor_chunks, fillvalue=''))
            last_k_idx = -1
            for idx, (e_c, k_c) in enumerate(zipped_chunks):
                if k_c and k_c.strip():
                    last_k_idx = idx

            chunk_pairs = []
            for idx, (e_c, k_c) in enumerate(zipped_chunks):
                e_str = e_c.strip() if e_c else ''
                k_str = k_c.strip() if k_c else ''

                if not e_str and not k_str: continue

                # 마지막 한글 텍스트 바로 옆에 요약 배지 추가
                if idx == last_k_idx and summary_badge_span:
                    k_str += summary_badge_span
                elif last_k_idx == -1 and idx == len(zipped_chunks) - 1 and summary_badge_span:
                    e_str += summary_badge_span

                e_html = f'<div class="eng-chunk">{e_str}</div>' if e_str else ''
                k_html = f'<div class="kor-chunk" style="display: inline-flex; align-items: center;">{k_str}</div>' if k_str else ''

                chunk_pairs.append(f'<div class="chunk-pair">{e_html}{k_html}</div>')

            combined_eng_kor = '\n<div class="slash-divider">/</div>\n'.join(chunk_pairs)

            # 독립된 요약 배지 html을 비워 중복 렌더링 방지
            summary_html = ""

            tip_data = s.get('syntax_tip', '')
            if isinstance(tip_data, list):
                tip_lines = []
                for tip_item in tip_data:
                    if isinstance(tip_item, dict):
                        tag = "[구문팁]"
                        target = tip_item.get('target', '')
                        exp = tip_item.get('explanation', '')
                        tip_lines.append(f"{tag} <b>{target}</b>: {exp}")
                    else:
                        tip_lines.append(str(tip_item))
                tip = "<br>".join(tip_lines)
            else:
                tip = str(tip_data).strip().replace('\\n', '\n')

            easy_exp = s.get('easy_exp', '')
            easy_exp_html = f"<div class='easy-exp-box'><span class='easy-label'>쉬운풀이</span>{easy_exp}</div>" if easy_exp else ""
            tip_html = f"<div class='syntax-tip'><span class='syntax-label'>구문팁</span>{tip}</div>" if tip else ""

            card_class = "analysis-card"

            if num_val in sent_bg_map:
                card_class += f" {sent_bg_map[num_val]}"

            if '《Theme sentence》' in s.get('eng_analyzed', '') or '《Them sentence》' in s.get('eng_analyzed', ''):
                card_class += " card-them"
            elif '《Key sentence》' in s.get('eng_analyzed', '') or '《Key sentence 》' in s.get('eng_analyzed', ''):
                card_class += " card-key"

            micro_html = ""
            if num_val in micro_logic_map:
                micro_text = micro_logic_map[num_val]
                micro_text = re.sub(r'^([A-Za-z0-9~\s-]+\(.*\))', r'<b>\1</b>', micro_text)
                micro_html = f"""
                <div class="logic-flow-card" style="background-color: #f5f5f5; border-color: #e0e0e0; color: #333; font-family: 'D2Coding', monospace; font-weight: bold; margin-bottom: 8px;">
                    <span class="logic-desc" style="font-weight: 900;">{convert_common_tags(micro_text)}</span>
                </div>
                """

            logic_html = ""
            if num_val in logic_flow_map:
                info = logic_flow_map[num_val]
                logic_html = f"""
                <div class="logic-flow-card {info['class']}">
                    <div style="margin-bottom:6px;">
                        <span class="logic-title" style="display:inline; margin-bottom:0;">{info['title']}</span>
                        <span style="font-size:12px; font-weight:bold; opacity:0.8; margin-left:5px;">{info['range']}</span>
                    </div>
                    <span class="logic-desc">{convert_common_tags(info['content'])}</span>
                </div>
                """

            combined_logic_html = micro_html + logic_html

            exam_inline_html = ""
            if num_val in exam_points_map:
                for item in exam_points_map[num_val]:
                    e_type = item.get('type', '')
                    t_phrase = item.get('target', '')
                    reason = item.get('reason', '')

                    if e_type in ["blank_inference", "빈칸 추론", "빈칸출제", "빈칸"]:
                        badge = "<span class='exam-badge exam-badge-blank'>빈칸출제</span>"
                        strat = f"➔ 변형: {item.get('paraphrase', '')}"
                    elif e_type in ["implied_meaning", "함축 의미", "함축의미", "함축"]:
                        badge = "<span class='exam-badge exam-badge-implied'>함축의미</span>"
                        strat = f"➔ 의미: {item.get('meaning', '')}"
                    elif e_type in ["grammar_correction", "어법 대비", "어법주의", "어법"]:
                        badge = "<span class='exam-badge exam-badge-grammar'>어법주의</span>"
                        strat = f"➔ 오답함정: {item.get('distractor', '')}"
                    else:
                        badge = ""
                        strat = ""

                    exam_inline_html += f"""
                    <div class='exam-point-box'>
                        <div style='margin-bottom:3px;'>{badge} <span class='exam-target'>{t_phrase}</span> {strat}</div>
                        <div style='font-size:11px; color:#666;'>💡 {reason}</div>
                    </div>
                    """

            sentence_analysis_html += f"""
            <div class="sent-container">
                <div class="sent-logic-col">
                    {combined_logic_html}
                </div>
                <div class="sent-analysis-col">
                    <div class="{card_class}">
                        <div class="eng-sent">
                            {combined_eng_kor}
                            {summary_html}
                        </div>
                        <div class="analysis-footer">{easy_exp_html}{tip_html}</div>
                        {exam_inline_html}
                    </div>
                </div>
            </div>"""

        three_stage_flow_html = ""
        card_classes = ['flow-intro', 'flow-body', 'flow-conc']
        for i, flow in enumerate(three_stage):
            arrow = "<div class='flow-arrow'>→</div>" if i < len(three_stage) - 1 else ""
            flow_content = convert_common_tags(flow.get('content', ''))
            card_cls = card_classes[i % 3]

            three_stage_flow_html += f"""
            <div class='flow-card {card_cls}'>
                <div class='flow-header'>
                    <span class='flow-title'>{flow.get('title', '')}</span>
                    <span class='flow-num-badge'>{flow.get('range', '')}</span>
                </div>
                <div class='flow-content'>{flow_content}</div>
            </div>
            {arrow}
            """

        tf_html = ""
        if tf_data:
            tf_rows = ""
            for idx, tf in enumerate(tf_data, 1):
                ans = tf.get('answer', '')
                ans_color = "#2e7d32" if ans.upper() == 'T' else "#c62828"
                ans_badge = f"<span style='color:white; background-color:{ans_color}; padding:2px 8px; border-radius:4px; font-weight:bold; font-family:var(--font-eng); margin-right:8px;'>{ans}</span>"

                tf_rows += f"""
                <div style="margin-bottom:10px; border:1px solid #e0e0e0; border-radius:6px; padding:12px; background:#fff; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                    <div style="display:flex; align-items:flex-start; margin-bottom:6px;">
                        <div>{ans_badge}</div>
                        <div style="flex:1;">
                            <div style="font-family:var(--font-eng); font-size:15px; font-weight:bold; color:#222;">{tf.get('question', '')}</div>
                            <div style="font-size:13.5px; color:#555; margin-top:2px;">{tf.get('translation', '')}</div>
                        </div>
                    </div>
                    <div style="background:#f5f5f5; padding:8px 10px; border-radius:4px; font-size:12.5px; color:#333; border-left:3px solid {ans_color}; line-height:1.4;">
                        💡 <b>해설:</b> {tf.get('reason', '')}
                    </div>
                </div>
                """
            true_false_html = tf_rows
        else:
            true_false_html = "<div style='font-size:13px; color:#777;'>True/False 데이터가 없습니다.</div>"

        eng_def_html = ""
        if eng_def_data:
            def_rows = ""
            for ed in eng_def_data:
                def_rows += f"<tr><td class='vocab-word-bold' style='text-align:center;'>{ed.get('word', '')}</td><td style='text-align:left; font-family:var(--font-eng); font-size:14.5px;'>{ed.get('definition', '')}</td><td style='text-align:left; font-size:13.5px; color:#444;'>{ed.get('translation', '')}</td></tr>"

            eng_def_html = f"""
            <table class="analysis-table">
                <colgroup><col width="20%"><col width="50%"><col width="30%"></colgroup>
                <thead><tr><th>Word</th><th>Definition</th><th>Translation</th></tr></thead>
                <tbody>{def_rows}</tbody>
            </table>
            """
        else:
            eng_def_html = "<div style='font-size:13px; color:#777;'>영영 풀이 데이터가 없습니다.</div>"

        final_html = HTML_TEMPLATE.format(
            topic_keywords=topic.get('keywords', ''),
            topic_summary=convert_common_tags(topic.get('summary', '')),
            question_header=meta.get('question_header', ''),
            source_origin=meta.get('source_origin', ''),
            visual_passage=visual_passage_html,
            options_html=options_html,
            vocab_table_rows="",
            key_sentence_rows=key_rows,
            sentence_analysis_html=sentence_analysis_html,
            correct_choice=ans.get('correct_choice', ''),
            explanation_summary=convert_common_tags(ans.get('explanation_summary', '')),
            clue_targets_html=targets_html,
            clue_material=convert_common_tags(topic.get('keywords', '')),
            clue_logic=convert_common_tags(ans.get('clues', {}).get('logic_flow', '')),
            logic_map_text=logic_map_text,
            three_stage_flow_html=three_stage_flow_html,
            scenario_sim=convert_common_tags(scene.get('simulation_text', '')),
            scenario_guide=scene.get('guide_ment', ''),
            scenario_tip=scene.get('tip_ment', ''),
            header_badges=header_badges,
            full_translation_text=full_translation_text,
            english_sentences_text=english_sentences_text,
            raw_english_text=raw_english_text,
            literal_translation_text=literal_translation_text,
            syntax_tips_text=syntax_tips_text,
            vocab_modal_content=vocab_modal_content,
            key_sent_modal_content=key_sent_modal_content,
            answer_modal_content=answer_modal_content,
            visual_clean_text=visual_clean_html,
            options_modal_content=options_modal_content,
            logic_modal_content=logic_modal_content,
            learning_logic_html=learning_logic_html,
            learning_grammar_html=learning_grammar_html,
            difficulty_html=difficulty_html,
            csat_summary_html=csat_summary_html,
            exam_modal_content=exam_modal_content,
            vocab_block=vocab_block,
            true_false_html=true_false_html,
            eng_def_html=eng_def_html
        )

        final_html = repair_html_content(final_html)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_html)

        print(f"✅ 변환 완료: {os.path.basename(output_path)}")

    except Exception as e:
        print(f"❌ 오류 ({os.path.basename(output_path)}): {e}")


# ==========================================
# [실행 영역: 폴더 일괄 처리]
# ==========================================
if __name__ == "__main__":
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    target_folder = os.path.join(desktop_path, "3")

    if not os.path.exists(target_folder):
        print("=" * 60)
        print(f"⚠️ 바탕화면에 '3' 폴더가 없습니다.")
        print(f"경로: {target_folder}")
        print("=" * 60)
    else:
        files = [f for f in os.listdir(target_folder) if f.endswith('.json')]

        if not files:
            print("=" * 60)
            print("⚠️ '3' 폴더 안에 처리할 .json 파일이 없습니다.")
            print("=" * 60)
        else:
            print(f"📂 총 {len(files)}개의 파일을 변환합니다...")
            print("=" * 60)

            for file_name in files:
                input_path = os.path.join(target_folder, file_name)
                output_name = file_name.replace('.json', '.html')
                output_path = os.path.join(target_folder, output_name)

                try:
                    with open(input_path, 'r', encoding='utf-8') as f:
                        json_data = f.read()
                    generate_html_from_json(json_data, output_path)
                except Exception as e:
                    print(f"❌ 읽기 오류 ({file_name}): {e}")

            print("=" * 60)
            print("🎉 모든 작업이 완료되었습니다!")
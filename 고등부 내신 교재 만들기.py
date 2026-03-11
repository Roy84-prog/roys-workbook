import json
import re
import os
import random
import copy
from playwright.sync_api import sync_playwright

# ==========================================
# [페이지별 폰트 및 줄간격 통합 설정 (Global Configuration)]
# 이곳에서 각 페이지의 글자 크기와 줄간격을 한 번에 조절할 수 있습니다.
# ==========================================
PAGE_CONFIG = {
    "STEP1_OVERVIEW": {
        "text_font_size": "13px",  # 기본 지문 글자 크기
        "text_line_height": "2.15",  # 기본 지문 줄간격
        "long_text_font_size": "13px",  # 장문독해 글자 크기
        "long_text_line_height": "1.8",  # 장문독해 줄간격
    },
    "STEP2_VOCAB": {
        "word_font_size": "11.5px",  # 영어 단어 크기
        "mean_font_size": "11px",  # 한글 뜻 크기
        "chunk_font_size": "11.5px",  # 예문 청크 크기
    },
    "STEP3_LOGIC_FLOW": {
        "eng_font_size_normal": "13px",  # 10문장 이하 기본 영어 크기
        "eng_font_size_long": "12px",  # 11문장 이상 영어 크기
        "line_height_standard": "2.8",  # 6문장 이하 줄간격
        "line_height_semi_compact": "2.7",  # 7~9문장 줄간격
        "line_height_compact": "2.6",  # 10문장 이상 줄간격

        "logic_box_text_size": "11px",  # 우측 논리박스 본문 요약 (기본)
        "logic_box_vocab_size": "10px",  # 우측 논리박스 단어 (기본)
        "logic_box_syn_size": "8.5px",  # 우측 논리박스 유의어 (기본)
        "logic_box_text_size_compact": "10px",  # 우측 논리박스 본문 요약 (컴팩트)
        "logic_box_vocab_size_compact": "9px",  # 우측 논리박스 단어 (컴팩트)
        "logic_box_syn_size_compact": "7.5px",  # 우측 논리박스 유의어 (컴팩트)
    },
    "STEP4_CHECKPOINT": {
        "text_font_size": "13.5px",  # 뷰어 본문 글자 크기
        "text_line_height": "3.0",  # 뷰어 본문 줄간격
        "dense_font_size": "13px",  # 뷰어 본문 글자 크기 (텍스트 많을 때)
        "dense_line_height": "2.1",  # 뷰어 본문 줄간격 (텍스트 많을 때 - 12문장 이상 시 대폭 축소)
    },
    "STEP5_INTENSIVE": {
        "kor_font_size": "11.5",  # 한글 해석 글자 크기 (숫자만 입력)
        "eng_line_height": "3.3",  # 영어 분석 문장 줄간격
        "kor_line_height": "1.8",  # 한글 해석 줄간격
    },
    "STEP6_SUMMARY_SYNTAX": {
        # 40번 요약문 박스 설정
        "summary_font_size": "14px",  # 요약문 글자 크기
        "summary_line_height": "1.8",  # 요약문 줄간격
        # 구문 분석 설정
        "syntax_eng_font_size": "15px",  # 핵심 구문 영어 크기
        "syntax_eng_line_height": "1.7",  # 핵심 구문 영어 줄간격
        "syntax_kor_font_size": "10.5px",  # 핵심 구문 해석 크기
        "syntax_kor_line_height": "1.3",  # 핵심 구문 해석 줄간격
    },
    "STEP7_REVIEW": {
        "text_font_size": "13.5px",  # 변형 문제 지문 글자 크기
        "text_line_height": "1.9",  # 변형 문제 지문 줄간격
        "dense_font_size": "13px",  # 장문 변형 지문 글자 크기
        "dense_line_height": "2.0",  # 장문 변형 지문 줄간격
    }
}

# ==========================================
# [해석 모드 설정 (Translation Mode Configuration)]
# STEP-5(Intensive) 및 STEP-0(Full Text)의 한글 해석 출력 방식을 선택합니다.
# "literal" : 직독직해 (kor_translation) 우선 출력
# "liberal" : 자연스러운 해석 (kor_liberal_translation) 우선 출력
# ==========================================
TRANSLATION_MODE = "literal"

# ==========================================
# [표지 텍스트 설정 (Cover Page Configuration)]
# 표지에 들어가는 문구를 자유롭게 수정할 수 있습니다.
# HTML 태그인 <br>을 사용하면 줄바꿈이 적용됩니다.
# ==========================================
COVER_CONFIG = {
    "top_subtitle": "PREMIUM ENGLISH WORKBOOK",
    "main_title_eng": "ROY'S CLASS",
    "main_title_kor": "고등부 내신 영어<br>마스터 워크북",
    "teacher_badge": "교사용 (정답 및 해설)",
    "bottom_desc": "최상위권을 향한 확실한 선택<br>내신 1등급 완성 프로젝트"
}

# ==========================================
# [푸터 워터마크 설정 (Footer Watermark Configuration)]
# 짝수 페이지 하단(페이지 번호 왼쪽)에 들어갈 텍스트입니다.
# 빈 문자열("")로 두면 표시되지 않습니다.
# ==========================================
WATERMARK_TEXT = "ROY'S ENGLISH"

# ==========================================
# [출력 모드 설정 (Output Mode Configuration)]
# True로 설정된 버전만 HTML 및 PDF 파일로 생성됩니다.
# ==========================================
GENERATE_STANDARD_VERSION = True  # 일반 프린트용 (좌우 15mm 동일 여백)
GENERATE_BOOK_VERSION = True  # 책 제본용 (안쪽 20mm, 바깥쪽 10mm 대칭 여백)

# ==========================================
# [HTML/CSS 템플릿: A4 Portrait V21.23 바탕 + 페이지 넘버링 추가]
# ==========================================
WORKBOOK_PORTRAIT_TEMPLATE_V21_23 = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>Roy's Class - Premium Workbook</title>
<style>
    /* 폰트 로드 */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&display=swap');
    @import url('https://cdn.jsdelivr.net/npm/font-kopub@1.0/kopubbatang.min.css');
    @import url('https://cdn.jsdelivr.net/gh/moonspam/NanumSquare@1.0/nanumsquareround.css');
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;700&family=Times+New_Roman:wght@400;700&display=swap');

    @media print {
        body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
        .page-break { page-break-after: always; }
        .page-container { margin: 0 !important; border: none !important; width: 210mm !important; height: 297mm !important; box-shadow: none !important; }
        @page { size: A4 portrait; margin: 0; }
    }

    :root {
        --c-brand: #003b6f;
        --c-accent: #00897b;
        --c-text: #263238;
        --c-gray-line: #cfd8dc;

        --c-chunk-text: #455a64;
        --c-chunk-hl: #e65100;
        --c-synonym: #4e342e; 

        /* Updated Syntax Colors */
        --c-S: #0d47a1;   /* Subject: Darker Blue */
        --c-V: #b71c1c;   /* Verb: Darker Red */
        --c-O: #4e342e;   /* Object: Dark Brown */
        --c-C: #1b5e20;   /* Complement: Dark Green */
        --c-M: #7b1fa2;   /* Modifier: Purple */
        --c-con: #263238; /* Connective: No Color (Text) */

        /* Fonts */
        --font-sans: 'Pretendard', sans-serif;
        --font-serif: 'KoPub Batang', serif;
        --font-eng: 'Montserrat', sans-serif; 
        --font-head: 'NanumSquareRound', sans-serif;

        --font-eng-text: 'KoPub Batang', serif; 

        --lf-blue-bg: #e3f2fd; --lf-blue-text: #1565c0;
        --lf-org-bg: #fff8e1; --lf-org-text: #ef6c00;
        --lf-grn-bg: #e8f5e9; --lf-grn-text: #2e7d32;

        /* Highlight Colors */
        --bg-blank: #fffde7; --bg-gram: #ffebee;  
        --bg-ins: #e3f2fd;   --bg-mean: #f3e5f5;
        --bg-sub: #e0f2f1; 

        --col-blank: #f9a825; --col-gram: #c62828;   
        --col-ins: #1565c0;   --col-mean: #6a1b9a;   
        --col-sub: #00695c;

        --radius-sm: 6px;
    }

    body { margin: 0; padding: 0; background-color: #f5f5f5; font-family: var(--font-sans); color: var(--c-text); }

    .page-container {
        width: 210mm; height: 297mm; background-color: white;
        margin: 40px auto; padding: 0; position: relative; overflow: hidden;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15); display: flex; flex-direction: column;
    }

    /* Header */
    .page-header { 
        height: 13mm; min-height: 13mm; max-height: 13mm;   
        border-top: 5px solid var(--c-brand); border-bottom: 2px solid #b0bec5; 
        display: flex; justify-content: space-between; align-items: center; 
        padding: 0 15mm; background: #fff; box-sizing: border-box; overflow: hidden; flex-shrink: 0;         
    }
    .ph-left { display: flex; align-items: center; font-family: var(--font-eng); height: 100%; gap: 8px; }
    .ph-source-origin {
        font-weight: 800; color: var(--c-text); font-size: 14.5px; letter-spacing: -0.5px;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 320px;
    }
    .unit-badge-group { display: flex; align-items: center; font-family: var(--font-eng); flex-shrink: 0; }
    .ub-label { background-color: var(--c-brand); color: white; font-size: 11px; font-weight: 700; padding: 3px 6px; border-top-left-radius: 4px; border-bottom-left-radius: 4px; }
    .ub-num { background-color: var(--c-accent); color: white; font-size: 11px; font-weight: 800; padding: 3px 8px; border-top-right-radius: 4px; border-bottom-right-radius: 4px; }

    /* Syntax Legend in Header */
    .syntax-legend { display: flex; gap: 6px; margin-left: 12px; align-items: center; border-left: 1px solid #cfd8dc; padding-left: 10px; height: 14px; }
    .sl-item { font-size: 9px; font-weight: 700; font-family: var(--font-head); letter-spacing: -0.5px; }

    /* Reduced Level Badge Size */
    .header-diff-bar { 
        display: inline-flex; align-items: center; gap: 6px; 
        background: #fafafa; border: 1.5px solid #90a4ae; 
        padding: 1px 8px; border-radius: 12px; margin-left: 8px; 
        height: 18px; 
        box-sizing: border-box; font-family: var(--font-eng); 
    }
    .h-label { font-size: 9px; font-weight: 700; color: #455a64; margin-right: 2px; }
    .h-stars { color: #f57f17; font-size: 10px; letter-spacing: 1px; font-weight: bold; }

    .ph-right { display: flex; align-items: center; gap: 6px; font-family: var(--font-eng); font-size: 14px; color: var(--c-brand); font-weight: 800; letter-spacing: 0.5px; }

    /* Footer Fixed Watermark -> 워터마크 삭제, 하단 2mm 페이지 넘버링 추가 */
    .page-footer { 
        position: absolute; bottom: 1.5mm; right: 1.5mm; width: auto; height: auto;
        border: none; pointer-events: none; 
    }
    .footer-logo { display: none; /* 워터마크 제거 */ }

    .page-num-box {
        position: absolute;
        bottom: 2mm;
        font-family: var(--font-eng);
        font-size: 12px;
        font-weight: 700;
        color: #546e7a;
        letter-spacing: 1px;
    }
    .page-num-left { left: 15mm; }
    .page-num-right { right: 15mm; }

    .txt-point { color: #d32f2f; font-weight: 700; }
    .txt-org { color: #e65100; font-weight: 700; }

    /* ================= Page 1 Specific ================= */
    .q-title-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 8px; }
    .q-label { font-size: 14px; font-weight: 800; color: var(--c-brand); font-family: var(--font-head); margin-bottom: 0; }

    /* ================= Common Styles ================= */
    .v-sec-title { font-family: var(--font-head); font-weight: 800; font-size: 13px; color: #37474f; margin: 10px 0 5px 0; display: flex; align-items: center; gap: 6px; }

    /* Page 1 Body */
    .p1-body { 
        flex: 1; 
        padding: 5mm 15mm 15mm 15mm; 
        display: flex; flex-direction: column; 
        gap: 25px; 
        background: #fff;
        justify-content: flex-start;
    }
    .card-q { flex: 0 0 auto; }
    .q-box { border: 1px solid #cfd8dc; border-radius: 12px; padding: 20px; background: #f8f9fa; }

    /* Visual Types Styles */
    .q-text { font-family: var(--font-serif); font-size: __S1_FS__; line-height: __S1_LH__; text-align: justify; margin-bottom: 15px; color: #212121; }
    .q-text.long-passage { font-size: __S1_LONG_FS__; line-height: __S1_LONG_LH__; }

    .box-container { 
        border: 2px solid #b0bec5; border-radius: 8px; 
        padding: 12px 15px; 
        background-color: #ffffff; 
        margin-bottom: 10px; 
        font-family: var(--font-serif); 
    }

    .order-chunk { 
        margin-bottom: 3px; 
        padding-left: 5px; 
        line-height: 1.8; 
        font-family: var(--font-serif); 
    }

    .summary-sentence-box { border: 2px solid var(--c-accent); border-radius: 8px; padding: 12px; background-color: #e0f2f1; margin-top: 15px; font-weight: 600; color: #004d40; font-family: var(--font-serif); }

    .para-mark { 
        display: inline-block;
        width: 1.3em; height: 1.3em; 
        line-height: 1.3em;
        text-align: center;
        border-radius: 50%;
        background-color: #37474f; 
        color: #fff;
        font-family: var(--font-eng);
        font-weight: 700;
        font-size: 0.65em; 
        margin-right: 4px;
        vertical-align: middle;
        transform: translateY(-1px);
    }

    .main-text { font-family: var(--font-serif); font-size: 13px; line-height: 1.8; text-align: justify; color: #212121; }

    .q-options { 
        border: 2px dashed #b0bec5; 
        border-radius: 8px; 
        padding: 12px 15px; 
        margin-top: 15px; 
        background-color: #ffffff; 
    }
    .q-options-title {
        font-family: var(--font-eng);
        font-size: 11px;
        font-weight: 800;
        color: #78909c;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 5px;
    }

    /* ================= 1페이지 Vocab Section ================= */
    .sec-vocab { 
        flex: 0 0 auto; 
        display: flex; flex-direction: column; 
        margin-top: 0px; border: 1px solid #cfd8dc; border-radius: 8px; overflow: hidden; 
    }

    /* 1페이지 단어장 세로폭 극강 축소 (장문 대응) */
    .sec-vocab.compact-mode { border: 1px solid #cfd8dc; width: 100%; margin: 0; }
    .sec-vocab.compact-mode .v-row { min-height: 20px; }
    .sec-vocab.compact-mode .cell { padding: 2px 6px; }
    .sec-vocab.compact-mode .v-header { padding: 3px 0; }
    .sec-vocab.compact-mode .v-header .cell { padding: 1px 6px; }
    .sec-vocab.compact-mode .word-txt { font-size: 11.5px; }
    .sec-vocab.compact-mode .vm-kor { font-size: 10.5px; line-height: 1.1; }
    .sec-vocab.compact-mode .vm-syn { font-size: 8.5px; padding: 0 2px; margin-top: 2px; }
    .sec-vocab.compact-mode .vch-en { font-size: 9.5px; line-height: 1.1; margin-bottom: 0; }
    .sec-vocab.compact-mode .vch-ko { font-size: 8.5px; line-height: 1.0; }

    /* 순서배열, 요약문용 Semi-Compact 모드 CSS (적절한 비율) */
    .sec-vocab.semi-compact-mode { border: 1px solid #cfd8dc; width: 100%; margin: 0; }
    .sec-vocab.semi-compact-mode .v-row { min-height: 26px; }
    .sec-vocab.semi-compact-mode .cell { padding: 4px 8px; }
    .sec-vocab.semi-compact-mode .v-header { padding: 4px 0; }
    .sec-vocab.semi-compact-mode .v-header .cell { padding: 2px 8px; }
    .sec-vocab.semi-compact-mode .word-txt { font-size: 12.5px; }
    .sec-vocab.semi-compact-mode .vm-kor { font-size: 11.5px; line-height: 1.15; }
    .sec-vocab.semi-compact-mode .vm-syn { font-size: 9.5px; padding: 1px 3px; margin-top: 3px; }
    .sec-vocab.semi-compact-mode .vch-en { font-size: 10.5px; line-height: 1.15; margin-bottom: 1px; }
    .sec-vocab.semi-compact-mode .vch-ko { font-size: 9.5px; line-height: 1.1; }

    .v-header { display: flex; background: #37474f; color: white; font-family: var(--font-eng); font-size: 11px; font-weight: 700; padding: 6px 0; border-bottom: 1px solid #cfd8dc; }
    .v-list { flex: 1; display: flex; flex-direction: column; overflow-y: hidden; }
    .v-row { 
        display: flex; align-items: stretch; border-bottom: 1px solid #eceff1; padding: 0; 
        min-height: 28px; 
    }
    .v-row:nth-child(even) { background-color: #fafafa; }

    .cell { display: flex; align-items: flex-start; padding: 3px 8px; border-right: 1px solid rgba(0,0,0,0.05); box-sizing: border-box; }
    .cell:last-child { border-right: none; }
    .v-header .cell { align-items: center; border-right: 1px solid rgba(255,255,255,0.2); justify-content: center; padding: 3px 8px; }
    .v-header .cell:last-child { border-right: none; }

    .col-chk { width: 30px; justify-content: center; flex-shrink: 0; }
    .col-word { width: 22%; flex-shrink: 0; }
    .col-mean { width: 32%; flex-shrink: 0; flex-direction: column; justify-content: flex-start; align-items: flex-start; }
    .col-chunk { flex: 1; flex-direction: column; justify-content: flex-start; align-items: flex-start; }

    .cell.col-word { border-right: 1px solid rgba(0,0,0,0.05); } 
    .v-header .cell.col-word { border-right: 1px solid rgba(255,255,255,0.2); position: relative; }

    .chk-box { width: 10px; height: 10px; border: 1px solid var(--c-brand); border-radius: 2px; background: white; margin-top: 3px; }

    .word-txt { font-family: var(--font-eng); font-weight: 700; color: var(--c-brand); font-size: 13.5px; } 
    .vm-kor { font-weight: 600; color: #212121; font-size: 12px; line-height: 1.15; word-break: keep-all; }
    .vm-syn { font-family: var(--font-eng); font-size: 10.5px; line-height: 1.1; margin-top: 4px; color: var(--c-synonym); font-weight: 400; background: rgba(78, 52, 46, 0.08); padding: 1px 4px; border-radius: 4px; display: inline-block; }
    .vm-syn::before { content: "≒ "; font-weight: 600; opacity: 0.7; }
    .vch-en { font-family: var(--font-eng); font-weight: 600; color: var(--c-chunk-text); font-size: 11px; line-height: 1.15; margin-bottom: 0; }
    .vch-ko { font-size: 10px; color: #78909c; line-height: 1.1; font-weight: 400; }
    .c-hl { color: var(--c-chunk-hl); font-weight: 700; } 

    /* =========================================
       [Answer Box & Options Box] 교사용 1페이지 하단 교체 영역 스타일
    ========================================= */
    .answer-box { background-color: #f0f8ff; border: 1px solid #b3e5fc; border-radius: 8px; padding: 15px; display: flex; flex-direction: column; }
    .ans-header { font-family: var(--font-head); font-weight: 800; color: #0277bd; font-size: 13.5px; margin-bottom: 10px; border-bottom: 1px solid #b3e5fc; padding-bottom: 6px; line-height: 1.4; }
    .ans-content { font-family: var(--font-sans); font-size: 11px; color: #37474f; line-height: 1.5; overflow-y: auto; }
    .ans-content b { color: #0277bd; }

    .options-box { border: 1px solid #e0e0e0; border-radius: 8px; background: #fff; padding: 12px; display: flex; flex-direction: column; }
    .option-item { margin-bottom: 6px; border: 1px solid #eceff1; border-radius: 6px; padding: 8px; background-color: #fff; box-shadow: 0 1px 2px rgba(0,0,0,0.02); }
    .opt-header { margin-bottom: 3px; line-height: 1.2; }
    .opt-text { font-family: var(--font-serif); font-weight: bold; font-size: 12.5px; color: #212121; }
    .opt-trans { font-family: var(--font-sans); font-size: 10.5px; color: #546e7a; margin-bottom: 5px; display: block; line-height: 1.3; word-break: keep-all; }
    .opt-analysis { background-color: #f8f9fa; padding: 5px 8px; border-radius: 4px; font-size: 10.5px; color: #455a64; line-height: 1.4; display: flex; align-items: flex-start; gap: 6px; border-left: 2px solid #cfd8dc;}

    .err-badge-wrong { font-size: 9.5px; background-color: #fff3e0; color: #ef6c00; padding: 2px 5px; border-radius: 4px; border: 1px solid #ffe0b2; font-weight: 800; font-family: var(--font-head); flex-shrink: 0; white-space: nowrap; }
    .err-badge-correct { font-size: 9.5px; background-color: #e8f5e9; color: #2e7d32; padding: 2px 5px; border-radius: 4px; border: 1px solid #a5d6a7; font-weight: 800; font-family: var(--font-head); flex-shrink: 0; white-space: nowrap; }

    /* ================= Page 2 (Voca) Styles ================= */
    .p4-body { flex: 1; padding: 5mm 15mm 0 15mm; display: flex; flex-direction: column; gap: 20px; background: #fff; }
    .test-section { display: flex; flex-direction: column; gap: 8px; }
    .step1-container { display: flex; justify-content: space-between; gap: 20px; }
    .step1-table { width: 48%; border-collapse: collapse; font-family: var(--font-sans); }
    .step1-table th { background: #f5f5f5; color: #546e7a; padding: 5px; font-size: 10px; border: 1px solid #e0e0e0; font-family: var(--font-head); font-weight: 700;}
    .step1-table td { padding: 2px 6px; border: 1px solid #e0e0e0; font-size: 11px; vertical-align: middle; }
    .step2-container { display: flex; justify-content: space-between; gap: 20px; }
    .step2-subtable { width: 100%; height: 100%; border-collapse: collapse; font-family: var(--font-sans); }
    .step2-subtable td { padding: 6px 0; border-bottom: 1px dashed #eceff1; font-size: 11.5px; vertical-align: middle; height: 32px; box-sizing: border-box; }
    .match-dot { width: 8px; height: 8px; background-color: #cfd8dc; border-radius: 50%; display: inline-block; flex-shrink: 0; }
    .step3-table { width: 100%; border-collapse: collapse; font-family: var(--font-sans); }
    .step3-table th { background: #f5f5f5; color: #546e7a; padding: 6px; font-size: 10px; border: 1px solid #e0e0e0; font-family: var(--font-head); font-weight: 700;}
    .step3-table td { padding: 3px 6px; border: 1px solid #e0e0e0; font-size: __S2_CHUNK_FS__; vertical-align: middle; }

    .tt-word { font-family: var(--font-eng); font-weight: 700; color: var(--c-brand); font-size: __S2_WORD_FS__; }
    .tt-mean-p1 { font-weight: 600; color: #212121; font-size: __S2_MEAN_FS__; line-height: 1.2; word-break: keep-all; }
    .tt-empty-box { height: 20px; } 

    /* ================= Common Section Header ================= */
    .sec-head-style { font-size: 13px; font-weight: 800; color: #37474f; font-family: var(--font-head); margin-bottom: 8px; display: flex; align-items: center; gap: 6px; border-bottom: 1px solid rgba(0,0,0,0.1); padding-bottom: 6px; }
    .sec-head-style .sub-info { font-size: 10.5px; color: #90a4ae; font-weight: 600; margin-left: auto; font-family: var(--font-sans); letter-spacing: -0.3px;}
    .icon-box { width:18px; height:18px; color:white; font-size:10px; display:flex; justify-content:center; align-items:center; border-radius:4px; font-family: var(--font-eng); font-weight: 700; }
    .icon-f { background: #ef5350; } .icon-r { background: var(--c-brand); } 
    .icon-s { background: #ff9800; } .icon-a { background: #7b1fa2; } 
    .icon-t { background: #00897b; } .icon-w { background: #5d4037; } 
    .icon-v { background: #5c6bc0; } 
    .icon-p { background: #ab47bc; }

    /* ================= Logic Styles (P3, P5) ================= */
    .p2-body { flex: 1; padding: 5mm 15mm 10mm 15mm; display: flex; flex-direction: column; gap: 15px; }
    .topic-box { flex: 0 0 auto; background: #e8eaf6; border: 1px solid #c5cae9; border-radius: 8px; padding: 12px 15px; display: flex; flex-direction: column; gap: 10px; }
    .tb-row { display: flex; align-items: baseline; gap: 10px; }

    .tb-label { 
        display: inline-flex; align-items: center; justify-content: center;
        height: 20px; padding: 0 10px; border-radius: 4px;
        font-size: 11px; font-weight: 700; color: white;
        background-color: #5c6bc0; 
        font-family: var(--font-head); margin-right: 10px; flex-shrink: 0; width: 80px; 
    }
    .lbl-key { background-color: #3949ab; } 
    .lbl-sum { background-color: #00897b; } 

    .tb-content { flex: 1; font-size: 13px; color: #37474f; font-family: var(--font-head); line-height: 1.5; }
    .tb-content b { color: #c62828; font-weight: 700; }
    .logic-divider { display: flex; align-items: center; margin: 15px 0 5px 0; color: #546e7a; font-size: 11px; font-weight: 700; font-family: var(--font-head); }
    .logic-divider::after { content: ""; flex: 1; height: 1px; background: #cfd8dc; margin-left: 10px; border-bottom: 1px solid #b0bec5; }
    .split-container { flex: 1; display: flex; flex-direction: column; justify-content: space-between; border-top: 2px solid var(--c-brand); }

    /* Flexbox 찌그러짐 완벽 방지를 위한 너비 강제 고정 및 box-sizing */
    .row-pair { display: flex; align-items: flex-start; padding: 5px 0; width: 100%; box-sizing: border-box; page-break-inside: avoid; break-inside: avoid; }
    .rp-eng { flex: 0 0 70%; width: 70%; max-width: 70%; min-width: 0; padding-right: 15px; border-right: 1px dashed #cfd8dc; display: flex; flex-direction: column; gap: 8px; box-sizing: border-box; overflow-wrap: break-word; overflow: hidden; }
    .rp-kor { flex: 0 0 30%; width: 30%; max-width: 30%; min-width: 0; padding-left: 15px; font-family: var(--font-sans); color: #546e7a; text-align: left; display: block; padding-top: 10px; font-weight: 400; box-sizing: border-box; word-break: normal; overflow-wrap: break-word; }

    .eng-analyzed-box { 
        font-family: var(--font-eng-text); 
        font-size: __ENG_FONT_SIZE__; 
        background-color: #ffffff; 
        padding: __ENG_BOX_PADDING__; 
        border: 1px solid #e0e0e0; border-left-width: 5px; 
        border-radius: 6px; 
        line-height: 2.0; 
        color: #222; box-shadow: none; text-align: justify; 
        word-wrap: break-word; overflow-wrap: break-word; 
    }

    .ec-theme { border-left-color: #e53935; } .ec-key { border-left-color: #fbc02d; } .ec-normal { border-left-color: #9e9e9e; }

    .txt-S { color: var(--c-S); font-weight: 500; } 
    .txt-V { color: var(--c-V); font-weight: 500; } 
    .txt-O { color: var(--c-O); font-weight: 500; } 
    .txt-C { color: var(--c-C); font-weight: 500; } 
    .txt-M { color: var(--c-M); font-weight: 400; font-style: normal; } 
    .txt-con { color: var(--c-con); font-weight: 500; }

    .star-red { color: #e53935; margin-left: 3px; font-size: 13px; vertical-align: 1px; } .star-yel { color: #fbc02d; margin-left: 3px; font-size: 13px; vertical-align: 1px; }

    .vocab-container { display: inline; position: relative; text-indent: 0; line-height: 1.0; } 
    .vocab-text { color: inherit; font-weight: inherit; border-bottom: 1px dotted #bbb; -webkit-box-decoration-break: clone; box-decoration-break: clone; } 

    .vocab-sub { 
        position: absolute; top: 100%; 
        left: 0; 
        transform: none; 
        width: max-content; margin-top: 2px; 
        font-size: 7.5px; color: #546e7a; font-family: 'Pretendard', sans-serif; font-weight: 600; 
        letter-spacing: -0.5px; text-shadow: 1px 1px 0 #fff, -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff; 
        padding: 0 1px; z-index: 10; line-height: 1.1; pointer-events: none; 
        text-align: left; 
    }

    .para-idx { font-family: var(--font-eng); font-weight: 700; color: var(--c-brand); margin-right: 2px; font-size: 16px; }

    /* ================= Page 6 (Predictive & Logic) Styles ================= */
    .p3-body { flex: 1; padding: 5mm 15mm 10mm 15mm; display: flex; flex-direction: column; gap: 15px; }

    .sec-logic { flex: 1; display: flex; flex-direction: column; gap: 4px; }
    .flow-container { display: flex; gap: 5px; align-items: stretch; justify-content: space-between; margin-top: 4px; }
    .flow-box { flex: 1; border-radius: 8px; display: flex; flex-direction: column; border: 1px solid #cfd8dc; overflow: hidden; }
    .fb-header { padding: 8px 10px; border-bottom: 1px solid rgba(0,0,0,0.05); display: flex; flex-direction: column; gap: 4px; align-items: flex-start; }
    .flow-box.theme-blue .fb-header { background-color: var(--lf-blue-bg); } .flow-box.theme-blue .fb-struct-label { color: #000; } 
    .flow-box.theme-yel .fb-header { background-color: var(--lf-org-bg); } .flow-box.theme-yel .fb-struct-label { color: #000; } 
    .flow-box.theme-grn .fb-header { background-color: var(--lf-grn-bg); } .flow-box.theme-grn .fb-struct-label { color: #000; } 
    .fb-label-row { display: flex; justify-content: space-between; width: 100%; align-items: center; }
    .fb-struct-label { font-size: 11px; font-weight: 700; font-family: var(--font-head); }

    .fb-range-badge { 
        background-color: rgba(255,255,255,0.7); 
        color: #546e7a; 
        font-weight: 700; 
        border-radius: 6px; 
        font-family: var(--font-eng);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 34px; 
        height: 19px;
        flex-shrink: 0;
        white-space: nowrap;
        letter-spacing: -0.2px;
        box-sizing: border-box;
    }

    .fb-title-text { width: 100%; font-family: var(--font-serif); font-size: 10.5px; font-weight: 700; color: #37474f; border-bottom: 1px solid rgba(0,0,0,0.1); padding-bottom: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .fb-body { flex: 1; background-color: white; padding: 10px; display: flex; flex-direction: column; min-height: 110px; }
    .fb-body-text { flex: 1; font-family: var(--font-serif); font-size: 10.5px; line-height: 1.5; color: #455a64; text-align: justify; word-break: keep-all; display: flex; flex-direction: column; }
    .fb-body-text b { color: #d32f2f; font-weight: 700; }
    .arrow { display: flex; align-items: center; color: #b0bec5; font-size: 14px; flex-basis: 10px; justify-content: center; font-family: var(--font-eng); }

    .sec-passage-view { flex: 0 0 auto; display: flex; flex-direction: column; gap: 4px; }

    .p6-passage-viewer { font-family: var(--font-serif); font-size: __S4_FS__; line-height: __S4_LH__ !important; text-align: justify; color: #263238; margin-top: 4px; padding: 15px; border: 1px solid #cfd8dc; border-radius: 8px; background: white; }
    .p6-passage-viewer.dense-mode { font-size: __S4_DENSE_FS__; line-height: __S4_DENSE_LH__ !important; }

    .visual-exam-target { 
        position: relative; 
        -webkit-box-decoration-break: clone; 
        box-decoration-break: clone;
        display: inline;
    }
    .visual-exam-label { 
        position: absolute; 
        top: -14px; 
        left: 0; 
        font-size: 8.5px; 
        color: #fff; 
        padding: 1px 3px; 
        border-radius: 3px; 
        font-family: var(--font-sans); 
        font-weight: 700; 
        letter-spacing: 0.5px; 
        white-space: nowrap; 
        line-height: 1; 
        z-index: 5; 
    }

    .sec-annotations { flex: 0 0 auto; display: flex; flex-direction: column; margin-top: 5px; }
    .anno-list { display: flex; flex-direction: column; gap: 0; border: none; }

    /* ================= Page 4 (Summary & Syntax) Styles ================= */
    .p5-body { flex: 1; padding: 5mm 15mm 0 15mm; display: flex; flex-direction: column; gap: 25px; background: #fff; }

    .sb-sec-header { 
        font-family: var(--font-eng); font-weight: 800; font-size: 16px; color: #37474f; 
        border-bottom: 2px solid #37474f; padding-bottom: 5px; margin-bottom: 10px;
        display: flex; align-items: center; gap: 8px;
    }
    .sb-sec-header .badge { background: #37474f; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; }

    .summary-box { 
        background-color: #fffde7; border-radius: 8px; padding: 20px; 
        border: 1px solid #fff59d; display: flex; flex-direction: column; gap: 15px;
    }
    .sb-content { 
        font-family: var(--font-serif); font-size: __S6_SUM_FS__; line-height: __S6_SUM_LH__; color: #263238; 
        text-align: justify; font-weight: 500;
    }
    .sb-trans-box {
        margin-top: 0; padding: 12px; background: rgba(255,255,255,0.7); border-radius: 6px;
        font-family: var(--font-sans); font-size: 12px; color: #546e7a; line-height: 1.6;
        border: 1px dashed #cfd8dc;
    }

    .p5-simple-title {
        font-family: var(--font-head); font-weight: 800; font-size: 16px; color: #37474f;
        border-bottom: 2px solid #37474f; padding-bottom: 8px; margin-bottom: 15px; margin-top: 10px;
    }

    .sa-card {
        background: white; border: 1px solid #e0e0e0; border-radius: 8px; 
        padding: 10px; 
        display: flex; flex-direction: column; 
        gap: 6px; 
        box-shadow: none; 
        page-break-inside: avoid; 
        break-inside: avoid;
    }

    .sa-badge-row { display: flex; align-items: center; gap: 6px; margin-bottom: 2px; }
    .sa-num { font-family: var(--font-eng); font-weight: 900; color: #bf360c; font-size: 14px; }
    .sa-title { font-family: var(--font-eng); font-weight: 800; color: #bf360c; font-size: 12px; letter-spacing: 0.5px; }

    .sa-eng { 
        font-family: var(--font-eng-text); 
        font-size: __S6_SYN_ENG_FS__; 
        font-weight: 700; 
        color: #212121; 
        line-height: __S6_SYN_ENG_LH__; 
        margin-bottom: 6px; 
        padding-bottom: 4px;
        border-bottom: 1px dashed #eceff1; 
    } 

    .sa-kor { 
        font-family: var(--font-sans); font-size: __S6_SYN_KOR_FS__; color: #546e7a; line-height: __S6_SYN_KOR_LH__; 
        background-color: #f9fafb; 
        border: 1px solid #eceff1;
        padding: 5px; 
        border-radius: 4px;
        display: block; 
        font-weight: 400;
    } 

    .sa-note {
        margin-top: 4px; 
        padding: 8px 10px; 
        background-color: #f8f9fa; 
        border: 1px solid #e0e0e0;
        border-radius: 6px; display: flex; align-items: flex-start; gap: 8px;
    }
    .sa-point-tag {
        background: #eceff1; 
        color: #546e7a; 
        font-size: 10px; 
        font-weight: 700; 
        padding: 3px 8px; 
        border-radius: 4px;
        border: 1px solid #cfd8dc;
        font-family: var(--font-eng); 
        flex-shrink: 0;
    }
    .sa-desc { font-size: 9.5px; color: #37474f; line-height: 1.35; font-family: var(--font-sans); font-weight: 500; } 

    /* ================= Page 7 (Review Test) Styles ================= */
    .p6-body { flex: 1; padding: 5mm 15mm 0 15mm; display: flex; flex-direction: column; gap: 10px; background: #fff; } 

    .mod-passage-box {
        border: 2px solid #b0bec5; border-radius: 8px;
        padding: 15px 18px;
        background-color: #fcfcfc;
        font-family: var(--font-serif);
        font-size: __S7_FS__; line-height: __S7_LH__;
        text-align: justify; color: #263238;
        margin-bottom: 10px;
    }

    .mod-passage-box.dense-mode { font-size: __S7_DENSE_FS__; line-height: __S7_DENSE_LH__; }

    .q-marker { font-weight: 700; color: #e65100; font-family: var(--font-eng); margin-right: 2px; }

    .q-list-container {
        display: flex; flex-direction: column; gap: 12px;
        padding: 10px 5px; 
    }

    .qa-item { display: flex; align-items: flex-end; gap: 10px; margin-bottom: 12px; page-break-inside: avoid; break-inside: avoid; }
    .qa-text { font-size: 12.5px; font-weight: 700; color: #37474f; font-family: var(--font-head); white-space: nowrap; }
    .qa-line { flex: 1; border-bottom: 1px solid #b0bec5; height: 18px; min-width: 50px; }

    .g-row { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; font-family: var(--font-eng); font-size: 12px; color: #455a64; page-break-inside: avoid; break-inside: avoid;}
    .arrow-icon { font-weight: 800; color: #e65100; margin: 0 4px; font-size: 14px; }

    .a-line { 
        border-bottom: 1px solid #90a4ae; width: 100%; max-width: 400px; height: 18px; 
        display: inline-block; 
    }
    .a-line-short { width: 120px; border-bottom: 1px solid #90a4ae; display: inline-block; height: 18px;}

    .writing-section {
        margin-top: 20px; 
        padding-top: 15px; border-top: 1px dashed rgba(0,0,0,0.1); 
        display: flex; flex-direction: column; gap: 20px; 
    }

    .ws-item { display: flex; flex-direction: column; gap: 8px; page-break-inside: avoid; break-inside: avoid; }
    .ws-kor { font-size: 12.5px; font-weight: 700; color: #263238; }

    .ws-hint-box {
        background-color: #f5f5f5; 
        border: 1px solid #e0e0e0; border-radius: 4px;
        padding: 6px 10px; margin-bottom: 4px;
        font-family: var(--font-eng); font-size: 11.5px; color: #546e7a;
        word-break: break-all;
    }

    .ws-line-box { 
        height: 24px; border-bottom: 1px solid #cfd8dc; width: 100%; 
        background: rgba(0,0,0,0.02);
    }

    /* ================= Syntax Tip Styles ================= */
    .syntax-tip-box {
        font-size: 10.5px;
        font-family: var(--font-sans);
        color: #263238;
        display: flex;
        align-items: flex-start;
        gap: 8px;
        line-height: 1.3;
    }

    __MIRRORED_CSS__

</style>
</head>
<body>

__STEP0_PAGE_HTML__

<div class="page-container page-break">
    __PAGE_NUM__
    <div class="page-header">
        <div class="ph-left">
            <span class="ph-source-origin">__SOURCE_ORIGIN__</span>
            <div class="unit-badge-group">
                <span class="ub-label">NO.</span>
                <span class="ub-num">__Q_NUM__</span>
            </div>
        </div>
        <div class="ph-right">STEP-1 [Overview]</div>
    </div>
    <div class="p1-body">
        <div class="card-q">
            __PAGE1_TOP_HEADER__
            <div class="q-box"><div class="q-text __Q_TEXT_CLASS__">__PASSAGE_HTML__</div>__OPTIONS_HTML__</div>
        </div>

        __PAGE1_BOTTOM_BLOCK__
    </div>
    <div class="page-footer">
        <div class="footer-logo"></div>
    </div>
</div>

__STEP1_PAGE2_HTML__

<div class="page-container page-break">
    __PAGE_NUM__
    <div class="page-header">
        <div class="ph-left">
            <span class="ph-source-origin">__SOURCE_ORIGIN__</span>
            <div class="unit-badge-group">
                <span class="ub-label">NO.</span>
                <span class="ub-num">__Q_NUM__</span>
            </div>
        </div>
        <div class="ph-right">STEP-2 [Vocabulary]</div>
    </div>
    <div class="p4-body">
        <div class="test-section">
            <div class="sec-head-style"><div class="icon-box icon-v">V</div>STEP 1. Speed Check (철자 & 뜻 확인 - Random)</div>
            <div class="step1-container">
                <table class="step1-table"><colgroup><col width="40%"><col width="60%"></colgroup><thead><tr><th>Word</th><th>Meaning</th></tr></thead><tbody>__STEP1_LEFT__</tbody></table>
                <table class="step1-table"><colgroup><col width="40%"><col width="60%"></colgroup><thead><tr><th>Meaning</th><th>Word Spelling</th></tr></thead><tbody>__STEP1_RIGHT__</tbody></table>
            </div>
        </div>
        <div class="test-section">
            <div class="sec-head-style"><div class="icon-box icon-v">V</div>STEP 2. Match Synonyms (유의어 연결 - 2단 구성)</div>
            <div class="step2-container">
                <div style="width: 48%; position: relative;">
                    __STEP2_SVG_LEFT__
                    <table class="step2-subtable" style="width:100%; height:100%;"><colgroup><col width="32%"><col width="36%"><col width="32%"></colgroup><tbody>__STEP2_LEFT__</tbody></table>
                </div>
                <div style="width: 48%; position: relative;">
                    __STEP2_SVG_RIGHT__
                    <table class="step2-subtable" style="width:100%; height:100%;"><colgroup><col width="32%"><col width="36%"><col width="32%"></colgroup><tbody>__STEP2_RIGHT__</tbody></table>
                </div>
            </div>
        </div>
        __STEP3_AND_4_BLOCK__
    </div>
    <div class="page-footer">
        <div class="footer-logo"></div>
    </div>
</div>

<div class="page-container page-break">
    __PAGE_NUM__
    <div class="page-header">
        <div class="ph-left">
            <span class="ph-source-origin">__SOURCE_ORIGIN__</span>
            <div class="unit-badge-group">
                <span class="ub-label">NO.</span>
                <span class="ub-num">__Q_NUM__</span>
            </div>
        </div>
        <div class="ph-right">STEP-3 [Logic Flow & Clean Text]</div>
    </div>
    <div class="p2-body" style="display: block;">
        <div class="topic-box">
            <div class="tb-row"><div class="tb-label lbl-key" style="background-color: #3949ab;">Subject</div><div class="tb-content" style="font-weight: 900; font-size: 14px;">__TOPIC_KEYWORD_EN__</div></div>
            <div class="tb-row" style="align-items: flex-start;"><div class="tb-label lbl-sum" style="background-color: #00897b;">Summary</div><div class="tb-content" style="line-height: 1.5;">__TOPIC_SUMMARY_EN__</div></div>
        </div>

        <div style="display: flex; flex-direction: column; flex: 1; margin-top: -5px;">
            <div style="display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 1px; line-height: 1;">
                <div style="font-family: var(--font-eng); font-weight: 800; font-size: 12px; color: var(--c-brand);">Main Text <span style="font-family: var(--font-sans); font-size: 11px;">(본문)</span></div>
            </div>
            <div class="split-container" style="border-top: 2px solid var(--c-brand); margin-top: 0;">
                __P3_LOGIC_CLEAN_ROWS__
            </div>
        </div>
    </div>
    <div class="page-footer">
        <div class="footer-logo"></div>
    </div>
</div>

__STEP3_PAGE2_HTML__

<div class="page-container page-break">
    __PAGE_NUM__
    <div class="page-header">
        <div class="ph-left">
            <span class="ph-source-origin">__SOURCE_ORIGIN__</span>
            <div class="unit-badge-group">
                <span class="ub-label">NO.</span>
                <span class="ub-num">__Q_NUM__</span>
            </div>
        </div>
        <div class="ph-right">STEP-4 [Checkpoint]</div>
    </div>
    <div class="p3-body" style="display: flex; flex-direction: column; height: 100%; gap: 15px; padding-bottom: 15mm;">

        <div class="sec-passage-view" style="flex: 0 0 auto;">
            <div class="sec-head-style"><div class="icon-box icon-p">P</div>Predictive analysis for exams (시험 출제 예상 분석)<span class="sub-info">* 지문을 읽으면서 하단 출제 포인트를 확인하세요.</span></div>
            <div class="p6-passage-viewer __P4_DENSITY_CLASS__">__HIGHLIGHTED_PASSAGE__</div>
        </div>

        <div class="sec-annotations" style="flex: 0 0 auto;">
            <div class="anno-list">__ANNOTATION_ROWS__</div>
        </div>

    </div>
    <div class="page-footer">
        <div class="footer-logo"></div>
    </div>
</div>

__STEP5_PAGES__

<div class="page-container page-break">
    __PAGE_NUM__
    <div class="page-header">
        <div class="ph-left">
            <span class="ph-source-origin">__SOURCE_ORIGIN__</span>
            <div class="unit-badge-group">
                <span class="ub-label">NO.</span>
                <span class="ub-num">__Q_NUM__</span>
            </div>
        </div>
        <div class="ph-right">STEP-6 [Summary & Syntax]</div>
    </div>

    <div class="p5-body">

        <div class="test-section">
            <div class="sec-head-style"><div class="icon-box icon-s">S</div>Summary (빈칸 요약문 완성)<span class="sub-info">* (A), (B) 빈칸에 들어갈 영어 단어를 써보세요.</span></div>
            <div class="summary-box">
                <div class="sb-content">
                    __CSAT_SUMMARY_TEXT__
                </div>
                <div class="sb-trans-box">
                    <span style="font-weight:700; color:#ef6c00;">[해석]</span><br>
                    __CSAT_SUMMARY_KOR__
                </div>
            </div>
        </div>

        <div class="test-section">
            <div class="sec-head-style"><div class="icon-box icon-a">A</div>Sentence Analysis (구문 분석)<span class="sub-info">* 영어 문장 구조 분석을 한 후에 한글 해석을 적으세요.</span></div>
            __KEY_SENTENCES_HTML__
        </div>

    </div>
    <div class="page-footer">
        <div class="footer-logo"></div>
    </div>
</div>

<div class="page-container">
    __PAGE_NUM__
    <div class="page-header">
        <div class="ph-left">
            <span class="ph-source-origin">__SOURCE_ORIGIN__</span>
            <div class="unit-badge-group">
                <span class="ub-label">NO.</span>
                <span class="ub-num">__Q_NUM__</span>
            </div>
        </div>
        <div class="ph-right">STEP - 7 [Review]</div>
    </div>
    <div class="p6-body">

        <div class="test-section">
            <div class="sec-head-style"><div class="icon-box icon-t">T</div>Review Test (변형 문제 및 어법 대비)<span class="sub-info">__P7_SUB_INFO__</span></div>
            <div class="mod-passage-box __P6_DENSITY_CLASS__">
                __MODIFIED_PASSAGE_HTML__
            </div>
            <div class="q-list-container">
                __INTEGRATED_QUESTIONS_HTML__
            </div>
        </div>

        <div class="writing-section">
            <div class="sec-head-style"><div class="icon-box icon-w">W</div>Key Sentence Writing (서술형 영작 대비)<span class="sub-info">* 한글 문장에 주어, 동사를 먼저 표시해보세요.</span></div>
            __WRITING_ROWS_HTML__
        </div>

    </div>
    <div class="page-footer">
        <div class="footer-logo"></div>
    </div>
</div>
"""

# ==========================================
# [표지 템플릿 추가]
# ==========================================
COVER_PAGE_STUDENT = f"""
<div class="page-container page-break" style="display: flex; flex-direction: column; justify-content: center; align-items: center; background-color: #fff; padding: 20mm; box-sizing: border-box;">
    <div style="width: 100%; height: 100%; border: 3px solid var(--c-brand); padding: 4px; box-sizing: border-box;">
        <div style="width: 100%; height: 100%; border: 1px solid var(--c-brand); display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 40px; box-sizing: border-box; position: relative;">
            <div style="position: absolute; top: 80px; font-family: var(--font-eng); font-size: 18px; color: #78909c; font-weight: 700; letter-spacing: 4px;">{COVER_CONFIG['top_subtitle']}</div>

            <div style="font-family: var(--font-eng); font-size: 28px; color: var(--c-accent); font-weight: 900; margin-bottom: 20px; letter-spacing: 2px;">{COVER_CONFIG['main_title_eng']}</div>
            <div style="font-family: var(--font-head); font-size: 48px; color: var(--c-brand); font-weight: 900; margin-bottom: 40px; text-align: center; line-height: 1.4;">{COVER_CONFIG['main_title_kor']}</div>

            <div style="width: 60px; height: 5px; background-color: var(--c-accent); margin-bottom: 60px; border-radius: 3px;"></div>

            <div style="font-family: var(--font-sans); font-size: 16px; color: #546e7a; font-weight: 600; text-align: center; line-height: 1.8;">
                {COVER_CONFIG['bottom_desc']}
            </div>

            <div style="position: absolute; bottom: 100px; display: flex; align-items: flex-end; gap: 15px; font-family: var(--font-eng); font-size: 20px; color: #37474f; font-weight: 800;">
                <span style="font-family: var(--font-sans);">이름 :</span>
                <div style="border-bottom: 2px solid #37474f; width: 220px;"></div>
            </div>
        </div>
    </div>
</div>
"""

COVER_PAGE_TEACHER = f"""
<div class="page-container page-break" style="display: flex; flex-direction: column; justify-content: center; align-items: center; background-color: #fff; padding: 20mm; box-sizing: border-box;">
    <div style="width: 100%; height: 100%; border: 3px solid #b71c1c; padding: 4px; box-sizing: border-box;">
        <div style="width: 100%; height: 100%; border: 1px solid #b71c1c; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 40px; box-sizing: border-box; position: relative;">
            <div style="position: absolute; top: 80px; font-family: var(--font-eng); font-size: 18px; color: #78909c; font-weight: 700; letter-spacing: 4px;">{COVER_CONFIG['top_subtitle']}</div>

            <div style="font-family: var(--font-eng); font-size: 28px; color: #b71c1c; font-weight: 900; margin-bottom: 20px; letter-spacing: 2px;">{COVER_CONFIG['main_title_eng']}</div>
            <div style="font-family: var(--font-head); font-size: 48px; color: var(--c-brand); font-weight: 900; margin-bottom: 40px; text-align: center; line-height: 1.4;">{COVER_CONFIG['main_title_kor']}</div>

            <div style="background-color: #ffebee; color: #b71c1c; font-family: var(--font-head); font-size: 20px; font-weight: 800; padding: 8px 25px; border-radius: 30px; border: 2px solid #ef5350; margin-bottom: 60px;">
                {COVER_CONFIG['teacher_badge']}
            </div>

            <div style="font-family: var(--font-sans); font-size: 16px; color: #546e7a; font-weight: 600; text-align: center; line-height: 1.8;">
                {COVER_CONFIG['bottom_desc']}
            </div>
        </div>
    </div>
</div>
"""


# ==========================================
# [함수 추가] HTML을 PDF로 저장하는 함수 (Playwright 사용)
# ==========================================
def save_html_to_pdf(html_content, output_pdf_path):
    """
    HTML 문자열을 입력받아 지정된 경로에 PDF 파일로 저장하는 함수입니다.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = browser.new_page()
        page.set_content(html_content, wait_until="networkidle", timeout=60000)

        # 웹 폰트 강제 로딩 대기 (각 폰트를 명시적으로 load 요청)
        font_status = page.evaluate("""
            () => {
                const fontFamilies = ['Montserrat', 'Noto Sans KR', 'Noto Serif KR', 'NanumSquareRound', 'KoPub Batang', 'KoPubBatang'];
                const checks = fontFamilies.map(f =>
                    document.fonts.load('16px "' + f + '"').then(() => ({family: f, ok: true}))
                        .catch(() => ({family: f, ok: false}))
                );
                return Promise.all(checks).then(results => {
                    return document.fonts.ready.then(() => {
                        const failed = results.filter(r => !r.ok).map(r => r.family);
                        return { total: document.fonts.size, failed: failed };
                    });
                });
            }
        """)

        # 폰트 렌더링 안정화를 위해 추가 대기
        page.wait_for_timeout(2000)

        if font_status.get('failed'):
            print(f"   ⚠️ 폰트 로딩 실패: {', '.join(font_status['failed'])} - PDF에 기본 폰트가 적용될 수 있습니다.")
        page.pdf(
            path=output_pdf_path,
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
        )
        browser.close()


# ==========================================
# [함수 수정] 페이지 넘버링 후처리 함수 (교차 정렬 적용 & 워터마크 추가)
# ==========================================
def insert_page_numbers(html_str):
    parts = html_str.split('__PAGE_NUM__')

    if len(parts) <= 1:
        return html_str

    res = parts[0]
    for i, p in enumerate(parts[1:], 1):
        align = "page-num-left" if i % 2 != 0 else "page-num-right"

        watermark_html = ""
        if i % 2 == 0 and WATERMARK_TEXT:
            watermark_html = f'<span style="color: #cfd8dc; font-weight: 800; font-size: 14px; margin-right: 15px; letter-spacing: 2px;">{WATERMARK_TEXT}</span>'

        page_html = f'<div class="page-num-box {align}" style="display: flex; align-items: center;">{watermark_html}- {i} -</div>\n'
        res += page_html + p

    return res


# [단어 의미 정리 유틸 함수]
def get_clean_mean(raw_mean):
    clean = re.sub(r'[①-⑳]', '|', raw_mean)
    clean = re.sub(r'\(.*?\)', '', clean).strip()
    parts = [p.strip() for p in clean.split('|') if p.strip()]
    return ", ".join(parts)


# ==========================================
# [함수 추가] 교사용 1페이지 분석 박스 텍스트 포맷팅 유틸
# ==========================================
def convert_common_tags(text):
    if not text: return ""
    text = str(text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'《(.*?)》', r'<span class="txt-org">\1</span>', text)
    text = text.replace('\n', '<br>')
    return text


# ==========================================
# [함수 추가] STEP-5 인라인 구문팁 매칭용 정규식 빌더
# ==========================================
def build_target_regex(target_str):
    wildcards = re.split(r'[~…⋯]+|\.\.\.', target_str)
    final_regex_parts = []
    for wc in wildcards:
        wc = wc.strip()
        if not wc: continue
        words = re.findall(r'\w+|[^\w\s]', wc)
        escaped_words = [re.escape(w) for w in words]
        wc_regex = r'(?:<[^>]+>|\s)+'.join(escaped_words)
        final_regex_parts.append(wc_regex)
    if not final_regex_parts: return ""
    return r'[\s\S]*?'.join(final_regex_parts)


# ==========================================
# [함수 수정] 파일 저장이 아닌 HTML 텍스트를 뱉어내고, 교사용 모드 지원
# ==========================================
def generate_unit_pages(json_str, is_teacher=False, file_name=""):
    data = json.loads(json_str) if isinstance(json_str, str) else json_str

    # 파일명 기반 시드 고정: 같은 파일이면 학생용/교사용 셔플 순서가 동일
    random.seed(hash(file_name) if file_name else 0)

    meta = data.get('meta_info', {})
    visual = data.get('visual_data', {})

    base_name = ""
    if file_name:
        base_name = os.path.splitext(file_name)[0]
        if base_name.endswith('_json'):
            base_name = base_name[:-5]
        source_origin = base_name
    else:
        source_origin = meta.get('source_origin', 'Roy\'s Logic English')

    passage_label_html = ""
    if base_name and '-' in base_name:
        passage_label = base_name.split('-')[-1].strip()
        passage_label_html = f'<div style="display: inline-flex; align-items: center; background-color: #e3f2fd; color: #1565c0; padding: 4px 10px; border-radius: 6px; font-family: var(--font-head); font-weight: 800; font-size: 13px; border: 1px solid #90caf9;">{passage_label}</div>'

    question_header_html = ""
    q_header_text = meta.get('question_header', '').strip()
    if q_header_text:
        question_header_html = f'<div class="q-label" style="font-size: 14px; font-weight: 800; color: var(--c-brand); font-family: var(--font-head); margin-bottom: 0;">{q_header_text}</div>'

    raw_text = visual.get('question_text_visual', '')

    clean_text = re.sub(r'《BLANK》.*?《/BLANK》', ' ____________ ', raw_text)
    clean_text = re.sub(r'《[^》]+》', '', clean_text)
    clean_text = re.sub(r'([❶-❿⓫-⓴])', r'<span class="para-mark-placeholder">\1</span>', clean_text)
    clean_text = clean_text.replace('\n', '<br>')

    try:
        q_type = int(meta.get('question_type', 0))
    except (ValueError, TypeError):
        q_type = 0

    final_passage_html = clean_text

    if q_type == 4:
        parts = re.split(r'(\([ABC]\))', clean_text)
        if len(parts) > 1:
            box_content = parts[0]
            box_content = re.sub(r'(<br>\s*)+$', '', box_content).strip()
            new_html = f'<div class="box-container">{box_content}</div>'
            for i in range(1, len(parts), 2):
                label = parts[i]
                content = parts[i + 1] if i + 1 < len(parts) else ""
                content = re.sub(r'^\s*(<br>\s*)+', '', content)
                content = re.sub(r'(<br>\s*)+$', '', content).strip()
                new_html += f'<div class="order-chunk"><span class="para-mark-placeholder">{label}</span>{content}</div>'
            final_passage_html = new_html

    elif q_type == 5:
        match = re.search(
            r'(<span class="para-mark-placeholder">❶</span>.*?)(?=<span class="para-mark-placeholder">❷</span>)',
            clean_text)
        if match:
            box_content = match.group(1)
            rest_content = clean_text[match.end():]
            final_passage_html = f'<div class="box-container">{box_content}</div><div class="main-text">{rest_content}</div>'

    elif q_type == 6:
        summary_keyword_match = re.search(r'(Summary|요약문)', clean_text, re.IGNORECASE)
        if summary_keyword_match:
            split_idx = summary_keyword_match.start()
            main_text = clean_text[:split_idx]
            summary_text = clean_text[split_idx:]
            final_passage_html = f'{main_text}<div class="summary-sentence-box">{summary_text}</div>'
        else:
            last_mark_match = list(re.finditer(r'<span class="para-mark-placeholder">[❶-❿⓫-⓴]</span>', clean_text))
            if last_mark_match:
                last_idx = last_mark_match[-1].start()
                main_text = clean_text[:last_idx]
                summary_text = clean_text[last_idx:]
                final_passage_html = f'{main_text}<div class="summary-sentence-box">{summary_text}</div>'

    def replace_unicode_with_css_circle(match):
        char = match.group(1)
        unicode_map = {
            '❶': '1', '❷': '2', '❸': '3', '❹': '4', '❺': '5',
            '❻': '6', '❼': '7', '❽': '8', '❾': '9', '❿': '10',
            '⓫': '11', '⓬': '12', '⓭': '13', '⓮': '14', '⓯': '15',
            '⓰': '16', '⓱': '17', '⓲': '18', '⓳': '19', '⓴': '20'
        }
        num = unicode_map.get(char, char)
        if num.startswith('('):
            return f'<span class="para-mark" style="background:none; color:var(--c-brand); width:auto; padding-right:4px;">{num}</span>'
        return f'<span class="para-mark">{num}</span>'

    final_passage_html = re.sub(r'<span class="para-mark-placeholder">(.*?)</span>', replace_unicode_with_css_circle,
                                final_passage_html)
    final_passage_html = re.sub(r'([❶-❿⓫-⓴])', lambda m: replace_unicode_with_css_circle(m), final_passage_html)

    passage_div_class = ""
    vocab_class = ""

    if q_type == 9 or re.search(r'(\d+)[\-~](\d+)', q_header_text):
        passage_div_class = "long-passage"
        vocab_class = "compact-mode"
    elif q_type in [4, 6]:
        passage_div_class = "long-passage"
        vocab_class = "semi-compact-mode"

    options_visual_data = visual.get('options_visual', [])
    flat_options_list = []

    for opt_group in options_visual_data:
        if isinstance(opt_group, str):
            flat_options_list.append(opt_group)
        elif isinstance(opt_group, dict):
            flat_options_list.extend(opt_group.get('options', []))

    options_html = ""
    tf_data = data.get('true_false_details', [])

    if tf_data:
        tf_html = "<div class='q-options'><div class='q-options-title'>▼ True / False Details</div>"
        for i, tf in enumerate(tf_data):
            q_text = str(tf.get('question', ''))
            if is_teacher:
                ans = str(tf.get('answer', ''))
                trans_text = convert_common_tags(str(tf.get('translation', tf.get('trans', ''))))
                color = "#2e7d32" if ans == 'T' else "#d32f2f"
                tf_html += f"<div style='padding: 6px 0; font-size: 12.5px; color: #455a64; font-family: var(--font-serif); display: flex; flex-direction: column; border-bottom: 1px dashed #eceff1;'><div style='display: flex; justify-content: space-between; align-items: flex-start;'><span><b>{i + 1}.</b> {q_text}</span><span style='white-space: nowrap; margin-left: 10px; font-weight: 800; color: {color};'>[ {ans} ]</span></div><div style='font-size: 11.5px; color: #1565c0; font-family: var(--font-sans); margin-top: 4px; font-weight: 500;'>{trans_text}</div></div>"
            else:
                tf_html += f"<div style='padding: 6px 0; font-size: 12.5px; color: #455a64; font-family: var(--font-serif); display: flex; justify-content: space-between; border-bottom: 1px dashed #eceff1;'><span><b>{i + 1}.</b> {q_text}</span><span style='white-space: nowrap; margin-left: 10px; font-weight: 800; color: #90a4ae;'>[ T / F ]</span></div>"
        tf_html += "</div>"
        options_html = tf_html
    elif not is_teacher and options_visual_data and q_type not in [2,
                                                                   5] and '무관한' not in q_header_text and '흐름' not in q_header_text:
        options_html = "<div class='q-options'><div class='q-options-title'>▼ CHOICES</div>"
        for opt_group in options_visual_data:
            if isinstance(opt_group, str):
                options_html += f"<div style='padding: 4px 0; font-size: 13px; color: #455a64; font-family: var(--font-serif);'>{opt_group}</div>"
            elif isinstance(opt_group, dict):
                sub_q = opt_group.get('sub_question', '')
                opts = opt_group.get('options', [])

                if q_type == 9 and sub_q:
                    options_html += f"<div style='padding: 8px 0 4px 0; font-size: 12.5px; font-weight: 700; color: #37474f; font-family: var(--font-head); word-break: keep-all;'>{sub_q}</div>"

                for opt in opts:
                    indent = " margin-left: 8px;" if (q_type == 9 and sub_q) else ""
                    options_html += f"<div style='padding: 4px 0; font-size: 13px; color: #455a64; font-family: var(--font-serif);{indent}'>{opt}</div>"
        options_html += "</div>"

    def highlight_chunk_word(target_word, full_sentence):
        if not target_word or not full_sentence: return full_sentence
        clean_word = re.sub(r'\(.*?\)', '', target_word.lower().strip()).strip()
        base = clean_word
        if len(base) > 3:
            if base.endswith('y'):
                base = base[:-1]
            elif base.endswith('e'):
                base = base[:-1]
            elif base.endswith('s'):
                base = base[:-1]

        pattern = r'\b' + re.escape(base) + r'[a-z]*(?![^<]*>)'
        try:
            return re.sub(pattern, lambda m: f'<span class="c-hl">{m.group()}</span>', full_sentence,
                          flags=re.IGNORECASE)
        except re.error:
            return full_sentence

    vocab_subset = data.get('vocab_list', [])[:10]

    list_for_left = random.sample(vocab_subset, len(vocab_subset))
    list_for_right = random.sample(vocab_subset, len(vocab_subset))

    step1_left = ""
    step1_right = ""

    for v in list_for_left:
        ans = f'<span style="color:#c62828; font-weight:700; letter-spacing:-0.5px;">{get_clean_mean(v.get("meaning", ""))}</span>' if is_teacher else ""
        step1_left += f"""<tr><td class="tt-word">{v["word"]}</td><td><div class="tt-empty-box" style="display:flex; justify-content:center; align-items:center;">{ans}</div></td></tr>"""

    for v in list_for_right:
        final_mean = get_clean_mean(v.get('meaning', ''))
        ans = f'<span style="color:#1565c0; font-family:var(--font-eng); font-weight:700;">{v["word"]}</span>' if is_teacher else ""
        step1_right += f"""<tr><td class="tt-mean-p1">{final_mean}</td><td><div class="tt-empty-box" style="display:flex; justify-content:center; align-items:center;">{ans}</div></td></tr>"""

    vocab_step2 = random.sample(vocab_subset, len(vocab_subset))
    half = (len(vocab_step2) + 1) // 2
    group_a = vocab_step2[:half]
    group_b = vocab_step2[half:]

    def generate_matching_rows(group, is_teacher_mode):
        rows_html = ""
        syn_pool = []
        for i, v in enumerate(group):
            syn = v.get('synonym', '')
            if not syn or syn == '-': syn = "No Synonym"
            clean_syn = syn.replace('/', ',').replace('(', '').replace(')', '')
            parts = [s.strip() for s in clean_syn.split(',') if s.strip()]
            final_syn = ", ".join(parts)
            syn_pool.append({'syn': final_syn, 'id': i})
        random.shuffle(syn_pool)

        svg_lines = ""
        if is_teacher_mode:
            svg_lines += '<svg style="position:absolute; top:0; left:32%; width:36%; height:100%; pointer-events:none; z-index:10; overflow:visible;">'

        for i, v in enumerate(group):
            shuffled_syn = syn_pool[i]['syn'] if i < len(syn_pool) else ""
            dot_cell = '<div style="display:flex; justify-content:space-between; width:100%; padding:0 20px; box-sizing:border-box; margin:0 auto;"><div class="match-dot"></div><div class="match-dot"></div></div>'
            rows_html += f"""<tr><td class="tt-word" style="text-align:left; padding-left:0;">{v["word"]}</td><td style="text-align:center; width:36%;">{dot_cell}</td><td class="tt-mean-p1" style="text-align:right; padding-right:0;">{shuffled_syn}</td></tr>"""

            if is_teacher_mode:
                target_j = next((j for j, sp in enumerate(syn_pool) if sp['id'] == i), -1)
                if target_j != -1:
                    y1 = f"{(i + 0.5) * 100 / len(group)}%"
                    y2 = f"{(target_j + 0.5) * 100 / len(group)}%"
                    svg_lines += f'<line x1="24px" y1="{y1}" x2="calc(100% - 24px)" y2="{y2}" stroke="#ef5350" stroke-width="1.8" opacity="0.6"/>'

        if is_teacher_mode:
            svg_lines += '</svg>'

        return rows_html, svg_lines

    step2_left, step2_svg_left = generate_matching_rows(group_a, is_teacher)
    step2_right, step2_svg_right = generate_matching_rows(group_b, is_teacher)

    step3_rows = ""
    vocab_rows = ""

    for idx, v in enumerate(vocab_subset):
        chunk_en_hl = highlight_chunk_word(v.get('word', ''), v.get('chunk_example', ''))
        chunk_ko = v.get('chunk_translation', '')
        synonyms = v.get('synonym', '')
        final_mean = get_clean_mean(v.get('meaning', ''))

        clean_syn = ""
        if synonyms and synonyms != "-":
            syn_parts = [s.strip() for s in synonyms.replace('/', ',').split(',') if s.strip()]
            clean_syn = ", ".join(syn_parts)
            syn_html = f'<div class="vm-syn">{clean_syn}</div>'
        else:
            syn_html = ""
        vocab_rows += f"""<div class="v-row"><div class="cell col-chk"><div class="chk-box"></div></div><div class="cell col-word"><span class="word-txt">{v["word"]}</span></div><div class="cell col-mean"><span class="vm-kor">{final_mean}</span>{syn_html}</div><div class="cell col-chunk"><span class="vch-en">{chunk_en_hl}</span><span class="vch-ko">{chunk_ko}</span></div></div>"""

    vocab_step3 = random.sample(vocab_subset, len(vocab_subset))

    for v in vocab_step3:
        chunk_raw = v.get('chunk_example', '')
        word_esc = re.escape(v.get('word', '').split('(')[0].strip())
        if len(word_esc) > 2:
            chunk_step3 = re.sub(r'\b' + word_esc + r'[a-z]*(?![^<]*>)',
                                 lambda m: f'<span class="chunk-hl">{m.group()}</span>',
                                 chunk_raw, flags=re.IGNORECASE)
        else:
            chunk_step3 = chunk_raw

        ans = f'<span style="color:#c62828; font-weight:700; letter-spacing:-0.5px;">{v.get("chunk_translation", "")}</span>' if is_teacher else ""
        step3_rows += f"""<tr><td style="color:#37474f; line-height:1.4;">{chunk_step3}</td><td><div class="tt-empty-box" style="display:flex; justify-content:center; align-items:center;">{ans}</div></td></tr>"""

    step3_and_4_html = ""
    eng_defs = data.get('english_definitions', [])

    if eng_defs:
        shuffled_defs = random.sample(eng_defs, len(eng_defs))
        step4_rows = ""
        for ed in shuffled_defs:
            ans = f'<span style="color:#c62828; font-weight:700; letter-spacing:-0.5px;">{ed.get("word", "")}</span>' if is_teacher else ""
            def_text = str(ed.get("definition", ""))
            trans_text = str(ed.get("translation", ed.get("trans", "")))
            if is_teacher:
                def_html = f'{def_text}<br><span style="color:#1565c0; font-size:10.5px; font-weight:600; margin-top:3px; display:inline-block;">{trans_text}</span>'
            else:
                def_html = f'{def_text}<br><span style="opacity:0; visibility:hidden; font-size:10.5px; font-weight:600; margin-top:3px; display:inline-block; user-select:none;">{trans_text if trans_text else "A"}</span>'

            step4_rows += f"""<tr><td style="color:#37474f; line-height:1.3; font-size:10.5px; padding: 4px 6px;">{def_html}</td><td style="width:120px; padding: 4px 6px;"><div class="tt-empty-box" style="display:flex; justify-content:center; align-items:center; height:14px;">{ans}</div></td></tr>"""

        step3_and_4_html = f"""
        <div class="test-section">
            <div class="sec-head-style"><div class="icon-box icon-v">V</div>STEP 3. English Definition (영영 풀이에 해당하는 단어를 쓰시오)</div>
            <table class="step3-table">
                <colgroup><col width="80%"><col width="20%"></colgroup>
                <tbody>{step4_rows}</tbody>
            </table>
        </div>
        """
    else:
        step3_and_4_html = f"""
        <div class="test-section">
            <div class="sec-head-style"><div class="icon-box icon-v">V</div>STEP 3. Chunk Context (단어가 아닌 예시 문장 전체 뜻을 적으시오)</div>
            <table class="step3-table"><colgroup><col width="50%"><col width="50%"></colgroup><thead><tr><th>English Chunk</th><th>Korean Translation</th></tr></thead><tbody>{step3_rows}</tbody></table>
        </div>
        """

    ans_data = data.get('answer_data', {})
    wrong_data = data.get('wrong_answer_analysis', [])
    if not wrong_data:
        wrong_data = data.get('options_analysis', [])

    clues_data = data.get('clues_data', {})

    if is_teacher:
        if ans_data or wrong_data:
            correct_choice = ans_data.get('correct_choice', '')
            explanation_summary = convert_common_tags(ans_data.get('explanation_summary', ''))
            clue_logic = convert_common_tags(ans_data.get('clues', {}).get('logic_flow', ''))

            targets_html = ""
            if 'clues' in ans_data and 'target_sentences' in ans_data['clues']:
                targets_html = "".join([f"<li style='margin-bottom:3px;'>{convert_common_tags(t)}</li>" for t in
                                        ans_data['clues']['target_sentences']])
            opt_box_html = ""
            if flat_options_list:
                for i, opt_text in enumerate(flat_options_list):
                    analysis_item = None
                    opt_num_match = re.search(r'^[①-⑤]', opt_text)
                    opt_num = opt_num_match.group(0) if opt_num_match else str(i + 1)
                    for w in wrong_data:
                        w_choice = str(w.get('choice', '')).strip()
                        # 정확한 번호 매칭 (startswith는 "1"이 "10"도 매칭하는 버그 방지)
                        w_choice_num = re.match(r'^([①-⑤]|\d+)', w_choice)
                        w_choice_id = w_choice_num.group(1) if w_choice_num else w_choice
                        if w_choice_id == opt_num or w_choice_id == str(i + 1):
                            analysis_item = w
                            break

                    if analysis_item:
                        err_type = analysis_item.get('error_type', '')
                        reason = convert_common_tags(
                            analysis_item.get('correct_reason', analysis_item.get('reason', '')))
                        trans = convert_common_tags(analysis_item.get('trans', ''))

                        is_correct = "정답" in err_type
                        badge_class = "err-badge-correct" if is_correct else "err-badge-wrong"
                        badge_html = f"<span class='{badge_class}'>{err_type}</span>"

                        analysis_html = f"<div class='opt-analysis'>{badge_html} <div style='flex:1; word-break:keep-all;'>{reason}</div></div>"
                        trans_html = f"<span class='opt-trans'>{trans}</span>" if trans else ""
                    else:
                        analysis_html = ""
                        trans_html = ""
                    opt_box_html += f"<div class='option-item'><div class='opt-header'><span class='opt-text'>{opt_text}</span></div>{trans_html}{analysis_html}</div>"

            page1_bottom_html = f"""
            <div style="display: flex; gap: 15px; margin-top: 0; flex: 1; min-height: 0;">
                <div style="flex: 1; display: flex; flex-direction: column; overflow: hidden;">
                    <div class="answer-box" style="flex: 1; overflow-y: auto;">
                        <div class="ans-header">✅ 정답: {correct_choice}</div>
                        <div class="ans-content">
                            <div style="font-weight:800; margin-bottom:4px; color:#37474f;">[해설 요약]</div>
                            <div style="margin-bottom:12px; word-break:keep-all;">{explanation_summary}</div>
                            <div style="font-weight:800; margin-bottom:4px; color:#37474f;">[논리적 근거]</div>
                            <ul style="margin-top:0; padding-left:20px; margin-bottom:12px; word-break:keep-all;">{targets_html}</ul>
                            <div style="font-weight:800; margin-bottom:4px; color:#37474f;">[논리 연결]</div>
                            <div style="word-break:keep-all;">{clue_logic}</div>
                        </div>
                    </div>
                </div>
                <div style="flex: 1; display: flex; flex-direction: column; overflow: hidden;">
                    <div class="options-box" style="flex: 1; overflow-y: auto;">
                        <div style="font-family:var(--font-head); font-weight:800; font-size:13px; color:#37474f; margin-bottom:8px; display:flex; align-items:center; gap:6px;">
                            <span>🧐 선택지 분석 (Why & Why not?)</span>
                        </div>
                        {opt_box_html}
                    </div>
                </div>
            </div>
            """
        elif tf_data:
            tf_box_html = ""
            for i, tf in enumerate(tf_data):
                ans = str(tf.get('answer', ''))
                reason = convert_common_tags(str(tf.get('reason', '')))
                badge_class = "err-badge-correct" if ans == 'T' else "err-badge-wrong"

                tf_box_html += f"<div class='option-item' style='display:flex; align-items:flex-start; gap:8px;'><span class='{badge_class}' style='flex-shrink:0;'>Q{i + 1}. {ans}</span><div style='flex:1; font-size:11px; color:#455a64; line-height:1.4; word-break:keep-all; margin-top:1px;'>{reason}</div></div>"

            page1_bottom_html = f"""
            <div style="display: flex; gap: 15px; margin-top: 0; flex: 1; min-height: 0;">
                <div style="flex: 1; display: flex; flex-direction: column; overflow: hidden;">
                    <div class="options-box" style="flex: 1; overflow-y: auto;">
                        <div style="font-family:var(--font-head); font-weight:800; font-size:13px; color:#37474f; margin-bottom:8px; display:flex; align-items:center; gap:6px;">
                            <span>🧐 True / False 팩트 체크</span>
                        </div>
                        {tf_box_html}
                    </div>
                </div>
            </div>
            """
        else:
            page1_bottom_html = f'<div class="sec-vocab {vocab_class}"><div class="v-header"><div class="cell col-chk">Chk</div><div class="cell col-word">Word</div><div class="cell col-mean">Mean & Syn</div><div class="cell col-chunk">Chunk</div></div><div class="v-list">{vocab_rows}</div></div>'
    else:
        page1_bottom_html = f'<div class="sec-vocab {vocab_class}"><div class="v-header"><div class="cell col-chk">Chk</div><div class="cell col-word">Word</div><div class="cell col-mean">Mean & Syn</div><div class="cell col-chunk">Chunk</div></div><div class="v-list">{vocab_rows}</div></div>'

    def clean_text_logic(text):
        processed = re.sub(r'\s*\[/?.*?\]\s*$', '', text)
        processed = re.sub(r'《\s*(?:Theme|Key|Topic)\s*sentence\s*》', '', processed, flags=re.IGNORECASE)
        processed = re.sub(r'《\s*/\s*(?:Theme|Key|Topic)\s*sentence\s*》', '', processed, flags=re.IGNORECASE)
        for _ in range(3):
            processed = re.sub(r'《([^》/]+)》(.*?)《/\1》', r'\2', processed, flags=re.IGNORECASE)
        processed = re.sub(r'《.*?》', '', processed)
        return processed

    def remove_source_bracket(text):
        return re.sub(r'\s*\[.*?\]\s*$', '', text)

    def clean_syntax_debris(text):
        return re.sub(r'\[/?(?:S|V|O|C|OC|M|con|IO|DO)\]', '', text, flags=re.IGNORECASE)

    def convert_num_to_badge_str(num_str):
        try:
            return str(int(num_str))
        except (ValueError, TypeError):
            return str(num_str)

    def parse_local_vocab(word_str):
        if not word_str: return []
        result = []
        items = word_str.split(',')
        for item in items:
            if ':' in item:
                parts = item.split(':', 1)
                result.append({'word': parts[0].strip(), 'meaning': parts[1].strip()})
        return result

    def apply_vocab_style(text, vocab_list_dicts, show_meaning=True):
        if not vocab_list_dicts: return text
        sorted_vocab = sorted(vocab_list_dicts, key=lambda x: len(x.get('word', '').split('[')[0].strip()),
                              reverse=True)
        for v in sorted_vocab:
            raw_word = v.get('word', '').split('[')[0].strip()
            meaning = v.get('meaning', '').replace('①', '').replace('②', ',').strip() if show_meaning else ""
            if not raw_word: continue
            try:
                pattern = re.compile(r'\b' + re.escape(raw_word) + r'\b(?![^<]*>)', re.IGNORECASE)
                replacement = rf'<span class="vocab-container"><span class="vocab-sub">{meaning}</span><span class="vocab-text">\g<0></span></span>'
                text = pattern.sub(replacement, text)
            except re.error:
                pass
        return text

    def convert_eng_tags_color_only(text):
        tags = {'S': 'txt-S', 'V': 'txt-V', 'O': 'txt-O', 'C': 'txt-C', 'OC': 'txt-C', 'M': 'txt-M', 'con': 'txt-con',
                'IO': 'txt-O', 'DO': 'txt-O'}
        for _ in range(2):
            for tag, cls in tags.items():
                pattern = re.compile(rf'\[{tag}\](.*?)\[/{tag}\]', re.IGNORECASE | re.DOTALL)
                text = pattern.sub(rf'<span class="{cls}">\1</span>', text)
        return text

    topic = data.get('topic_data', {})

    raw_kw = topic.get('keywords', '')
    kw = re.sub(r'\[소재\]\s*', '', raw_kw).strip()
    kw = clean_text_logic(kw)

    raw_summ = topic.get('summary', '')
    summ = re.sub(r'\[한줄\s*요약\]\s*', '', raw_summ).strip()
    summ = re.sub(r'\[요약\]\s*', '', summ).strip()
    summ = clean_text_logic(summ)

    raw_kw_en = topic.get('keywords_en', '')
    kw_en = clean_text_logic(raw_kw_en)

    raw_summ_en = topic.get('summary_en', '')
    summ_en = clean_text_logic(raw_summ_en)

    eng_sentences = data.get('sentence_analysis', [])

    if len(eng_sentences) > 10:
        font_size_eng = PAGE_CONFIG["STEP3_LOGIC_FLOW"]["eng_font_size_long"]
        box_padding_eng = "4px 12px 6px 12px"
    else:
        font_size_eng = PAGE_CONFIG["STEP3_LOGIC_FLOW"]["eng_font_size_normal"]
        box_padding_eng = "4px 12px 6px 12px"

    stage_data = data.get('three_stage_flow', [])
    if not stage_data: stage_data = [{"title": "도입", "range": "1"}, {"title": "전개", "range": "2"},
                                     {"title": "결론", "range": "3"}]

    def parse_range(rng_str):
        nums = []
        parts = rng_str.replace('~', '-').split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                subparts = part.split('-')
                if len(subparts) == 2 and subparts[0].strip().isdigit() and subparts[1].strip().isdigit():
                    start, end = int(subparts[0].strip()), int(subparts[1].strip())
                    nums.extend(range(start, end + 1))
            elif part.isdigit():
                nums.append(int(part))
        return nums

    total_sents = len(eng_sentences)
    is_long_passage = total_sents >= 12

    step0_paragraphs_html = ""

    if total_sents >= 12:
        s0_gap = "12px"
        s0_eng_lh = "1.6"
        s0_kor_lh = "1.4"
        s0_pad = "10px 12px"
        s0_eng_fs = "12.5px"
        s0_kor_fs = "10.5px"
    else:
        s0_gap = "20px"
        s0_eng_lh = "1.85"
        s0_kor_lh = "1.6"
        s0_pad = "12px 15px"
        s0_eng_fs = "13.5px"
        s0_kor_fs = "11px"

    for stg in stage_data:
        title = stg.get('title', '')
        rng = stg.get('range', '')
        target_nums = parse_range(rng)

        eng_sents = []
        kor_sents = []

        for n in target_nums:
            s_dict = next((item for item in eng_sentences if str(item.get('num', -1)) == str(n)), None)
            if s_dict:
                raw_eng = s_dict.get('eng_analyzed', '').replace('\\n', ' ')
                clean_eng = clean_syntax_debris(clean_text_logic(raw_eng)).strip()
                clean_eng = clean_eng.replace('/', '')
                clean_eng = re.sub(r'\s+', ' ', clean_eng)
                clean_eng = re.sub(r'^[❶-❿⓫-⓴①-⑳0-9.\s]+', '', clean_eng).strip()

                # 프롤로그는 항상 자연스러운 해석(liberal) 사용
                raw_kor = s_dict.get('kor_liberal_translation', s_dict.get('kor_translation', ''))
                clean_kor = clean_syntax_debris(clean_text_logic(raw_kor)).strip()
                clean_kor = re.sub(r'^[❶-❿⓫-⓴①-⑳0-9.\s]+', '', clean_kor).strip()

                badge_num = convert_num_to_badge_str(s_dict.get('num', n))

                eng_sents.append(
                    f'<span class="para-mark" style="width:1.2em; height:1.2em; line-height:1.2em; font-size:0.7em;">{badge_num}</span> {clean_eng}')
                kor_sents.append(
                    f'<span class="para-mark" style="width:1.2em; height:1.2em; line-height:1.2em; font-size:0.7em; background-color:#90a4ae;">{badge_num}</span> {clean_kor}')

        if not eng_sents: continue

        eng_para = " ".join(eng_sents)
        # 프롤로그 영문에서 핵심 단어 하이라이트 (vocab_subset 기반)
        for v in vocab_subset:
            word_raw = v.get('word', '').split('[')[0].split('(')[0].strip()
            if len(word_raw) > 2:
                base = word_raw
                if base.endswith('y'): base = base[:-1]
                elif base.endswith('e'): base = base[:-1]
                elif base.endswith('s'): base = base[:-1]
                try:
                    hl_pattern = r'\b' + re.escape(base) + r'[a-z]*(?![^<]*>)'
                    eng_para = re.sub(hl_pattern, lambda m: f'<b style="color:var(--c-brand);">{m.group()}</b>', eng_para, flags=re.IGNORECASE)
                except re.error:
                    pass
        kor_para = " ".join(kor_sents)

        clean_title = re.sub(r'^\[.*?\]\s*', '', title).strip()
        if not clean_title:
            clean_title = title

        step0_paragraphs_html += f'''
        <div style="margin-bottom: {s0_gap}; page-break-inside: avoid; break-inside: avoid;">
            <div style="font-family: var(--font-head); font-weight: 800; font-size: 12.5px; color: var(--c-brand); margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                <div style="width:4px; height:12px; background-color:var(--c-accent); border-radius:2px;"></div>{title}
            </div>
            <div style="background: #f8f9fa; border: 1px solid #cfd8dc; border-radius: 8px; padding: {s0_pad};">
                <div style="font-family: var(--font-serif); font-size: {s0_eng_fs}; line-height: {s0_eng_lh}; color: #212121; text-align: justify; margin-bottom: 8px; word-break: break-word;">
                    {eng_para}
                </div>
                <div style="font-family: var(--font-sans); font-size: {s0_kor_fs}; line-height: {s0_kor_lh}; color: #546e7a; text-align: justify; border-top: 1px dashed #cfd8dc; padding-top: 8px; word-break: keep-all;">
                    {kor_para}
                </div>
            </div>
        </div>
        '''

    q_num = base_name.split('-')[-1].strip() if (base_name and '-' in base_name) else (
        re.match(r'(\d+)', meta.get('question_header', '').strip()).group(1) if re.match(r'(\d+)',
                                                                                         meta.get('question_header',
                                                                                                  '').strip()) else "00")

    step0_page_html = f"""
<div class="page-container page-break">
    __PAGE_NUM__
    <div class="page-header">
        <div class="ph-left">
            <span class="ph-source-origin">{source_origin}</span>
            <div class="unit-badge-group">
                <span class="ub-label">NO.</span>
                <span class="ub-num">{q_num}</span>
            </div>
        </div>
        <div class="ph-right">PROLOGUE [Full Text]</div>
    </div>
    <div class="p0-body" style="padding: 10mm 15mm; flex: 1; display: block; overflow: hidden; background: #fff;">
        <div class="sec-head-style" style="margin-bottom: 15px;"><div class="icon-box icon-r">R</div>Read & Comprehend (정답 반영 본문 한눈에 보기)</div>
        <div style="display: flex; flex-direction: column;">
            {step0_paragraphs_html}
        </div>
    </div>
    <div class="page-footer">
        <div class="footer-logo"></div>
    </div>
</div>
"""

    # ==========================================
    # 5페이지 STEP-5 동적 분할 로직 (문장 개수에 따라 자동 2장 렌더링)
    # ==========================================
    step5_blocks = []

    if total_sents <= 10:
        row_mb = "1cm"
    else:
        row_mb = "0.6cm"

    for i, stg in enumerate(stage_data):
        title = stg.get('title', '')
        rng = stg.get('range', '')

        match = re.match(r'(\[.*?\])', title)
        short_title = match.group(1) if match else (title.split()[0] if title else "")

        target_nums = parse_range(rng)

        step5_blocks.append(('divider', f'<div class="logic-divider">{short_title}</div>'))

        for n in target_nums:
            s_dict = next((item for item in eng_sentences if str(item.get('num', -1)) == str(n)), None)
            if s_dict:
                raw_eng = s_dict.get('eng_analyzed', '').replace('\\n', '\n')
                raw_eng_clean = clean_text_logic(raw_eng)
                text_body = re.sub(r'^[❶-❿⓫-⓴]', '', raw_eng_clean.strip()).strip()

                num_str = str(n)
                num_html = f'<span class="para-mark">{num_str}</span>'

                star_html = ""
                card_class = "ec-normal"
                if 'Theme sentence' in raw_eng:
                    star_html = '<span class="star-red">★</span>'
                    card_class = "ec-theme"
                elif 'Key sentence' in raw_eng:
                    star_html = '<span class="star-yel">★</span>'
                    card_class = "ec-key"

                st_data = s_dict.get('syntax_tip', [])
                syntax_html = ""
                if st_data:
                    st_items = []
                    for st in st_data:
                        t_tag = st.get('tag', '')
                        tgt = st.get('target', '')
                        exp = st.get('explanation', '')
                        t_color = "#d32f2f" if "어법" in t_tag else ("#1976d2" if "구조" in t_tag else "#f57c00")

                        if tgt:
                            target_parts = [p.strip() for p in re.split(r'[~…⋯]+|\.\.\.', tgt) if p.strip()]
                            for idx, part in enumerate(target_parts):
                                if not part: continue
                                words = re.findall(r'\w+|[^\w\s]', part)
                                escaped_words = [re.escape(w) for w in words]
                                part_pattern = r'(?:\[/?.*?\]|/|\s)+'.join(escaped_words)

                                if idx == 0:
                                    def st_replacer_first(m):
                                        text = m.group(0)
                                        parts = re.split(r'(\[/?.*?\])', text)
                                        res = ""
                                        for p in parts:
                                            if p.startswith('[') and p.endswith(']'):
                                                res += p
                                            elif p:
                                                res += f'<span style="background-color:#dcdcdc; border-radius:3px; padding:2px 0;">{p}</span>'
                                        badge = f'<span style="position:relative; display:inline;"><span style="position:absolute; top:-12px; left:0; font-size:7.5px; color:{t_color}; font-weight:800; font-family:var(--font-head); letter-spacing:-0.5px; line-height:1; white-space:nowrap; z-index:10;">{t_tag}</span></span>'
                                        return badge + res

                                    try:
                                        text_body = re.sub(f'({part_pattern})', st_replacer_first, text_body, count=1,
                                                           flags=re.IGNORECASE)
                                    except re.error:
                                        pass
                                else:
                                    def st_replacer_rest(m):
                                        text = m.group(0)
                                        parts = re.split(r'(\[/?.*?\])', text)
                                        res = ""
                                        for p in parts:
                                            if p.startswith('[') and p.endswith(']'):
                                                res += p
                                            elif p:
                                                res += f'<span style="background-color:#dcdcdc; border-radius:3px; padding:2px 0;">{p}</span>'
                                        return res

                                    try:
                                        text_body = re.sub(f'({part_pattern})', st_replacer_rest, text_body, count=1,
                                                           flags=re.IGNORECASE)
                                    except re.error:
                                        pass

                        st_items.append(f"""
                        <div style="display:flex; align-items:flex-start; gap:4px; margin-bottom:2px;">
                            <span style="color:{t_color}; font-weight:800; flex-shrink:0;">{t_tag}</span>
                            <span style="color:#455a64; line-height:1.4; flex:1; min-width:0; word-break:break-word; overflow-wrap:break-word;"><b style="color:#212121;">"{tgt}"</b> : {exp}</span>
                        </div>
                        """)
                    syntax_html = f'<div style="margin-top: 6px; font-size: 10.5px; font-family: var(--font-sans);">{"".join(st_items)}</div>'

                local_vocab = parse_local_vocab(s_dict.get('context_meaning', ''))
                eng_with_vocab = apply_vocab_style(text_body, local_vocab, show_meaning=True)

                eng_html = convert_eng_tags_color_only(eng_with_vocab)

                eng_html = clean_syntax_debris(eng_html)

                if TRANSLATION_MODE == "literal":
                    raw_kor_clean = re.sub(r'《/?.*?》', '', s_dict.get('kor_translation',
                                                                      s_dict.get('kor_liberal_translation',
                                                                                 ''))).strip()
                else:
                    raw_kor_clean = re.sub(r'《/?.*?》', '', s_dict.get('kor_liberal_translation',
                                                                      s_dict.get('kor_translation', ''))).strip()

                kor_html = convert_eng_tags_color_only(raw_kor_clean)
                kor_html = clean_syntax_debris(kor_html)

                eng_fs_val = int(font_size_eng.replace("px", "")) - 1
                kor_fs_val = PAGE_CONFIG["STEP5_INTENSIVE"]["kor_font_size"]
                s5_eng_lh = PAGE_CONFIG["STEP5_INTENSIVE"]["eng_line_height"]
                s5_kor_lh = PAGE_CONFIG["STEP5_INTENSIVE"]["kor_line_height"]

                row_html = f"""
                <div class="row-pair" style="display: flex; align-items: flex-start; padding: 0; width: 100%; margin-bottom: {row_mb}; box-sizing: border-box; page-break-inside: avoid; break-inside: avoid;">
                    <div class="rp-eng" style="flex: 0 0 70%; width: 70%; max-width: 70%; min-width: 0; padding-right: 15px; border-right: 1px dashed #cfd8dc; display: flex; flex-direction: column; box-sizing: border-box; overflow-wrap: break-word; overflow: hidden;">
                        <div class="eng-analyzed-box {card_class}" style="font-size: {eng_fs_val}px; padding: {box_padding_eng}; padding-top: 4px; line-height: {s5_eng_lh}; margin-bottom: 0; word-wrap: break-word; overflow-wrap: break-word;">
                            {num_html}{star_html} {eng_html}
                        </div>
                        {syntax_html}
                    </div>
                    <div class="rp-kor" style="flex: 0 0 30%; width: 30%; max-width: 30%; min-width: 0; padding-left: 15px; font-size: {kor_fs_val}px; line-height: {s5_kor_lh}; color: #546e7a; text-align: left; font-weight: 400; padding-top: 10px; box-sizing: border-box; word-break: normal; overflow-wrap: break-word;">
                        {kor_html}
                    </div>
                </div>
                """
                step5_blocks.append(('row', row_html))

    total_rows = sum(1 for b_type, _ in step5_blocks if b_type == 'row')
    half_limit = (total_rows + 1) // 2

    pages = []
    current_page_html = ""
    row_count = 0
    current_section_title = ""

    for b_type, b_content in step5_blocks:
        if b_type == 'row':
            if row_count >= half_limit:
                pages.append(current_page_html)
                current_page_html = ""
                row_count = 0
                if current_section_title:
                    current_page_html += f'<div class="logic-divider" style="margin-top:15px; margin-bottom:1cm;">{current_section_title} (계속)</div>'
            current_page_html += b_content
            row_count += 1
        elif b_type == 'divider':
            match = re.search(r'<div class="logic-divider">(.*?)</div>', b_content)
            if match:
                current_section_title = match.group(1)

            if row_count >= half_limit:
                pages.append(current_page_html)
                current_page_html = ""
                row_count = 0

            if not current_page_html:
                current_page_html += b_content.replace('<div class="logic-divider">',
                                                       '<div class="logic-divider" style="margin-top: 15px; margin-bottom: 0.5cm;">')
            else:
                current_page_html += b_content.replace('<div class="logic-divider">',
                                                       '<div class="logic-divider" style="margin-top: 0.5cm; margin-bottom: 0.5cm;">')

    if current_page_html:
        pages.append(current_page_html)

    if not pages:
        pages.append("")

    step5_pages_final_html = ""
    total_p = len(pages)

    for p_idx, sents_list in enumerate(pages):
        p_str = f" ({p_idx + 1}/{total_p})" if total_p > 1 else ""

        if p_idx == 0:
            top_box = f"""
            <div class="topic-box" style="margin-bottom: 0;">
                <div class="tb-row"><div class="tb-label lbl-key">소재</div><div class="tb-content" style="font-weight: 800; font-size: 14px;">{kw}</div></div>
                <div class="tb-row"><div class="tb-label lbl-sum">한줄요약</div><div class="tb-content">{summ}</div></div>
            </div>
            <div style="display: flex; flex-direction: column; flex: 1; margin-top: -5px;">
                <div style="display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 1px; line-height: 1;">
                    <div style="font-family: var(--font-eng); font-weight: 800; font-size: 12px; color: var(--c-brand);">Main Text <span style="font-family: var(--font-sans); font-size: 11px;">(본문)</span></div>
                    <div style="font-size: 10.5px; color: #90a4ae; font-weight: 600; font-family: var(--font-sans); letter-spacing: -0.3px;">* 수업 후 반드시 읽으면서 해석 되는지 확인하세요.</div>
                </div>
            """
        else:
            top_box = f"""
            <div style="display: flex; flex-direction: column; flex: 1; margin-top: 5px;">
                <div style="display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 1px; line-height: 1;">
                    <div style="font-family: var(--font-eng); font-weight: 800; font-size: 12px; color: var(--c-brand);">Main Text <span style="font-family: var(--font-sans); font-size: 11px;">(본문 - 계속)</span></div>
                </div>
            """

        page_html = f"""
<div class="page-container page-break">
    __PAGE_NUM__
    <div class="page-header">
        <div class="ph-left">
            <span class="ph-source-origin">{source_origin}</span>
            <div class="unit-badge-group">
                <span class="ub-label">NO.</span>
                <span class="ub-num">{q_num}</span>
            </div>
        </div>
        <div class="ph-right">STEP-5 [Intensive]<span style="font-size:11px; margin-left:4px; color:#90a4ae;">{p_str}</span></div>
    </div>
    <div class="p2-body">
        {top_box}
            <div class="split-container" style="border-top: 2px solid var(--c-brand); margin-top: 0; justify-content: flex-start; display: flex; flex-direction: column;">
                {sents_list}
            </div>
        </div>
    </div>
    <div class="page-footer">
        <div class="footer-logo"></div>
    </div>
</div>
        """
        step5_pages_final_html += page_html

    # ==========================================
    # Logic Flow (Step 6) Generation -> (Actually STEP-3 in the logic flow container)
    # ==========================================
    themes = ["theme-blue", "theme-yel", "theme-grn"]

    p3_logic_clean_html_p1 = ""
    p3_logic_clean_html_p2 = ""

    intro_cnt = 0
    concl_cnt = 0
    for stg in stage_data:
        stg_title = stg.get('title', '')
        if '도입' in stg_title:
            intro_cnt = len(parse_range(stg.get('range', '')))
        elif '결론' in stg_title:
            concl_cnt = len(parse_range(stg.get('range', '')))

    if (intro_cnt == 1 and concl_cnt == 1) or total_sents >= 8:
        step3_margin_tier = "compact"
    elif total_sents == 7:
        step3_margin_tier = "semi-compact"
    else:
        step3_margin_tier = "standard"

    if total_sents >= 10:
        step3_lh = PAGE_CONFIG["STEP3_LOGIC_FLOW"]["line_height_compact"]
    elif total_sents >= 7:
        step3_lh = PAGE_CONFIG["STEP3_LOGIC_FLOW"]["line_height_semi_compact"]
    else:
        step3_lh = PAGE_CONFIG["STEP3_LOGIC_FLOW"]["line_height_standard"]

    for i, stg in enumerate(stage_data):
        title = stg.get('title', '')
        rng = stg.get('range', '')
        content = stg.get('content', '').replace('\n', '<br>')

        content = re.sub(r'《fill》(.*?)《/fill》', r'<U>\1</U>', content, flags=re.IGNORECASE)
        content = re.sub(r'<fill>(.*?)</fill>', r'<U>\1</U>', content, flags=re.IGNORECASE)

        target_nums = parse_range(rng)

        stage_sents_list = []
        combined_eng_for_stage = ""

        for n in target_nums:
            s_dict = next((item for item in eng_sentences if str(item.get('num', -1)) == str(n)), None)
            if s_dict:
                raw_eng = s_dict.get('eng_analyzed', '').replace('\\n', '\n')
                combined_eng_for_stage += " " + raw_eng

                p3_clean_eng = re.sub(r'\[/?(?:S|V|O|C|OC|M|con|IO|DO)\]', '', raw_eng, flags=re.IGNORECASE)
                p3_clean_eng = re.sub(r'《.*?》', '', p3_clean_eng)
                p3_clean_eng = p3_clean_eng.replace('/', '')
                p3_clean_eng = re.sub(r'\s+', ' ', p3_clean_eng).strip()
                p3_text_body = re.sub(r'^[❶-❿⓫-⓴]', '', p3_clean_eng).strip()

                num_str = str(n)
                num_html = f'<span class="para-mark">{num_str}</span>'

                local_vocab = parse_local_vocab(s_dict.get('context_meaning', ''))
                p3_text_body = apply_vocab_style(p3_text_body, local_vocab, show_meaning=False)

                stage_sents_list.append(
                    f'<div class="eng-analyzed-box ec-normal" style="font-size: {font_size_eng}; padding: {box_padding_eng}; margin-bottom: 6px; line-height: {step3_lh}; word-wrap: break-word; overflow-wrap: break-word;">{num_html} {p3_text_body}</div>')

        if stage_sents_list:
            stage_sents_list[-1] = stage_sents_list[-1].replace('margin-bottom: 6px;', 'margin-bottom: 0px;')
        stage_sents_html = "".join(stage_sents_list)

        if total_sents >= 7 and i == len(stage_data) - 1:
            fb_body_text_size = PAGE_CONFIG["STEP3_LOGIC_FLOW"]["logic_box_text_size_compact"]
            vocab_container_size = PAGE_CONFIG["STEP3_LOGIC_FLOW"]["logic_box_vocab_size_compact"]
            syn_mean_size = PAGE_CONFIG["STEP3_LOGIC_FLOW"]["logic_box_syn_size_compact"]
        else:
            fb_body_text_size = PAGE_CONFIG["STEP3_LOGIC_FLOW"]["logic_box_text_size"]
            vocab_container_size = PAGE_CONFIG["STEP3_LOGIC_FLOW"]["logic_box_vocab_size"]
            syn_mean_size = PAGE_CONFIG["STEP3_LOGIC_FLOW"]["logic_box_syn_size"]

        stage_vocab_html = ""
        horizontal_vocab_html = ""
        found_vocabs = []
        for v in vocab_subset:
            word_raw = v.get('word', '').split('[')[0].split('(')[0].strip()
            if len(word_raw) > 2:
                base = word_raw
                if base.endswith('y'):
                    base = base[:-1]
                elif base.endswith('e'):
                    base = base[:-1]
                elif base.endswith('s'):
                    base = base[:-1]
                pattern = r'\b' + re.escape(base) + r'[a-z]*'
                if re.search(pattern, combined_eng_for_stage, re.IGNORECASE):
                    found_vocabs.append(v)

        if found_vocabs:
            if len(target_nums) == 1:
                horizontal_vocab_html += f'<div style="margin-top: 8px; padding: 8px 12px; background-color: #f8f9fa; border: 1px dashed #cfd8dc; border-radius: 6px; display: flex; flex-wrap: wrap; gap: 12px; font-size: {vocab_container_size}; color: #37474f;">'
                for v in found_vocabs:
                    w = v.get('word', '')
                    syn = v.get('synonym', '')
                    if syn and syn != '-':
                        syn_parts = [s.strip() for s in syn.replace('/', ',').split(',') if s.strip()]
                        syn_clean = ", ".join(syn_parts)
                        syn_html = f'<span style="font-size: {syn_mean_size}; color: #5d4037; background: rgba(121, 85, 72, 0.08); padding: 1px 5px; border-radius: 3px; font-family: var(--font-eng); display: inline-block; margin-left: 0;">≒ {syn_clean}</span>'
                    else:
                        m_raw = v.get('meaning', '')
                        m = re.sub(r'[①-⑳]', '|', m_raw)
                        m = re.sub(r'\(.*?\)', '', m).strip()
                        parts = [p.strip() for p in m.split('|') if p.strip()]
                        m_clean = ", ".join(parts)
                        syn_html = f'<span style="font-size: {syn_mean_size}; color: #546e7a; background: rgba(144, 164, 174, 0.1); padding: 1px 5px; border-radius: 3px; font-family: var(--font-sans); display: inline-block; margin-left: 0;">{m_clean}</span>'
                    horizontal_vocab_html += f'<div style="display: flex; align-items: baseline; gap: 4px;"><b style="color:var(--c-brand); font-family:var(--font-eng); font-weight:600;">{w}</b>{syn_html}</div>'
                horizontal_vocab_html += '</div>'
            else:
                stage_vocab_html += f'<div style="margin-top: auto; padding-top: 8px; border-top: 1px dashed #90a4ae; font-size: {vocab_container_size}; color: #37474f;">'
                for v in found_vocabs:
                    w = v.get('word', '')
                    syn = v.get('synonym', '')
                    if syn and syn != '-':
                        syn_parts = [s.strip() for s in syn.replace('/', ',').split(',') if s.strip()]
                        syn_clean = ", ".join(syn_parts)
                        syn_html = f'<span style="font-size: {syn_mean_size}; color: #5d4037; background: rgba(121, 85, 72, 0.08); padding: 1px 5px; border-radius: 3px; font-family: var(--font-eng); display: inline-block; margin-left: 0;">≒ {syn_clean}</span>'
                    else:
                        m_raw = v.get('meaning', '')
                        m = re.sub(r'[①-⑳]', '|', m_raw)
                        m = re.sub(r'\(.*?\)', '', m).strip()
                        parts = [p.strip() for p in m.split('|') if p.strip()]
                        m_clean = ", ".join(parts)
                        syn_html = f'<span style="font-size: {syn_mean_size}; color: #546e7a; background: rgba(144, 164, 174, 0.1); padding: 1px 5px; border-radius: 3px; font-family: var(--font-sans); display: inline-block; margin-left: 0;">{m_clean}</span>'
                    stage_vocab_html += f'<div style="margin-bottom: 4px; line-height:1.3; display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px;"><b style="color:var(--c-brand); font-family:var(--font-eng); font-weight:600;">{w}</b>{syn_html}</div>'
                stage_vocab_html += '</div>'

        stage_sents_html += horizontal_vocab_html

        theme_class = themes[i] if i < len(themes) else "theme-blue"

        match = re.match(r'(\[.*?\])', title)
        short_title = match.group(1) if match else (title.split()[0] if title else "")

        clean_title = re.sub(r'^\[.*?\]\s*', '', title).strip()

        p3_title_html = f'<span class="fb-struct-label" style="font-family: var(--font-head); color:#000; font-size: 11.5px; font-weight:700;">{clean_title}</span>'

        rng_clean = rng.replace(' ', '')
        rng_len = len(rng_clean)

        if rng_len <= 1:
            f_size = "11px"
        elif rng_len <= 3:
            f_size = "10px"
        elif rng_len <= 5:
            f_size = "8px"
        else:
            f_size = "7px"

        logic_box_html = f'''
        <div class="flow-box {theme_class}" style="margin-bottom: 0px; width: 100%; height: 100%; box-sizing: border-box;">
            <div class="fb-header" style="padding: 10px;">
                <div class="fb-label-row">
                    {p3_title_html}
                    <span class="fb-range-badge" style="background-color: rgba(0,0,0,0.06); font-size: {f_size};">{rng_clean}</span>
                </div>
            </div>
            <div class="fb-body">
                <div class="fb-body-text" style="font-size: {fb_body_text_size}; line-height: 1.6; font-family: var(--font-head); text-align: justify; word-break: keep-all; display: flex; flex-direction: column; height: 100%;">
                    <div style="margin-bottom: 10px;">{content}</div>
                    {stage_vocab_html}
                </div>
            </div>
        </div>
        '''

        if step3_margin_tier == "compact":
            div_mt, div_mb, cont_mb, cont_mt = "2px", "0px", "2px", "0px"
        elif step3_margin_tier == "semi-compact":
            div_mt, div_mb, cont_mb, cont_mt = "6px", "1px", "6px", "1px"
        else:
            div_mt, div_mb, cont_mb, cont_mt = "10px", "3px", "10px", "3px"

        stage_block_html = f'''
        <div class="logic-divider" style="margin-top: {div_mt}; margin-bottom: {div_mb};">{short_title}</div>
        <div class="stage-container" style="display: flex; gap: 20px; align-items: stretch; margin-bottom: {cont_mb}; margin-top: {cont_mt}; box-sizing: border-box;">
            <div class="stage-left" style="flex: 0 0 calc(70% - 10px); width: calc(70% - 10px); max-width: calc(70% - 10px); display: flex; flex-direction: column; box-sizing: border-box;">
                {stage_sents_html}
            </div>
            <div class="stage-right" style="flex: 0 0 calc(30% - 10px); width: calc(30% - 10px); max-width: calc(30% - 10px); display: flex; box-sizing: border-box;">
                {logic_box_html}
            </div>
        </div>
        '''

        if is_long_passage and i == len(stage_data) - 1 and len(stage_data) > 1:
            p3_logic_clean_html_p2 += stage_block_html
        else:
            p3_logic_clean_html_p1 += stage_block_html

    reconstructed_sentences = []
    for sent in eng_sentences:
        s_num = sent.get('num', '')
        s_raw = sent.get('eng_analyzed', '')

        s_clean = re.sub(r'\[/?(?:S|V|O|C|OC|M|con|IO|DO)\]', '', s_raw, flags=re.IGNORECASE)
        s_clean = re.sub(r'《.*?》', '', s_clean)
        s_clean = re.sub(r'\s*\[.*?\]', '', s_clean)
        s_clean = re.sub(r'^[❶-❿⓫-⓴①-⑳0-9.\s]+', '', s_clean).strip()
        s_clean = s_clean.replace('/', '')
        s_clean = re.sub(r'\s+', ' ', s_clean).strip()

        badge_num = convert_num_to_badge_str(s_num)
        reconstructed_sentences.append(f'<span class="para-mark">{badge_num}</span> {s_clean}')

    plain_passage_base = " ".join(reconstructed_sentences)

    pred_data = data.get('predicted_exam_data', [])
    anno_rows = ""

    processing_data = []
    for idx, item in enumerate(pred_data):
        item_copy = item.copy()
        item_copy['original_index'] = idx + 1
        item_copy['seq_num'] = idx + 1

        raw_p_type = str(item.get('type', '')).lower()
        if 'insert' in raw_p_type or '삽입' in raw_p_type:
            s_num = item.get('sentence_no')
            found_sent = next((s for s in data.get('sentence_analysis', []) if str(s.get('num', -1)) == str(s_num)),
                              None)
            if found_sent:
                raw = found_sent.get('eng_analyzed', '')
                no_tags = re.sub(r'《.*?》', '', raw)
                no_tags = re.sub(r'\[.*?\]', '', no_tags)
                target = re.sub(r'^[\s\d.❶-❿⓫-⓴①-⑳]+', '', no_tags).strip()
                target = target.replace('/', '')
                item_copy['real_target'] = re.sub(r'\s+', ' ', target).strip()
            else:
                item_copy['real_target'] = item.get('target', '')
        else:
            item_copy['real_target'] = item.get('target', '')
        processing_data.append(item_copy)

    hl_passage = plain_passage_base

    highlight_queue = sorted(processing_data, key=lambda x: len(x['real_target']), reverse=True)
    for item in highlight_queue:
        target = item['real_target']
        seq_num = item['seq_num']
        raw_p_type = str(item.get('type', '')).lower()

        if 'blank' in raw_p_type or '빈칸' in raw_p_type:
            border_color, bg_color, label = "#7cb342", "rgba(124, 179, 66, 0.15)", "빈칸출제"
        elif 'implied' in raw_p_type or '함축' in raw_p_type or 'meaning' in raw_p_type:
            border_color, bg_color, label = "#ab47bc", "rgba(171, 71, 188, 0.15)", "함축의미"
        elif 'grammar' in raw_p_type or '어법' in raw_p_type:
            border_color, bg_color, label = "#d32f2f", "rgba(211, 47, 47, 0.15)", "어법주의"
        elif 'insert' in raw_p_type or '삽입' in raw_p_type:
            border_color, bg_color, label = "#29b6f6", "rgba(41, 182, 246, 0.15)", "문장삽입"
        else:
            border_color, bg_color, label = "#fb8c00", "rgba(251, 140, 0, 0.15)", "서술형"

        label_text = f"{seq_num}. {label}"
        escaped_words = [re.escape(w) for w in target.split()]
        join_pattern = r'(?:\s|<[^>]+>|\[/?.*?\]|《/?.*?》)+'
        pattern_str = join_pattern.join(escaped_words)

        try:
            replacement = rf'<span class="visual-exam-target" style="border-bottom: 2px dashed {border_color}; background-color: {bg_color};"><span class="visual-exam-label" style="background-color: {border_color}; font-size:8.5px; top:-14px; padding:1px 3px;">{label_text}</span>\g<0></span>'
            regex = re.compile(f'({pattern_str})', re.IGNORECASE)
            hl_passage = regex.sub(replacement, hl_passage, count=1)
        except re.error:
            pass

    for item in processing_data:
        seq_num = item['seq_num']
        target = item.get('target', '').strip()
        raw_p_type = str(item.get('type', '')).lower()
        reason = item.get('reason', '')

        if 'grammar' in raw_p_type or '어법' in raw_p_type:
            wrong = item.get('distractor', item.get('wrong_form', target))
            if '①' in wrong or '②' in wrong or '③' in wrong:
                parts = re.split(r'[①②③④⑤⑥⑦⑧⑨⑩]', wrong)
                parts = [p.strip() for p in parts if p.strip()]
                if parts:
                    wrong = random.choice(parts)
            elif '/' in wrong:
                wrong = wrong.split('/')[0].strip()
            item['chosen_distractor'] = wrong

        if 'blank' in raw_p_type or '빈칸' in raw_p_type:
            badge_bg, label = "#7cb342", "빈칸"
            extra_val = item.get("paraphrase", "")
            if not extra_val: extra_val = "변형 없음"
            trans_val = item.get("paraphrase_trans", "")
            trans_html = f'<div style="font-family:var(--font-sans); font-size:10px; color:#78909c; font-weight:500; margin-top:2px; word-break:keep-all;">{trans_val}</div>' if trans_val else ""
            left_content = f'<div style="font-family:var(--font-eng); font-size:12px; font-weight:600; color:#212121; margin-bottom:5px; line-height: 1.3;">{target}</div><div style="display:flex; align-items:flex-start; gap:6px;"><div style="color:#7cb342; font-weight:900; margin-top: 1px;">➔</div><div style="flex:1;"><div style="font-size:11px; color:#90a4ae; font-weight:700;">[변형] <span style="font-family:var(--font-eng); font-size:11.5px; font-weight:600; color:#37474f;">{extra_val}</span></div>{trans_html}</div></div>'

        elif 'implied' in raw_p_type or '함축' in raw_p_type or 'meaning' in raw_p_type:
            badge_bg, label = "#ab47bc", "함축"
            extra_val = item.get("meaning", "")
            trans_val = item.get("meaning_trans", "")
            trans_html = f'<div style="font-family:var(--font-sans); font-size:10px; color:#78909c; font-weight:500; margin-top:2px; word-break:keep-all;">{trans_val}</div>' if trans_val else ""
            left_content = f'<div style="font-family:var(--font-eng); font-size:12px; font-weight:600; color:#212121; margin-bottom:5px; line-height: 1.3;">{target}</div><div style="display:flex; align-items:flex-start; gap:6px;"><div style="color:#ab47bc; font-weight:900; margin-top: 1px;">➔</div><div style="flex:1;"><div style="font-size:11px; color:#90a4ae; font-weight:700;">[의미] <span style="font-family:var(--font-eng); font-size:11.5px; font-weight:600; color:#37474f;">{extra_val}</span></div>{trans_html}</div></div>'

        elif 'grammar' in raw_p_type or '어법' in raw_p_type:
            badge_bg, label = "#d32f2f", "어법"
            wrong = item.get("distractor", "")
            left_content = f'<div style="font-family:var(--font-eng); font-size:12px; font-weight:600; color:#212121; margin-bottom:5px; line-height: 1.3;">{target}</div><div style="display:flex; align-items:flex-start; gap:6px;"><div style="color:#d32f2f; font-weight:900; margin-top: 1px;">➔</div><div style="flex:1;"><div style="font-size:11px; color:#90a4ae; font-weight:700;">[오답 함정] <span style="font-family:var(--font-eng); font-size:11.5px; font-weight:600; color:#d32f2f;">{wrong} (X)</span></div></div></div>'

        elif 'insert' in raw_p_type or '삽입' in raw_p_type:
            badge_bg, label = "#29b6f6", "삽입"
            left_content = f'<div style="font-family:var(--font-eng); font-size:12px; font-weight:600; color:#212121; margin-bottom:5px; line-height: 1.3;">{target}</div><div style="display:flex; align-items:flex-start; gap:6px;"><div style="color:#29b6f6; font-weight:900; margin-top: 1px;">➔</div><div style="flex:1;"><div style="font-size:11px; color:#90a4ae; font-weight:700;">[위치] <span style="font-family:var(--font-sans); font-size:11.5px; font-weight:600; color:#263238;">#{item.get("sentence_no", "")}번 문장 근처</span></div></div></div>'

        else:
            badge_bg, label = "#fb8c00", "서술"
            left_content = f'<div style="font-family:var(--font-eng); font-size:12px; font-weight:600; color:#212121; margin-bottom:5px; line-height: 1.3;">{target}</div><div style="display:flex; align-items:flex-start; gap:6px;"><div style="color:#fb8c00; font-weight:900; margin-top: 1px;">➔</div><div style="flex:1;"><div style="font-size:11px; color:#90a4ae; font-weight:700;">[출제 포인트] <span style="font-family:var(--font-sans); font-size:11.5px; font-weight:600; color:#263238;">{item.get("key_point", "")}</span></div></div></div>'

        anno_rows += f"""
        <div style="border: 1px dashed #cfd8dc; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px; display: flex; align-items: stretch; background: #fff;">
            <div style="flex: 5.5; display: flex; align-items: flex-start; gap: 12px; border-right: 1px dashed #eceff1; padding-right: 12px;">
                <div style="background:{badge_bg}; color:white; font-size:10.5px; font-weight:700; padding:4px 8px; border-radius:4px; font-family:var(--font-head); white-space:nowrap; flex-shrink:0;">{seq_num}. {label}</div>
                <div style="flex:1; line-height:1.35; word-break:keep-all; display:flex; flex-direction:column; justify-content:center;">{left_content}</div>
            </div>
            <div style="flex: 4.5; font-size: 10.5px; color: #546e7a; line-height: 1.45; padding-left: 12px; word-break: keep-all; display:flex; align-items:center;">
                <div><span style="opacity:0.5; margin-right:4px;">💡</span>{reason}</div>
            </div>
        </div>
        """

    csat = data.get('topic_data', {}).get('csat_summary_problem', {})
    answer_key = str(csat.get('answer', '')).strip()
    summary_kor = csat.get('translation', '해석 데이터가 없습니다.')

    ans_words = []
    if flat_options_list and answer_key:
        ans_idx = -1
        match = re.search(r'([1-5①-⑤])', answer_key)
        if match:
            char = match.group(1)
            if char in '1①':
                ans_idx = 0
            elif char in '2②':
                ans_idx = 1
            elif char in '3③':
                ans_idx = 2
            elif char in '4④':
                ans_idx = 3
            elif char in '5⑤':
                ans_idx = 4

        if 0 <= ans_idx < len(flat_options_list):
            ans_str = flat_options_list[ans_idx]
            ans_str = re.sub(r'^[①-⑤\d\.\s]+', '', ans_str)
            ans_words = [w.strip() for w in re.split(r'[.]{2,}|[…⋯]+|,|/', ans_str) if w.strip()]
    else:
        if answer_key:
            clean_ans = re.sub(r'\([A-Z]\)', '', answer_key)
            ans_words = [w.strip() for w in re.split(r'[.]{2,}|[…⋯]+|,|/', clean_ans) if w.strip()]

    if len(ans_words) < 2:
        ans_dict = {}
        for char in ['A', 'B']:
            pattern1 = rf'\({char}\)[^\(\)]*?\(([A-Za-z]+)\)'
            m1 = re.search(pattern1, summary_kor)
            if m1:
                ans_dict[char] = m1.group(1)
            else:
                pattern2 = rf'\({char}\)\s*\*\*([A-Za-z]+)\*\*'
                m2 = re.search(pattern2, summary_kor)
                if m2:
                    ans_dict[char] = m2.group(1)

        if 'A' in ans_dict and 'B' in ans_dict:
            ans_words = [ans_dict['A'], ans_dict['B']]
        elif 'A' in ans_dict and len(ans_words) < 1:
            ans_words = [ans_dict['A']]

    def process_page5_summary(text, is_teacher_mode, ans_words_list):
        if '《' in text or '**' in text:
            if is_teacher_mode:
                text = re.sub(r'《(.*?)》', r'<span class="txt-org">\1</span>', text)
                text = re.sub(r'\*\*(.*?)\*\*', r'<span class="txt-org">\1</span>', text)
            else:
                def hint_replacer_tags(match):
                    word = match.group(1).strip()
                    prefix_match = re.match(r'^(\([A-Z]\)\s*)(.*)', word)
                    if prefix_match:
                        prefix = prefix_match.group(1)
                        clean_word = prefix_match.group(2)
                    else:
                        prefix = ""
                        clean_word = word

                    eng_match = re.search(r'[A-Za-z]+', clean_word)
                    if eng_match:
                        first_char = eng_match.group(0)[0]
                    elif clean_word:
                        first_char = clean_word[0]
                    else:
                        return prefix + "_______________"
                    return f"{prefix}{first_char}_______________"

                text = re.sub(r'《(.*?)》', hint_replacer_tags, text)
                text = re.sub(r'\*\*(.*?)\*\*', hint_replacer_tags, text)

            text = re.sub(r'(_+)', lambda m: '_' * max(15, int(len(m.group(1)) * 1.5)), text)
            return text

        word_idx = 0

        def blank_replacer(match):
            nonlocal word_idx
            prefix = match.group(1) or ""
            underscores = match.group(2)

            if word_idx < len(ans_words_list):
                w = ans_words_list[word_idx]
                word_idx += 1

                prefix_match = re.match(r'^(\([A-Z]\)\s*)(.*)', w)
                if prefix_match:
                    w_clean = prefix_match.group(2)
                else:
                    w_clean = w

                eng_match = re.search(r'[A-Za-z]+', w_clean)

                if is_teacher_mode:
                    return f"{prefix}<span class='txt-org'>{w_clean}</span>"
                else:
                    space = " " if prefix and not prefix.endswith(' ') else ""
                    new_len = max(15, int(len(underscores) * 1.5))
                    new_underscores = '_' * new_len

                    if eng_match:
                        return f"{prefix}{space}{eng_match.group(0)[0]}{new_underscores}"
                    elif w_clean:
                        return f"{prefix}{space}{w_clean[0]}{new_underscores}"
                    else:
                        return f"{prefix}{space}{new_underscores}"
            else:
                return prefix + "_" * max(15, int(len(match.group(2)) * 1.5))

        text = re.sub(r'(\([A-Z]\)\s*)?(_+)', blank_replacer, text)
        return text

    summary_text = csat.get('summary_text', '요약문 데이터가 없습니다.')
    summary_text = process_page5_summary(summary_text, is_teacher, ans_words)

    summary_kor_processed = summary_kor
    if is_teacher:
        summary_kor_processed = re.sub(r'\*\*(.*?)\*\*', r'<span class="txt-org">\1</span>', summary_kor_processed)
        summary_kor_processed = re.sub(r'《(.*?)》', r'<span class="txt-org">\1</span>', summary_kor_processed)
        summary_kor_processed = re.sub(r'"([^"]+)"', r'"<span class="txt-org">\1</span>"', summary_kor_processed)
    else:
        summary_kor_processed = re.sub(r'\*\*(.*?)\*\*', r'____________', summary_kor_processed)
        summary_kor_processed = re.sub(r'《(.*?)》', r'____________', summary_kor_processed)
        summary_kor_processed = re.sub(r'"([^"]+)"', r'"_________" ', summary_kor_processed)

        def kor_fallback_replacer(match):
            return f"{match.group(1)} ____________"

        summary_kor_processed = re.sub(r'(\([A-Z]\))\s*[가-힣0-9]+\s*\([A-Za-z]+\)', kor_fallback_replacer,
                                       summary_kor_processed)

    key_sents_data = data.get('key_sentences', [])
    key_sentences_html = ""
    for i, ks in enumerate(key_sents_data):
        num = i + 1
        eng = ks.get('sentence', '')
        kor = ks.get('translation', '')

        desc = ks.get('reason', '')
        desc = re.sub(r'《(.*?)》', r'<span class="txt-org">《\1》</span>', desc)

        s_type = ks.get('type', 'Key Sentence')

        s_type = re.sub(r'\s*\(.*?\)', '', s_type)

        eng_no_source = remove_source_bracket(eng)

        def process_page5_syntax(t, is_t_mode):
            t = re.sub(r'(_+)', lambda m: '_' * int(len(m.group(1)) * 1.8), t)
            t = re.sub(r'《(.*?)》', r'<span class="txt-org">\1</span>', t)
            return t

        eng_orange = process_page5_syntax(eng_no_source, is_teacher)
        eng_colored = convert_eng_tags_color_only(eng_orange)
        eng_html = clean_syntax_debris(eng_colored)

        if is_teacher:
            kor_html_display = f'<div class="sa-kor" style="color: #c62828; font-weight: 600;">{kor}</div>'
        else:
            kor_html_display = f'<div style="margin-top: 8px; margin-bottom: 4px;"><div class="ws-line-box" style="height:24px;"></div><div class="ws-line-box" style="height:24px;"></div></div>'

        key_sentences_html += f"""
        <div class="sa-card">
            <div class="sa-badge-row"><span class="sa-num">#{num}</span><span class="sa-title">{s_type.upper()}</span></div>
            <div class="sa-eng">{eng_html}</div>
            {kor_html_display}
            <div class="sa-note"><span class="sa-point-tag">Analysis</span><span class="sa-desc">{desc}</span></div>
        </div>
        """

    clean_text_p6 = clean_text_logic(plain_passage_base)
    clean_text_p6 = clean_text_p6.replace('\n', ' ')
    clean_text_p6 = re.sub(r'\s+', ' ', clean_text_p6).strip()

    modified_text = clean_text_p6
    questions_html = ""

    blank_meaning_q = []
    grammar_q_count = 0
    q_counter = 1

    processing_data.sort(key=lambda x: modified_text.find(x.get('real_target', '')))

    for item in processing_data:
        raw_p_type = str(item.get('type', '')).lower()
        target = item.get('real_target', '').strip()

        if not target or target not in modified_text:
            continue

        if 'blank' in raw_p_type or '빈칸' in raw_p_type:
            marker = f'<span class="q-marker">({q_counter})</span>'
            if is_teacher:
                modified_text = modified_text.replace(target,
                                                      f"{marker} <span style='color:#c62828; font-weight:700;'>{target}</span>",
                                                      1)
                ans_text = item.get('paraphrase', target) if item.get('paraphrase') else target
                qa_line_html = f'<div class="qa-line" style="color:#c62828; font-weight:700; font-family:var(--font-eng); text-align:center; border-bottom:1px solid #c62828; line-height:1.2;">{ans_text}</div>'
            else:
                modified_text = modified_text.replace(target, f"{marker} ______________________", 1)
                qa_line_html = '<div class="qa-line"></div>'

            blank_meaning_q.append(f"""
            <div class="qa-item">
                <div class="qa-text">Q{q_counter}. 빈칸 ({q_counter})에 들어갈 영어 어구를 쓰시오.</div>
                {qa_line_html}
            </div>""")
            q_counter += 1

        elif 'implied' in raw_p_type or '함축' in raw_p_type or 'meaning' in raw_p_type:
            marker = f'<span class="q-marker">({q_counter})</span>'
            if is_teacher:
                modified_text = modified_text.replace(target,
                                                      f"{marker} <U>{target}</U> <span style='color:#c62828; font-size:11px;'>({item.get('meaning', '')})</span>",
                                                      1)
                ans_text = item.get('meaning', target)
                qa_line_html = f'<div class="qa-line" style="color:#c62828; font-weight:700; font-family:var(--font-sans); font-size:11.5px; text-align:center; border-bottom:1px solid #c62828; line-height:1.2;">{ans_text}</div>'
            else:
                modified_text = modified_text.replace(target, f"{marker} <U>{target}</U>", 1)
                qa_line_html = '<div class="qa-line"></div>'

            blank_meaning_q.append(f"""
            <div class="qa-item">
                <div class="qa-text">Q{q_counter}. 밑줄 친 ({q_counter})가 의미하는 바를 우리말로 쓰시오.</div>
                {qa_line_html}
            </div>""")
            q_counter += 1

        elif 'grammar' in raw_p_type or '어법' in raw_p_type:
            wrong = item.get('chosen_distractor', item.get('distractor', item.get('wrong_form', target)))

            if is_teacher:
                modified_text = modified_text.replace(target,
                                                      f"<span style='color:#c62828; font-weight:700; text-decoration:line-through;'>{wrong}</span> <span style='color:#1565c0; font-weight:700;'>({target})</span>",
                                                      1)
            else:
                modified_text = modified_text.replace(target, wrong, 1)
            grammar_q_count += 1

    questions_html += "".join(blank_meaning_q)

    if grammar_q_count > 0:
        g_rows = ""
        grammar_items = [x for x in processing_data if
                         'grammar' in str(x.get('type', '')).lower() or '어법' in str(x.get('type', '')).lower()]

        for item in grammar_items:
            if is_teacher:
                found_num = item.get('sentence_no', '')
                if not found_num:
                    target_word = item.get('target', '').strip()
                    for s in eng_sentences:
                        if target_word in s.get('eng_analyzed', ''):
                            found_num = s.get('num', '')
                            break
                s_num_display = f"<span style='color:#c62828; font-weight:bold;'>{found_num}</span>" if found_num else "&nbsp;&nbsp;"

                # chosen_distractor는 이미 정리된 값이므로 재파싱 불필요
                wrong = item.get('chosen_distractor',
                                 item.get('distractor', item.get('wrong_form', item.get('target', ''))))

                correct = item.get('real_target', item.get('target', ''))
                g_rows += f'<div class="g-row">( {s_num_display} ) : <div class="a-line-short" style="color:#c62828; text-align:center; font-weight:bold; border-bottom:1px solid #c62828; line-height:1.2;">{wrong}</div> <span class="arrow-icon">➜</span> <div class="a-line-short" style="color:#1565c0; text-align:center; font-weight:bold; border-bottom:1px solid #1565c0; line-height:1.2;">{correct}</div></div>'
            else:
                g_rows += '<div class="g-row">( &nbsp;&nbsp;&nbsp; ) : <div class="a-line-short"></div> <span class="arrow-icon">➜</span> <div class="a-line-short"></div></div>'

        questions_html += f"""
        <div class="qa-set" style="margin-top:10px;">
            <div class="qa-text">Q{q_counter}. 위 지문에서 어법상 틀린 문장의 번호와 틀린 부분을 올바르게 고치시오.</div>
            <div style="display:flex; flex-direction:column; margin-top:5px;">
                {g_rows}
            </div>
        </div>"""

    analyzed_sentences = data.get('sentence_analysis', [])
    writing_html = ""
    w_idx = 1
    w_count = 0

    for ks in key_sents_data:
        if w_count >= 2: break

        s_type = ks.get('type', '')
        if 'Theme' in s_type or 'Topic' in s_type:
            continue

        kor = ks.get('translation', '')
        eng_target = ks.get('sentence', '').strip()
        clean_target = remove_source_bracket(eng_target)

        if is_teacher:
            hint_text = "어순 배열 및 영작"
            lines_html = f'<div class="ws-line-box" style="color:#c62828; font-weight:700; font-family:var(--font-eng); font-size:14px; display:flex; align-items:flex-end; padding-left:10px; border-bottom:1px solid #c62828;">{clean_target}</div><div class="ws-line-box"></div>'
        else:
            found_s = None
            for s in eng_sentences:
                analyzed = s.get('eng_analyzed', '')
                cleaned = re.sub(r'\[/?(?:S|V|O|C|OC|M|con|IO|DO)\]', '', analyzed)
                cleaned = re.sub(r'《.*?》', '', cleaned)
                cleaned = re.sub(r'^[❶-❿⓫-⓴①-⑳0-9.\s]+', '', cleaned).strip()

                if clean_target[:20] in cleaned or cleaned[:20] in clean_target:
                    found_s = analyzed
                    break

            chunks = []
            if found_s:
                raw_chunks = re.split(r'(\[/?(?:S|V|O|C|OC|M|con|IO|DO)\])', found_s)
                for t in raw_chunks:
                    if not re.match(r'\[/?(?:S|V|O|C|OC|M|con|IO|DO)\]', t):
                        c_text = re.sub(r'[.,?!,"\']', '', re.sub(r'《.*?》', '', re.sub(r'[❶-❿⓫-⓴①-⑳]', '', t))).replace(
                            '/', '').strip()
                        if c_text:
                            chunks.append(c_text)

                if len(chunks) > 1:
                    orig = list(chunks)
                    for _ in range(10):
                        random.shuffle(chunks)
                        if chunks != orig:
                            break

            if chunks:
                hint_text = " // ".join(chunks)
            else:
                words = [w for w in re.sub(r'[.,?!,"\']', '', clean_target).split() if w]
                random.shuffle(words)
                hint_text = " / ".join(words)

            lines_html = '<div class="ws-line-box"></div><div class="ws-line-box"></div>'

        writing_html += f"""
        <div class="ws-item">
            <div class="ws-kor">{w_idx}. {kor}</div>
            <div class="ws-hint-box">{hint_text}</div>
            {lines_html}
        </div>
        """
        w_idx += 1
        w_count += 1

    p4_text_only = re.sub(r'<[^>]+>', '', hl_passage)
    p4_density_class = ""
    if len(p4_text_only) > 800 or total_sents >= 12:
        p4_density_class = "dense-mode"

    p6_text_only = re.sub(r'<[^>]+>', '', modified_text)
    p6_density_class = ""
    if len(p6_text_only) > 800:
        p6_density_class = "dense-mode"

    body_match = re.search(r'<body>(.*?)</body>', WORKBOOK_PORTRAIT_TEMPLATE_V21_23, re.DOTALL)
    unit_template = body_match.group(1) if body_match else WORKBOOK_PORTRAIT_TEMPLATE_V21_23

    html = unit_template

    page1_bottom_in_p1 = ""
    step1_page2_html = ""

    if is_long_passage:
        page1_bottom_in_p1 = ""
        step1_page2_html = f"""
<div class="page-container page-break">
    __PAGE_NUM__
    <div class="page-header">
        <div class="ph-left">
            <span class="ph-source-origin">{source_origin}</span>
            <div class="unit-badge-group">
                <span class="ub-label">NO.</span>
                <span class="ub-num">{q_num}</span>
            </div>
        </div>
        <div class="ph-right">STEP-1 [Analysis & Vocab]</div>
    </div>
    <div class="p1-body" style="padding-top: 15mm;">
        {page1_bottom_html}
    </div>
    <div class="page-footer">
        <div class="footer-logo"></div>
    </div>
</div>
"""
    else:
        page1_bottom_in_p1 = page1_bottom_html
        step1_page2_html = ""

    html = html.replace("__STEP0_PAGE_HTML__", step0_page_html)
    html = html.replace("__STEP5_PAGES__", step5_pages_final_html)
    html = html.replace("__UNIT_NUM__", "09")
    html = html.replace("__SOURCE_ORIGIN__", source_origin)

    top_header_html = f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;"><div style="display: flex; align-items: center; gap: 8px;">{question_header_html}</div>__DIFF_BAR_HTML__</div>'
    html = html.replace("__PAGE1_TOP_HEADER__", top_header_html)

    is_textbook = False
    if base_name and '-' in base_name:
        is_textbook = True

    diff_bar_html = ""
    if not is_textbook:
        try:
            diff = int(meta.get('difficulty_level', 3))
        except (ValueError, TypeError):
            diff = 3
        stars = "★" * diff + "☆" * (5 - diff)
        diff_bar_html = f'<div class="header-diff-bar"><span class="h-label">LEVEL</span><span class="h-stars">{stars}</span></div>'

    html = html.replace("__DIFF_BAR_HTML__", diff_bar_html)

    q_num = "00"
    if base_name and '-' in base_name:
        q_num = base_name.split('-')[-1].strip()
    else:
        q_header = meta.get('question_header', '')
        q_match = re.match(r'(\d+)', q_header.strip())
        q_num = q_match.group(1) if q_match else "00"

    html = html.replace("__Q_NUM__", q_num)

    html = html.replace("__PASSAGE_HTML__", final_passage_html)
    html = html.replace("__Q_TEXT_CLASS__", passage_div_class)
    html = html.replace("__VOCAB_CLASS__", vocab_class)
    html = html.replace("__OPTIONS_HTML__", options_html)

    html = html.replace("__PAGE1_BOTTOM_BLOCK__", page1_bottom_in_p1)
    html = html.replace("__STEP1_PAGE2_HTML__", step1_page2_html)

    html = html.replace("__STEP1_LEFT__", step1_left)
    html = html.replace("__STEP1_RIGHT__", step1_right)
    html = html.replace("__STEP2_LEFT__", step2_left)
    html = html.replace("__STEP2_RIGHT__", step2_right)
    html = html.replace("__STEP2_SVG_LEFT__", step2_svg_left)
    html = html.replace("__STEP2_SVG_RIGHT__", step2_svg_right)
    html = html.replace("__STEP3_AND_4_BLOCK__", step3_and_4_html)

    html = html.replace("__TOPIC_KEYWORD_EN__", kw_en)
    html = html.replace("__TOPIC_SUMMARY_EN__", summ_en)
    html = html.replace("__TOPIC_KEYWORD__", kw)
    html = html.replace("__TOPIC_SUMMARY__", summ)

    html = html.replace("__P3_LOGIC_CLEAN_ROWS__", p3_logic_clean_html_p1)

    step3_page2_html_block = ""
    if is_long_passage and p3_logic_clean_html_p2:
        step3_page2_html_block = f"""
<div class="page-container page-break">
    __PAGE_NUM__
    <div class="page-header">
        <div class="ph-left">
            <span class="ph-source-origin">{source_origin}</span>
            <div class="unit-badge-group">
                <span class="ub-label">NO.</span>
                <span class="ub-num">{q_num}</span>
            </div>
        </div>
        <div class="ph-right">STEP-3 [Logic Flow & Clean Text] (2/2)</div>
    </div>
    <div class="p2-body" style="display: block;">
        <div class="split-container" style="border-top: 2px solid var(--c-brand); margin-top: 0;">
            {p3_logic_clean_html_p2}
        </div>
    </div>
    <div class="page-footer">
        <div class="footer-logo"></div>
    </div>
</div>
"""
    html = html.replace("__STEP3_PAGE2_HTML__", step3_page2_html_block)

    html = html.replace("__S1_FS__", PAGE_CONFIG["STEP1_OVERVIEW"]["text_font_size"])
    html = html.replace("__S1_LH__", PAGE_CONFIG["STEP1_OVERVIEW"]["text_line_height"])
    html = html.replace("__S1_LONG_FS__", PAGE_CONFIG["STEP1_OVERVIEW"]["long_text_font_size"])
    html = html.replace("__S1_LONG_LH__", PAGE_CONFIG["STEP1_OVERVIEW"]["long_text_line_height"])

    html = html.replace("__S2_WORD_FS__", PAGE_CONFIG["STEP2_VOCAB"]["word_font_size"])
    html = html.replace("__S2_MEAN_FS__", PAGE_CONFIG["STEP2_VOCAB"]["mean_font_size"])
    html = html.replace("__S2_CHUNK_FS__", PAGE_CONFIG["STEP2_VOCAB"]["chunk_font_size"])

    html = html.replace("__S4_FS__", PAGE_CONFIG["STEP4_CHECKPOINT"]["text_font_size"])
    html = html.replace("__S4_LH__", PAGE_CONFIG["STEP4_CHECKPOINT"]["text_line_height"])
    html = html.replace("__S4_DENSE_FS__", PAGE_CONFIG["STEP4_CHECKPOINT"]["dense_font_size"])
    html = html.replace("__S4_DENSE_LH__", PAGE_CONFIG["STEP4_CHECKPOINT"]["dense_line_height"])

    html = html.replace("__S6_SUM_FS__", PAGE_CONFIG["STEP6_SUMMARY_SYNTAX"]["summary_font_size"])
    html = html.replace("__S6_SUM_LH__", PAGE_CONFIG["STEP6_SUMMARY_SYNTAX"]["summary_line_height"])
    html = html.replace("__S6_SYN_ENG_FS__", PAGE_CONFIG["STEP6_SUMMARY_SYNTAX"]["syntax_eng_font_size"])
    html = html.replace("__S6_SYN_ENG_LH__", PAGE_CONFIG["STEP6_SUMMARY_SYNTAX"]["syntax_eng_line_height"])
    html = html.replace("__S6_SYN_KOR_FS__", PAGE_CONFIG["STEP6_SUMMARY_SYNTAX"]["syntax_kor_font_size"])
    html = html.replace("__S6_SYN_KOR_LH__", PAGE_CONFIG["STEP6_SUMMARY_SYNTAX"]["syntax_kor_line_height"])

    html = html.replace("__S7_FS__", PAGE_CONFIG["STEP7_REVIEW"]["text_font_size"])
    html = html.replace("__S7_LH__", PAGE_CONFIG["STEP7_REVIEW"]["text_line_height"])
    html = html.replace("__S7_DENSE_FS__", PAGE_CONFIG["STEP7_REVIEW"]["dense_font_size"])
    html = html.replace("__S7_DENSE_LH__", PAGE_CONFIG["STEP7_REVIEW"]["dense_line_height"])

    html = html.replace("__HIGHLIGHTED_PASSAGE__", hl_passage)
    html = html.replace("__ANNOTATION_ROWS__", anno_rows)
    html = html.replace("__P4_DENSITY_CLASS__", p4_density_class)

    html = html.replace("__CSAT_SUMMARY_TEXT__", summary_text)
    html = html.replace("__CSAT_SUMMARY_KOR__", summary_kor_processed)
    html = html.replace("__KEY_SENTENCES_HTML__", key_sentences_html)

    html = html.replace("__ANSWER_KEY_BLOCK__", "")

    html = html.replace("__MODIFIED_PASSAGE_HTML__", modified_text)
    html = html.replace("__INTEGRATED_QUESTIONS_HTML__", questions_html)
    html = html.replace("__WRITING_ROWS_HTML__", writing_html)
    html = html.replace("__P6_DENSITY_CLASS__", p6_density_class)

    html = html.replace("__P7_SUB_INFO__", "* 선생님용 정답 확인 모드입니다." if is_teacher else "* Step-6에서 정답을 확인하세요.")

    html = re.sub(r'<div class="syntax-legend">.*?</div>', '', html, flags=re.DOTALL)

    html = html.replace("* 먼저 한글 해석을 가리고 영어 문장 구조 분석을 해보세요.", "* 영어 문장 구조 분석을 한 후에 한글 해석을 적으세요.")

    html = html.replace("__STEP0_PAGE_HTML__", "")

    # ==========================================
    # 에필로그 (EPILOGUE) - 백지 노트 학습용
    # ==========================================
    epilogue_paragraphs_html = ""

    ep_eng_fs = "12.5px" if total_sents >= 12 else "13.5px"
    ep_eng_lh = "1.6" if total_sents >= 12 else "1.85"
    ep_gap = "10px" if total_sents >= 12 else "16px"
    ep_pad = "10px 12px" if total_sents >= 12 else "12px 15px"
    ep_line_height = "22px" if total_sents >= 12 else "26px"

    for stg in stage_data:
        title = stg.get('title', '')
        rng = stg.get('range', '')
        target_nums = parse_range(rng)

        eng_sents = []
        sent_count = 0
        for n in target_nums:
            s_dict = next((item for item in eng_sentences if str(item.get('num', -1)) == str(n)), None)
            if s_dict:
                raw_eng = s_dict.get('eng_analyzed', '').replace('\\n', ' ')
                clean_eng = clean_syntax_debris(clean_text_logic(raw_eng)).strip()
                clean_eng = clean_eng.replace('/', '')
                clean_eng = re.sub(r'\s+', ' ', clean_eng)
                clean_eng = re.sub(r'^[❶-❿⓫-⓴①-⑳0-9.\s]+', '', clean_eng).strip()

                badge_num = convert_num_to_badge_str(s_dict.get('num', n))
                eng_sents.append(
                    f'<span class="para-mark" style="width:1.2em; height:1.2em; line-height:1.2em; font-size:0.7em;">{badge_num}</span> {clean_eng}')
                sent_count += 1

        if not eng_sents:
            continue

        eng_para = " ".join(eng_sents)

        # 빈 밑줄 노트 라인: 문장 개수 + 1
        note_lines_html = ""
        for _ in range(sent_count + 1):
            note_lines_html += f'<div style="border-bottom: 1px solid #cfd8dc; height: {ep_line_height};"></div>'

        epilogue_paragraphs_html += f'''
        <div style="margin-bottom: {ep_gap}; page-break-inside: avoid; break-inside: avoid;">
            <div style="font-family: var(--font-head); font-weight: 800; font-size: 12.5px; color: var(--c-brand); margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                <div style="width:4px; height:12px; background-color:var(--c-accent); border-radius:2px;"></div>{title}
            </div>
            <div style="background: #fff; border: 1px solid #cfd8dc; border-radius: 8px; padding: {ep_pad};">
                <div style="font-family: var(--font-serif); font-size: {ep_eng_fs}; line-height: {ep_eng_lh}; color: #212121; text-align: justify; margin-bottom: 10px; word-break: break-word;">
                    {eng_para}
                </div>
                <div style="border-top: 1px dashed #cfd8dc; padding-top: 8px;">
                    {note_lines_html}
                </div>
            </div>
        </div>
        '''

    epilogue_page_html = f"""
<div class="page-container page-break">
    __PAGE_NUM__
    <div class="page-header">
        <div class="ph-left">
            <span class="ph-source-origin">{source_origin}</span>
            <div class="unit-badge-group">
                <span class="ub-label">NO.</span>
                <span class="ub-num">{q_num}</span>
            </div>
        </div>
        <div class="ph-right">EPILOGUE [Study Note]</div>
    </div>
    <div class="p0-body" style="padding: 10mm 15mm; flex: 1; display: block; overflow: hidden; background: #fff;">
        <div class="sec-head-style" style="margin-bottom: 15px;"><div class="icon-box icon-r">N</div>Note & Review (지문을 읽고 해석을 직접 써보세요)</div>
        <div style="display: flex; flex-direction: column;">
            {epilogue_paragraphs_html}
        </div>
    </div>
    <div class="page-footer">
        <div class="footer-logo"></div>
    </div>
</div>
"""

    return step0_page_html, html, epilogue_page_html


# ==========================================
# 4. 일괄 처리 실행 블록
# ==========================================
if __name__ == "__main__":
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    target_folder = os.path.join(desktop_path, "3")

    if not os.path.exists(target_folder):
        print("=" * 60)
        print(f"⚠️ 바탕화면에 '3' 폴더가 없습니다.")
        print("=" * 60)
    else:
        files = [f for f in os.listdir(target_folder) if f.endswith('.json')]
        try:
            files.sort(key=lambda f: int(re.sub(r'\D', '', f) or '0'))
        except (ValueError, TypeError):
            files.sort()

        if not files:
            print("=" * 60)
            print(f"⚠️ '3' 폴더 안에 처리할 .json 파일이 없습니다.")
            print("=" * 60)
        else:
            print(f"📂 총 {len(files)}개의 파일을 병합합니다...")
            print("=" * 60)

            head_match = re.search(r'(<!DOCTYPE html>.*?<body>)', WORKBOOK_PORTRAIT_TEMPLATE_V21_23, re.DOTALL)
            html_wrapper_start = head_match.group(1) if head_match else "<html><body>"

            # 속표지 블록 (페이지 번호 매기기 전 가장 처음에 삽입)
            student_body = COVER_PAGE_STUDENT
            teacher_body = COVER_PAGE_TEACHER

            all_step0_student = ""
            all_step0_teacher = ""
            all_units_student = ""
            all_units_teacher = ""

            for i, file_name in enumerate(files):
                input_path = os.path.join(target_folder, file_name)
                print(f"   processing: {file_name}...")

                try:
                    with open(input_path, 'r', encoding='utf-8') as f:
                        json_str = f.read()

                        s0_stu, u_stu = generate_unit_pages(json_str, is_teacher=False, file_name=file_name)
                        s0_tch, u_tch = generate_unit_pages(json_str, is_teacher=True, file_name=file_name)

                        all_step0_student += s0_stu
                        all_step0_teacher += s0_tch
                        all_units_student += u_stu
                        all_units_teacher += u_tch

                except Exception as e:
                    print(f"   ❌ Error reading {file_name}: {e}")


            # 🚀 프롤로그(STEP0) 페이지들 뒷장에 간지(MEMO)를 자동 삽입하여
            # 다음 본학습(STEP1)이 항상 홀수 페이지(우측)에서 시작되도록 보정
            def get_blank_page_if_needed(html_content):
                count = html_content.count('__PAGE_NUM__')
                if count % 2 != 0:
                    return """
<div class="page-container page-break">
    __PAGE_NUM__
    <div style="display:flex; justify-content:center; align-items:center; height:100%; color:#e0e0e0; font-family:var(--font-eng); font-size:32px; font-weight:900; letter-spacing: 6px; background-color:#fafafa;">
        M E M O
    </div>
</div>
"""
                return ""


            blank_stu = get_blank_page_if_needed(all_step0_student)
            blank_tch = get_blank_page_if_needed(all_step0_teacher)

            # 프롤로그 먼저 묶고 -> (간지) -> 유닛 본문
            student_body += all_step0_student + blank_stu + all_units_student
            teacher_body += all_step0_teacher + blank_tch + all_units_teacher

            student_body = insert_page_numbers(student_body)
            teacher_body = insert_page_numbers(teacher_body)

            html_student_std = html_wrapper_start.replace("__MIRRORED_CSS__", "") + student_body + "\n</body>\n</html>"
            html_teacher_std = html_wrapper_start.replace("__MIRRORED_CSS__", "") + teacher_body + "\n</body>\n</html>"

            student_std_path = os.path.join(target_folder, "Merged_Workbook_Student_Standard.html")
            teacher_std_path = os.path.join(target_folder, "Merged_Workbook_Answer_Standard.html")
            student_std_pdf_path = os.path.join(target_folder, "Merged_Workbook_Student_Standard.pdf")
            teacher_std_pdf_path = os.path.join(target_folder, "Merged_Workbook_Answer_Standard.pdf")

            if GENERATE_STANDARD_VERSION:
                with open(student_std_path, 'w', encoding='utf-8') as f:
                    f.write(html_student_std)
                with open(teacher_std_path, 'w', encoding='utf-8') as f:
                    f.write(html_teacher_std)

            # 책 제본용 대칭 모드 파일 (안쪽 20mm / 바깥쪽 10mm)
            mirrored_css = """
    /* =========================================
       [제본용 대칭 여백 모드 (Book Binding Mode)]
       - 홀수 페이지(오른쪽): 왼쪽 여백 20mm, 오른쪽 여백 10mm
       - 짝수 페이지(왼쪽): 오른쪽 여백 20mm, 왼쪽 여백 10mm
    ========================================= */
    @page :right { margin-left: 20mm; margin-right: 10mm; }
    @page :left { margin-left: 10mm; margin-right: 20mm; }

    .page-container:nth-of-type(odd) .page-header { padding-left: 20mm !important; padding-right: 10mm !important; }
    .page-container:nth-of-type(odd) .p0-body,
    .page-container:nth-of-type(odd) .p1-body, .page-container:nth-of-type(odd) .p2-body,
    .page-container:nth-of-type(odd) .p3-body, .page-container:nth-of-type(odd) .p4-body,
    .page-container:nth-of-type(odd) .p5-body, .page-container:nth-of-type(odd) .p6-body { padding-left: 20mm !important; padding-right: 10mm !important; }
    .page-container:nth-of-type(odd) .page-num-left { left: 20mm !important; }
    .page-container:nth-of-type(odd) .page-num-right { right: 10mm !important; }

    .page-container:nth-of-type(even) .page-header { padding-left: 10mm !important; padding-right: 20mm !important; }
    .page-container:nth-of-type(even) .p0-body,
    .page-container:nth-of-type(even) .p1-body, .page-container:nth-of-type(even) .p2-body,
    .page-container:nth-of-type(even) .p3-body, .page-container:nth-of-type(even) .p4-body,
    .page-container:nth-of-type(even) .p5-body, .page-container:nth-of-type(even) .p6-body { padding-left: 10mm !important; padding-right: 20mm !important; }
    .page-container:nth-of-type(even) .page-num-left { left: 10mm !important; }
    .page-container:nth-of-type(even) .page-num-right { right: 20mm !important; }
            """

            html_student_book = html_wrapper_start.replace("__MIRRORED_CSS__",
                                                           mirrored_css) + student_body + "\n</body>\n</html>"
            html_teacher_book = html_wrapper_start.replace("__MIRRORED_CSS__",
                                                           mirrored_css) + teacher_body + "\n</body>\n</html>"

            student_book_path = os.path.join(target_folder, "Merged_Workbook_Student_Book.html")
            teacher_book_path = os.path.join(target_folder, "Merged_Workbook_Answer_Book.html")
            student_book_pdf_path = os.path.join(target_folder, "Merged_Workbook_Student_Book.pdf")
            teacher_book_pdf_path = os.path.join(target_folder, "Merged_Workbook_Answer_Book.pdf")

            if GENERATE_BOOK_VERSION:
                with open(student_book_path, 'w', encoding='utf-8') as f:
                    f.write(html_student_book)
                with open(teacher_book_path, 'w', encoding='utf-8') as f:
                    f.write(html_teacher_book)

            print("=" * 60)
            print("📄 PDF 변환을 시작합니다. (Playwright 백그라운드 렌더링 중...)")
            try:
                if GENERATE_STANDARD_VERSION:
                    save_html_to_pdf(html_student_std, student_std_pdf_path)
                    save_html_to_pdf(html_teacher_std, teacher_std_pdf_path)
                if GENERATE_BOOK_VERSION:
                    save_html_to_pdf(html_student_book, student_book_pdf_path)
                    save_html_to_pdf(html_teacher_book, teacher_book_pdf_path)
            except Exception as e:
                print(f"❌ PDF 생성 중 에러 발생: {e}")
                print("⚠️ 먼저 터미널에서 'pip install playwright' 및 'playwright install'을 실행해 주세요.")

            print("=" * 60)
            print(f"🎉 완벽 병합 생성 완료! 폴더 3을 확인해 주세요.")
            if GENERATE_STANDARD_VERSION:
                print(f"   [기본 프린트용 - 15mm 일정]")
                print(f"   📘 학생용: {os.path.basename(student_std_path)} / .pdf")
                print(f"   📕 교사용: {os.path.basename(teacher_std_path)} / .pdf")
            if GENERATE_BOOK_VERSION:
                print(f"\n   [정식 책 제본용 - 안쪽 20mm / 바깥쪽 10mm]")
                print(f"   📘 학생용(Book): {os.path.basename(student_book_path)} / .pdf")
                print(f"   📕 교사용(Book): {os.path.basename(teacher_book_path)} / .pdf")
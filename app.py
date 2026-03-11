import streamlit as st
import json
import re
import os
import subprocess
import tempfile
import zipfile
import io
import datetime

# ==========================================
# Playwright 브라우저 자동 설치 (클라우드 배포 대응)
# ==========================================
@st.cache_resource
def install_playwright_browser():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch(headless=True).close()
    except Exception:
        subprocess.run(["playwright", "install", "chromium"], check=True)

install_playwright_browser()

import importlib.util

_module_path = os.path.join(os.path.dirname(__file__), "고등부 내신 교재 만들기.py")
_spec = importlib.util.spec_from_file_location("workbook_engine", _module_path)
engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(engine)

# ==========================================
# PDF 저장 디렉토리 (이전 생성 기록 보관용)
# ==========================================
PDF_HISTORY_DIR = os.path.join(os.path.dirname(__file__), "pdf_history")
os.makedirs(PDF_HISTORY_DIR, exist_ok=True)

# ==========================================
# 페이지 설정
# ==========================================
st.set_page_config(
    page_title="Roy's 고등학교 내신 교재 만들기",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-title { font-size: 2.2rem; font-weight: 900; color: #003b6f; margin-bottom: 0; letter-spacing: -1px; }
    .sub-title { font-size: 1rem; color: #78909c; font-weight: 500; margin-top: -10px; margin-bottom: 30px; }
    .log-box { background: #263238; color: #b0bec5; font-family: 'Courier New', monospace; font-size: 13px;
               padding: 15px; border-radius: 8px; max-height: 300px; overflow-y: auto; line-height: 1.6; }
    .log-ok { color: #66bb6a; } .log-err { color: #ef5350; } .log-warn { color: #ffa726; } .log-info { color: #42a5f5; }
    .log-time { color: #78909c; }
    .stDownloadButton > button { width: 100%; font-weight: 700; font-size: 1rem; }
    .history-item { background: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px 16px; margin: 6px 0; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 로그 시스템
# ==========================================
def init_log():
    if 'log_messages' not in st.session_state:
        st.session_state['log_messages'] = []

def log(msg, level="info"):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    icon = {"ok": "✅", "err": "❌", "warn": "⚠️", "info": "📋"}.get(level, "📋")
    css = {"ok": "log-ok", "err": "log-err", "warn": "log-warn", "info": "log-info"}.get(level, "log-info")
    st.session_state['log_messages'].append(
        f'<span class="log-time">[{now}]</span> {icon} <span class="{css}">{msg}</span>'
    )

def render_log():
    if st.session_state.get('log_messages'):
        lines = "<br>".join(st.session_state['log_messages'])
        st.markdown(f'<div class="log-box">{lines}</div>', unsafe_allow_html=True)


# ==========================================
# 병합 빌드 + PDF 생성 (한 번에 처리)
# ==========================================
def build_and_generate_pdf(uploaded_files, cover_config, translation_mode,
                           watermark_text, gen_standard, gen_book):
    """업로드된 JSON → HTML 병합 → PDF 변환까지 한 번에 처리합니다."""

    init_log()
    st.session_state['log_messages'] = []
    log("워크북 생성을 시작합니다.", "info")

    # 엔진 설정 반영
    engine.COVER_CONFIG.update(cover_config)
    engine.TRANSLATION_MODE = translation_mode
    engine.WATERMARK_TEXT = watermark_text

    # 파일 정렬
    file_entries = []
    for uf in uploaded_files:
        file_entries.append({'name': uf.name, 'content': uf.getvalue().decode('utf-8')})

    try:
        file_entries.sort(key=lambda x: int(re.sub(r'\D', '', x['name']) or '0'))
    except (ValueError, TypeError):
        file_entries.sort(key=lambda x: x['name'])

    log(f"{len(file_entries)}개 JSON 파일 로드 완료", "ok")

    # HTML 래퍼
    head_match = re.search(r'(<!DOCTYPE html>.*?<body>)', engine.WORKBOOK_PORTRAIT_TEMPLATE_V21_23, re.DOTALL)
    html_wrapper_start = head_match.group(1) if head_match else "<html><body>"

    student_body = engine.COVER_PAGE_STUDENT
    teacher_body = engine.COVER_PAGE_TEACHER

    all_step0_student = ""
    all_step0_teacher = ""
    all_units_student = ""
    all_units_teacher = ""

    errors = []
    progress_bar = st.progress(0, text="HTML 생성 중...")

    for i, entry in enumerate(file_entries):
        progress_bar.progress((i + 1) / len(file_entries) * 0.5, text=f"HTML 생성 중: {entry['name']}")

        try:
            s0_stu, u_stu = engine.generate_unit_pages(entry['content'], is_teacher=False, file_name=entry['name'])
            s0_tch, u_tch = engine.generate_unit_pages(entry['content'], is_teacher=True, file_name=entry['name'])

            all_step0_student += s0_stu
            all_step0_teacher += s0_tch
            all_units_student += u_stu
            all_units_teacher += u_tch
            log(f"  {entry['name']} 처리 완료", "ok")
        except Exception as e:
            errors.append(f"{entry['name']}: {str(e)}")
            log(f"  {entry['name']} 오류: {str(e)}", "err")

    # 간지 삽입
    def get_blank_page_if_needed(html_content):
        count = html_content.count('__PAGE_NUM__')
        if count % 2 != 0:
            return '<div class="page-container page-break">__PAGE_NUM__<div style="display:flex; justify-content:center; align-items:center; height:100%; color:#e0e0e0; font-family:var(--font-eng); font-size:32px; font-weight:900; letter-spacing: 6px; background-color:#fafafa;">M E M O</div></div>'
        return ""

    student_body += all_step0_student + get_blank_page_if_needed(all_step0_student) + all_units_student
    teacher_body += all_step0_teacher + get_blank_page_if_needed(all_step0_teacher) + all_units_teacher

    student_body = engine.insert_page_numbers(student_body)
    teacher_body = engine.insert_page_numbers(teacher_body)

    html_results = {}
    mirrored_css = """
    @page :right { margin-left: 20mm; margin-right: 10mm; }
    @page :left { margin-left: 10mm; margin-right: 20mm; }
    .page-container:nth-of-type(odd) .page-header { padding-left: 20mm !important; padding-right: 10mm !important; }
    .page-container:nth-of-type(odd) .p0-body, .page-container:nth-of-type(odd) .p1-body, .page-container:nth-of-type(odd) .p2-body,
    .page-container:nth-of-type(odd) .p3-body, .page-container:nth-of-type(odd) .p4-body,
    .page-container:nth-of-type(odd) .p5-body, .page-container:nth-of-type(odd) .p6-body { padding-left: 20mm !important; padding-right: 10mm !important; }
    .page-container:nth-of-type(odd) .page-num-left { left: 20mm !important; }
    .page-container:nth-of-type(odd) .page-num-right { right: 10mm !important; }
    .page-container:nth-of-type(even) .page-header { padding-left: 10mm !important; padding-right: 20mm !important; }
    .page-container:nth-of-type(even) .p0-body, .page-container:nth-of-type(even) .p1-body, .page-container:nth-of-type(even) .p2-body,
    .page-container:nth-of-type(even) .p3-body, .page-container:nth-of-type(even) .p4-body,
    .page-container:nth-of-type(even) .p5-body, .page-container:nth-of-type(even) .p6-body { padding-left: 10mm !important; padding-right: 20mm !important; }
    .page-container:nth-of-type(even) .page-num-left { left: 10mm !important; }
    .page-container:nth-of-type(even) .page-num-right { right: 20mm !important; }
    """

    if gen_standard:
        html_results['student_std'] = html_wrapper_start.replace("__MIRRORED_CSS__", "") + student_body + "\n</body>\n</html>"
        html_results['teacher_std'] = html_wrapper_start.replace("__MIRRORED_CSS__", "") + teacher_body + "\n</body>\n</html>"
    if gen_book:
        html_results['student_book'] = html_wrapper_start.replace("__MIRRORED_CSS__", mirrored_css) + student_body + "\n</body>\n</html>"
        html_results['teacher_book'] = html_wrapper_start.replace("__MIRRORED_CSS__", mirrored_css) + teacher_body + "\n</body>\n</html>"

    log("HTML 생성 완료. PDF 변환을 시작합니다.", "info")

    # PDF 변환
    pdf_tasks = []
    label_map = {
        'student_std': ('학생용_Standard.pdf', '학생용 Standard'),
        'teacher_std': ('교사용_Standard.pdf', '교사용 Standard'),
        'student_book': ('학생용_Book.pdf', '학생용 Book'),
        'teacher_book': ('교사용_Book.pdf', '교사용 Book'),
    }
    for key in html_results:
        fname, label = label_map[key]
        pdf_tasks.append((key, fname, label))

    pdf_files = {}
    total_tasks = len(pdf_tasks)

    for idx, (key, fname, label) in enumerate(pdf_tasks):
        progress_bar.progress(0.5 + (idx + 1) / total_tasks * 0.5, text=f"PDF 변환 중: {label}...")
        log(f"  PDF 변환 중: {label}...", "info")

        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp_path = tmp.name
            engine.save_html_to_pdf(html_results[key], tmp_path)
            with open(tmp_path, 'rb') as f:
                pdf_files[fname] = f.read()
            os.unlink(tmp_path)
            log(f"  {label} PDF 변환 완료", "ok")
        except Exception as e:
            log(f"  {label} PDF 변환 실패: {str(e)}", "err")
            errors.append(f"PDF 변환 실패 ({label}): {str(e)}")

    progress_bar.progress(1.0, text="완료!")

    # PDF 히스토리에 저장
    if pdf_files:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = os.path.join(PDF_HISTORY_DIR, timestamp)
        os.makedirs(session_dir, exist_ok=True)

        file_list = [e['name'] for e in file_entries]
        for fname, data in pdf_files.items():
            with open(os.path.join(session_dir, fname), 'wb') as f:
                f.write(data)

        # 메타 정보 저장
        meta = {
            'timestamp': timestamp,
            'files': file_list,
            'standard': gen_standard,
            'book': gen_book,
            'translation_mode': translation_mode,
            'pdf_count': len(pdf_files),
        }
        with open(os.path.join(session_dir, 'meta.json'), 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        log(f"PDF {len(pdf_files)}개 저장 완료 (기록: {timestamp})", "ok")

    total_time_msg = f"총 {len(pdf_files)}개 PDF 생성 완료"
    if errors:
        total_time_msg += f" ({len(errors)}개 오류 발생)"
        log(total_time_msg, "warn")
    else:
        log(total_time_msg, "ok")

    return pdf_files, errors


def create_zip(file_dict):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, data in file_dict.items():
            if isinstance(data, str):
                data = data.encode('utf-8')
            zf.writestr(name, data)
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def load_history():
    """이전 생성 기록 목록을 반환합니다."""
    history = []
    if not os.path.exists(PDF_HISTORY_DIR):
        return history
    for dirname in sorted(os.listdir(PDF_HISTORY_DIR), reverse=True):
        meta_path = os.path.join(PDF_HISTORY_DIR, dirname, 'meta.json')
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            meta['dir'] = os.path.join(PDF_HISTORY_DIR, dirname)
            history.append(meta)
    return history


# ==========================================
# 사이드바
# ==========================================
with st.sidebar:
    st.markdown("## 설정")

    st.markdown("#### 표지 텍스트")
    cover_top = st.text_input("상단 부제", value="PREMIUM ENGLISH WORKBOOK")
    cover_eng = st.text_input("영어 타이틀", value="ROY'S CLASS")
    cover_kor = st.text_input("한글 타이틀", value="고등부 내신 영어 마스터 워크북")
    cover_desc = st.text_input("하단 설명", value="최상위권을 향한 확실한 선택 내신 1등급 완성 프로젝트")

    st.markdown("---")
    st.markdown("#### 해석 모드")
    translation_mode = st.radio(
        "STEP-5 한글 해석 방식",
        options=["literal", "liberal"],
        format_func=lambda x: "직독직해" if x == "literal" else "자연스러운 해석",
        index=0,
        help="프롤로그는 항상 자연스러운 해석을 사용합니다."
    )

    st.markdown("---")
    st.markdown("#### 출력 옵션")
    watermark = st.text_input("워터마크 텍스트", value="ROY'S ENGLISH", help="빈칸이면 워터마크 없음")
    gen_standard = st.checkbox("일반 프린트용 (Standard)", value=True)
    gen_book = st.checkbox("책 제본용 (Book)", value=True)

    st.markdown("---")
    st.markdown("<div style='color:#90a4ae; font-size:12px; text-align:center;'>Roy's Class Workbook Generator v2.0</div>", unsafe_allow_html=True)


# ==========================================
# 메인 영역
# ==========================================
st.markdown('<div class="main-title">Roy\'s 고등학교 내신 수업 자료 생성기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">JSON 파일을 업로드하면 학생용/교사용 PDF 워크북을 자동 생성합니다.</div>', unsafe_allow_html=True)

# 탭: 생성 / 이전 기록
tab_create, tab_history = st.tabs(["PDF 생성", "이전 생성 기록"])

with tab_create:
    uploaded_files = st.file_uploader(
        "JSON 파일을 드래그하여 업로드하세요 (복수 선택 가능)",
        type=['json'],
        accept_multiple_files=True,
        help="분석 완료된 JSON 파일을 여기에 올리면 됩니다."
    )

    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)}개 파일 업로드됨**")

        with st.expander("업로드된 파일 목록", expanded=False):
            for uf in uploaded_files:
                size_kb = len(uf.getvalue()) / 1024
                st.markdown(f"- `{uf.name}` ({size_kb:.1f} KB)")

        if st.button("PDF 워크북 생성하기", type="primary", use_container_width=True):
            if not gen_standard and not gen_book:
                st.error("최소 하나의 출력 옵션(Standard 또는 Book)을 선택하세요.")
            else:
                cover_config = {
                    "top_subtitle": cover_top,
                    "main_title_eng": cover_eng,
                    "main_title_kor": cover_kor.replace("\n", "<br>"),
                    "teacher_badge": "교사용 (정답 및 해설)",
                    "bottom_desc": cover_desc.replace("\n", "<br>")
                }

                pdf_files, errors = build_and_generate_pdf(
                    uploaded_files, cover_config, translation_mode,
                    watermark, gen_standard, gen_book
                )

                if pdf_files:
                    st.session_state['pdf_files'] = pdf_files
                    st.session_state['generation_done'] = True

        # 로그 표시
        init_log()
        if st.session_state.get('log_messages'):
            st.markdown("#### 처리 로그")
            render_log()

        # PDF 다운로드 버튼
        if st.session_state.get('generation_done') and st.session_state.get('pdf_files'):
            pdf_files = st.session_state['pdf_files']

            st.markdown("---")
            st.markdown("### PDF 다운로드")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**학생용**")
                for name, data in pdf_files.items():
                    if '학생' in name:
                        label = "Standard" if "Standard" in name else "Book"
                        st.download_button(
                            f"학생용 ({label}) PDF",
                            data=data,
                            file_name=name,
                            mime="application/pdf",
                            use_container_width=True,
                            key=f"dl_{name}"
                        )

            with col2:
                st.markdown("**교사용**")
                for name, data in pdf_files.items():
                    if '교사' in name:
                        label = "Standard" if "Standard" in name else "Book"
                        st.download_button(
                            f"교사용 ({label}) PDF",
                            data=data,
                            file_name=name,
                            mime="application/pdf",
                            use_container_width=True,
                            key=f"dl_{name}"
                        )

            if len(pdf_files) > 1:
                st.markdown("---")
                zip_data = create_zip(pdf_files)
                st.download_button(
                    "전체 PDF ZIP 다운로드",
                    data=zip_data,
                    file_name=uploaded_files[0].name.replace('.json', '') + ".zip",
                    mime="application/zip",
                    use_container_width=True,
                    key="dl_zip"
                )

    else:
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("#### 1. 업로드\n분석 완료된 JSON 파일을\n드래그 앤 드롭하세요.")
        with col2:
            st.markdown("#### 2. 설정\n왼쪽 사이드바에서\n표지, 해석 모드를 조정하세요.")
        with col3:
            st.markdown("#### 3. 다운로드\n'PDF 워크북 생성하기'를 누르면\nPDF를 바로 다운로드합니다.")


with tab_history:
    st.markdown("### 이전 생성 기록")
    st.markdown("이전에 생성한 PDF를 다시 다운로드할 수 있습니다.")
    st.markdown("---")

    history = load_history()

    if not history:
        st.info("아직 생성된 기록이 없습니다. 'PDF 생성' 탭에서 워크북을 먼저 생성하세요.")
    else:
        for h in history:
            ts = h.get('timestamp', '')
            display_time = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]} {ts[9:11]}:{ts[11:13]}:{ts[13:15]}" if len(ts) >= 15 else ts
            file_names = ", ".join(h.get('files', []))
            pdf_count = h.get('pdf_count', 0)
            mode_str = []
            if h.get('standard'): mode_str.append("Standard")
            if h.get('book'): mode_str.append("Book")
            trans = "직독직해" if h.get('translation_mode') == 'literal' else "자연스러운 해석"

            with st.expander(f"{display_time}  |  PDF {pdf_count}개  |  {', '.join(mode_str)}", expanded=False):
                st.markdown(f"**소스 파일:** {file_names}")
                st.markdown(f"**해석 모드:** {trans}")

                session_dir = h.get('dir', '')
                if os.path.exists(session_dir):
                    pdf_in_dir = [f for f in os.listdir(session_dir) if f.endswith('.pdf')]

                    col1, col2 = st.columns(2)
                    with col1:
                        for pf in pdf_in_dir:
                            if '학생' in pf:
                                with open(os.path.join(session_dir, pf), 'rb') as f:
                                    st.download_button(
                                        f"{pf}",
                                        data=f.read(),
                                        file_name=pf,
                                        mime="application/pdf",
                                        use_container_width=True,
                                        key=f"hist_{ts}_{pf}"
                                    )
                    with col2:
                        for pf in pdf_in_dir:
                            if '교사' in pf:
                                with open(os.path.join(session_dir, pf), 'rb') as f:
                                    st.download_button(
                                        f"{pf}",
                                        data=f.read(),
                                        file_name=pf,
                                        mime="application/pdf",
                                        use_container_width=True,
                                        key=f"hist_{ts}_{pf}"
                                    )

                    # ZIP 다운로드
                    if len(pdf_in_dir) > 1:
                        zip_dict = {}
                        for pf in pdf_in_dir:
                            with open(os.path.join(session_dir, pf), 'rb') as f:
                                zip_dict[pf] = f.read()
                        st.download_button(
                            "전체 ZIP 다운로드",
                            data=create_zip(zip_dict),
                            file_name=f"Workbook_{ts}.zip",
                            mime="application/zip",
                            use_container_width=True,
                            key=f"hist_zip_{ts}"
                        )

                    # 삭제 버튼
                    if st.button(f"이 기록 삭제", key=f"del_{ts}"):
                        import shutil
                        shutil.rmtree(session_dir)
                        st.rerun()

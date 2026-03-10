import streamlit as st
import json
import re
import os
import tempfile
import zipfile
import io

# 기존 워크북 생성 모듈에서 필요한 함수/변수 임포트
import importlib.util

# ==========================================
# 모듈 동적 로드 (한글 파일명 대응)
# ==========================================
_module_path = os.path.join(os.path.dirname(__file__), "고등부 내신 교재 만들기.py")
_spec = importlib.util.spec_from_file_location("workbook_engine", _module_path)
engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(engine)

# ==========================================
# 페이지 설정
# ==========================================
st.set_page_config(
    page_title="Roy's Class - 워크북 생성기",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 커스텀 CSS
# ==========================================
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem; font-weight: 900; color: #003b6f;
        margin-bottom: 0; letter-spacing: -1px;
    }
    .sub-title {
        font-size: 1rem; color: #78909c; font-weight: 500;
        margin-top: -10px; margin-bottom: 30px;
    }
    .status-box {
        padding: 15px; border-radius: 10px; margin: 10px 0;
        border-left: 5px solid;
    }
    .status-processing { background: #fff8e1; border-color: #ffa000; }
    .status-done { background: #e8f5e9; border-color: #43a047; }
    .status-error { background: #ffebee; border-color: #e53935; }
    .file-card {
        background: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 8px;
        padding: 12px 16px; margin: 6px 0;
        display: flex; align-items: center; gap: 10px;
    }
    .stDownloadButton > button {
        width: 100%; font-weight: 700; font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 병합 빌드 함수 (기존 __main__ 로직 재활용)
# ==========================================
def build_merged_workbook(uploaded_files, cover_config, translation_mode,
                          watermark_text, gen_standard, gen_book):
    """업로드된 JSON 파일들로 병합 워크북 HTML/PDF를 생성합니다."""

    # 엔진 설정 반영
    engine.COVER_CONFIG.update(cover_config)
    engine.TRANSLATION_MODE = translation_mode
    engine.WATERMARK_TEXT = watermark_text

    # 파일 정렬
    file_entries = []
    for uf in uploaded_files:
        file_entries.append({
            'name': uf.name,
            'content': uf.getvalue().decode('utf-8')
        })

    try:
        file_entries.sort(key=lambda x: int(re.sub(r'\D', '', x['name']) or '0'))
    except (ValueError, TypeError):
        file_entries.sort(key=lambda x: x['name'])

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
    progress_bar = st.progress(0, text="워크북 생성 중...")

    for i, entry in enumerate(file_entries):
        progress_bar.progress((i + 1) / len(file_entries), text=f"처리 중: {entry['name']}")

        try:
            s0_stu, u_stu = engine.generate_unit_pages(entry['content'], is_teacher=False, file_name=entry['name'])
            s0_tch, u_tch = engine.generate_unit_pages(entry['content'], is_teacher=True, file_name=entry['name'])

            all_step0_student += s0_stu
            all_step0_teacher += s0_tch
            all_units_student += u_stu
            all_units_teacher += u_tch
        except Exception as e:
            errors.append(f"{entry['name']}: {str(e)}")

    # 간지 삽입 (홀수 페이지 보정)
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

    student_body += all_step0_student + blank_stu + all_units_student
    teacher_body += all_step0_teacher + blank_tch + all_units_teacher

    student_body = engine.insert_page_numbers(student_body)
    teacher_body = engine.insert_page_numbers(teacher_body)

    results = {}

    # Standard 버전
    if gen_standard:
        results['student_std_html'] = html_wrapper_start.replace("__MIRRORED_CSS__", "") + student_body + "\n</body>\n</html>"
        results['teacher_std_html'] = html_wrapper_start.replace("__MIRRORED_CSS__", "") + teacher_body + "\n</body>\n</html>"

    # Book 버전
    if gen_book:
        mirrored_css = """
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
        results['student_book_html'] = html_wrapper_start.replace("__MIRRORED_CSS__", mirrored_css) + student_body + "\n</body>\n</html>"
        results['teacher_book_html'] = html_wrapper_start.replace("__MIRRORED_CSS__", mirrored_css) + teacher_body + "\n</body>\n</html>"

    progress_bar.progress(1.0, text="완료!")

    return results, errors


def generate_pdf_from_html(html_content):
    """HTML을 PDF로 변환하여 bytes로 반환합니다."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        engine.save_html_to_pdf(html_content, tmp_path)
        with open(tmp_path, 'rb') as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def create_zip(file_dict):
    """파일명:바이트 딕셔너리로 ZIP 파일을 생성합니다."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, data in file_dict.items():
            zf.writestr(name, data)
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


# ==========================================
# 사이드바: 설정
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
    gen_pdf = st.checkbox("PDF도 함께 생성", value=True, help="HTML만 필요하면 해제하세요 (PDF 생성은 시간이 걸립니다)")

    st.markdown("---")
    st.markdown(
        "<div style='color:#90a4ae; font-size:12px; text-align:center;'>"
        "Roy's Class Workbook Generator v1.0"
        "</div>",
        unsafe_allow_html=True
    )


# ==========================================
# 메인 영역
# ==========================================
st.markdown('<div class="main-title">Roy\'s Class 워크북 생성기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">JSON 파일을 업로드하면 학생용/교사용 워크북을 자동 생성합니다.</div>', unsafe_allow_html=True)

# 파일 업로드
uploaded_files = st.file_uploader(
    "JSON 파일을 드래그하여 업로드하세요 (복수 선택 가능)",
    type=['json'],
    accept_multiple_files=True,
    help="바탕화면 '3' 폴더에 넣던 JSON 파일들을 여기에 올리면 됩니다."
)

if uploaded_files:
    st.markdown(f"**{len(uploaded_files)}개 파일 업로드됨**")

    # 파일 목록 미리보기
    with st.expander("업로드된 파일 목록 보기", expanded=False):
        for uf in uploaded_files:
            size_kb = len(uf.getvalue()) / 1024
            st.markdown(f"- `{uf.name}` ({size_kb:.1f} KB)")

    # 생성 버튼
    if st.button("워크북 생성하기", type="primary", use_container_width=True):

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

            # HTML 생성
            with st.spinner("워크북을 생성하고 있습니다..."):
                results, errors = build_merged_workbook(
                    uploaded_files, cover_config, translation_mode,
                    watermark, gen_standard, gen_book
                )

            if errors:
                st.warning(f"일부 파일에서 오류가 발생했습니다:")
                for err in errors:
                    st.markdown(f"- {err}")

            if not results:
                st.error("생성된 결과가 없습니다. 파일을 확인해주세요.")
            else:
                st.success(f"워크북 생성 완료! 아래에서 다운로드하세요.")

                # 결과를 세션에 저장
                st.session_state['results'] = results
                st.session_state['gen_pdf'] = gen_pdf
                st.session_state['pdf_generated'] = False

    # 다운로드 섹션
    if 'results' in st.session_state and st.session_state['results']:
        results = st.session_state['results']
        gen_pdf_flag = st.session_state.get('gen_pdf', False)

        st.markdown("---")
        st.markdown("### 다운로드")

        # HTML 다운로드
        tab_html, tab_pdf = st.tabs(["HTML 파일", "PDF 파일"])

        with tab_html:
            download_files = {}

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**학생용**")
                if 'student_std_html' in results:
                    st.download_button(
                        "학생용 (Standard) HTML",
                        data=results['student_std_html'].encode('utf-8'),
                        file_name="Workbook_Student_Standard.html",
                        mime="text/html",
                        use_container_width=True
                    )
                    download_files['Workbook_Student_Standard.html'] = results['student_std_html'].encode('utf-8')

                if 'student_book_html' in results:
                    st.download_button(
                        "학생용 (Book) HTML",
                        data=results['student_book_html'].encode('utf-8'),
                        file_name="Workbook_Student_Book.html",
                        mime="text/html",
                        use_container_width=True
                    )
                    download_files['Workbook_Student_Book.html'] = results['student_book_html'].encode('utf-8')

            with col2:
                st.markdown("**교사용**")
                if 'teacher_std_html' in results:
                    st.download_button(
                        "교사용 (Standard) HTML",
                        data=results['teacher_std_html'].encode('utf-8'),
                        file_name="Workbook_Answer_Standard.html",
                        mime="text/html",
                        use_container_width=True
                    )
                    download_files['Workbook_Answer_Standard.html'] = results['teacher_std_html'].encode('utf-8')

                if 'teacher_book_html' in results:
                    st.download_button(
                        "교사용 (Book) HTML",
                        data=results['teacher_book_html'].encode('utf-8'),
                        file_name="Workbook_Answer_Book.html",
                        mime="text/html",
                        use_container_width=True
                    )
                    download_files['Workbook_Answer_Book.html'] = results['teacher_book_html'].encode('utf-8')

            # HTML 전체 ZIP 다운로드
            if len(download_files) > 1:
                st.markdown("---")
                zip_data = create_zip(download_files)
                st.download_button(
                    "전체 HTML 파일 ZIP 다운로드",
                    data=zip_data,
                    file_name="Workbook_HTML_All.zip",
                    mime="application/zip",
                    use_container_width=True
                )

        with tab_pdf:
            if not gen_pdf_flag:
                st.info("사이드바에서 'PDF도 함께 생성' 옵션을 켜고 다시 생성하세요.")
            else:
                if st.button("PDF 변환 시작", type="secondary", use_container_width=True,
                             help="PDF 변환은 파일당 10~30초 소요됩니다."):
                    pdf_files = {}

                    pdf_tasks = []
                    if 'student_std_html' in results:
                        pdf_tasks.append(('Workbook_Student_Standard.pdf', 'student_std_html', '학생용 Standard'))
                    if 'teacher_std_html' in results:
                        pdf_tasks.append(('Workbook_Answer_Standard.pdf', 'teacher_std_html', '교사용 Standard'))
                    if 'student_book_html' in results:
                        pdf_tasks.append(('Workbook_Student_Book.pdf', 'student_book_html', '학생용 Book'))
                    if 'teacher_book_html' in results:
                        pdf_tasks.append(('Workbook_Answer_Book.pdf', 'teacher_book_html', '교사용 Book'))

                    pdf_progress = st.progress(0, text="PDF 변환 준비 중...")

                    for idx, (pdf_name, html_key, label) in enumerate(pdf_tasks):
                        pdf_progress.progress((idx) / len(pdf_tasks), text=f"PDF 변환 중: {label}...")
                        try:
                            pdf_bytes = generate_pdf_from_html(results[html_key])
                            pdf_files[pdf_name] = pdf_bytes
                        except Exception as e:
                            st.error(f"PDF 변환 실패 ({label}): {str(e)}")

                    pdf_progress.progress(1.0, text="PDF 변환 완료!")
                    st.session_state['pdf_files'] = pdf_files

                if 'pdf_files' in st.session_state and st.session_state['pdf_files']:
                    pdf_files = st.session_state['pdf_files']

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**학생용**")
                        for name, data in pdf_files.items():
                            if 'Student' in name:
                                label = "Standard" if "Standard" in name else "Book"
                                st.download_button(
                                    f"학생용 ({label}) PDF",
                                    data=data,
                                    file_name=name,
                                    mime="application/pdf",
                                    use_container_width=True
                                )

                    with col2:
                        st.markdown("**교사용**")
                        for name, data in pdf_files.items():
                            if 'Answer' in name:
                                label = "Standard" if "Standard" in name else "Book"
                                st.download_button(
                                    f"교사용 ({label}) PDF",
                                    data=data,
                                    file_name=name,
                                    mime="application/pdf",
                                    use_container_width=True
                                )

                    # PDF 전체 ZIP
                    if len(pdf_files) > 1:
                        st.markdown("---")
                        zip_data = create_zip(pdf_files)
                        st.download_button(
                            "전체 PDF 파일 ZIP 다운로드",
                            data=zip_data,
                            file_name="Workbook_PDF_All.zip",
                            mime="application/zip",
                            use_container_width=True
                        )

else:
    # 초기 안내 화면
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        #### 1단계: 업로드
        분석 완료된 JSON 파일을 위 영역에
        드래그 앤 드롭하세요.
        여러 파일을 한 번에 올릴 수 있습니다.
        """)

    with col2:
        st.markdown("""
        #### 2단계: 설정
        왼쪽 사이드바에서 표지 텍스트,
        해석 모드, 출력 옵션을
        원하는 대로 조정하세요.
        """)

    with col3:
        st.markdown("""
        #### 3단계: 다운로드
        '워크북 생성하기' 버튼을 누르면
        학생용/교사용 HTML과 PDF를
        바로 다운로드할 수 있습니다.
        """)

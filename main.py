# Streamlit 기반 C 코드 분석기 메인 엔트리포인트
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from agents import build_graph

st.set_page_config(page_title="C Code Analyzer", page_icon="💻")
st.title("💻 C Code Analyzer")

if "graph" not in st.session_state:
    st.session_state.graph = build_graph()
    st.session_state.messages = []
    st.session_state.uploaded_name = None
    st.session_state.uploaded_code = None
    st.session_state.uploaded_files = []  # 파일 목록: [{name, code, analysis, report_pdf}]

# --- 왼쪽 사이드바: 업로드 파일 목록 ---
st.sidebar.header("업로드된 파일 목록")
if st.session_state.uploaded_files:
    for idx, f in enumerate(st.session_state.uploaded_files):
        if st.sidebar.button(f["name"], key=f"file_{idx}"):
            # 파일 클릭 시 해당 코드/분석 결과를 대화창에 표시
            st.session_state.messages.append(HumanMessage(content=f"[파일: {f['name']} 내용]\n" + f["code"]))
            if "analysis" in f:
                st.session_state.messages.append(AIMessage(content=f"[분석 결과: {f['name']}]\n" + f["analysis"]))
            st.rerun()
else:
    st.sidebar.write("아직 업로드된 파일이 없습니다.")

# --- 대화 메시지 영역 ---
for m in st.session_state.messages:
    role = "user" if isinstance(m, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.write(m.content)

# --- 채팅 입력창 ---
if prompt := st.chat_input("메시지를 입력하세요"):
    sanitized = prompt.encode("utf-8", "replace").decode("utf-8", "replace")
    # '분석' 또는 '업로드' 키워드로 업로드된 파일 분석
    if (sanitized.strip().startswith("분석") or sanitized.strip().startswith("업로드")) and st.session_state.uploaded_code:
        st.session_state.messages.append(HumanMessage(content=st.session_state.uploaded_code))
    else:
        st.session_state.messages.append(HumanMessage(content=sanitized))
    result = st.session_state.graph.invoke({"messages": st.session_state.messages})
    st.session_state.messages = result["messages"]
    st.rerun()

# --- 파일 업로드 UI를 화면 하단에 고정 ---
with st.container():
    st.markdown("---")
    uploaded_file = st.file_uploader("C 소스코드 업로드 (분석하려면 '분석' 또는 '업로드' 입력)", type=["c", "h"])
    if uploaded_file is not None:
        code = uploaded_file.read().decode("utf-8", errors="replace")
        st.session_state.uploaded_name = uploaded_file.name
        st.session_state.uploaded_code = code
        # 파일 목록에 추가 (중복 방지)
        if not any(f["name"] == uploaded_file.name for f in st.session_state.uploaded_files):
            st.session_state.uploaded_files.append({"name": uploaded_file.name, "code": code})
        st.success(f"{uploaded_file.name} 업로드 완료! '분석' 또는 '업로드' 입력 시 분석됩니다.")

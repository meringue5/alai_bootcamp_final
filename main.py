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

# 1. 대화 메시지 영역을 먼저 보여줌 (대화에 집중)
for m in st.session_state.messages:
    role = "user" if isinstance(m, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.write(m.content)

# 2. 채팅 입력창
if prompt := st.chat_input("메시지를 입력하세요"):
    sanitized = prompt.encode("utf-8", "replace").decode("utf-8", "replace")
    # '분석' 키워드로도 업로드된 파일 분석 가능
    if (sanitized.strip().startswith("분석") or sanitized.strip().startswith("업로드")) and st.session_state.uploaded_code:
        st.session_state.messages.append(HumanMessage(content=st.session_state.uploaded_code))
    else:
        st.session_state.messages.append(HumanMessage(content=sanitized))
    result = st.session_state.graph.invoke({"messages": st.session_state.messages})
    st.session_state.messages = result["messages"]
    st.rerun()

# 3. 파일 업로드 UI를 화면 하단에 배치
with st.container():
    st.markdown("---")
    uploaded_file = st.file_uploader("C 소스코드 업로드 (분석하려면 '분석' 또는 '업로드' 입력)", type=["c", "h"])
    if uploaded_file is not None:
        code = uploaded_file.read().decode("utf-8", errors="replace")
        st.session_state.uploaded_name = uploaded_file.name
        st.session_state.uploaded_code = code
        st.success(f"{uploaded_file.name} 업로드 완료! '분석' 또는 '업로드' 입력 시 분석됩니다.")

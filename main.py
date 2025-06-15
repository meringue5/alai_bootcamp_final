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

uploaded_file = st.file_uploader("C 소스코드 업로드", type=["c", "h"])

for m in st.session_state.messages:
    role = "user" if isinstance(m, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.write(m.content)

# 새 파일이 업로드되면 자동 분석 실행
if uploaded_file is not None and st.session_state.uploaded_name != uploaded_file.name:
    code = uploaded_file.read().decode("utf-8", errors="replace")
    st.session_state.uploaded_name = uploaded_file.name
    st.session_state.messages.append(HumanMessage(content=code))
    result = st.session_state.graph.invoke({"messages": st.session_state.messages})
    st.session_state.messages = result["messages"]
    st.experimental_rerun()

if prompt := st.chat_input("메시지를 입력하세요"):
    sanitized = prompt.encode("utf-8", "replace").decode("utf-8", "replace")
    st.session_state.messages.append(HumanMessage(content=sanitized))
    result = st.session_state.graph.invoke({"messages": st.session_state.messages})
    st.session_state.messages = result["messages"]
    st.experimental_rerun()

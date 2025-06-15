import streamlit as st
from langchain_core.messages import HumanMessage
from app.agents import build_graph

st.set_page_config(page_title="C Code Analyzer", page_icon="💻")

st.title("💻 C Code Analyzer")

uploaded_file = st.file_uploader("C 소스코드 업로드", type=["c", "h"])
command = st.text_input("명령어 입력 (업로드, 분석 결과 추출, 질문 <내용>, 종료)")

if "graph" not in st.session_state:
    st.session_state.graph = build_graph()
    st.session_state.messages = []

if st.button("실행"):
    if uploaded_file and command.startswith("업로드"):
        code = uploaded_file.getvalue().decode("utf-8")
        st.session_state.messages.append(HumanMessage(content=code))
    else:
        st.session_state.messages.append(HumanMessage(content=command))
    result = st.session_state.graph.invoke({"messages": st.session_state.messages})
    st.session_state.messages = result["messages"]
    for msg in st.session_state.messages:
        if hasattr(msg, "content"):
            st.write(f"{getattr(msg, 'role', 'bot')}: {msg.content}")

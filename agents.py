# 에이전트 관련 클래스와 함수 정의
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from langgraph.graph import StateGraph, MessagesState
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import AzureChatOpenAI

import config

from analysis import analyze_static, detect_anti_patterns
from vector_store import VectorStore
#from reportlab.pdfgen import canvas
#from reportlab.lib.pagesizes import A4
import io
import base64
import streamlit as st

@dataclass
class Agent:
    name: str  # 에이전트 이름
    description: str  # 에이전트 설명
    tools: List[str] = field(default_factory=list)  # 사용 가능한 도구 목록
    memory: Dict[str, str] = field(default_factory=dict)  # 에이전트 메모리

    def add_tool(self, tool_name: str):
        """에이전트의 도구 목록에 도구를 추가합니다."""
        self.tools.append(tool_name)

    def update_memory(self, key: str, value: str):
        """에이전트의 메모리를 업데이트합니다."""
        self.memory[key] = value

    def __post_init__(self):
        # 복잡한 속성 초기화
        self.state_graph = StateGraph()
        self.messages_state = MessagesState()

    def process_message(self, message: str):
        """들어온 메시지를 처리하고 상태를 업데이트합니다."""
        # ...구현부...

    def generate_response(self, prompt: str) -> str:
        """프롬프트를 기반으로 언어 모델을 사용해 응답을 생성합니다."""
        llm = AzureChatOpenAI(deployment_name=config.OPENAI_DEPLOYMENT_NAME)
        response = llm([HumanMessage(content=prompt), AIMessage(content="")])
        return response.content

    def analyze_code(self, code: str):
        """코드를 분석하여 잠재적 문제를 찾습니다."""
        issues = analyze_static(code)
        anti_patterns = detect_anti_patterns(code)
        return {"issues": issues, "anti_patterns": anti_patterns}

    def search_codebase(self, query: str) -> List[str]:
        """벡터스토어를 사용해 코드베이스를 검색합니다."""
        vector_store = VectorStore()
        results = vector_store.similarity_search(query)
        return results

    def run_tool(self, tool_name: str, *args, **kwargs):
        """지정한 도구를 실행합니다."""
        if tool_name in self.tools:
            tool = getattr(self, f"_{tool_name}_tool", None)
            if callable(tool):
                return tool(*args, **kwargs)
        raise ValueError(f"Tool {tool_name} is not available to this agent.")

    def _example_tool(self, *args, **kwargs):
        """도구 구현 예시입니다."""
        # ...구현부...


# --- 간단한 그래프 빌더 구현 ---

@dataclass
class Memory:
    """분석 결과를 저장하기 위한 메모리"""

    analyses: List[Dict] = field(default_factory=list)


def get_llm() -> AzureChatOpenAI:
    """Azure OpenAI LLM 인스턴스를 반환합니다."""

    return AzureChatOpenAI(
        azure_endpoint=config.AOAI_ENDPOINT,
        api_key=config.AOAI_API_KEY,
        azure_deployment=config.AOAI_DEPLOY_GPT4O,
        api_version=config.AOAI_API_VERSION,
        temperature=0.0,
    )


vector_store = VectorStore()
mem = Memory()
llm = get_llm()


def analyzer_node(state: MessagesState) -> Command[str]:
    """
    업로드된 코드를 분석하고, 분석 결과를 st.session_state.uploaded_files에 저장합니다.
    """
    last = state["messages"][-1]
    if isinstance(last, HumanMessage):
        code = last.content
        # 분석 수행
        analysis = analyze_static(code)
        anti = detect_anti_patterns(code)
        # 분석 결과 문자열 생성 (한국어)
        analysis_str = f"총 라인 수: {analysis.total_lines}\n함수 개수: {analysis.function_count}\n변수 개수: {analysis.variable_count}\n순환 복잡도: {analysis.cyclomatic_complexity}\n사유: {analysis.complexity_reasoning}"
        if anti:
            analysis_str += "\n안티패턴:\n" + "\n".join(f"- {a.type}: {a.details}" for a in anti)
        # 업로드 파일 목록(state["uploaded_files"])에 분석 결과 저장
        found = False
        for f in state["uploaded_files"]:
            if f["code"] == code:
                f["analysis"] = analysis_str
                found = True
        if not found:
            state["uploaded_files"].append({"name": "업로드파일", "code": code, "analysis": analysis_str})
        # 안내 메시지
        ai_msg = AIMessage(content="분석이 완료되었습니다. '분석 결과 추출' 명령을 입력하면 PDF 리포트를 다운로드할 수 있습니다.")
        return Command(update={"messages": [ai_msg]}, goto="supervisor")
    return Command(goto="supervisor")


def report_node(state: MessagesState) -> Command[str]:
    # 마크다운 리포트 생성 및 다운로드 링크 제공 (외부 패키지 없이)
    files = state.get("uploaded_files", [])
    if not files:
        return Command(update={"messages": [AIMessage(content="분석된 파일이 없습니다.")]}, goto="supervisor")
    buffer = io.StringIO()
    buffer.write("# C 코드 분석 리포트\n\n")
    for f in files:
        buffer.write(f"## 파일명: {f['name']}\n")
        buffer.write(f"### 분석 결과\n")
        buffer.write(f"{f.get('analysis', '분석 결과 없음')}\n\n")
    md_bytes = buffer.getvalue().encode("utf-8")
    b64 = base64.b64encode(md_bytes).decode()
    href = f'<a href="data:text/markdown;base64,{b64}" download="report.md">마크다운 리포트 다운로드</a>'
    ai_msg = AIMessage(content=f"분석 리포트가 생성되었습니다. 아래 링크를 클릭해 마크다운(.md) 파일로 다운로드하세요.\n{href}")
    return Command(update={"messages": [ai_msg]}, goto="supervisor")


def supervisor_node(state: MessagesState) -> Command[str]:
    """사용자 명령을 해석하여 다음 노드를 결정합니다."""

    # 업로드 파일 목록을 state에 저장/기억
    if "uploaded_files" not in state:
        state["uploaded_files"] = []
    last = state["messages"][-1]
    if isinstance(last, HumanMessage):
        text = last.content.strip()
        if text.lower().startswith("업로드") or text.lower().startswith("분석"):
            return Command(goto="analyzer")
        if text.lower().startswith("분석 결과 추출"):
            return Command(goto="report")
        if text.lower().startswith("종료"):
            return Command(goto="__end__")
        if text.lower().startswith("질문"):
            return Command(goto="supervisor")
        # 일반 대화 처리 (생략)
    return Command(goto="__end__")


def build_graph() -> StateGraph:
    """에이전트 노드를 연결한 그래프를 생성합니다."""

    builder = StateGraph(MessagesState)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("analyzer", analyzer_node)
    builder.add_node("report", report_node)
    builder.set_entry_point("supervisor")
    return builder.compile()



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
    """업로드된 코드를 분석하여 결과를 저장합니다."""

    last = state["messages"][-1]
    if isinstance(last, HumanMessage) and last.content:
        code = last.content
        analysis = analyze_static(code)
        anti = detect_anti_patterns(code)
        mem.analyses.append({
            "analysis": analysis,
            "anti_patterns": anti,
            "code": code,
        })
        vector_store.add_documents([code])
        msg = (
            f"Lines: {analysis.total_lines}, Functions: {analysis.function_count}, "
            f"Variables: {analysis.variable_count}, Cyclomatic: {analysis.cyclomatic_complexity}"
        )
        return Command(update={"messages": [AIMessage(content=msg)]}, goto="supervisor")
    return Command(goto="__end__")


def report_node(state: MessagesState) -> Command[str]:
    """현재까지 저장된 분석 결과를 요약합니다."""

    report_lines = []
    for i, entry in enumerate(mem.analyses):
        a = entry["analysis"]
        report_lines.append(
            f"File {i+1}: lines={a.total_lines} functions={a.function_count} variables={a.variable_count} complexity={a.cyclomatic_complexity}"
        )
    report = "\n".join(report_lines) or "No analysis yet"
    return Command(update={"messages": [AIMessage(content=report)]}, goto="supervisor")


def supervisor_node(state: MessagesState) -> Command[str]:
    """사용자 명령을 해석하여 다음 노드를 결정합니다."""

    last = state["messages"][-1]
    if isinstance(last, HumanMessage):
        text = last.content.strip()
        if text.lower().startswith("업로드"):
            return Command(goto="analyzer")
        if text.lower().startswith("분석 결과 추출"):
            return Command(goto="report")
        if text.lower().startswith("종료"):
            return Command(goto="__end__")
        if text.lower().startswith("질문"):
            # 질문 처리 예시 (실제 로직에 맞게 수정)
            return Command(goto="supervisor")
        # 명령어가 아니면 챗봇 답변 생성
        llm = AzureChatOpenAI(deployment_name="gpt-3.5-turbo")  # 실제 환경에 맞게 deployment_name 수정
        response = llm([last])
        ai_msg = AIMessage(content=response.content)
        return Command(update={"messages": [ai_msg]}, goto="supervisor")
    # 종료 조건에 해당하지 않으면 반드시 종료
    return Command(goto="__end__")

def build_graph() -> StateGraph:
    """에이전트 노드를 연결한 그래프를 생성합니다."""

    builder = StateGraph(MessagesState)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("analyzer", analyzer_node)
    builder.add_node("report", report_node)
    builder.set_entry_point("supervisor")
    return builder.compile()



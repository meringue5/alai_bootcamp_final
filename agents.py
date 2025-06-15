# 에이전트 관련 클래스와 함수 정의
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from langgraph.graph import StateGraph, MessagesState
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import AzureChatOpenAI

from analysis import analyze_static, detect_anti_patterns
from vector_store import CodeVectorStore
import config

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
        vector_store = CodeVectorStore()
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

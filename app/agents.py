from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from langgraph.graph import StateGraph, MessagesState
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import AzureChatOpenAI

from .analysis import analyze_static, detect_anti_patterns
from .vector_store import CodeVectorStore
from . import config


@dataclass
class Memory:
    analyses: List[Dict] = field(default_factory=list)


def get_llm():
    return AzureChatOpenAI(
        azure_endpoint=config.AOAI_ENDPOINT,
        api_key=config.AOAI_API_KEY,
        azure_deployment=config.AOAI_DEPLOY_GPT4O,
        api_version=config.AOAI_API_VERSION,
        temperature=0.0,
    )


vector_store = CodeVectorStore()
mem = Memory()
llm = get_llm()


# Analyzer node

def analyzer_node(state: MessagesState) -> Command[str]:
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
        vector_store.add_code(code, metadata={"index": len(mem.analyses) - 1})
        msg = (
            f"Lines: {analysis.total_lines}, Functions: {analysis.function_count}, "
            f"Variables: {analysis.variable_count}, Cyclomatic: {analysis.cyclomatic_complexity}"
        )
        return Command(update={"messages": [AIMessage(content=msg)]}, goto="supervisor")
    return Command(goto="supervisor")


# Report extractor node

def report_node(state: MessagesState) -> Command[str]:
    report_lines = []
    for i, entry in enumerate(mem.analyses):
        a = entry["analysis"]
        report_lines.append(
            f"File {i+1}: lines={a.total_lines} functions={a.function_count} variables={a.variable_count} complexity={a.cyclomatic_complexity}"
        )
    report = "\n".join(report_lines) or "No analysis yet"
    return Command(update={"messages": [AIMessage(content=report)]}, goto="supervisor")


# Supervisor node

def supervisor_node(state: MessagesState) -> Command[str]:
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
            # Query vector store
            query = text.split(maxsplit=1)[-1]
            docs = vector_store.similarity_search(query)
            context = "\n".join(d.page_content for d in docs)
            prompt = f"Answer the question based on code context:\n{context}\nQuestion: {query}"
            answer = llm.invoke([HumanMessage(content=prompt)]).content
            return Command(update={"messages": [AIMessage(content=answer)]}, goto="supervisor")
    return Command(goto="supervisor")


def build_graph() -> StateGraph:
    builder = StateGraph(MessagesState)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("analyzer", analyzer_node)
    builder.add_node("report", report_node)
    builder.set_entry_point("supervisor")
    return builder.compile()

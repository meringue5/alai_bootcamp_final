"""
Simple multi-agent example built with LangGraph.
This script demonstrates a supervisor agent coordinating two
sub-agents. The supervisor keeps track of the conversation and
routes work to the appropriate sub-agent. Once the user types
"FINISH" the graph stops.

This implementation avoids explicit edges between nodes and relies
on `langgraph.types.Command` to move between agents. Conversation
history is stored on each run and logged to ``conversation.log`` so
that the flow can be analysed later.
"""

from __future__ import annotations

import logging
from typing import TypedDict, Literal, List

from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.types import Command

import os
from langchain_openai import AzureChatOpenAI
import time
import json

AOAI_ENDPOINT=os.getenv("AOAI_ENDPOINT")
AOAI_API_KEY=os.getenv("AOAI_API_KEY")
AOAI_DEPLOY_GPT4O=os.getenv("AOAI_DEPLOY_GPT4O")
AOAI_DEPLOY_GPT4O_MINI=os.getenv("AOAI_DEPLOY_GPT4O_MINI")
AOAI_DEPLOY_EMBED_3_LARGE=os.getenv("AOAI_DEPLOY_EMBED_3_LARGE")
AOAI_DEPLOY_EMBED_3_SMALL=os.getenv("AOAI_DEPLOY_EMBED_3_SMALL")
AOAI_DEPLOY_EMBED_ADA=os.getenv("AOAI_DEPLOY_EMBED_ADA")

llm = AzureChatOpenAI(
    azure_endpoint=AOAI_ENDPOINT,
    azure_deployment=AOAI_DEPLOY_GPT4O_MINI,
    api_version="2024-10-21",
    api_key=AOAI_API_KEY
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 대화 진행 상황을 담는 상태 클래스
class State(MessagesState):
    """Conversation state shared by all agents."""

    step: int  # track which agent should run next
    thread_id: str  # context-awareness by thread id (supervisor only)


# 질문에서 회사 이름을 추출하는 함수
def _extract_company(text: str) -> str:
    """Very small helper to guess a company name from a question."""
    words = [w.strip(".,?!") for w in text.split()]
    for w in words:
        if w.istitle():
            return w
    return "Unknown"


# --- Sub-agent implementations -------------------------------------------------

# 트럼프와 밴스 관련 뉴스를 반환하는 서브 에이전트
def trump_vance_news_node(state: State) -> Command[Literal["supervisor"]]:
    user_msg = next((m for m in state["messages"] if hasattr(m, "content") and isinstance(m, HumanMessage)), None)
    query = "Donald Trump and J.D. Vance news. Please search the web and summarize the latest news about them."
    llm_result = llm.invoke([HumanMessage(content=query)])
    news = f"LLM web search result: {llm_result.content}"
    return Command(
        update={"messages": [AIMessage(content=news, name="trump_vance_news")]},
        goto="supervisor",
    )

# 사용자가 요청한 회사의 가상 정보를 제공하는 서브 에이전트

def company_info_node(state: State) -> Command[Literal["supervisor"]]:
    user_msg = next((m for m in state["messages"] if hasattr(m, "content") and isinstance(m, HumanMessage)), None)
    company = _extract_company(user_msg.content if user_msg else "")
    query = f"Please search the web and summarize the latest stock price and news for {company}."
    llm_result = llm.invoke([HumanMessage(content=query)])
    info = f"LLM web search result: {llm_result.content}"
    return Command(
        update={"messages": [AIMessage(content=info, name="company_info")]},
        goto="supervisor",
    )


# --- Supervisor implementation -------------------------------------------------

# 각 서브 에이전트를 호출하고 최종 보고서를 만드는 감독 에이전트
def supervisor_node(state: State) -> Command[Literal["trump_vance_news", "company_info", "__end__"]]:
    last: BaseMessage = state["messages"][-1]
    memory = load_memory()
    thread_id = getattr(state, "thread_id", "default")
    user_question = ""
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            user_question = m.content.strip()
            break
    now = time.time()
    # Check memory for similar question
    for q, v in memory.get(thread_id, {}).items():
        if q == user_question:
            ago = int((now - v["ts"]) // 3600)
            answer = v["answer"]
            msg = f"You asked this {ago} hour(s) ago. My answer was:\n{answer}\nIf you want a new search, say 'search again'."
            return Command(update={"messages": [AIMessage(content=msg)]}, goto=END)
    if user_question.lower().strip() == "search again":
        # Remove last question from memory to force new search
        for q in list(memory.get(thread_id, {})):
            if q == user_question:
                del memory[thread_id][q]
        save_memory(memory)
        return Command(update={"messages": [AIMessage(content="Okay, I'll search again. Please ask your question.")]}, goto=END)
    if isinstance(last, HumanMessage) and last.content.strip().upper() == "FINISH":
        logger.info("User requested conversation end.")
        return Command(goto=END)
    if isinstance(last, HumanMessage) and not any(
        word in last.content.lower() for word in ["stock", "price", "market"]
    ):
        refusal = "I only answer questions related to the stock market."
        return Command(update={"messages": [AIMessage(content=refusal)]}, goto=END)
    step = state.get("step", 0)
    if step == 0:
        # First gather Trump and Vance news
        return Command(update={"step": 1}, goto="trump_vance_news")
    elif step == 1:
        # Then gather company market info
        return Command(update={"step": 2}, goto="company_info")
    else:
        # Prepare a short report combining sub-agent outputs
        trump_news = next(
            (m.content for m in state["messages"] if getattr(m, "name", "") == "trump_vance_news"),
            "",
        )
        company_info = next(
            (m.content for m in state["messages"] if getattr(m, "name", "") == "company_info"),
            "",
        )
        # Use LLM to summarize the results
        summary_prompt = f"Summarize the following information for the user.\nTrump/Vance: {trump_news}\nCompany: {company_info}"
        summary = llm.invoke([HumanMessage(content=summary_prompt)])
        # Save answer to memory
        if thread_id not in memory:
            memory[thread_id] = {}
        memory[thread_id][user_question] = {"answer": summary.content, "ts": now}
        save_memory(memory)
        return Command(update={"messages": [AIMessage(content=summary.content)]}, goto=END)


# --- Utility -------------------------------------------------------------------

# 대화 내용을 파일로 기록하는 함수
def log_history(messages: List[BaseMessage]) -> None:
    """Append the conversation to ``conversation.log``."""
    with open("conversation.log", "a", encoding="utf-8") as f:
        for m in messages:
            role = getattr(m, "role", getattr(m, "name", ""))
            f.write(f"{role}: {m.content}\n")
        f.write("-" * 20 + "\n")

MEMORY_FILE = "memory_saver.json"
def load_memory():
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


# --- Entry point ---------------------------------------------------------------

# 그래프를 구성하고 예시 대화를 실행하는 메인 함수
def main() -> None:
    builder = StateGraph(State)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("trump_vance_news", trump_vance_news_node)
    builder.add_node("company_info", company_info_node)
    builder.set_entry_point("supervisor")
    graph = builder.compile()

    import uuid
    thread_id = str(uuid.uuid4())
    conversation: List[BaseMessage] = []
    while True:
        question = input("User: ")
        conversation.append(HumanMessage(content=question))
        result = graph.invoke({"messages": conversation, "step": 0, "thread_id": thread_id})
        new_messages = result["messages"][len(conversation) :]
        conversation = result["messages"]
        log_history(conversation)
        for msg in new_messages:
            if isinstance(msg, AIMessage):
                print(msg.content)
        if question.strip().upper() == "FINISH":
            break


if __name__ == "__main__":
    main()

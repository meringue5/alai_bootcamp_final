# 📄 AI 기반 C 소스코드 분석기 - 시스템 설계 요구사항서

---

## 📌 프로젝트 개요

본 프로젝트는 **LangGraph 기반 Multi-Agent 구조**와 **RAG(벡터스토어 기반 검색)**를 활용하여 C 소스코드의 정적분석, 안티패턴 검출, 유사도 기반 의사코드 생성 및 리포트 추출을 수행하는 대화형 AI 에이전트 시스템이다. 전체 시스템은 Streamlit UI를 통해 사용자와 인터랙션한다.

---

## 📌 시스템 아키텍처

### 전체 컴포넌트 구성

- **Supervisor Agent**
  - 사용자의 커맨드 기반 대화 세션 관리 ("분석 결과 추출", "종료" 명령 등)
  - Analyzer 및 Report Extractor 호출을 제어

- **Analyzer Sub-Agent**
  - 업로드된 C 소스코드 분석 담당
  - Chain-of-Thought 기반 추론 수행
  - 정적 분석 → 안티패턴 검출 → 유사사례 참조 → 의사코드 생성 → 결과 DB 저장

- **Report Extractor Sub-Agent**
  - 누적된 분석 결과를 PDF로 추출하여 제공

- **Vector Store (FAISS + Semantic Chunker)**
  - 업로드된 소스코드 임베딩 저장
  - 유사도 검색 기반 RAG 적용

- **Streamlit UI**
  - 사용자가 코드 업로드 및 결과 확인
  - 분석 상태 및 PDF 다운로드 제공

---

## 📌 전체 사용자 흐름 (User Flow)

### 1️⃣ 초기화

- Streamlit UI 접속
- 소스코드 업로드 준비 상태 확인

### 2️⃣ C 소스코드 업로드

- 사용자가 C 파일 업로드
- SemanticChunker로 소스코드 문서 임베딩 수행
- FAISS 벡터스토어에 임베딩 저장

### 3️⃣ Analyzer Sub-Agent 분석 흐름 (Chain-of-Thought 적용)

#### CoT 단계 1: 정적 분석

- 총 라인수, 함수수, 변수수, 순환복잡도 산출
- 복잡도 지표에 기반한 코드 복잡성 추론
- 예시 추론:
  - "순환 복잡도가 18로 높다 → 조건문 중첩이 심하다 → 유지보수 난이도 상승 예상"

#### CoT 단계 2: 안티패턴 검출

- 주요 안티패턴 탐지:
  - Global Variable Misuse
  - Deeply Nested Conditionals
- 안티패턴 영향 및 난이도 추론
- 예시 추론:
  - "글로벌 변수 다중 접근 → 상태 추적 어려움 → 리팩토링 시 파라미터화 필요"

#### CoT 단계 3: 유사 사례 참조 (RAG 기반)

- FAISS 검색으로 유사도 높은 과거 분석 사례 조회
- 기존 리팩토링/분석 패턴을 참조
- 예시 추론:
  - "85% 유사도 사례 참고 → 함수 분리와 캡슐화 접근 적용"

#### CoT 단계 4: 의사코드 생성

- 상기 추론 결과를 통합하여 유지보수성 중심 의사코드 생성
- 예시 추론:
  - "글로벌 변수를 함수 인자로 치환 → 조건문 간소화 → 로직 흐름 명확화"

#### CoT 단계 5: 결과 저장

- 분석 결과 DB에 저장:
  - 정적분석 스코어
  - 안티패턴 리스트
  - 의사코드
  - 유사사례 참조정보

### 4️⃣ 추가 소스코드 반복 업로드

- 매번 새로운 소스코드 분석 시, 기존 벡터스토어와 DB를 활용하여 효율 증가

### 5️⃣ 분석 결과 추출

- 사용자가 "분석 결과를 추출" 명령 입력
- Report Extractor가 DB에서 PDF 리포트 생성
- PDF 다운로드 제공

### 6️⃣ 세션 종료

- 사용자가 "종료" 명령 입력
- Supervisor가 세션 종료

---

## 📌 핵심 기술 스택 매핑표

| 요구사항 | 구현 상세 |
| ---- | ---- |
| Prompt Engineering | Chain-of-Thought 기반 다단계 추론 프롬프트 |
| LangChain / LangGraph | Supervisor + Analyzer + Report Extractor Agent |
| Multi-Agent | 역할 분리 명확 |
| RAG (검색강화생성) | Semantic Chunker + FAISS 유사도 검색 |
| Streamlit | 전체 UI 구현 |
| 환경변수 관리 | API Key 등 민감정보는 ENV 변수 사용 |
| 파일 구조 | 서비스 수준 모듈화 설계 |
| PDF Export | 분석 리포트화 기능 포함 |

---

## 📌 추가 고도화 고려사항 (선택사항)

- 멀티턴 메모리 적용 (LangChain Memory)
- FastAPI 연동 (백엔드 API 확장성 확보)
- Docker 패키징 (서비스 이식성 확보)

---

## 📌 시스템 설계 핵심 요약

- **LangGraph 기반 Multi-Agent 시스템**
- **Streamlit UI 제공**
- **Chain-of-Thought 기반 다단계 추론 설계**
- **FAISS 기반 RAG 적용**
- **업로드 → 분석 → 누적 DB화 → 유사도 보정 → 의사코드 생성 → 리포트 추출**

---

# 📄 Analyzer Sub-Agent: Chain-of-Thought 프롬프트 설계서

---

## 📌 목적

본 프롬프트는 업로드된 C 소스코드를 **정적 분석 → 안티패턴 검출 → 유사사례 참조 → 의사코드 생성** 단계로 분석하는 **Chain-of-Thought 기반 다단계 추론 프롬프트**이다.  
LLM이 각 단계에서 reasoning을 통해 설명 가능한 추론 경로를 따라가도록 설계한다.

---

## 📌 시스템 역할 정의 (System Prompt)

> 당신은 숙련된 C 소스코드 분석 전문가입니다.  
> 업로드된 C 소스코드를 입력받아 다음과 같은 단계로 체계적이고 논리적으로 분석하십시오.  
> 각 단계에서 추론 과정(reasoning)을 반드시 상세히 기술하십시오.

---

## 📌 입력

- `소스코드` : 업로드된 C 소스 전체 텍스트
- `이전 분석 사례` (선택) : 벡터스토어에서 검색된 유사 소스코드 분석 결과

---

## 📌 Chain-of-Thought 단계별 프롬프트 흐름

### **Step 1: 정적 분석**

- 소스코드의 다음 요소를 추출하라:
  - 총 라인수
  - 함수 개수
  - 변수 개수
  - 순환 복잡도 (Cyclomatic Complexity)

- 추출된 수치를 기반으로 **복잡도 및 유지보수 난이도에 대한 추론**을 서술하라.

#### 💡 예시 reasoning
- "이 소스코드는 350 라인, 12개의 함수, 45개의 변수를 포함합니다."
- "순환 복잡도가 18로 높습니다 → 중첩된 조건문 및 반복문 사용이 많은 것으로 추정됩니다."
- "유지보수 및 리팩토링 난이도가 높을 수 있습니다."

---

### **Step 2: 안티패턴 검출**

- 소스코드에서 다음 주요 안티패턴을 검출하라:
  - Global Variable Misuse
  - Deeply Nested Conditionals
  - Magic Numbers 사용
  - Long Function (200라인 초과 함수 등)

- 발견된 안티패턴이 코드 품질 및 리팩토링 난이도에 미치는 영향을 논리적으로 추론하라.

#### 💡 예시 reasoning
- "전역변수 `global_count`가 5개의 함수에서 사용됨 → 상태 추적이 어렵다."
- "중첩된 조건문이 최대 5단계 깊이로 확인됨 → 복잡성 및 가독성 저하."
- "매직 넘버 `57`이 반복 사용됨 → 의미 불명확, 수정 어려움."

---

### **Step 3: 유사 사례 참조 (RAG)**

- 만약 `이전 분석 사례`가 존재할 경우 다음처럼 활용하라:
  - 유사 사례에서 리팩토링에 사용된 전략을 추출하라.
  - 현재 분석 대상에도 적용할 수 있는 개선 방향을 제안하라.

#### 💡 예시 reasoning
- "유사 사례에서 전역변수를 파라미터 객체로 캡슐화함"
- "함수 분리 및 상태 패턴 적용 → 유지보수성 향상 확인"
- "동일한 접근법을 본 분석에도 추천함"

---

### **Step 4: 의사코드 생성**

- 앞 단계의 분석 결과를 통합하여 의사코드를 생성하라.
- 핵심 로직, 입출력 흐름, 상태 전환 등을 명확히 드러내라.
- 코드 내 불필요한 복잡성은 제거하고, 유지보수성을 최우선으로 고려하라.
- 주석 및 설명을 충분히 삽입하라.

#### 💡 예시 의사코드 포맷
```pseudocode
// 주요 데이터 초기화
state = initialize_state()

// 메인 처리 루프
for item in dataset:
    if is_valid(item):
        process(item, state)
    else:
        log_error(item)

// 결과 반환
return state.summary()
```
### Step 5: 결과 저장 형식
- 최종 출력은 다음 형태로 정리하라:
```json
{
  "static_analysis": {
    "total_lines": ...,
    "function_count": ...,
    "variable_count": ...,
    "cyclomatic_complexity": ...,
    "complexity_reasoning": "..."
  },
  "anti_patterns": [
    { "type": "Global Variable Misuse", "details": "..." },
    { "type": "Deeply Nested Conditionals", "details": "..." },
    ...
  ],
  "case_reference": {
    "similarity_score": ...,
    "reference_summary": "...",
    "adaptation_suggestion": "..."
  },
  "pseudocode": "... (문자열)"
}
```

### 📌 중요 원칙
- reasoning 설명은 생략 없이 구체적으로 작성할 것
- 각 단계 결과는 논리적으로 연결되도록 서술할 것
- 단순 요약이 아닌 분석자의 사고과정처럼 작성할 것

---

### 📌 시스템 주의사항
- 이 프롬프트는 실 서비스 시스템에서 반복 사용됨
- 신뢰도, 일관성, 재현성을 중시
- 동일 입력에 대해 일관된 분석 결과 도출할 것

# 📄 C 코드 분석기: LangGraph Edgeless 기반 설계서 (최소형 업무지시서)

---

## 📌 시스템 개요

LangGraph 기반 edgeless graph로 동작하는 Multi-Agent AI 시스템이다.  
Supervisor Agent가 명령을 해석하여 하위 Agent를 호출하며, 전체 command 기반 인터랙션으로 제어된다.

---

## 📌 주요 컴포넌트

- Supervisor Agent (Command Router)
- Analyzer Agent (소스코드 분석 담당)
- Report Extractor Agent (리포트 생성 담당)
- FAISS Vector Store (임베딩 검색)
- Streamlit UI (사용자 인터페이스)

---

## 📌 Supervisor Agent (Command 기반 Edgeless Controller)

- 사용자 입력을 command로 파싱
- 지원 명령어:
  - `"업로드"` → Analyzer Agent 호출
  - `"분석 결과 추출"` → Report Extractor Agent 호출
  - `"종료"` → 세션 종료
  - (예외처리: 정의되지 않은 명령 → 에러 응답)

---

## 📌 Analyzer Agent 작업 절차

1. **정적 분석**
   - 라인수, 함수수, 변수수, 복잡도 산출
   - 복잡도 추론 reasoning 포함

2. **안티패턴 검출**
   - Global Variable, Deep Nesting 등 탐지
   - 영향도 추론 reasoning 포함

3. **유사 사례 검색**
   - FAISS 유사도 검색 → 과거 사례 참조
   - 적용 가능 개선안 reasoning

4. **의사코드 생성**
   - 상기 추론을 통합 → 유지보수성 강조 pseudocode 생성

5. **결과 DB 저장**
   - 분석 결과 전체 저장 (메모리 DB)

---

## 📌 Report Extractor Agent 작업 절차

- 내부 DB를 기반으로 전체 분석 요약
- PDF 리포트 생성 및 Streamlit을 통해 다운로드 제공

---

## 📌 RAG 구조

- 소스코드 업로드 시 Semantic Chunker → FAISS 임베딩 등록
- Analyzer에서 FAISS 검색 → 유사사례 활용 reasoning 수행

---

## 📌 Streamlit UI 기능

- 파일 업로드 기능
- 소스코드 목록 표시
- 명령어 입력 인터페이스 (커맨드 기반)
- 분석 결과 PDF 다운로드 제공

---

## 📌 Prompt 설계 (Analyzer Agent)

- Chain-of-Thought 기반 reasoning 포함
- 각 분석 단계 reasoning → 최종 pseudocode
- 출력 형식은 JSON 객체로 통일

> 별도의 상세 프롬프트 설계는 [Analyzer CoT Prompt 설계서] 참고 (이미 설계됨)

---

## 📌 필수 고려사항

- 모든 API Key / 민감정보는 환경변수 사용
- 코드 모듈화 (서비스 수준 구조)
- 일관된 재현성 확보
- 오류 내성 설계

---

## 📌 선택 고도화 항목 (Optional)

- 멀티턴 메모리 적용
- FastAPI 백엔드화
- Docker 컨테이너 패키징

---

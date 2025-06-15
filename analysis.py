# 코드 정적 분석 및 안티패턴 탐지 함수 정의
import re
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class StaticAnalysisResult:
    total_lines: int  # 전체 코드 라인 수
    function_count: int  # 함수 개수
    variable_count: int  # 변수 개수
    cyclomatic_complexity: int  # 순환 복잡도
    complexity_reasoning: str  # 복잡도 산출 근거

def analyze_static(code: str) -> StaticAnalysisResult:
    """코드의 기본 통계와 복잡도를 분석합니다."""
    lines = code.splitlines()
    total_lines = len(lines)

    func_pattern = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\s*\([^;]*?\)\s*{")
    function_count = len(func_pattern.findall(code))

    var_pattern = re.compile(r"\b(?:int|float|double|char|long|short|unsigned|signed)\s+[A-Za-z_][A-Za-z0-9_]*\s*(?:=|;)")
    variable_count = len(var_pattern.findall(code))

    cyclomatic_complexity = len(re.findall(r"\b(if|for|while|case|&&|\|\|)\b", code)) + 1
    reasoning = "Cyclomatic complexity estimated from control flow statements."

    return StaticAnalysisResult(
        total_lines=total_lines,
        function_count=function_count,
        variable_count=variable_count,
        cyclomatic_complexity=cyclomatic_complexity,
        complexity_reasoning=reasoning,
    )

@dataclass
class AntiPattern:
    type: str  # 안티패턴 종류
    details: str  # 상세 설명

def detect_anti_patterns(code: str) -> List[AntiPattern]:
    """코드에서 안티패턴을 탐지합니다."""
    patterns: List[AntiPattern] = []
    if re.search(r"^\s*(?:int|float|double|char)\s+[A-Za-z_][A-Za-z0-9_]*\s*(?:=|;)", code, re.MULTILINE):
        patterns.append(AntiPattern("Global Variable Misuse", "Global variable detected."))
    if len(re.findall(r"if\s*\([^)]*\)\s*{", code)) >= 3:
        patterns.append(AntiPattern("Deeply Nested Conditionals", "Multiple nested if statements."))
    return patterns

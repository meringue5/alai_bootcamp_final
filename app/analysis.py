import re
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class StaticAnalysisResult:
    total_lines: int
    function_count: int
    variable_count: int
    cyclomatic_complexity: int
    complexity_reasoning: str


def analyze_static(code: str) -> StaticAnalysisResult:
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
    type: str
    details: str


def detect_anti_patterns(code: str) -> List[AntiPattern]:
    patterns: List[AntiPattern] = []
    if re.search(r"^\s*(?:int|float|double|char)\s+[A-Za-z_][A-Za-z0-9_]*\s*(?:=|;)", code, re.MULTILINE):
        patterns.append(AntiPattern("Global Variable Misuse", "Global variable detected."))
    if len(re.findall(r"if\s*\([^)]*\)\s*{", code)) >= 3:
        patterns.append(AntiPattern("Deeply Nested Conditionals", "Multiple nested if statements."))
    return patterns

import re
import json
from typing import List, Tuple


class GuardrailResult:
    def __init__(self, passed: bool, risk_score: float, flags: List[str]):
        self.passed = passed
        self.risk_score = risk_score
        self.flags = flags

    def dict(self) -> dict:
        return {
            "passed": self.passed,
            "risk_score": self.risk_score,
            "flags": self.flags,
        }


class PiiDetector:
    PATTERNS = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        "aws_key": r"AKIA[0-9A-Z]{16}",
    }

    def scan(self, text: str) -> GuardrailResult:
        flags = []
        for pii_type, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                flags.append(f"{pii_type}: {len(matches)} occurrence(s)")
        risk_score = min(1.0, len(flags) * 0.3)
        return GuardrailResult(
            passed=len(flags) == 0,
            risk_score=risk_score,
            flags=flags,
        )


class PromptInjectionDetector:
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions",
        r"forget\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|directions)",
        r"you\s+(are\s+)?(now|must\s+act\s+as)\s+",
        r"system\s+prompt:",
        r"new\s+instructions?:",
        r"override\s+(mode|instructions|commands)",
        r"do\s+not\s+(follow|obey|adhere)",
        r"disregard\s+(all\s+)?(previous|system)",
        r"you\s+are\s+(now|free|allowed)",
        r"simulate\s+(a\s+)?different",
        r"role.?play\s+as",
        r"bypass\s+(your\s+)?(restrictions|constraints|guidelines|rules)",
        r"act\s+as\s+(if|though)\s+you\s+(are|were)",
    ]

    def scan(self, text: str) -> GuardrailResult:
        flags = []
        text_lower = text.lower()
        for i, pattern in enumerate(self.INJECTION_PATTERNS):
            if re.search(pattern, text_lower):
                flags.append(f"injection_pattern_{i}")
        risk_score = min(1.0, len(flags) * 0.25)
        return GuardrailResult(
            passed=len(flags) == 0,
            risk_score=risk_score,
            flags=flags,
        )


class SafetyClassifier:
    UNSAFE_PATTERNS = [
        (r"\b(kill|murder|harm|attack)\b.*\b(people|person|child|group)", "violence"),
        (r"\b(hate|discriminat|racist|sexist)\b", "hate_speech"),
        (r"\b(suicide|self.?harm|self.?delete)\b", "self_harm"),
        (r"\b(drugs|illegal|weapon|explosive)\b.*\b(how|make|create|buy)", "illegal_activity"),
        (r"\b(explicit|porn|sexual)\s+content", "adult_content"),
    ]

    def scan(self, text: str) -> GuardrailResult:
        flags = []
        text_lower = text.lower()
        for pattern, category in self.UNSAFE_PATTERNS:
            if re.search(pattern, text_lower):
                flags.append(category)
        risk_score = min(1.0, len(flags) * 0.35)
        return GuardrailResult(
            passed=len(flags) == 0,
            risk_score=risk_score,
            flags=flags,
        )


class GuardrailEngine:
    def __init__(self):
        self.pii = PiiDetector()
        self.injection = PromptInjectionDetector()
        self.safety = SafetyClassifier()

    def scan_input(self, text: str) -> dict:
        return {
            "pii": self.pii.scan(text).dict(),
            "injection": self.injection.scan(text).dict(),
            "safety": self.safety.scan(text).dict(),
        }

    def scan_output(self, text: str) -> dict:
        return {
            "pii": self.pii.scan(text).dict(),
            "safety": self.safety.scan(text).dict(),
        }

    def should_block(self, scan_result: dict, threshold: float = 0.7) -> Tuple[bool, List[str]]:
        reasons = []
        for guard, result in scan_result.items():
            if result["risk_score"] >= threshold:
                reasons.append(f"{guard}: {', '.join(result['flags'])}")
        return (len(reasons) > 0, reasons)

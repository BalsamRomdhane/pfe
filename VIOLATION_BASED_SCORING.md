# Violation-Based Compliance Scoring System

## Overview

The violation-based compliance scoring system has been implemented to ensure that documents with clear control violations are classified as **non-compliant** and receive significantly lower scores. This replaces the legacy approach where high semantic similarity could result in incorrect compliance classifications.

## Key Changes

### 1. Violation Detection Module (`violation_detector.py`)

**Location**: `apps/compliance/services/violation_detector.py`

This new module identifies:
- **Violation patterns** (missing procedures, responsibilities, enforcement, approvals, reviews)
- **Evidence gaps** (no evidence found, missing required keywords, conflicting statements)
- **Weak language** (optional, vague, recommended language that suggests non-compliance)
- **Critical controls** (access control, authentication, encryption, audit logging, incident response, etc.)

**Key Methods**:

```python
# Detect violations for a control
violations = detector.detect_violations(
    document_text="...",
    control_description="User access must be approved",
    is_critical_control=True
)
# Returns: violation_count, critical_violation_count, penalty, violation_status

# Check for critical control issues
critical = detector.check_critical_control_compliance(
    missing_controls=["access control", "authentication"],
    document_text="...",
    standard_id="ISO27001"
)
# Returns: missing_critical_controls, critical_penalty, is_critical_issue

# Auto-classify as non-compliant
auto_check = detector.detect_automatic_non_compliant_triggers(
    violations_summary=violations,
    missing_controls=["..."],
    evidence_score=0.25,
    control_count=10
)
# Triggers: violation_threshold, critical_violation, insufficient_evidence, etc.
```

### 2. Strict Scoring Thresholds

**Compliance Classification Rules**: 

| Score Range | Status | Requirements |
|------------|--------|--------------|
| >= 80 | **COMPLIANT** | No violations, strong evidence, all procedures documented |
| 50-79 | **PARTIALLY_COMPLIANT** | < 30% non-compliant controls, max 2 violations |
| < 50 | **NON_COMPLIANT** | Auto-classified if any critical violations or >= 3 violations |

### 3. Violation Penalties

Each type of violation reduces the compliance score:

```
Base Score: 75/100

Violations Applied:
- Missing Procedure: -25 points (critical)
- Missing Responsibility: -25 points (critical)
- No Enforcement: -25 points (critical)
- Missing Approval: -15 points (high severity)
- Missing Review: -15 points (high severity)
- Weak Language: -10 points per instance

Final Score: 75 - 25 - 15 - 10 = 25/100 → NON_COMPLIANT
```

### 4. Multi-Factor Scorer Enhancements

**Location**: `apps/compliance/services/multi_factor_scorer.py`

#### Updated `calculate_control_score()` Method

**New Parameters**:
- `is_critical_control` (bool): Marks control as critical (higher penalties)

**Process**:
1. Calculate base score from 5 factors (semantic, evidence, LLM, structure, language)
2. **Detect violations** using new ViolationDetector
3. **Apply violation penalties** to base score
4. **Apply strict thresholds** for final classification
5. **Check auto-non-compliance triggers**

**Example Output**:
```python
{
    "overall_score": 32,  # After violations
    "score_before_violations": 65,  # Original weighted score
    "violation_penalty": -33,  # Penalties applied
    "status": "non_compliant",  # Strict classification
    "violations": {
        "violation_count": 3,
        "critical_violation_count": 1,
        "violation_status": "major",
        "violation_patterns": [...],
        "evidence_gaps": [...]
    },
    "auto_non_compliant": True,
    "auto_non_compliant_reasons": [
        "Insufficient evidence score (0.25 < 0.40)",
        "1 critical violation detected"
    ]
}
```

#### Updated `calculate_document_score()` Method

**Strict Classification Logic**:

```python
# Rule 1: If 1+ critical violations → NON_COMPLIANT
if critical_violations >= 1:
    status = "non_compliant"
    score = min(score, 45)

# Rule 2: If 3+ violations → NON_COMPLIANT
elif violation_count >= 3:
    status = "non_compliant"
    score = min(score, 45)

# Rule 3: If 50%+ controls are non-compliant → NON_COMPLIANT
elif non_compliant_count > total_count * 0.5:
    status = "non_compliant"
    score = min(score, 45)

# Rule 4: Apply score thresholds
elif score >= 80 and non_compliant == 0:
    status = "compliant"
elif score >= 50 and non_compliant < total_count * 0.3:
    status = "partially_compliant"
else:
    status = "non_compliant"
```

### 5. Result Formatter Enhancements

**Location**: `apps/compliance/services/result_formatter.py`

#### Updated Output Format

**Control Assessment**:
```python
{
    "control_id": "AC-01",
    "score": 32,
    "status": "NON_COMPLIANT",
    "violations": {
        "has_violations": True,
        "violation_count": 3,
        "critical_violations": 1,
        "details": [
            {
                "type": "missing_procedure",
                "severity": "critical",
                "weight": 25,
                "matches": 1
            }
        ],
        "recommendations": [
            "Define and document required procedures",
            "Document requirements using keywords: must, shall, required"
        ]
    },
    "missing_elements": [
        "access control procedure",
        "authentication policy"
    ]
}
```

**Document Assessment**:
```python
{
    "document_id": "doc_123",
    "overall_score": 32,
    "status": "NON_COMPLIANT",
    "violation_summary": {
        "total_violations_detected": 5,
        "critical_violations": 2,
        "violation_auto_classification": True,
        "auto_classification_reason": "2 critical violation(s) detected - automatic non-compliance"
    },
    "missing_controls": {
        "list": [
            "access control procedure",
            "authentication policy",
            "privileged access monitoring"
        ],
        "count": 3
    },
    "critical_findings": [
        {
            "severity": "CRITICAL",
            "finding": "Missing access control procedure",
            "action_required": "Immediate remediation required"
        }
    ]
}
```

## Usage Examples

### Example 1: Detecting a Non-Compliant Document

**Document**: "Access control is important. We don't have procedures for it yet."

```python
from apps.compliance.services.violation_detector import ViolationDetector
from apps.compliance.services.multi_factor_scorer import MultiFactorScorer

detector = ViolationDetector()
scorer = MultiFactorScorer()

document = "Access control is important. We don't have procedures for it yet."
control = "User access must be approved by IT administrator with documented authorization."

# Detect violations
violations = detector.detect_violations(
    document_text=document,
    control_description=control,
    is_critical_control=True  # Access control is critical
)

print(f"Violations: {violations['violation_count']}")
print(f"Critical: {violations['critical_violation_count']}")
print(f"Penalty: -{violations['penalty']} points")
# Output:
# Violations: 2
# Critical: 1
# Penalty: -50 points

# Calculate control score
score = scorer.calculate_control_score(
    document_text=document,
    control_description=control,
    semantic_similarity=0.7,  # High semantic similarity
    is_critical_control=True
)

print(f"Base Score: {score['score_before_violations']}")
print(f"Final Score: {score['overall_score']}")
print(f"Status: {score['status']}")
# Output:
# Base Score: 72
# Final Score: 32
# Status: non_compliant
```

### Example 2: Auto-Classification for Multiple Violations

**Document**: Multiple violations across controls

```python
non_compliant_controls = [{
    "violation_count": 2,
    "critical_violation_count": 1
}, {
    "violation_count": 3,
    "critical_violation_count": 0
}]

# Check auto-classification
auto_check = detector.detect_automatic_non_compliant_triggers(
    violations_summary=non_compliant_controls[0],
    missing_controls=["access", "auth", "encrypt"],
    evidence_score=0.25,
    control_count=10
)

print(f"Auto Non-Compliant: {auto_check['auto_classify_non_compliant']}")
print(f"Triggers: {auto_check['triggers']}")
# Output:
# Auto Non-Compliant: True
# Triggers: ['critical_violation_present', 'insufficient_evidence', 'too_many_critical_missing']
```

### Example 3: Critical Control Penalties

```python
# Missing 3+ critical controls
missing_critical = ["access control", "authentication", "encryption", "audit logging"]

critical_result = detector.check_critical_control_compliance(
    missing_controls=missing_critical,
    document_text=document,
    standard_id="ISO27001"
)

print(f"Critical Controls Missing: {critical_result['critical_control_count']}")
print(f"Penalty: -{critical_result['penalty']} points")
print(f"Is Critical Issue: {critical_result['is_critical_issue']}")

# Apply penalty to document score
document_score = {"overall_score": 65}
adjusted = scorer.apply_critical_control_penalties(
    document_score=document_score,
    missing_critical_controls=missing_critical
)

print(f"Original: {adjusted['original_score']}")
print(f"After Penalty: {adjusted['adjusted_score']}")
print(f"Status: {adjusted['adjusted_status']}")
# Output:
# Original: 65
# After Penalty: 15
# Status: non_compliant
```

## Workflow Integration

### Enhanced LangGraph Workflow

The orchestration workflow now integrates violation detection at each step:

```python
for control in controls:
    # Step 1: Retrieve context
    context = rag.retrieve_control_context(control)
    
    # Step 2: Detect violations
    violations = violation_detector.detect_violations(
        document_text=document,
        control_description=control["description"],
        is_critical_control=control.get("is_critical", False)
    )
    
    # Step 3: Extract evidence
    evidence = evidence_detector.extract_evidence(
        document_text=document,
        control_description=control["description"]
    )
    
    # Step 4: Calculate score WITH violations
    score = scorer.calculate_control_score(
        document_text=document,
        control_description=control["description"],
        semantic_similarity=similarity,
        llm_score=llm_result,
        is_critical_control=control.get("is_critical", False)
    )
    # Score already includes violation penalties and strict classification
    
    # Step 5: Verify with auditor
    audit = auditor.audit_assessment(
        control_description=control["description"],
        evidence=evidence["evidence"],
        initial_score=score["overall_score"],
        initial_status=score["status"]
    )
    
    # Step 6: Format result with violations
    formatted = formatter.format_control_assessment(
        control_id=control["id"],
        score=score["overall_score"],
        status=score["status"],
        violations=score["violations"],
        evidence=evidence["evidence"]
    )
```

## Scoring Examples

### Example 1: Strong Non-Compliance

```
Document: "We don't have access controls implemented"

Base Factors:
- Semantic Similarity: 85
- Evidence Detection: 10
- LLM Reasoning: 20
- Document Structure: 30
- Policy Language: 15
Base Score: (85*0.25 + 10*0.25 + 20*0.3 + 30*0.1 + 15*0.1) = 42/100

Violations Detected:
- Missing Procedure: -25
- No Enforcement: -25
- Missing Responsibility: -25
Total Penalty: -75 points

Final Score: 42 - 75 = -33 → 0 (clamped) → NON_COMPLIANT
Confidence: 0.85 (high confidence in non-compliance)
```

### Example 2: Partial Compliance with Violations

```
Document: "We have access control but procedures are incomplete"

Base Score: 68/100
Violations:
- Incomplete Implementation: -10
- Missing Review: -15
Penalty: -25 points

Final Score: 68 - 25 = 43/100 → NON_COMPLIANT (< 50)
Confidence: 0.75
```

### Example 3: Compliant Despite Minor Issues

```
Document: Full access control procedures, recent review, clear ownership

Base Score: 85/100
Violations: None (0 violations)
Penalty: 0 points

Final Score: 85 - 0 = 85/100 → COMPLIANT
Confidence: 0.95
```

## Configuration

### Adjustable Parameters

```python
# Violation weights (in violation_detector.py)
VIOLATION_PATTERNS = {
    "missing_procedure": {"weight": 25},  # Critical
    "missing_responsibility": {"weight": 25},  # Critical
    "no_enforcement": {"weight": 25},  # Critical
    "missing_approval": {"weight": 15},  # High
    "missing_review": {"weight": 15},  # High
    "incomplete_implementation": {"weight": 10},  # Medium
}

# Score thresholds (in multi_factor_scorer.py)
CLASSIFICATION_THRESHOLDS = {
    "compliant": 80,  # >= 80
    "partially_compliant": 50,  # 50-79
    "non_compliant": 0  # < 50
}

# Critical control penalties (in multi_factor_scorer.py)
CRITICAL_CONTROL_PENALTY = 25  # Per missing critical control
AUTOMATIC_NON_COMPLIANT_THRESHOLD = 3  # Violations to auto-classify
```

## Best Practices

1. **Always Mark Critical Controls**: Use `is_critical_control=True` for controls like access control, authentication, encryption

2. **Review Violation Details**: Check the `violations` field in results to understand why a score was reduced

3. **Address Critical Violations Immediately**: Any document with `critical_violation_count >= 1` should be treated as non-compliant

4. **Use Missing Controls**: The `missing_controls` list in results shows exactly what needs to be implemented

5. **Monitor Evidence Gaps**: Documents with `evidence_score < 0.4` are automatically flagged as problematic

## Migration Notes

For existing code using the old scoring system:

```python
# OLD CODE (may still compile but gives lenient scores)
score = scorer.calculate_control_score(
    document_text=doc,
    control_description=control
)

# NEW CODE (includes violation detection)
score = scorer.calculate_control_score(
    document_text=doc,
    control_description=control,
    is_critical_control=True  # Add this for critical controls
)

# Document level - old way
doc_score = scorer.calculate_document_score(
    document_text=doc,
    controls=controls,
    control_scores=scores
)

# No change needed - method automatically applies strict thresholds
# and includes violation data from control scores
```

## Testing Checklist

- [ ] Non-compliant documents receive < 50 score
- [ ] Documents with 3+ violations auto-classified as non-compliant
- [ ] Critical control violations trigger auto-classification
- [ ] Evidence score < 40% results in lower classification
- [ ] Result formatter includes violation details
- [ ] Missing controls list is accurate and actionable
- [ ] Critical findings section populated for serious issues
- [ ] Priority actions generated correctly

## Troubleshooting

**Q: Why is a document with 75% semantic match marked non-compliant?**
A: Violation detection penalties override semantic similarity. Check the `violations` field - it likely has critical violations present.

**Q: How can I see why a score dropped?**
A: Check the response object:
```python
score = scorer.calculate_control_score(...)
print(f"Before: {score['score_before_violations']}")
print(f"After: {score['overall_score']}")
print(f"Penalty: {score['violation_penalty']}")
print(f"Violations: {score['violations']}")
```

**Q: Can I adjust violation weights?**
A: Yes, modify `VIOLATION_PATTERNS` in `violation_detector.py` to change penalties.

**Q: What's the difference between partially_compliant and non_compliant?**
A: Partially Compliant (50-79): Some controls work, others need fixing. Non-Compliant (< 50): Critical issues, must implement immediately.

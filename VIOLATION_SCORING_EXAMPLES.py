"""Integration Examples: Violation-Based Compliance Scoring

This file contains practical examples showing how to use the new violation-based
compliance scoring system in your compliance engine.
"""

# ============================================================================
# EXAMPLE 1: Basic Control Assessment with Violations
# ============================================================================

def example_1_basic_assessment():
    """Assess a single control with violation detection."""
    from apps.compliance.services.multi_factor_scorer import MultiFactorScorer
    from apps.compliance.services.evidence_detector import EvidenceDetector
    
    scorer = MultiFactorScorer()
    evidence_detector = EvidenceDetector()
    
    # Control requirement
    control_desc = "User access must be approved by IT administrator with documented authorization"
    
    # Document with issue
    document = """
    Access Control Policy
    
    Our organization has user access processes. However, we don't have documented 
    approval procedures. Access is sometimes granted without formal authorization.
    No periodic reviews are conducted.
    """
    
    # Calculate score WITH violation penalties
    score_result = scorer.calculate_control_score(
        document_text=document,
        control_description=control_desc,
        semantic_similarity=0.65,  # Some relevant content
        is_critical_control=True   # Access control is critical
    )
    
    # Results show violation penalties applied
    print(f"Score Before Violations: {score_result['score_before_violations']}")  # ~65
    print(f"Violation Penalty: -{score_result['violation_penalty']}")  # -50
    print(f"Final Score: {score_result['overall_score']}")  # ~15
    print(f"Status: {score_result['status']}")  # non_compliant
    print(f"Violations: {score_result['violations']['violation_count']}")  # 3
    print(f"Critical Violations: {score_result['violations']['critical_violation_count']}")  # 2
    
    # Auto-classification triggers
    if score_result['auto_non_compliant']:
        print(f"Auto-Classified: {score_result['auto_non_compliant_reasons']}")
        # ['Insufficient evidence detected', 'Critical violation present']
    
    return score_result


# ============================================================================
# EXAMPLE 2: Document-Level Assessment with Multiple Controls
# ============================================================================

def example_2_document_assessment():
    """Assess entire document against multiple controls."""
    from apps.compliance.services.multi_factor_scorer import MultiFactorScorer
    from apps.compliance.services.violation_detector import ViolationDetector
    
    scorer = MultiFactorScorer()
    detector = ViolationDetector()
    
    document = """
    IT Security Policy - Draft
    
    1. Access Control
    Status: We are working on this. No procedures yet.
    
    2. Authentication
    Status: We use passwords. No MFA implementation planned.
    
    3. Data Encryption
    Status: Not implemented. We store data in plain text.
    
    4. Audit Logging
    Status: Basic logs exist. No centralized monitoring.
    
    5. Incident Response
    Status: No documented process defined.
    """
    
    controls = [
        {
            "id": "AC-01",
            "description": "Access control procedures must be documented",
            "is_critical": True
        },
        {
            "id": "AUTH-01",
            "description": "Multi-factor authentication must be implemented",
            "is_critical": True
        },
        {
            "id": "DES-01",
            "description": "Data must be encrypted at rest and in transit",
            "is_critical": True
        },
        {
            "id": "AUD-01",
            "description": "Audit logs must be centrally monitored",
            "is_critical": False
        },
        {
            "id": "IR-01",
            "description": "Incident response procedure must be documented",
            "is_critical": True
        }
    ]
    
    # Score each control
    control_scores = []
    for control in controls:
        score = scorer.calculate_control_score(
            document_text=document,
            control_description=control["description"],
            semantic_similarity=0.5,
            is_critical_control=control["is_critical"]
        )
        control_scores.append(score)
    
    # Calculate document-level score WITH strict thresholds
    doc_score = scorer.calculate_document_score(
        document_text=document,
        controls=controls,
        control_scores=control_scores
    )
    
    print(f"Document Score: {doc_score['overall_score']}/100")
    print(f"Status: {doc_score['status']}")
    print(f"Compliance: {doc_score['summary']['compliant']}/{doc_score['summary']['total_controls']}")
    print(f"Violations: {doc_score['violation_summary']['total_violations_detected']}")
    print(f"Critical Violations: {doc_score['violation_summary']['critical_violations']}")
    print(f"Missing Controls: {len(doc_score['missing_controls'])}")
    
    # Likely result:
    # Document Score: 18/100
    # Status: non_compliant
    # Violations: 8+
    # Critical Violations: 3+
    # Missing Controls: 5
    
    return doc_score


# ============================================================================
# EXAMPLE 3: Violation Detection Analysis
# ============================================================================

def example_3_violation_analysis():
    """Detailed analysis of violations in a document."""
    from apps.compliance.services.violation_detector import ViolationDetector
    
    detector = ViolationDetector()
    
    document = """
    Access Control Guidelines
    
    We believe access control is important but we don't have procedures for it.
    No one is assigned responsibility. The system is not monitored.
    """
    
    control = "User access must be approved and monitored"
    
    # Get detailed violation information
    violations = detector.detect_violations(
        document_text=document,
        control_description=control,
        is_critical_control=True
    )
    
    print(f"Has Violations: {violations['has_violations']}")
    print(f"Violation Count: {violations['violation_count']}")
    print(f"Critical Violations: {violations['critical_violation_count']}")
    print(f"Violation Status: {violations['violation_status']}")  # e.g., "major"
    print(f"Total Penalty: -{violations['penalty']} points")
    
    # Examine specific violations
    print("\nViolation Patterns Detected:")
    for pattern in violations['violation_patterns'][:3]:
        print(f"  • {pattern['type']}: {pattern['severity']} severity")
        print(f"    Weight: -{pattern['weight']} points")
        print(f"    Matches: {pattern['matches']}")
    
    # View evidence gaps
    print("\nEvidence Gaps:")
    for gap in violations['evidence_gaps'][:3]:
        print(f"  • {gap['type']}: {gap.get('severity', 'N/A')}")
    
    # Recommendations for fixing
    print("\nRecommendations:")
    for rec in violations['recommendations'][:3]:
        print(f"  • {rec}")
    
    return violations


# ============================================================================
# EXAMPLE 4: Auto-Classification for Non-Compliance
# ============================================================================

def example_4_auto_classification():
    """Show how violations trigger automatic non-compliance classification."""
    from apps.compliance.services.violation_detector import ViolationDetector
    
    detector = ViolationDetector()
    
    # Build a violations summary with 3+ violations
    violations = {
        "violation_count": 5,
        "critical_violation_count": 2,
        "violation_patterns": [
            {"severity": "critical"},
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "high"},
            {"severity": "medium"}
        ]
    }
    
    # Check if auto-classification triggers
    auto_check = detector.detect_automatic_non_compliant_triggers(
        violations_summary=violations,
        missing_controls=["access", "authentication", "encryption"],
        evidence_score=0.25,  # Low evidence score
        control_count=10
    )
    
    print(f"Auto-Classify Non-Compliant: {auto_check['auto_classify_non_compliant']}")
    print(f"Number of Triggers: {auto_check['trigger_count']}")
    print(f"Triggers Activated:")
    for trigger in auto_check['triggers']:
        print(f"  • {trigger}")
    
    print(f"\nReasons for Classification:")
    for reason in auto_check['reasons']:
        print(f"  • {reason}")
    
    # Likely output:
    # Auto-Classify Non-Compliant: True
    # Triggers: ['critical_violation_present', 'violation_threshold', 'insufficient_evidence', 'too_many_critical_missing']
    
    return auto_check


# ============================================================================
# EXAMPLE 5: Critical Control Penalties
# ============================================================================

def example_5_critical_control_penalties():
    """Apply penalties for missing critical controls."""
    from apps.compliance.services.multi_factor_scorer import MultiFactorScorer
    from apps.compliance.services.violation_detector import ViolationDetector
    
    scorer = MultiFactorScorer()
    
    # After scoring all controls, we found missing critical ones
    missing_critical_controls = [
        "access control",
        "authentication",
        "encryption",
        "audit logging"
    ]
    
    # Document had moderate score without considering critical controls
    document_score = {
        "overall_score": 55,
        "status": "partially_compliant"
    }
    
    # Apply critical control penalties
    adjusted = scorer.apply_critical_control_penalties(
        document_score=document_score,
        missing_critical_controls=missing_critical_controls
    )
    
    print(f"Score Before Critical Penalties: {adjusted['original_score']}")
    print(f"Critical Controls Missing: {adjusted['critical_controls_missing']}")
    print(f"Penalty Per Control: 25 points × {adjusted['critical_controls_missing']} = {adjusted['critical_penalty']}")
    print(f"Score After Penalties: {adjusted['adjusted_score']}")
    print(f"Final Status: {adjusted['adjusted_status']}")  # Now non_compliant
    
    # Output:
    # Score Before: 55
    # Critical Missing: 4
    # Penalty: -100 points
    # Score After: 0 (clamped) → non_compliant
    
    return adjusted


# ============================================================================
# EXAMPLE 6: Full Workflow Integration
# ============================================================================

def example_6_full_workflow():
    """Complete workflow showing all components working together."""
    from apps.compliance.services.multi_factor_scorer import MultiFactorScorer
    from apps.compliance.services.violation_detector import ViolationDetector
    from apps.compliance.services.evidence_detector import EvidenceDetector
    from apps.compliance.services.result_formatter import ComplianceResultFormatter
    
    scorer = MultiFactorScorer()
    detector = ViolationDetector()
    evidence_detector = EvidenceDetector()
    formatter = ComplianceResultFormatter()
    
    # Sample document
    document = """
    Information Security Policy v0.5
    
    Access Control:
    - Process: To be determined
    - Responsibility: Unassigned
    - Review: None scheduled
    
    Authentication:
    - Status: Passwords only, no MFA
    - May implement MFA in future if needed
    
    Incident Response:
    - No documented process yet
    """
    
    controls = [
        {"id": "AC-01", "description": "Access control must be documented and enforced", "is_critical": True},
        {"id": "AUTH-01", "description": "MFA must be implemented", "is_critical": True},
        {"id": "IR-01", "description": "Incident response procedure required", "is_critical": True}
    ]
    
    # Step 1: Score each control
    all_scores = []
    for control in controls:
        score = scorer.calculate_control_score(
            document_text=document,
            control_description=control["description"],
            semantic_similarity=0.4,
            is_critical_control=control["is_critical"]
        )
        all_scores.append({
            **control,
            "score": score["overall_score"],
            "status": score["status"],
            "violations": score["violations"],
            "confidence": score["confidence"]
        })
    
    # Step 2: Calculate document-level compliance
    doc_result = scorer.calculate_document_score(
        document_text=document,
        controls=controls,
        control_scores=[{"overall_score": s["score"], "status": s["status"], "confidence": s["confidence"], "violations": s["violations"]} for s in all_scores]
    )
    
    # Step 3: Extract missing controls
    missing = [c["id"] for c in all_scores if c["status"] != "compliant"]
    
    # Step 4: Format for user consumption
    formatted = formatter.format_document_assessment(
        document_id="doc_001",
        standard_id="ISO27001",
        overall_score=doc_result["overall_score"],
        overall_status=doc_result["status"],
        confidence=doc_result["confidence"],
        controls=all_scores,
        document_structure_score=35,
        language_quality_score=25,
        document_language="en",
        violations_summary=doc_result["violation_summary"],
        missing_controls=missing
    )
    
    # Print results
    print("=== COMPLIANCE ASSESSMENT REPORT ===")
    print(f"Document: {formatted['document_id']}")
    print(f"Standard: {formatted['standard_id']}")
    print(f"\nOVERALL SCORE: {formatted['overall_assessment']['score']}/100")
    print(f"STATUS: {formatted['overall_assessment']['status_label']}")
    print(f"CONFIDENCE: {formatted['overall_assessment']['confidence_percentage']}")
    
    print(f"\nVIOLATIONS:")
    print(f"  Total: {formatted['violation_summary']['total_violations_detected']}")
    print(f"  Critical: {formatted['violation_summary']['critical_violations']}")
    print(f"  Auto-Classification: {formatted['violation_summary']['violation_auto_classification']}")
    
    print(f"\nCOMPLIANCE:")
    print(f"  Compliant: {formatted['compliance_summary']['compliant']}")
    print(f"  Partial: {formatted['compliance_summary']['partially_compliant']}")
    print(f"  Non-Compliant: {formatted['compliance_summary']['non_compliant']}")
    
    print(f"\nMISSING CONTROLS: {formatted['missing_controls']['count']}")
    for control in formatted['missing_controls']['list']:
        print(f"  • {control}")
    
    print(f"\nCRITICAL FINDINGS:")
    for finding in formatted['critical_findings']:
        print(f"  • [{finding['severity']}] {finding['finding']}")
        print(f"    Action: {finding['action_required']}")
    
    print(f"\nPRIORITY ACTIONS:")
    for action in formatted['priority_actions'][:3]:
        print(f"  • [{action['priority']}] {action['action']}")
        print(f"    Deadline: {action['deadline']}")
    
    return formatted


# ============================================================================
# EXAMPLE 7: Comparing Old vs New Scoring
# ============================================================================

def example_7_scoring_comparison():
    """Show the difference between old (lenient) and new (strict) scoring."""
    
    document = "We use passwords for access control but no formal procedures exist."
    control = "User access must be approved and documented"
    
    # OLD APPROACH (would give higher score):
    # - Semantic similarity alone: 0.65 → 65/100
    # - Status: "partially_compliant" ✗ WRONG for this case
    # - Confidence: 0.68
    
    # NEW APPROACH (violation-aware):
    from apps.compliance.services.multi_factor_scorer import MultiFactorScorer
    
    scorer = MultiFactorScorer()
    new_score = scorer.calculate_control_score(
        document_text=document,
        control_description=control,
        semantic_similarity=0.65,
        is_critical_control=True
    )
    
    print("OLD SCORING (Semantic-Only):")
    print("  Score: 65/100")
    print("  Status: partially_compliant")
    print("  ✗ PROBLEM: Ignores violations, high false positive")
    
    print("\nNEW SCORING (Violation-Aware):")
    print(f"  Base Score: {new_score['score_before_violations']}/100")
    print(f"  Violations: {new_score['violations']['violation_count']}")
    print(f"  Penalty: -{new_score['violation_penalty']} points")
    print(f"  Final Score: {new_score['overall_score']}/100")
    print(f"  Status: {new_score['status']}")
    print("  ✓ CORRECT: Violations reduce score, accurate classification")


# ============================================================================
# EXAMPLE 8: Weak Language Detection
# ============================================================================

def example_8_weak_language():
    """Show how weak language impacts compliance scoring."""
    from apps.compliance.services.language_analyzer import LanguageAnalyzer
    
    analyzer = LanguageAnalyzer()
    
    # Document with weak language
    weak_doc = """
    Password Policy
    
    We recommend using strong passwords.
    Users should consider using passphrases.
    MFA might be helpful if users prefer it.
    Management may want to review this policy.
    """
    
    # Same policy with strong language
    strong_doc = """
    Password Policy
    
    Users must use strong passwords.
    Passphrases are required for administrators.
    MFA is mandatory for all accounts.
    Management shall review this policy quarterly.
    """
    
    weak_score = analyzer.language_compliance_score(weak_doc)
    strong_score = analyzer.language_compliance_score(strong_doc)
    
    print(f"Weak Language Document: {weak_score}/100")
    print("  Contains: recommend, should, might, may")
    
    print(f"\nStrong Language Document: {strong_score}/100")
    print("  Contains: must, required, mandatory, shall")
    
    print(f"\nDifference: {strong_score - weak_score} points")
    print("  → Weak language results in lower compliance score")


# ============================================================================
# Usage in Django View
# ============================================================================

def example_view_usage():
    """Example of using violation-based scoring in a Django view."""
    
    # In your views.py:
    from django.http import JsonResponse
    from apps.compliance.services.multi_factor_scorer import MultiFactorScorer
    from apps.compliance.services.result_formatter import ComplianceResultFormatter
    from apps.documents.models import Document
    from apps.standards.models import Standard
    
    def assess_document(request, document_id):
        doc = Document.objects.get(id=document_id)
        standard = Standard.objects.get(id=request.GET.get('standard_id'))
        
        scorer = MultiFactorScorer()
        formatter = ComplianceResultFormatter()
        
        # Score each control
        scores = []
        for control in standard.controls.all():
            score = scorer.calculate_control_score(
                document_text=doc.content,
                control_description=control.description,
                semantic_similarity=0.5,  # From embeddings
                is_critical_control=control.identifier.startswith("CRITICAL")
            )
            scores.append(score)
        
        # Document assessment
        doc_score = scorer.calculate_document_score(
            document_text=doc.content,
            controls=[{"id": c.id, "description": c.description} for c in standard.controls.all()],
            control_scores=scores
        )
        
        # Format for API response
        result = formatter.format_document_assessment(
            document_id=doc.id,
            standard_id=standard.id,
            overall_score=doc_score["overall_score"],
            overall_status=doc_score["status"],
            confidence=doc_score["confidence"],
            controls=scores,
            document_structure_score=50,
            language_quality_score=60,
            violations_summary=doc_score["violation_summary"],
            missing_controls=doc_score.get("missing_controls", [])
        )
        
        return JsonResponse(result)


if __name__ == "__main__":
    print("Running Examples...\n")
    
    print("=" * 70)
    print("EXAMPLE 1: Basic Assessment")
    print("=" * 70)
    example_1_basic_assessment()
    
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Violation Analysis")
    print("=" * 70)
    example_3_violation_analysis()
    
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Auto-Classification")
    print("=" * 70)
    example_4_auto_classification()
    
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Comparison")
    print("=" * 70)
    example_7_scoring_comparison()

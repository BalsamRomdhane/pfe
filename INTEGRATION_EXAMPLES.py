"""
Integration Example: Using the Enhanced Compliance Engine

This example shows how to use the new reliability improvements
in your compliance analysis workflow.
"""

# Example 1: Using Enhanced Workflow Directly
# ============================================

from apps.orchestration.langgraph_workflow import EnhancedLangGraphWorkflow
from apps.documents.models import Document
from apps.standards.models import Standard

# Initialize the enhanced workflow
workflow = EnhancedLangGraphWorkflow()

# Get a document and standard
doc = Document.objects.get(id=1)
standard = Standard.objects.get(id=1)

# Convert to dict format for workflow
document_dict = {
    "id": doc.id,
    "text": doc.text,
    "file_name": doc.file.name if doc.file else "unknown"
}

standard_dict = {
    "id": standard.id,
    "name": standard.name,
    "description": standard.description,
    "controls": [
        {
            "id": control.id,
            "identifier": control.identifier,
            "description": control.description
        }
        for control in standard.controls.all()
    ]
}

# Run the workflow
result = workflow.run(document=document_dict, standard=standard_dict)

# Access the results
overall_score = result["compliance"]["overall_assessment"]["overall_assessment"]["score"]
overall_status = result["compliance"]["overall_assessment"]["overall_assessment"]["status"]
structure_score = result["structure_validation"]["structure_score"]
language_score = result["language_analysis"]["language_quality_score"]

print(f"Overall Compliance Score: {overall_score}/100")
print(f"Status: {overall_status}")
print(f"Structure Maturity: {result['structure_validation']['maturity']}")
print(f"Language Strength: {result['language_analysis']['language_type']}")


# Example 2: Using Individual Components
# ========================================

from apps.compliance.services.evidence_detector import EvidenceDetector
from apps.compliance.services.multi_factor_scorer import MultiFactorScorer
from apps.rag.hybrid_retriever import HybridRetriever

# Extract evidence for a specific control
evidence_detector = EvidenceDetector()
evidence = evidence_detector.extract_evidence(
    document_text=doc.text,
    control_description="Access controls must be implemented"
)

print(f"\nEvidence for Access Control:")
print(f"  - Found {len(evidence['evidence'])} evidence sentences")
print(f"  - Confidence: {evidence['confidence']:.0%}")
print(f"  - Type: {evidence['evidence_type']}")

# Use hybrid retrieval for better search
from apps.documents.services.semantic_chunker import SemanticChunker

chunker = SemanticChunker()
chunks = chunker.chunk(doc.text)

retriever = HybridRetriever(vector_weight=0.6, bm25_weight=0.4)
results = retriever.hybrid_search(
    query="How are user accounts managed?",
    chunks=[c["content"] for c in chunks],
    top_k=3
)

print(f"\nHybrid Search Results:")
for i, result in enumerate(results, 1):
    print(f"  {i}. Score: {result['hybrid_score']:.2f} - {result['chunk'][:100]}...")

# Calculate multi-factor score
scorer = MultiFactorScorer()
control_score = scorer.calculate_control_score(
    document_text=doc.text,
    control_description="Access controls must be implemented",
    semantic_similarity=0.8,
    llm_score={"score": 85, "explanation": "Document describes access control procedures"}
)

print(f"\nMulti-Factor Score Breakdown:")
for factor, data in control_score["factors"].items():
    print(f"  • {factor}: {data['score']}/100 ({data['weight']:.0%} weight)")
print(f"  Overall: {control_score['overall_score']}/100")
print(f"  Status: {control_score['status']}")


# Example 3: Auditor Verification
# ================================

from apps.agents.auditor_agent import AuditorAgent

auditor = AuditorAgent()

# Run auditor verification on the compliance score
auditor_result = auditor.audit_assessment(
    control_description="Access controls must be implemented",
    evidence=evidence["evidence"],
    llm_reasoning="The document describes how access is controlled",
    initial_score=control_score["overall_score"],
    initial_status=control_score["status"]
)

print(f"\nAuditor Verification:")
print(f"  Verdict: {auditor_result['audit_verdict']}")
if auditor_result["inconsistencies"]:
    print(f"  Issues Found: {len(auditor_result['inconsistencies'])}")
    for issue in auditor_result["inconsistencies"]:
        print(f"    - {issue}")
print(f"  Adjusted Score: {auditor_result['adjusted_score']}/100")
print(f"  Confidence Adjustment: {auditor_result['confidence_adjustment']:+.1f}")


# Example 4: Explainable Result Formatting
# =========================================

from apps.compliance.services.result_formatter import ComplianceResultFormatter

formatter = ComplianceResultFormatter()

# Format a single control assessment
formatted_result = formatter.format_control_assessment(
    control_id="AC-01",
    control_description="Access controls must be implemented",
    score=auditor_result["adjusted_score"],
    status=auditor_result["adjusted_status"],
    confidence=0.85,
    evidence=evidence["evidence"],
    missing_elements=[],
    factor_breakdown={
        "semantic_similarity": 80,
        "evidence_detection": 82,
        "llm_reasoning": 85,
        "document_structure": 78,
        "policy_language": 88
    }
)

print(f"\nFormatted Control Assessment:")
print(f"  Control: {formatted_result['control_id']}")
print(f"  Score: {formatted_result['score_out_of_100']}")
print(f"  Status: {formatted_result['status_label']}")
print(f"  Confidence: {formatted_result['confidence_percentage']}")
print(f"  Evidence Found: {formatted_result['evidence']['count']}")

if formatted_result["recommendations"]:
    print(f"  Recommendations:")
    for rec in formatted_result["recommendations"]:
        print(f"    - {rec}")


# Example 5: Document Structure Analysis
# ======================================

from apps.compliance.services.structure_validator import StructureValidator

validator = StructureValidator()
structure = validator.validate_structure(doc.text)

print(f"\nDocument Structure Analysis:")
print(f"  Score: {structure['structure_score']}/100")
print(f"  Maturity: {structure['maturity']}")
print(f"  Elements Found: {structure['elements_count']}")
print(f"  Missing Elements: {structure['missing_count']}")

if structure["recommendations"]:
    print(f"  Recommendations:")
    for rec in structure["recommendations"][:3]:
        print(f"    - {rec}")


# Example 6: Language Strength Analysis
# =====================================

from apps.compliance.services.language_analyzer import LanguageAnalyzer

analyzer = LanguageAnalyzer()
language = analyzer.analyze_language_strength(doc.text)

print(f"\nLanguage Strength Analysis:")
print(f"  Overall Strength: {language['language_quality_score']}/100")
print(f"  Language Type: {language['language_type']}")
print(f"  Strong Statements: {language['strong_percentage']}%")
print(f"  Weak Statements: {language['weak_percentage']}%")

if language["recommendations"]:
    print(f"  Recommendations:")
    for rec in language["recommendations"][:2]:
        print(f"    - {rec}")


# Example 7: Semantic Document Chunking
# =====================================

chunker = SemanticChunker()
chunks_with_types = chunker.chunk(doc.text)

print(f"\nSemantic Chunking Analysis:")
print(f"  Total Chunks: {len(chunks_with_types)}")

chunk_types = {}
for chunk in chunks_with_types:
    chunk_type = chunk["type"]
    chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1

for chunk_type, count in sorted(chunk_types.items()):
    print(f"  • {chunk_type}: {count} chunks")

# Extract key sections
sections = chunker.extract_sections(doc.text)
print(f"\nKey Sections Found:")
for section_type, content_list in sections.items():
    print(f"  • {section_type}: {len(content_list)} section(s)")


print("\n✅ Integration examples completed successfully!")

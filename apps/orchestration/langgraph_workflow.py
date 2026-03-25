"""Enhanced LangGraph orchestration workflow for reliable compliance processing.

This workflow integrates:
1. Evidence detection layer
2. Hybrid retrieval for better context
3. Semantic document chunking
4. Structural validation
5. Language strength analysis
6. Multi-factor compliance scoring
7. Auditor review for verification
8. Explainable result formatting
"""

from typing import Dict, List, Optional
import logging

from apps.agents.parser_agent import ParserAgent
from apps.agents.compliance_agent import ComplianceAgent
from apps.agents.risk_agent import RiskAgent
from apps.agents.recommendation_agent import RecommendationAgent
from apps.agents.auditor_agent import AuditorAgent

from apps.compliance.services.evidence_detector import EvidenceDetector
from apps.compliance.services.structure_validator import StructureValidator
from apps.compliance.services.language_analyzer import LanguageAnalyzer
from apps.compliance.services.multi_factor_scorer import MultiFactorScorer
from apps.compliance.services.result_formatter import ComplianceResultFormatter

from apps.rag.rag_pipeline import RAGPipeline
from apps.documents.services.semantic_chunker import SemanticChunker

logger = logging.getLogger(__name__)


class EnhancedLangGraphWorkflow:
    """Enhanced LangGraph workflow with multi-layer validation and explainability."""

    def __init__(self):
        # Parsing agents
        self.parser_agent = ParserAgent()
        self.compliance_agent = ComplianceAgent()
        self.risk_agent = RiskAgent()
        self.recommendation_agent = RecommendationAgent()
        
        # Auditor agent for verification
        self.auditor_agent = AuditorAgent()
        
        # Analysis tools
        self.evidence_detector = EvidenceDetector()
        self.structure_validator = StructureValidator()
        self.language_analyzer = LanguageAnalyzer()
        self.scorer = MultiFactorScorer()
        self.result_formatter = ComplianceResultFormatter()
        
        # RAG and chunking
        self.rag_pipeline = RAGPipeline()
        self.semantic_chunker = SemanticChunker()

    def run(self, document: Dict, standard: Dict) -> Dict:
        """Execute the enhanced workflow with document and standard.
        
        Returns:
            Comprehensive compliance assessment with all verification layers
        """
        logger.info("Starting enhanced compliance workflow")
        
        # 1. Document parsing
        logger.info("Step 1: Parsing document")
        parsed = self.parser_agent.parse_document(document)
        document_text = parsed.get("text", "")

        # 2. Structure validation
        logger.info("Step 2: Validating document structure")
        structure_validation = self.structure_validator.validate_structure(document_text)

        # 3. Language analysis
        logger.info("Step 3: Analyzing language strength")
        language_analysis = self.language_analyzer.analyze_language_strength(document_text)

        # 4. Semantic chunking
        logger.info("Step 4: Semantic chunking")
        chunks = self.semantic_chunker.chunk(document_text)

        # 5. Evidence detection and control evaluation
        logger.info("Step 5: Evaluating controls with multi-factor scoring")
        control_scores = []
        
        for control in standard.get("controls", []):
            # 5a. Retrieve enhanced context
            control_context = self.rag_pipeline.retrieve_control_context(
                document,
                control.get("description", ""),
                top_k=5
            )
            
            # 5b. Extract evidence
            evidence = self.evidence_detector.extract_evidence(
                document_text,
                control.get("description", "")
            )
            
            # 5c. Get LLM compliance assessment
            llm_assessment = self.compliance_agent._assess_single_control(
                control.get("description", ""),
                control_context
            )
            
            # 5d. Calculate multi-factor score
            control_score = self.scorer.calculate_control_score(
                document_text,
                control.get("description", ""),
                semantic_similarity=control_context.get("total_context_length", 0) / 100,
                llm_score=llm_assessment
            )
            
            # 5e. Run auditor verification
            auditor_result = self.auditor_agent.audit_assessment(
                control.get("description", ""),
                evidence["evidence"],
                llm_assessment.get("explanation", ""),
                control_score["overall_score"],
                control_score["status"]
            )
            
            # 5f. Apply auditor adjustments if needed
            if auditor_result["audit_verdict"] != "valid":
                control_score["overall_score"] = auditor_result["adjusted_score"]
                control_score["status"] = auditor_result["adjusted_status"]
                control_score["auditor_notes"] = auditor_result["audit_verdict"]
                control_score["confidence"] = max(0, control_score["confidence"] + auditor_result["confidence_adjustment"] / 100)
            
            # 5g. Format control result
            formatted_control = self.result_formatter.format_control_assessment(
                control_id=control.get("id", f"control_{len(control_scores)}"),
                control_description=control.get("description", ""),
                score=control_score["overall_score"],
                status=control_score["status"],
                confidence=control_score["confidence"],
                evidence=evidence["evidence"],
                missing_elements=evidence.get("missing_elements", []),
                factor_breakdown=control_score.get("factor_breakdown", {}),
                auditor_notes=auditor_result.get("audit_verdict", "")
            )
            
            control_scores.append({
                "control": control,
                "assessment": formatted_control,
                "evidence": evidence,
                "auditor_result": auditor_result
            })

        # 6. Calculate overall document score
        logger.info("Step 6: Calculating overall document score")
        document_score = self.scorer.calculate_document_score(
            document_text,
            standard.get("controls", []),
            [cs["assessment"] for cs in control_scores]
        )

        # 7. Risk assessment
        logger.info("Step 7: Detecting risks")
        risks = self.risk_agent.detect(parsed, {
            "score": document_score["overall_score"],
            "violations": [cs["assessment"]["recommendations"] for cs in control_scores]
        })

        # 8. Recommendations
        logger.info("Step 8: Generating recommendations")
        recommendations = self.recommendation_agent.suggest(
            parsed,
            {"score": document_score["overall_score"]},
            risks
        )

        # 9. Format final result
        logger.info("Step 9: Formatting final result")
        final_assessment = self.result_formatter.format_document_assessment(
            document_id=str(parsed.get("id", "unknown")),
            standard_id=str(standard.get("id", "unknown")),
            overall_score=document_score["overall_score"],
            overall_status=document_score["status"],
            confidence=document_score["confidence"],
            controls=[cs["assessment"] for cs in control_scores],
            document_structure_score=structure_validation["structure_score"],
            language_quality_score=language_analysis["language_quality_score"],
            document_language=language_analysis.get("language", "unknown"),
        )

        logger.info(f"Workflow complete. Overall score: {document_score['overall_score']}")

        return {
            "parsed": parsed,
            "structure_validation": structure_validation,
            "language_analysis": language_analysis,
            "compliance": {
                "overall_assessment": final_assessment,
                "control_details": control_scores
            },
            "risks": risks,
            "recommendations": recommendations,
            "metadata": {
                "workflow_version": "2.0_enhanced",
                "components": [
                    "evidence_detection",
                    "hybrid_retrieval",
                    "semantic_chunking",
                    "structure_validation",
                    "language_analysis",
                    "multi_factor_scoring",
                    "auditor_verification"
                ]
            }
        }


# Legacy compatibility class
class LangGraphWorkflow:
    """Legacy LangGraph workflow - wrapper for backward compatibility."""

    def __init__(self):
        self.enhanced_workflow = EnhancedLangGraphWorkflow()
        self.parser_agent = ParserAgent()
        self.compliance_agent = ComplianceAgent()
        self.risk_agent = RiskAgent()
        self.recommendation_agent = RecommendationAgent()

    def run(self, document: Dict, standard: Dict) -> Dict:
        """Execute workflow using enhanced version."""
        result = self.enhanced_workflow.run(document, standard)
        
        # Return legacy format for backward compatibility
        return {
            "parsed": result["parsed"],
            "compliance": result["compliance"]["overall_assessment"],
            "risks": result["risks"],
            "recommendations": result["recommendations"],
        }

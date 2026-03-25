"""Audit pipeline orchestrating compliance analysis steps.

This module implements the end-to-end pipeline from document parsing through
compliance scoring and report generation using a modular, explainable design.
"""

import logging
from typing import Dict, List, Any

from apps.agents.auditor_agent import AuditorAgent
from apps.agents.parser_agent import ParserAgent
from apps.agents.risk_agent import RiskAgent
from apps.agents.recommendation_agent import RecommendationAgent
from apps.compliance.services.report_service import ReportService
from apps.compliance.services.result_formatter import ComplianceResultFormatter
from apps.compliance.services.structure_validator import StructureValidator
from apps.compliance.services.language_analyzer import LanguageAnalyzer
from apps.documents.models import Document
from apps.documents.services.semantic_chunker import SemanticChunker
from apps.standards.models import Standard

from services.audit_reasoning_engine import AuditReasoningEngine
from services.compliance_engine import ComplianceEngine
from services.embedding_service import embed_texts
from services.evidence_detector import EvidenceDetector
from services.hybrid_retriever import HybridRetriever
from services.reranking_service import RerankingService
from services.scoring_engine import calculate_multi_factor_score
from services.vector_store import VectorStore
from services.rule_engine import RuleEngine
from services.neo4j_graph_manager import Neo4jGraphManager

logger = logging.getLogger(__name__)


class AuditPipeline:
    """Orchestrates the audit pipeline stages.

    Workflow:
        1. Document parsing
        2. Structure & language validation
        3. Semantic chunking
        4. Embedding generation & vector indexing
        5. Rule Retrieval
        6. Compliance Rule Evaluation
        7. Multi-factor scoring & risk detection
        8. Audit report generation
    """

    def __init__(self):
        self.parser = ParserAgent()
        self.chunker = SemanticChunker()
        self.vector_store = VectorStore()
        self.hybrid_retriever = HybridRetriever(vector_store=self.vector_store)
        self.reranker = RerankingService()
        self.evidence_detector = EvidenceDetector()
        self.structure_validator = StructureValidator()
        self.language_analyzer = LanguageAnalyzer()
        self.compliance_engine = ComplianceEngine()
        self.rule_engine = RuleEngine()
        self.auditor = AuditorAgent()
        self.reasoning_engine = AuditReasoningEngine()
        self.risk_agent = RiskAgent()
        self.recommendation_agent = RecommendationAgent()
        self.report_service = ReportService()
        self.result_formatter = ComplianceResultFormatter()
        self.neo4j = Neo4jGraphManager()

    def run(
        self,
        document: Document,
        standard: Standard,
        chunk_size: int = 500,
        overlap: int = 100,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        steps: List[Dict[str, Any]] = []

        # 1. Document parsing
        steps.append({"step": "Document Parsing", "status": "processing", "details": {}})
        parsed = self.parser.parse_document(document)
        document_text = parsed.get("text", "")
        steps[-1]["status"] = "completed"
        steps[-1]["details"] = {
            "document_id": parsed.get("document_id"),
            "file_name": parsed.get("file_name"),
            "text_length": len(document_text),
        }
        logger.info("Parsed document %s (length=%d)", parsed.get("file_name"), len(document_text))

        # 2. Structure + language validation
        steps.append({"step": "Document Structure Validation", "status": "processing", "details": {}})
        structure_report = self.structure_validator.validate_structure(document_text)
        language_report = self.language_analyzer.analyze_language_strength(document_text)
        missing_elements = structure_report.get("missing_elements", [])
        structure_score = max(0, 100 - len(missing_elements) * 10)
        language_score = language_report.get("language_quality_score", 0)
        detected_language = language_report.get("language", "unknown")

        steps[-1]["status"] = "completed"
        steps[-1]["details"] = {
            "structure_score": structure_score,
            "language_score": language_score,
            "detected_language": detected_language,
            "missing_elements": missing_elements,
        }

        # 3. Semantic chunking
        steps.append({"step": "Chunking", "status": "processing", "details": {}})
        chunks = self.chunker.chunk_with_overlap(document_text, overlap=overlap, chunk_size=chunk_size)

        normalized_chunks = [
            {
                "chunk_index": idx,
                "section_title": chunk.get("type", ""),
                "section_index": idx,
                "text": chunk.get("content", ""),
            }
            for idx, chunk in enumerate(chunks)
        ]

        steps[-1]["status"] = "completed"
        steps[-1]["details"] = {"chunk_count": len(normalized_chunks)}
        logger.info("Generated %d semantic chunks for document %s", len(normalized_chunks), document.id)

        # 4. Embedding generation & vector indexing
        steps.append({"step": "Embedding Generation", "status": "processing", "details": {}})

        valid_chunks = [c for c in normalized_chunks if (c.get("text") or "").strip()]
        valid_texts = [c.get("text").strip() for c in valid_chunks]
        embeddings = embed_texts(valid_texts)

        indexed_chunks = []
        indexed_embeddings = []
        for c, emb in zip(valid_chunks, embeddings):
            is_valid = False
            if emb is not None:
                if hasattr(emb, '__len__') and len(emb) > 0:
                    is_valid = True
                elif hasattr(emb, 'size') and emb.size > 0:
                    is_valid = True
                elif not hasattr(emb, '__len__') and not hasattr(emb, 'size'):
                    is_valid = True
            
            if is_valid:
                indexed_chunks.append(c)
                indexed_embeddings.append(emb)
            else:
                logger.warning("Skipping chunk %s due to empty/invalid embedding", c.get("chunk_index"))

        steps[-1]["status"] = "completed"
        steps[-1]["details"] = {"chunks_embedded": len(indexed_embeddings)}

        steps.append({"step": "Vector Indexing", "status": "processing", "details": {}})
        self.vector_store.add_chunks(
            document_id=str(document.id),
            standard_id=str(getattr(standard, "id", "")),
            chunks=indexed_chunks,
            embeddings=indexed_embeddings,
        )
        steps[-1]["status"] = "completed"
        steps[-1]["details"] = {"indexed_chunks": len(indexed_chunks)}

        try:
            self.neo4j.create_document_node(str(document.id), parsed.get("file_name", ""), document_text)
            for c in normalized_chunks:
                self.neo4j.create_chunk_node(str(document.id), c.get("chunk_index"), c.get("section_title", ""), c.get("text", ""))
        except Exception as ex:  # pragma: no cover
            logger.error("Neo4j document graph update failed: %s", ex)

        # 5. Rule retrieval
        steps.append({"step": "Rule Retrieval", "status": "processing", "details": {}})
        rules = self.rule_engine.rules_from_standard(standard)
        steps[-1]["status"] = "completed"
        steps[-1]["details"] = {"rules_retrieved": len(rules)}
        logger.info("Loaded %d rules for standard %s", len(rules), standard)

        # 6. Compliance Rule Evaluation
        steps.append({"step": "Compliance Rule Evaluation", "status": "processing", "details": {}})
        rule_evaluations: List[Dict[str, Any]] = []

        for rule in rules:
            try:
                eval_dict = self._evaluate_single_rule(rule, document, detected_language, top_k)
                rule_evaluations.append(eval_dict)
            except Exception as e:
                logger.error("Error evaluating rule %s: %s", getattr(rule, "id", "unknown"), e)
                # Avoid complete pipeline failure by appending a failed state
                rule_evaluations.append({
                    "rule": rule,
                    "rule_id": getattr(rule, "id", "unknown"),
                    "status": "NON_COMPLIANT",
                    "severity": getattr(rule, "severity", "medium"),
                    "score": 0,
                    "explanation": f"Evaluation pipeline failed internally: {str(e)}",
                    "missing": [],
                    "error": True
                })

        steps[-1]["status"] = "completed"
        steps[-1]["details"] = {"rules_evaluated": len(rules)}
        logger.info("Successfully evaluated %d rules.", len(rule_evaluations))

        # 7. Scoring and Risks
        steps.append({"step": "Compliance Scoring", "status": "processing", "details": {}})
        score_data = calculate_multi_factor_score(
            rule_evaluations, 
            structure_score=structure_score,
            missing_elements=missing_elements
        )

        violations = []
        for r in rule_evaluations:
            r_score = r.get("final_score", 0)
            if r_score < 80:
                r["severity"] = "HIGH" if r_score < 50 else "MEDIUM"
                rule_obj = r.get("rule", None)
                r["description"] = getattr(rule_obj, "description", r.get("rule_id", "Unknown description"))
                r["status"] = r.get("final_status", r.get("status", "NON_COMPLIANT"))
                violations.append(r)
                
        risks = self.risk_agent.detect(parsed, {"violations": violations})
        
        CRITICAL_FIELDS = ["effective_date", "scope", "responsibilities"]
        missing_critical = any(field in missing_elements for field in CRITICAL_FIELDS)
        doc_score = score_data.get("score", 0)
        
        if missing_critical:
            score_data["status"] = "non_compliant"
            doc_recommendation = "Non-compliant. Major issues detected (Missing critical sections)."
        elif doc_score >= 80:
            score_data["status"] = "compliant"
            doc_recommendation = "Document compliant"
        elif doc_score >= 50:
            score_data["status"] = "partially_compliant"
            doc_recommendation = "Partially compliant. Improvements needed"
        else:
            score_data["status"] = "non_compliant"
            doc_recommendation = "Non-compliant. Major issues detected"

        recommendations = [doc_recommendation]
        steps[-1]["status"] = "completed"
        steps[-1]["details"] = {**score_data, "risks": risks, "recommendations": recommendations}

        # 8. Audit report generation
        steps.append({"step": "Audit Report Generation", "status": "processing", "details": {}})
        report, report_path = self._compile_report(
            document, standard, rule_evaluations, structure_score, language_score, detected_language, score_data, violations
        )
        
        if report_path:
            steps[-1]["status"] = "completed"
            steps[-1]["details"] = {"report_path": report_path}
        else:
            steps[-1]["status"] = "failed"
            steps[-1]["details"] = {"error": "Failed to compile PDF report"}

        detected_keywords = sorted({kw for ev in rule_evaluations for kw in ev.get("detected_keywords", [])})

        logger.info(
            "Audit pipeline complete. Score: %s, Status: %s, Violations: %d", 
            score_data.get("score"), score_data.get("status"), len(violations)
        )

        return {
            "score": score_data.get("score", 0),
            "status": score_data.get("status", "non_compliant"),
            "risk_level": score_data.get("risk_level", "Unknown"),
            "violations": violations,
            "recommendations": recommendations,
            "risks": risks,
            "steps": steps,
            "rule_evaluations": rule_evaluations,
            "rules_evaluated": len(rules),
            "detected_keywords": detected_keywords,
            "report": report,
        }

    def _evaluate_single_rule(self, rule: Any, document: Document, detected_language: str, top_k: int) -> Dict[str, Any]:
        """Separated logic for retrieving evidence and evaluating a single compliance rule."""
        logger.debug("Evaluating rule %s (%s)", getattr(rule, "id", "unknown"), getattr(rule, "description", "")[:80])

        candidates = self.hybrid_retriever.retrieve(
            query=rule.description,
            document_id=str(document.id),
            top_k=top_k,
            document_language=detected_language,
        )

        reranked = self.reranker.rerank(rule.description, candidates, top_k=top_k)

        evidence_contexts = [c.get("text", "") for c in reranked]
        evidence_info = self.evidence_detector.extract_evidence(
            requirement=rule.description,
            candidate_texts=evidence_contexts,
            keywords=rule.keywords,
            top_n=3,
        )

        evaluation = self.compliance_engine.evaluate_rule(
            rule,
            reranked,
            evidence_items=evidence_info.get("evidence_sentences", []),
        )

        evaluation.evidence_score = evidence_info.get("evidence_score", 0.0)
        evaluation.evidence_sentences = evidence_info.get("evidence_sentences", [])
        evaluation.evidence_types = evidence_info.get("evidence_types", [])
        evaluation.evidence = evidence_info.get("evidence_sentences", [])

        audit = self.auditor.audit_assessment(
            control_description=rule.description,
            evidence=evaluation.evidence_sentences,
            llm_reasoning=evaluation.reason,
            initial_score=int(evaluation.confidence * 100),
            initial_status=evaluation.status,
        )

        evaluation.auditor = audit
        missing_elements = audit.get("missing_elements", []) if isinstance(audit, dict) else []

        try:
            self.neo4j.link_chunk_to_requirement(
                document_id=str(document.id),
                requirement_id=str(getattr(rule, "id", "")),
                chunk_ids=[c.get("chunk_id") for c in reranked if c.get("chunk_id")],
            )
        except Exception as ex:  # pragma: no cover
            logger.error("Neo4j relationship update failed: %s", ex)

        return {
            "rule": evaluation.rule,
            "rule_id": evaluation.rule_id,
            "status": evaluation.status or "unknown",
            "severity": evaluation.severity,
            "score": evaluation.score,
            "explanation": evaluation.reason,
            "missing": missing_elements,
            "semantic_similarity": evaluation.score,
            "confidence": evaluation.confidence,
            "llm_confidence": evaluation.llm_confidence,
            "reason": evaluation.reason,
            "recommendation": getattr(evaluation, "recommendation", None),
            "evidence": evaluation.evidence,
            "evidence_used": getattr(evaluation, "evidence_used", False),
            "evidence_strength": getattr(evaluation, "evidence_strength", 0.0),
            "evidence_score": evaluation.evidence_score,
            "evidence_sentences": evaluation.evidence_sentences,
            "evidence_types": evaluation.evidence_types,
            "auditor": evaluation.auditor,
            "detected_keywords": evidence_info.get("detected_keywords", []),
            "keyword_counts": evidence_info.get("keyword_counts", {}),
            "evidence_snippet": getattr(rule, "expected_evidence", None),
            "source_chunk": getattr(rule, "source_chunk", None),
            "keyword_score": evidence_info.get("keyword_match_score", 0.0),
        }

    def _compile_report(self, document: Document, standard: Standard, rule_evaluations: List[Dict[str, Any]], structure_score: int, language_score: int, detected_language: str, score_data: Dict[str, Any], violations: List[Dict[str, Any]]):
        """Constructs formatted controls and generates the PDF audit report."""
        formatted_controls = []
        for eval_item in rule_evaluations:
            evidence_sentences = eval_item.get("evidence_sentences") or [c.get("text", "") for c in eval_item.get("evidence", [])]
            auditor_info = eval_item.get("auditor", {})
            eval_missing_elements = auditor_info.get("missing_elements", []) if isinstance(auditor_info, dict) else []

            factor_breakdown = {
                "semantic_similarity": float(eval_item.get("score", 0.0)),
                "evidence_score": float(eval_item.get("evidence_score", 0.0)),
                "llm_confidence": float(eval_item.get("confidence", 0.0)),
                "keyword_score": float(eval_item.get("keyword_score", 0.0)),
                "structure_score": float(structure_score) / 100.0,
            }

            rule_obj = eval_item.get("rule")
            formatted_controls.append(
                self.result_formatter.format_control_assessment(
                    control_id=eval_item.get("rule_id"),
                    control_description=getattr(rule_obj, "description", ""),
                    score=eval_item.get("final_score", int(eval_item.get("confidence", 0.0) * 100)),
                    status=eval_item.get("final_status", eval_item.get("status", "non_compliant")),
                    confidence=eval_item.get("confidence", 0.0),
                    evidence=evidence_sentences,
                    missing_elements=eval_missing_elements,
                    factor_breakdown=factor_breakdown,
                    violations={
                        "has_violations": bool(auditor_info.get("inconsistencies")),
                        "violation_count": len(auditor_info.get("inconsistencies", []) if isinstance(auditor_info, dict) else []),
                        "critical_violation_count": 0,
                        "violation_status": eval_item.get("final_status", "non_compliant"),
                        "violation_patterns": auditor_info.get("inconsistencies", []) if isinstance(auditor_info, dict) else [],
                        "evidence_gaps": eval_missing_elements,
                        "recommendations": [eval_item.get("recommendation")] if eval_item.get("recommendation") else [],
                    },
                    reasoning=eval_item.get("reason", ""),
                    auditor_notes=str(auditor_info),
                )
            )

        try:
            missing_controls_list = [
                ev.get("rule_id") for ev in rule_evaluations 
                if ev.get("final_score", int(ev.get("confidence", 0.0) * 100)) < 50
            ]

            report = self.result_formatter.format_document_assessment(
                document_id=str(document.id),
                standard_id=str(getattr(standard, "id", "")),
                overall_score=score_data.get("score", 0),
                overall_status=score_data.get("status", "non_compliant"),
                confidence=score_data.get("score", 0) / 100.0,
                controls=formatted_controls,
                document_structure_score=structure_score,
                language_quality_score=language_score,
                document_language=detected_language,
                violations_summary={},
                missing_controls=missing_controls_list,
            )

            pdf_path = self.report_service.generate_pdf(report)
            return report, pdf_path
        except Exception as ex:
            logger.exception("Failed to generate audit report: %s", ex)
            return None, None

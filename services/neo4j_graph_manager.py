"""Graph persistence layer for compliance audit knowledge graph.

This module manages a Neo4j knowledge graph that captures relationships between
standards, requirements, documents, chunks, and evidence.

Graph schema:
    (Standard)-[:HAS_CLAUSE]->(Clause)
    (Clause)-[:HAS_REQUIREMENT]->(Requirement)
    (Requirement)-[:HAS_CONTROL]->(Control)

    (Document)-[:CONTAINS]->(Chunk)
    (Chunk)-[:PROVIDES_EVIDENCE_FOR]->(Requirement)
"""

import logging
from typing import List, Optional

from django.conf import settings
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class Neo4jGraphManager:
    """Manage the Neo4j knowledge graph for compliance audits."""

    def __init__(self):
        uri = getattr(settings, "NEO4J_URI", None)
        user = getattr(settings, "NEO4J_USER", None)
        password = getattr(settings, "NEO4J_PASSWORD", None)

        if not uri or not user or not password:
            logger.debug("Neo4j configuration missing; graph persistence will be disabled.")
            self._driver = None
            return

        try:
            self._driver = GraphDatabase.driver(uri, auth=(user, password))
            logger.debug("Neo4j driver initialized (uri=%s)", uri)
        except Exception as ex:  # pragma: no cover
            logger.exception("Failed to initialize Neo4j driver: %s", ex)
            self._driver = None

    def _execute(self, cypher: str, parameters: Optional[dict] = None) -> None:
        if self._driver is None:
            return

        try:
            with self._driver.session() as session:
                session.write_transaction(lambda tx: tx.run(cypher, parameters or {}))
        except Exception as ex:  # pragma: no cover
            logger.debug("Neo4j query failed: %s", ex)

    def create_document_node(self, document_id: str, name: str, text: str) -> None:
        """Register a document node in the graph."""
        cypher = (
            "MERGE (d:Document {id: $document_id}) "
            "SET d.name = $name, d.text = $text"
        )
        self._execute(cypher, {"document_id": document_id, "name": name, "text": text})

    def create_chunk_node(
        self,
        document_id: str,
        chunk_index: int,
        section_title: str,
        text: str,
    ) -> None:
        """Create a chunk node and link it to the containing document."""
        cypher = (
            "MERGE (d:Document {id: $document_id}) "
            "MERGE (c:Chunk {document_id: $document_id, chunk_index: $chunk_index}) "
            "SET c.section_title = $section_title, c.text = $text "
            "MERGE (d)-[:CONTAINS]->(c)"
        )
        self._execute(
            cypher,
            {
                "document_id": document_id,
                "chunk_index": chunk_index,
                "section_title": section_title,
                "text": text,
            },
        )

    def link_chunk_to_requirement(
        self,
        document_id: str,
        requirement_id: str,
        chunk_ids: Optional[List[str]] = None,
    ) -> None:
        """Link one or more chunks to a requirement node."""
        if not chunk_ids:
            return

        for chunk_id in chunk_ids:
            cypher = (
                "MERGE (r:Requirement {id: $requirement_id}) "
                "MERGE (c:Chunk {document_id: $document_id, chunk_id: $chunk_id}) "
                "MERGE (c)-[:PROVIDES_EVIDENCE_FOR]->(r)"
            )
            self._execute(
                cypher,
                {
                    "requirement_id": requirement_id,
                    "document_id": document_id,
                    "chunk_id": chunk_id,
                },
            )

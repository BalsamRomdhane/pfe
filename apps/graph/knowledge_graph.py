"""Knowledge Graph implementation using Neo4j for compliance knowledge."""

from typing import Dict, Optional

from .neo4j_connector import get_neo4j_session


class KnowledgeGraph:
    """High-level interface to the Neo4j knowledge graph."""

    def __init__(self):
        self.session = get_neo4j_session()

    def close(self):
        self.session.close()

    def sync_standard(self, standard: Dict) -> None:
        """Synchronize a standard and its controls into the knowledge graph."""
        # standard should include name and optional clauses/requirements
        name = standard.get("name")
        controls = standard.get("controls", [])

        query = (
            "MERGE (s:Standard {name: $name}) "
            "RETURN id(s) as id"
        )
        self.session.run(query, name=name)

        for control in controls:
            control_id = control.get("identifier") or control.get("title") or "unnamed"
            control_desc = control.get("description")
            self.session.run(
                ""
                "MATCH (s:Standard {name: $standard_name}) "
                "MERGE (c:Control {identifier: $control_id}) "
                "ON CREATE SET c.description = $description "
                "MERGE (s)-[:HAS_CONTROL]->(c)"
                "",
                standard_name=name,
                control_id=control_id,
                description=control_desc,
            )

    def query_controls(self, standard_name: str) -> Optional[list]:
        """Query the knowledge graph for controls under a standard."""
        result = self.session.run(
            "MATCH (s:Standard {name: $name})-[:HAS_CONTROL]->(c:Control) "
            "RETURN c.identifier AS identifier, c.description AS description",
            name=standard_name,
        )
        return [dict(record) for record in result]

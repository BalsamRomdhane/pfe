"""Neo4j connector and helper utilities."""

import os
from typing import Optional

from neo4j import GraphDatabase


class Neo4jConnector:
    """Simple Neo4j connection manager."""

    def __init__(self):
        self.uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.environ.get("NEO4J_USER", "neo4j")
        self.password = os.environ.get("NEO4J_PASSWORD", "password")
        self._driver: Optional[GraphDatabase.driver] = None

    @property
    def driver(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        return self._driver

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None


def get_neo4j_session():
    connector = Neo4jConnector()
    return connector.driver.session()

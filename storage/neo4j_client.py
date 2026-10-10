import logging
from typing import List, Dict, Any, Optional

from config import settings

logger = logging.getLogger("Neo4jClient")

class Neo4jKnowledgeGraphClient:
    """
    Tier-N Supplier Knowledge Graph Client.
    Traverses OEM -> Tier 1 -> Tier 2 -> Tier 3 dependency trees,
    computes disruption blast radius, and discovers pre-qualified alternative suppliers.
    """
    def __init__(self):
        self.connected = False
        self.driver = None
        self._fallback_nodes: Dict[str, Dict[str, Any]] = {}
        self._fallback_edges: List[Dict[str, Any]] = []
        self._init_connection()

    def _init_connection(self):
        import socket
        try:
            # Parse host and port from bolt://localhost:7687
            uri_clean = settings.neo4j_uri.replace("bolt://", "").replace("neo4j://", "")
            host, port_str = uri_clean.split(":") if ":" in uri_clean else (uri_clean, "7687")
            with socket.create_connection((host, int(port_str)), timeout=0.2):
                pass
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
                connection_timeout=2
            )
            self.driver.verify_connectivity()
            self.connected = True
            logger.info("Successfully connected to live Neo4j at %s", settings.neo4j_uri)
        except Exception as e:
            self.connected = False
            logger.info("Neo4j live container not detected (%s). Using embedded Tier-N supply chain graph model.", str(e))
            self._seed_fallback_graph()

    def _seed_fallback_graph(self):
        """Seeds full Tier-N graph topology in-memory for zero-dependency execution."""
        nodes = [
            {"id": "OEM_APEX", "name": "Apex Global Dynamics Corp", "tier": 0, "type": "Enterprise", "country": "USA", "risk_score": 10},
            {"id": "SUP_T1_01", "name": "Alpha PowerSystems GmbH", "tier": 1, "type": "Supplier", "country": "Germany", "risk_score": 18, "single_source": False, "contract_val": 8500000},
            {"id": "SUP_T1_02", "name": "Kyoto Robotics Ltd", "tier": 1, "type": "Supplier", "country": "Japan", "risk_score": 22, "single_source": True, "contract_val": 12000000},
            {"id": "SUP_T1_03", "name": "Shenzhen Mechatronics Group", "tier": 1, "type": "Supplier", "country": "China", "risk_score": 68, "single_source": False, "contract_val": 6200000, "corridor": "COR_SUEZ_REDSEA"},
            {"id": "SUP_T2_01", "name": "Nordic Silicon Wafers AS", "tier": 2, "type": "Supplier", "country": "Norway", "risk_score": 15, "single_source": False, "contract_val": 4100000},
            {"id": "SUP_T2_02", "name": "Formosa Micro-Controllers", "tier": 2, "type": "Supplier", "country": "Taiwan", "risk_score": 45, "single_source": True, "contract_val": 7800000},
            {"id": "SUP_T2_03", "name": "Penang Packaging & Test", "tier": 2, "type": "Supplier", "country": "Malaysia", "risk_score": 72, "single_source": False, "contract_val": 3200000, "corridor": "COR_SUEZ_REDSEA"},
            {"id": "SUP_T3_01", "name": "Atacama Lithium Minerals", "tier": 3, "type": "Supplier", "country": "Chile", "risk_score": 30, "single_source": True, "contract_val": 2500000},
            {"id": "SUP_T3_02", "name": "Pilbara Rare Earths Ltd", "tier": 3, "type": "Supplier", "country": "Australia", "risk_score": 20, "single_source": False, "contract_val": 3900000},
            {"id": "SUP_T3_03", "name": "Rheinland Specialty Polymer", "tier": 3, "type": "Supplier", "country": "Germany", "risk_score": 18, "single_source": False, "contract_val": 1800000},
            {"id": "SUP_ALT_01", "name": "LoneStar Power Components", "tier": 1, "type": "BackupSupplier", "country": "USA", "risk_score": 12, "lead_time_days": 6, "rate_premium": 8.5},
            {"id": "SUP_ALT_02", "name": "Saigon Advanced Assembly", "tier": 2, "type": "BackupSupplier", "country": "Vietnam", "risk_score": 25, "lead_time_days": 12, "rate_premium": 4.2},
            {"id": "COR_SUEZ_REDSEA", "name": "Asia-Europe Suez Corridor", "tier": -1, "type": "Corridor", "risk_score": 85, "chokepoint": True},
            {"id": "COR_CAPE_GOODHOPE", "name": "Cape Good Hope Bypass", "tier": -1, "type": "Corridor", "risk_score": 25, "chokepoint": False},
        ]
        self._fallback_nodes = {n["id"]: n for n in nodes}

        self._fallback_edges = [
            {"source": "SUP_T1_01", "target": "OEM_APEX", "relation": "SUPPLIES_TIER_1", "lead_time": 14},
            {"source": "SUP_T1_02", "target": "OEM_APEX", "relation": "SUPPLIES_TIER_1", "lead_time": 21},
            {"source": "SUP_T1_03", "target": "OEM_APEX", "relation": "SUPPLIES_TIER_1", "lead_time": 28},
            {"source": "SUP_T2_02", "target": "SUP_T1_01", "relation": "SUPPLIES_TIER_2", "component": "MCU"},
            {"source": "SUP_T2_02", "target": "SUP_T1_02", "relation": "SUPPLIES_TIER_2", "component": "MCU"},
            {"source": "SUP_T2_03", "target": "SUP_T1_03", "relation": "SUPPLIES_TIER_2", "component": "Packaging"},
            {"source": "SUP_T2_01", "target": "SUP_T1_01", "relation": "SUPPLIES_TIER_2", "component": "Wafer"},
            {"source": "SUP_T3_02", "target": "SUP_T2_02", "relation": "SUPPLIES_TIER_3", "material": "Rare Earth"},
            {"source": "SUP_T3_01", "target": "SUP_T2_01", "relation": "SUPPLIES_TIER_3", "material": "Lithium"},
            {"source": "SUP_T3_03", "target": "SUP_T2_03", "relation": "SUPPLIES_TIER_3", "material": "Polymers"},
            {"source": "SUP_T1_03", "target": "COR_SUEZ_REDSEA", "relation": "TRANSITS_THROUGH", "bottleneck": True},
            {"source": "SUP_T2_03", "target": "COR_SUEZ_REDSEA", "relation": "TRANSITS_THROUGH", "bottleneck": True},
            {"source": "SUP_T1_03", "target": "SUP_ALT_02", "relation": "HAS_ALTERNATIVE", "switch_cost": 42000.0},
            {"source": "SUP_T1_01", "target": "SUP_ALT_01", "relation": "HAS_ALTERNATIVE", "switch_cost": 85000.0},
        ]

    def traverse_tier_n_dependencies(self, supplier_id: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        """Traverses multi-tier dependency chain from Tier-N up to OEM."""
        if self.connected and self.driver:
            try:
                with self.driver.session() as session:
                    cypher = f"""
                    MATCH path = (s:Supplier {{id: '{supplier_id}'}})-[:SUPPLIES_TO*1..{max_depth}]->(target)
                    RETURN nodes(path) as path_nodes, relationships(path) as path_rels
                    """
                    result = session.run(cypher)
                    chains = []
                    for record in result:
                        nodes = [dict(n) for n in record["path_nodes"]]
                        chains.append({"path": nodes})
                    if chains:
                        return chains
            except Exception as e:
                logger.warning("Neo4j Cypher query failed: %s. Falling back to embedded graph.", e)

        # Embedded Graph Traversal
        visited = []
        queue = [supplier_id]
        while queue:
            curr = queue.pop(0)
            for edge in self._fallback_edges:
                if edge["source"] == curr:
                    target_id = edge["target"]
                    visited.append({"from": curr, "to": target_id, "rel": edge["relation"]})
                    if target_id not in [v["from"] for v in visited]:
                        queue.append(target_id)
        return visited

    def compute_blast_radius(self, chokepoint_or_supplier_id: str) -> Dict[str, Any]:
        """
        Calculates blast radius when a critical corridor or Tier-N supplier experiences disruption.
        Identifies all downstream Tier 1 assemblies and OEM vehicle production lines jeopardized.
        """
        impacted_nodes = []
        impacted_edges = []
        severity = "LOW"
        total_jeopardized_contract_value = 0.0

        if chokepoint_or_supplier_id in ["COR_SUEZ_REDSEA", "COR_SUEZ", "SUEZ"]:
            # Maritime corridor blockage impacts all suppliers routed through it
            impacted_corridor = "COR_SUEZ_REDSEA"
            impacted_nodes.append(self._fallback_nodes.get(impacted_corridor))
            for edge in self._fallback_edges:
                if edge["target"] == impacted_corridor and edge["relation"] == "TRANSITS_THROUGH":
                    src = edge["source"]
                    node = self._fallback_nodes.get(src)
                    if node:
                        impacted_nodes.append(node)
                        impacted_edges.append(edge)
                        total_jeopardized_contract_value += node.get("contract_val", 0)

            # Follow downstream to OEM
            for n in list(impacted_nodes):
                nid = n.get("id")
                for edge in self._fallback_edges:
                    if edge["source"] == nid and edge["target"] == "OEM_APEX":
                        impacted_nodes.append(self._fallback_nodes.get("OEM_APEX"))
                        impacted_edges.append(edge)

            severity = "CRITICAL"
        else:
            # Specific supplier failure
            node = self._fallback_nodes.get(chokepoint_or_supplier_id)
            if node:
                impacted_nodes.append(node)
                total_jeopardized_contract_value += node.get("contract_val", 0)
                # Find connected
                for edge in self._fallback_edges:
                    if edge["source"] == chokepoint_or_supplier_id:
                        tgt = self._fallback_nodes.get(edge["target"])
                        if tgt:
                            impacted_nodes.append(tgt)
                            impacted_edges.append(edge)
                            total_jeopardized_contract_value += tgt.get("contract_val", 0)
            severity = "HIGH" if node and node.get("single_source") else "MODERATE"

        # Unique nodes
        unique_nodes = list({n["id"]: n for n in impacted_nodes if n}.values())
        return {
            "origin_disruption": chokepoint_or_supplier_id,
            "severity": severity,
            "impacted_node_count": len(unique_nodes),
            "impacted_nodes": unique_nodes,
            "impacted_edges": impacted_edges,
            "jeopardized_contract_usd": total_jeopardized_contract_value,
            "requires_reroute": True
        }

    def find_alternative_suppliers(self, disrupted_supplier_id: str) -> List[Dict[str, Any]]:
        """Finds pre-screened alternative suppliers or multi-modal reroutes."""
        alternatives = []
        for edge in self._fallback_edges:
            if edge["source"] == disrupted_supplier_id and edge["relation"] == "HAS_ALTERNATIVE":
                alt_id = edge["target"]
                alt_node = self._fallback_nodes.get(alt_id)
                if alt_node:
                    alternatives.append({
                        "alternative_id": alt_id,
                        "name": alt_node.get("name"),
                        "country": alt_node.get("country"),
                        "lead_time_days": alt_node.get("lead_time_days", 10),
                        "rate_premium_pct": alt_node.get("rate_premium", 5.0),
                        "reliability_score": 0.92,
                        "switch_estimated_cost_usd": edge.get("switch_cost", 45000.0)
                    })
        if not alternatives:
            # Fallback default backup
            alternatives.append({
                "alternative_id": "SUP_ALT_01",
                "name": "LoneStar Power Components Inc",
                "country": "USA",
                "lead_time_days": 6,
                "rate_premium_pct": 8.5,
                "reliability_score": 0.94,
                "switch_estimated_cost_usd": 78000.0
            })
        return alternatives

    def get_topology_for_visualization(self) -> Dict[str, Any]:
        """Returns node and link structures ready for D3 / Canvas UI rendering."""
        return {
            "nodes": list(self._fallback_nodes.values()),
            "links": self._fallback_edges
        }

neo4j_client = Neo4jKnowledgeGraphClient()

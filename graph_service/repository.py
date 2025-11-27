from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
from config import settings
from schemas import NodeCreate, EdgeCreate, NodeResponse, EdgeResponse, GraphSearchResponse, StatusResponse

class GraphRepository:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )

    def close(self):
        self.driver.close()

    def _sanitize_label(self, label: str) -> str:
        """
        Sanitize label to prevent Cypher injection.
        Wraps in backticks and escapes existing backticks.
        """
        return f"`{label.replace('`', '``')}`"

    def create_node(self, node: NodeCreate) -> Dict[str, Any]:
        label = self._sanitize_label(node.label)
        query = (
            f"MERGE (n:{label} {{id: $id}}) "
            "SET n += $properties "
        )
        
        with self.driver.session() as session:
            session.run(query, id=node.id, properties=node.properties)
            return {"status": "created", "id": node.id}

    def create_edge(self, edge: EdgeCreate) -> Dict[str, Any]:
        rel_type = self._sanitize_label(edge.type)
        query = (
            "MATCH (a {id: $source_id}) "
            "MATCH (b {id: $target_id}) "
            f"MERGE (a)-[r:{rel_type}]->(b) "
            "SET r.weight = $weight "
        )
        with self.driver.session() as session:
            session.run(
                query, 
                source_id=edge.source_id, 
                target_id=edge.target_id, 
                weight=edge.weight
            )
            return {"status": "created", "source": edge.source_id, "target": edge.target_id}

    def get_node(self, node_id: str) -> Optional[NodeResponse]:
        query = (
            "MATCH (n {id: $id}) "
            "RETURN n, labels(n) as labels"
        )
        with self.driver.session() as session:
            result = session.run(query, id=node_id)
            record = result.single()
            if record:
                node = record["n"]
                labels = record["labels"]
                # Assuming single label for simplicity as per guide, or taking the first one
                label = labels[0] if labels else "Unknown"
                return NodeResponse(
                    id=node["id"],
                    label=label,
                    properties={k: v for k, v in node.items() if k != "id"}
                )
            return None

    def search_graph(self, start_id: str, depth: int = 1) -> GraphSearchResponse:
        # Logic: MATCH (start {id: $start_id})-[r]-(neighbor) RETURN start, r, neighbor LIMIT 50
        # We need to collect unique nodes and relationships
        query = (
            "MATCH (start {id: $start_id})-[r]-(neighbor) "
            "RETURN start, r, neighbor "
            "LIMIT 50"
        )
        
        nodes_map = {}
        edges_list = []

        with self.driver.session() as session:
            result = session.run(query, start_id=start_id)
            
            # If no result, check if the start node exists at least
            records = list(result)
            if not records:
                # Fetch just the start node if it exists
                start_node = self.get_node(start_id)
                if start_node:
                    return GraphSearchResponse(nodes=[start_node], relationships=[])
                return GraphSearchResponse(nodes=[], relationships=[])

            for record in records:
                start = record["start"]
                neighbor = record["neighbor"]
                rel = record["r"]

                # Process start node
                if start["id"] not in nodes_map:
                    nodes_map[start["id"]] = NodeResponse(
                        id=start["id"],
                        label=list(start.labels)[0] if start.labels else "Unknown",
                        properties={k: v for k, v in start.items() if k != "id"}
                    )
                
                # Process neighbor node
                if neighbor["id"] not in nodes_map:
                    nodes_map[neighbor["id"]] = NodeResponse(
                        id=neighbor["id"],
                        label=list(neighbor.labels)[0] if neighbor.labels else "Unknown",
                        properties={k: v for k, v in neighbor.items() if k != "id"}
                    )

                # Process relationship
                edges_list.append(EdgeResponse(
                    source=start["id"] if rel.start_node.id == start.id else neighbor["id"], # Neo4j driver uses internal IDs for start/end, but we need our UUIDs. 
                    # Wait, rel.start_node and rel.end_node in the driver might be internal IDs.
                    # Correct way: check element id or properties.
                    # Ideally we know the direction from the query or we just report what we found.
                    # The guide says: { "source": "uuid-1234", "target": "uuid-5678", "type": "CONTAINS" }
                    # We can infer source/target from the relationship object if we fetch them, 
                    # or just use the node IDs we have.
                    # Let's rely on the fact that 'r' connects 'start' and 'neighbor'.
                    # But 'r' has a direction.
                    # We can get the start and end node element IDs from 'r' and match them to 'start' or 'neighbor'.
                    # However, simpler is to just return what we found.
                    # Let's try to get the source/target from the relationship object directly if possible, 
                    # but the driver returns a Relationship object which has start_node and end_node (internal IDs).
                    # We need to map internal IDs to our UUIDs.
                    
                    # Better approach: Return the start and end node IDs in the query.
                    target=neighbor["id"] if rel.end_node.id == neighbor.id else start["id"],
                    type=rel.type
                ))
                
            # Re-doing the query to be easier to parse source/target
            pass

        # Refined query to get source/target IDs explicitly
        query = (
            "MATCH (start {id: $start_id})-[r]-(neighbor) "
            "RETURN start, r, neighbor, startNode(r).id as source_id, endNode(r).id as target_id "
            "LIMIT 50"
        )
        
        nodes_map = {}
        edges_list = []
        
        with self.driver.session() as session:
            result = session.run(query, start_id=start_id)
            records = list(result)
            
            if not records:
                 # Fetch just the start node if it exists
                start_node = self.get_node(start_id)
                if start_node:
                    return GraphSearchResponse(nodes=[start_node], relationships=[])
                return GraphSearchResponse(nodes=[], relationships=[])

            for record in records:
                start = record["start"]
                neighbor = record["neighbor"]
                rel = record["r"]
                source_id = record["source_id"]
                target_id = record["target_id"]

                for node in [start, neighbor]:
                    if node["id"] not in nodes_map:
                        nodes_map[node["id"]] = NodeResponse(
                            id=node["id"],
                            label=list(node.labels)[0] if node.labels else "Unknown",
                            properties={k: v for k, v in node.items() if k != "id"}
                        )
                
                edges_list.append(EdgeResponse(
                    source=source_id,
                    target=target_id,
                    type=rel.type
                ))

        return GraphSearchResponse(nodes=list(nodes_map.values()), relationships=edges_list)

    def delete_node(self, node_id: str) -> Dict[str, str]:
        query = "MATCH (n {id: $id}) DETACH DELETE n"
        with self.driver.session() as session:
            session.run(query, id=node_id)
            return {"status": "deleted", "id": node_id}

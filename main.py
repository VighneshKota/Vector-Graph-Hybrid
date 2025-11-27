from fastapi import FastAPI, HTTPException, Depends, Query
from typing import List, Dict, Any
from contextlib import asynccontextmanager
from repository import GraphRepository
from schemas import NodeCreate, EdgeCreate, NodeResponse, EdgeResponse, GraphSearchResponse

# Global repository instance
repo = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global repo
    repo = GraphRepository()
    yield
    repo.close()

app = FastAPI(title="Person D - Graph Service", lifespan=lifespan)

def get_repo():
    if not repo:
        raise HTTPException(status_code=503, detail="Database not initialized")
    return repo

@app.post("/nodes", response_model=Dict[str, str])
def create_node(node: NodeCreate, repository: GraphRepository = Depends(get_repo)):
    try:
        return repository.create_node(node)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/nodes/{node_id}", response_model=NodeResponse)
def get_node(node_id: str, repository: GraphRepository = Depends(get_repo)):
    node = repository.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node

@app.delete("/nodes/{node_id}", response_model=Dict[str, str])
def delete_node(node_id: str, repository: GraphRepository = Depends(get_repo)):
    try:
        return repository.delete_node(node_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/edges", response_model=Dict[str, str])
def create_edge(edge: EdgeCreate, repository: GraphRepository = Depends(get_repo)):
    try:
        return repository.create_edge(edge)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/graph", response_model=GraphSearchResponse)
def search_graph(
    start_id: str = Query(..., description="The ID of the node to start searching from"), 
    depth: int = Query(1, description="Depth of search"),
    repository: GraphRepository = Depends(get_repo)
):
    try:
        return repository.search_graph(start_id, depth)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

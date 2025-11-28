from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class NodeCreate(BaseModel):
    id: str
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)

class EdgeCreate(BaseModel):
    source_id: str
    target_id: str
    type: str
    weight: Optional[float] = 1.0

class EdgeUpdate(BaseModel):
    type: Optional[str] = None
    weight: Optional[float] = None

class NodeResponse(BaseModel):
    id: str
    label: str
    properties: Dict[str, Any]

class EdgeResponse(BaseModel):
    id: Optional[str] = None
    source: str
    target: str
    type: str
    weight: Optional[float] = None

class GraphSearchResponse(BaseModel):
    nodes: List[NodeResponse]
    relationships: List[EdgeResponse]

class StatusResponse(BaseModel):
    status: str
    id: Optional[str] = None
    source: Optional[str] = None
    target: Optional[str] = None

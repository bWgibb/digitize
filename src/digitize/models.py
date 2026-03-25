"""Pydantic models for the digitize JSON output schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DrawingMeta(BaseModel):
    number: str
    sheet: str
    revision: str
    title: str
    equipment: str = ""
    series: str = ""
    section: str = ""
    location: str = ""
    manufacturer: str = ""
    customer: str = ""
    customer_ref: str = ""
    date: str = ""
    status: str = ""
    source_file: str
    digitized_date: str


class DrawingType(BaseModel):
    discipline: str
    primary: str
    secondary: str | None = None
    confidence: str = "high"
    notes: str = ""


class Revision(BaseModel):
    rev: int | str
    date: str
    description: str


class Component(BaseModel):
    tag: str
    type: str
    description: str
    circuit: str = ""
    attributes: dict = Field(default_factory=dict)


class CrossReference(BaseModel):
    ref: str
    description: str


class CableRef(BaseModel):
    cable: str
    from_location: str = ""
    to_location: str = ""
    function: str = ""


class DigitizedDrawing(BaseModel):
    drawing: DrawingMeta
    drawing_type: DrawingType
    revisions: list[Revision] = Field(default_factory=list)
    content: dict = Field(default_factory=dict)
    components: list[Component] = Field(default_factory=list)
    terminal_strips: dict = Field(default_factory=dict)
    test_blocks: dict = Field(default_factory=dict)
    cross_references: list[CrossReference] = Field(default_factory=list)
    cross_reference_tables: dict = Field(default_factory=dict)
    cables_referenced: list[CableRef] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    project_context: dict | None = None

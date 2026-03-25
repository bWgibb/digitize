"""Extraction prompts for civil/structural drawing types."""

TYPES: dict[str, str] = {
    "site_plan": """\
This is a site plan or plot plan.

Extract the following into the "content" section:

"buildings": For each building or structure:
  - tag: building number or name
  - description: building function
  - position: grid coordinates or northing/easting if shown
  - dimensions: footprint dimensions if shown

"roads": For each road or access route:
  - name: road name or designation
  - width: road width if shown
  - surface: paved, gravel, etc.

"utilities": For each utility shown (power, water, sewer, gas, telecom):
  - type: utility type
  - route: general path description
  - size: pipe or conduit size if shown

"coordinates": Key survey points or benchmarks:
  - name: point name
  - northing: north coordinate
  - easting: east coordinate
  - elevation: elevation if shown

"setbacks": Property lines, setbacks, or easements:
  - type: property_line, setback, easement, right_of_way
  - dimension: distance or offset
  - description: additional context
""",
    "foundation_plan": """\
This is a foundation or footing plan.

Extract the following into the "content" section:

"foundations": For each foundation or footing:
  - tag: foundation mark (e.g., "F1", "F2")
  - type: spread_footing, strip_footing, pile_cap, mat, pier, etc.
  - dimensions: length x width x depth
  - elevation: top of concrete elevation
  - reinforcement: rebar description if shown (e.g., "#5 @ 12 EW")
  - concrete: concrete specification if shown (e.g., "4000 PSI")

"piles": For each pile:
  - tag: pile mark
  - type: driven, drilled, helical, etc.
  - size: pile diameter or cross-section
  - capacity: bearing capacity if shown
  - tip_elevation: pile tip elevation

"anchor_bolts": For each anchor bolt group:
  - equipment_tag: what equipment this anchors
  - pattern: bolt pattern description
  - bolt_size: bolt diameter
  - projection: projection above concrete
  - embedment: embedment depth

"grade_beams": For each grade beam or tie beam:
  - tag: beam mark
  - size: width x depth
  - reinforcement: rebar description
  - from_foundation: start foundation mark
  - to_foundation: end foundation mark

"elevations": Key elevation callouts:
  - description: what the elevation references
  - value: elevation value
""",
    "structural_steel": """\
This is a structural steel framing plan.

Extract the following into the "content" section:

"members": For each structural member:
  - mark: piece mark (e.g., "B1", "C2", "G3")
  - type: beam, column, girder, brace, joist, purlin, etc.
  - size: section size (e.g., "W12x26", "HSS6x6x1/4")
  - length: member length if shown
  - material: steel grade (e.g., "A992", "A500 Gr B")

"columns": For each column:
  - mark: column mark
  - grid: column grid location (e.g., "A-1")
  - size: section size
  - base_elevation: base plate elevation
  - top_elevation: top elevation
  - splice: splice elevation if shown

"connections": For each connection detail:
  - type: moment, shear, pin, base_plate, splice, etc.
  - members: list of member marks at this connection
  - detail_ref: detail drawing reference if shown

"bracing": For each brace:
  - mark: brace mark
  - type: chevron, x_brace, knee_brace, etc.
  - size: section size
  - from_point: lower connection point
  - to_point: upper connection point

"column_grid": Column grid layout:
  - Extract grid line names and spacings
""",
    "grading_plan": """\
This is a grading or drainage plan.

Extract the following into the "content" section:

"contours": Key contour information:
  - existing_contour_interval: contour interval for existing grade
  - proposed_contour_interval: contour interval for proposed grade
  - datum: elevation datum reference

"drainage": For each drainage feature:
  - type: ditch, culvert, catch_basin, manhole, swale, etc.
  - tag: structure tag or designation
  - size: pipe size or structure dimensions
  - invert_elevation: invert elevation if shown
  - rim_elevation: rim or top elevation if shown
  - slope: pipe slope if shown

"cut_fill": Areas of significant cut or fill:
  - location: area description
  - type: cut or fill
  - depth: maximum depth of cut or fill
  - area: approximate area if shown

"elevations": Key spot elevations:
  - location: location description
  - existing: existing elevation
  - proposed: proposed elevation
""",
    "section_detail": """\
This is a section or detail drawing.

Extract the following into the "content" section:

"section_info": Section identification:
  - designation: section mark (e.g., "A-A", "1/S3")
  - cut_from: which plan drawing shows the section cut
  - scale: drawing scale

"elements": For each structural or architectural element shown:
  - tag: element mark or tag
  - type: wall, slab, beam, column, footing, etc.
  - material: concrete, steel, masonry, wood, etc.
  - dimensions: key dimensions
  - reinforcement: rebar or reinforcement details if shown

"dimensions": All dimensions called out:
  - description: what is dimensioned
  - value: dimension with units

"notes": Construction notes or special requirements:
  - Extract each note as a separate entry

"materials": Material callouts:
  - description: what the material specification applies to
  - specification: material specification
""",
}

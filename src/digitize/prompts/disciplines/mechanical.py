"""Extraction prompts for mechanical drawing types."""

TYPES: dict[str, str] = {
    "equipment_layout": """\
This is an equipment layout or arrangement drawing.

Extract the following into the "content" section:

"equipment": For each piece of equipment shown:
  - tag: equipment tag
  - type: pump, compressor, vessel, tank, heat_exchanger, motor, etc.
  - description: equipment name or service
  - position: grid coordinates or physical location reference
  - dimensions: length x width footprint if shown
  - elevation: installation elevation if shown
  - weight: equipment weight if shown

"dimensions": Key dimensions shown on the layout:
  - description: what the dimension measures
  - value: dimension value with units

"clearances": Any noted clearances or access requirements:
  - description: what the clearance is for
  - value: clearance dimension
  - type: maintenance, safety, code, etc.

"notes": General notes or legends on the drawing
""",
    "piping_iso": """\
This is a piping isometric drawing.

Extract the following into the "content" section:

"line_designation": The main pipe line(s) shown:
  - line_number: pipe line designation
  - size: pipe size
  - spec: pipe specification/class
  - service: process fluid
  - insulation: insulation type and thickness if shown

"pipe_segments": For each straight run of pipe:
  - from_point: starting point (equipment nozzle, fitting, etc.)
  - to_point: ending point
  - length: segment length if dimensioned
  - slope: slope if shown

"fittings": For each fitting:
  - type: elbow, tee, reducer, flange, union, cap, etc.
  - size: fitting size(s)
  - rating: pressure rating if shown
  - material: material if different from line spec

"valves": For each valve:
  - tag: valve tag
  - type: gate, globe, ball, check, butterfly, etc.
  - size: valve size
  - rating: pressure class

"supports": For each pipe support:
  - tag: support tag/mark
  - type: shoe, guide, anchor, spring, hanger, etc.
  - location: position description

"welds": For each weld:
  - type: butt, socket, fillet, etc.
  - ndt: NDE requirements (RT, UT, MT, PT)

"bill_of_materials": If a BOM is shown, extract each item:
  - item: item number
  - description: item description
  - quantity: count
  - size: size
  - material: material specification
""",
    "piping_plan": """\
This is a piping plan or section drawing.

Extract the following into the "content" section:

"pipe_routes": For each visible pipe route:
  - line_number: pipe line designation
  - size: pipe size
  - from_equipment: starting equipment
  - to_equipment: ending equipment
  - routing: general path description
  - elevation: pipe elevation if shown

"equipment_nozzles": For each equipment nozzle connection:
  - equipment_tag: equipment tag
  - nozzle: nozzle designation (e.g., "N1", "N2")
  - size: nozzle size
  - rating: flange rating
  - orientation: direction the nozzle faces
  - elevation: nozzle elevation if shown

"penetrations": For each wall or floor penetration:
  - location: wall/floor identifier
  - size: penetration size
  - lines_through: list of pipe lines passing through

"dimensions": Key dimensions:
  - description: what is dimensioned
  - value: dimension with units
""",
    "hvac_diagram": """\
This is an HVAC system diagram.

Extract the following into the "content" section:

"air_handling_units": For each AHU:
  - tag: unit tag
  - type: ahu, rtu, fan_coil, etc.
  - capacity: heating/cooling capacity if shown
  - airflow: CFM or L/s if shown

"ductwork": For each duct section:
  - from: starting point
  - to: ending point
  - size: duct dimensions
  - type: supply, return, exhaust, outside_air
  - insulation: insulation type if shown

"diffusers": For each diffuser or grille:
  - tag: diffuser tag
  - type: supply_diffuser, return_grille, exhaust_grille, etc.
  - size: diffuser size
  - airflow: CFM if shown
  - location: room or area served

"dampers": For each damper:
  - tag: damper tag
  - type: volume, fire, smoke, balancing, etc.
  - size: damper size
  - actuator: manual, pneumatic, electric

"controls": For each control point:
  - tag: sensor or controller tag
  - type: thermostat, humidity_sensor, co2_sensor, etc.
  - setpoint: control setpoint if shown
""",
    "equipment_datasheet": """\
This is a mechanical equipment datasheet.

Extract the following into the "content" section:

"equipment": Equipment identification:
  - tag: equipment tag
  - type: equipment type
  - manufacturer: manufacturer name
  - model: model number
  - serial_number: serial number if shown

"ratings": Performance ratings:
  - Extract all key-value pairs shown as a flat dict
  - Common fields: capacity, flow_rate, head, pressure, temperature, speed, power, efficiency, weight

"materials": Materials of construction:
  - Extract all material specifications as key-value pairs
  - Common fields: casing, impeller, shaft, seal, gasket, bolting

"connections": Nozzle or connection data:
  - For each connection: tag, size, rating, type, orientation

"notes": Design notes, operating conditions, or special requirements
""",
}

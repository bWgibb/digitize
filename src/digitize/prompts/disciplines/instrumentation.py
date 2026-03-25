"""Extraction prompts for instrumentation drawing types."""

TYPES: dict[str, str] = {
    "pid": """\
This is a P&ID (piping and instrumentation diagram).

Extract the following into the "content" section:

"instruments": For each instrument bubble or device:
  - tag: ISA-style instrument tag (e.g., "FT-101", "LV-202")
  - service: process service description
  - signal_type: AI, AO, DI, DO, or manual
  - range: measurement range if shown
  - model: instrument model if shown

"control_valves": For each control valve:
  - tag: valve tag (e.g., "FV-101")
  - type: globe, ball, butterfly, gate, etc.
  - size: valve size if shown
  - fail_position: FC (fail closed), FO (fail open), FL (fail last)
  - actuator: pneumatic, electric, hydraulic

"process_lines": For each process line:
  - line_number: pipe line designation
  - size: pipe size
  - spec: pipe specification class
  - from_equipment: upstream equipment
  - to_equipment: downstream equipment
  - service: process fluid

"process_equipment": For each vessel, tank, pump, heat exchanger, etc.:
  - tag: equipment tag
  - type: vessel, tank, pump, heat_exchanger, column, etc.
  - description: equipment service description
""",
    "loop_diagram": """\
This is an instrument loop diagram.

Extract the following into the "content" section:

"instrument": The primary instrument in this loop:
  - tag: instrument tag
  - type: transmitter, switch, gauge, element, etc.
  - service: what it measures
  - model: model number if shown
  - range: measurement range
  - output: 4-20mA, HART, fieldbus, etc.

"signal_path": The signal path from field to control room. For each node:
  - device: device tag at this point in the path
  - type: transmitter, junction_box, marshalling_cabinet, io_card, dcs_channel
  - terminals: terminal designations at this device
  - cable: cable number between this node and the next

"junction_boxes": For each junction box in the loop:
  - tag: JB designation
  - terminals: list of terminal numbers used

"field_wiring": For each wire segment:
  - from_device: source device
  - from_terminal: source terminal
  - to_device: destination device
  - to_terminal: destination terminal
  - cable: cable number
  - wire_color: wire color if shown

"power_supply": If the loop shows power supply details:
  - source: power supply tag
  - voltage: supply voltage
  - fuse: fuse tag and rating
""",
    "instrument_index": """\
This is an instrument index or schedule.

Extract the following into the "content" section:

"instruments": For each row in the instrument index:
  - tag: instrument tag
  - service: process service description
  - type: instrument type (transmitter, switch, gauge, etc.)
  - range: measurement range
  - model: manufacturer and model
  - signal_type: 4-20mA, discrete, HART, etc.
  - location: installation location
  - sis: whether it is a safety instrument (yes/no)
  - notes: any additional notes
""",
    "hookup_drawing": """\
This is an instrument hook-up or installation detail drawing.

Extract the following into the "content" section:

"instrument": The instrument being installed:
  - tag: instrument tag
  - type: instrument type
  - model: model number
  - process_connection: connection size and type (e.g., "1/2 NPT")

"installation": Physical installation details:
  - mounting: pipe_mount, panel_mount, rack_mount, wall_mount, etc.
  - orientation: horizontal, vertical, angled
  - elevation: elevation or height if shown

"tubing": For each tubing run:
  - from: starting point
  - to: ending point
  - size: tubing size (e.g., "1/2 OD SS")
  - material: tubing material

"valves": For each isolation or drain valve:
  - tag: valve tag
  - type: block, drain, bleed, vent, etc.
  - size: valve size

"fittings": For each fitting:
  - type: tee, elbow, reducer, union, etc.
  - size: fitting size
  - material: fitting material
""",
    "cause_effect": """\
This is a cause and effect diagram or matrix.

Extract the following into the "content" section:

"causes": For each cause (input/trigger):
  - id: cause ID or number
  - tag: instrument or signal tag
  - description: what the cause represents
  - setpoint: trip or alarm setpoint if shown

"effects": For each effect (output/action):
  - id: effect ID or number
  - tag: device or valve tag
  - description: what the effect does
  - action: trip, close, open, alarm, etc.

"matrix": For each cause-to-effect relationship:
  - cause_id: cause ID
  - effect_id: effect ID
  - logic: AND, OR, voting (e.g., "2oo3"), direct, latched
  - delay_s: time delay in seconds if shown
  - notes: bypass or override notes
""",
    "logic_diagram": """\
This is a safety or control logic diagram (SIS/SIL).

Extract the following into the "content" section:

"inputs": For each input signal:
  - tag: instrument/signal tag
  - description: signal description
  - type: DI, AI
  - setpoint: trip setpoint for analog inputs
  - sil: SIL rating if shown

"outputs": For each output action:
  - tag: device tag
  - description: action description
  - type: DO, AO
  - fail_state: energize_to_trip or de-energize_to_trip

"logic_blocks": For each logic element:
  - function: AND, OR, NOT, VOTE, TIMER, etc.
  - voting: voting configuration if applicable (e.g., "2oo3")
  - inputs: list of input tags
  - outputs: list of output tags
  - timer_s: timer duration if applicable

"bypasses": For each bypass:
  - tag: bypass switch/signal tag
  - affects: what signal or logic block it bypasses
  - type: maintenance, startup, test
""",
}

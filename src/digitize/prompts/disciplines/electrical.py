"""Extraction prompts for electrical drawing types."""

# Maps drawing type to the content-specific extraction instructions.
# The base extraction prompt (in extract.py) wraps these with the
# common envelope instructions (title block, components, cross-refs, etc.)

TYPES: dict[str, str] = {
    "one_line": """\
This is an electrical one-line (single-line) diagram.

Extract the following into the "content" section:

"buses": For each bus shown:
  - name: bus designation
  - voltage: rated voltage
  - configuration: single, double, split, ring, etc.

"sources": For each source (generator, utility tie, etc.):
  - tag: device tag/designation
  - type: generator, utility_tie, ups, etc.
  - rating: kVA/kW/MVA rating
  - bus: which bus it connects to

"loads": For each load or feeder:
  - tag: device tag/designation
  - type: transformer, motor, feeder, mcc, panel, etc.
  - rating: kVA/kW/HP rating
  - bus: which bus it feeds from
  - feeder: feeder/breaker tag if shown

"protective_devices": For each breaker, fuse, or relay:
  - tag: device tag
  - type: breaker, fuse, relay, switch, etc.
  - rating: trip rating or fuse size
  - ansi_codes: list of ANSI protection codes if shown (e.g., ["50", "51"])
  - from_bus: upstream bus
  - to_bus: downstream bus or load

"metering": For each metering point:
  - tag: meter or instrument tag
  - type: ammeter, voltmeter, wattmeter, ct, pt, etc.
  - location: where on the one-line it appears
""",
    "ac_schematic": """\
This is an AC elementary (schematic) diagram.

Extract the following into the "content" section:

"power_supply": The AC power source details:
  - source: where the AC power originates
  - voltage: AC voltage level(s)
  - phases: number of phases
  - feed_from: upstream source reference

"circuits": Group components into functional circuits found on the drawing. \
Use descriptive names based on what the circuit does (e.g., "bus_voltage_sensing", \
"current_transformer_sensing", "motor_starter", "heater_circuit"). For each circuit:
  - description: what the circuit does
  - components: list of component tag references in this circuit

"instrument_transformers": For each CT or PT:
  - tag: device tag
  - type: ct, pt, zct, etc.
  - ratio: transformation ratio (e.g., "200:5A")
  - accuracy_class: if shown
  - connected_to: what device(s) it feeds

"relay_modules": For each relay or protection device:
  - tag: device tag
  - type: relay type
  - model: model number if shown
  - description: function
""",
    "dc_schematic": """\
This is a DC elementary (schematic) diagram.

Extract the following into the "content" section:

"power_supply": The DC supply details:
  - source: supply designation
  - voltage: DC voltage
  - feed_from: upstream source or panel reference
  - fuses: list of fuse tags and ratings in the supply path

"circuits": Group components into functional circuits found on the drawing. \
Name each circuit based on its function (e.g., "close_circuit", "trip_circuit", \
"indication", "spring_charging", "breaker_failure", "alarm_annunciation"). \
For each circuit:
  - description: what the circuit does
  - components: list of component tag references in this circuit

"relay_modules": For each relay, contactor, or module:
  - tag: device tag
  - type: relay, contactor, timer, etc.
  - description: function
""",
    "panel_schedule": """\
This is a panel schedule or breaker schedule.

Extract the following into the "content" section:

"panel": Panel header information:
  - designation: panel tag/name
  - voltage: rated voltage
  - phases: number of phases (1 or 3)
  - wires: number of wires (2, 3, or 4)
  - bus_amps: bus ampere rating
  - main_breaker: main breaker size
  - enclosure: enclosure type if shown

"circuits": For each circuit position, extract:
  - number: circuit number
  - breaker_size: breaker ampere rating
  - poles: number of poles (1, 2, or 3)
  - description: load description
  - load_va: connected load in VA if shown
  - wire_size: wire gauge if shown
  - status: active, spare, space

"spares": List of spare circuit numbers
"spaces": List of space (empty) positions
""",
    "wiring_diagram": """\
This is a point-to-point wiring diagram.

Extract the following into the "content" section:

"connections": For each wire or connection shown:
  - from_device: source device tag
  - from_terminal: source terminal designation
  - to_device: destination device tag
  - to_terminal: destination terminal designation
  - wire_number: wire number if shown
  - wire_color: wire color if shown
  - cable: cable number if part of a multi-conductor cable
  - signal_type: DI, DO, AI, AO, power, comm, etc.
  - description: signal function/purpose
""",
    "cable_schedule": """\
This is a cable schedule drawing.

Extract the following into the "content" section:

"cables": For each cable entry:
  - cable: cable number/designation
  - from_location: source device or panel
  - to_location: destination device or panel
  - spec: cable specification (e.g., "3C #12 AWG XLPE")
  - conductors: number of conductors
  - length: cable length if shown
  - routing: tray, conduit, or raceway reference
  - function: brief description of cable purpose
""",
    "control_logic": """\
This is a control logic diagram.

Extract the following into the "content" section:

"logic_blocks": For each logic block or function:
  - name: block name or tag
  - function: AND, OR, NOT, TIMER, COUNTER, SR_LATCH, COMPARATOR, etc.
  - inputs: list of input signal names/tags
  - outputs: list of output signal names/tags
  - parameters: dict of parameters (e.g., {"delay_s": 5, "preset": 100})

"interlocks": For each interlock condition:
  - name: interlock name
  - condition: boolean expression
  - effect: what happens when the interlock is active

"permissives": For each permissive:
  - name: permissive name
  - condition: boolean expression
  - enables: what action this permissive enables
""",
    "protection_scheme": """\
This is a protection / relay scheme diagram.

Extract the following into the "content" section:

"protection_functions": For each protection function:
  - ansi_code: ANSI/IEEE device number (e.g., "50", "51G", "87")
  - function: protection function name (e.g., "phase overcurrent", "ground fault")
  - relay_model: relay model number if shown
  - relay_tag: relay device tag
  - settings: dict of visible settings (pickup, time dial, curve, etc.)

"trip_matrix": For each trip output:
  - cause: what triggers the trip (protection function or ANSI code)
  - ansi_code: ANSI code
  - trips: list of breaker/device tags that trip

"ct_pt_assignments": For each instrument transformer:
  - tag: CT or PT tag
  - type: ct, pt, zct
  - ratio: transformation ratio
  - zone: protection zone
  - feeds_relay: which relay tag it feeds
""",
    "plc_io_wiring": """\
This is a PLC I/O wiring diagram.

Extract the following into the "content" section:

"modules": For each PLC module shown:
  - slot: rack/slot position
  - type: DI, DO, AI, AO, comms, etc.
  - model: module model number
  - address_range: I/O address range

"channels": For each I/O channel:
  - module_slot: which module slot
  - channel: channel number on the module
  - address: PLC address (e.g., "%I0.0", "I:1/0")
  - tag: field device tag connected to this channel
  - description: signal description
  - signal_type: DI, DO, AI, AO
  - range: engineering range for analog (e.g., "4-20mA", "0-10V")

"field_wiring": For each field connection:
  - tag: field device tag
  - cable: cable number
  - from_terminal: PLC-side terminal
  - to_terminal: field-side terminal
""",
}

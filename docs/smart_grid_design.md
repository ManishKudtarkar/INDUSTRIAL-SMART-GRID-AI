# Smart Grid Design

## Substations

Each substation reports:

- `substation_id`
- `timestamp`
- `voltage`
- `current`
- `temperature`
- `harmonic_5th`
- `load_percentage`

Clients may be simulated, USB serial hardware, or Android ADB data sources.

## Fault Rules

Fault isolation is rule-based so operators can understand the result:

- Overheat: temperature above the safe range.
- Voltage sag: voltage significantly below nominal.
- Voltage surge: voltage significantly above nominal.
- Overload: load percentage critically high.
- Harmonic distortion: fifth harmonic above limit.
- Overcurrent: current above rated capacity.

## Load Balancing

The system assigns equal load to healthy active substations. If some substations become critical, their target load is reduced and the remaining load is distributed across healthier substations.

`RedistributionEngine` smooths transitions so targets do not jump too aggressively.

## Self Healing

`SelfHealingEngine` watches health updates. When a previously degraded substation recovers above the configured threshold, load can gradually return toward normal distribution.

## Shutdown Boundary

`alerts/critical_shutdown.py` records and notifies critical shutdown events. Real relay trip commands require deployment-specific hardware details, so the module accepts an `on_shutdown` callback instead of hardcoding a relay protocol.

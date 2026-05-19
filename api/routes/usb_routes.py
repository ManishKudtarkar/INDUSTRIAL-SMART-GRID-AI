"""
USB status routes — lets the frontend show which physical USB devices
are connected and which substations are streaming from them.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/usb", tags=["USB Devices"])

_grid_service = None

def set_service(service):
    global _grid_service
    _grid_service = service


@router.get("/status")
def get_usb_status():
    """
    Return the list of available COM/serial ports and which substations
    are currently streaming (connected to the socket server).

    Response shape:
    {
      "ports": [
        {"port": "COM3", "description": "USB Serial Device", "active": true, "substation_id": "S1"},
        ...
      ],
      "connected_substations": ["S1", "S2"],
      "port_count": 1
    }
    """
    import serial.tools.list_ports

    # All physically present COM ports
    raw_ports = list(serial.tools.list_ports.comports())

    # Which substations are currently streaming
    connected = []
    if _grid_service:
        connected = _grid_service.get_active_substations()

    # Build port list — mark a port as "active" if any substation is connected
    # (we can't know exactly which port maps to which substation without tracking
    #  it in the client, so we mark all ports active when substations are streaming)
    ports = []
    for p in raw_ports:
        ports.append({
            "port":         p.device,
            "description":  p.description or "Unknown device",
            "hwid":         p.hwid or "",
            "active":       len(connected) > 0,
            "substation_id": None,   # populated below if we can match
        })

    # If the server tracks which port each substation came from, use that.
    # For now, assign substations to ports in order (best-effort).
    for i, sub in enumerate(connected):
        if i < len(ports):
            ports[i]["substation_id"] = sub
            ports[i]["active"] = True

    return {
        "ports":                  ports,
        "connected_substations":  connected,
        "port_count":             len(ports),
        "streaming_count":        len(connected),
    }


@router.get("/ports")
def list_ports():
    """List all available COM/serial ports on this machine."""
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())
    return {
        "ports": [
            {"port": p.device, "description": p.description, "hwid": p.hwid}
            for p in ports
        ],
        "count": len(ports),
    }

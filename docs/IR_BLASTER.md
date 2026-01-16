# IR Blaster Integration Guide

## Overview

The IR driver abstractions support multiple device platforms (Roku, Apple TV, and others via custom adapters).
This guide covers setup, configuration, and troubleshooting.

## Supported Platforms

### Roku
**Configuration:** `examples/roku_config.yaml`

Roku uses NEC IR codes. Broadlink RM or Orvibo blasters work reliably.

```yaml
ir_blaster_host: "192.168.1.100"
ir_blaster_type: "broadlink"  # or orvibo
ir_device_id: "aabbccddeeff"
```

### Apple TV
**Configuration:** `examples/appletv_config.yaml`

Apple TV devices respond to HDMI CEC or HomeKit commands. For IR control, use custom endpoints if available.

```yaml
ir_blaster_host: "192.168.1.60"
ir_blaster_type: "custom"
ir_device_id: "apple-tv-1"
```

For other platforms, adapt the IR driver settings and extend the command mappings as needed.

## Supported Blaster Types

### 1. Broadlink RM / Broadlink Mini
**Type:** `broadlink`

Broadlink devices are HTTP-enabled IR blasters commonly available on Amazon/retail.

**Configuration:**
```yaml
ir_blaster_host: "192.168.1.100"    # Broadlink device IP
ir_blaster_port: 80
ir_blaster_type: "broadlink"
ir_device_id: "aabbccddeeff"         # MAC address
```

**API Endpoint:**
```
POST http://{host}:{port}/api/irda/send
Content-Type: application/json

{
  "device_id": "aabbccddeeff",
  "code": "0xC23C"
}
```

**How to find MAC address:**
- Broadlink app → Device settings → MAC address
- Or use `nmap` to scan network

### 2. Orvibo AllOne
**Type:** `orvibo`

Orvibo AllOne is another popular HTTP-enabled IR blaster.

**Configuration:**
```yaml
ir_blaster_host: "192.168.1.101"
ir_blaster_port: 80
ir_blaster_type: "orvibo"
```

**API Endpoint:**
```
POST http://{host}:{port}/api/irda/send
Content-Type: application/json

{
  "code": "0xC23C"
}
```

### 3. Custom HTTP Endpoint
**Type:** `custom`

For any other HTTP-based IR blaster with a custom API.

**Configuration:**
```yaml
ir_blaster_host: "192.168.1.102"
ir_blaster_port: 8080
ir_blaster_type: "custom"
ir_device_id: "my_device_id"
```

**API Endpoint:**
```
POST http://{host}:{port}/api/ir/send
Content-Type: application/json

{
  "ir_code": "0xC23C",
  "command": "HOME",
  "device_id": "my_device_id"
}
```

## Python Usage

### Basic Usage

```python
from screen2events.control.ir import RokuIRDriver
from screen2events.models import RemoteCommand

# Initialize driver
driver = RokuIRDriver(
    ir_blaster_host="192.168.1.100",
    ir_blaster_port=80,
    blaster_type="broadlink",
    device_id="aabbccddeeff",
)

# Send commands
driver.send(RemoteCommand.HOME)
driver.send(RemoteCommand.PLAY_PAUSE)
driver.send(RemoteCommand.UP)
```

### Using Factory Function

```python
from screen2events.control.ir import make_remote_driver

# Returns RokuIRDriver if host provided, LogOnlyDriver otherwise
driver = make_remote_driver(
    ir_blaster_host="192.168.1.100",
    ir_blaster_type="broadlink",
)

driver.send(RemoteCommand.SELECT)
```

### Manual Testing (LogOnlyDriver)

```python
from screen2events.control.ir import LogOnlyDriver

driver = LogOnlyDriver()
driver.send(RemoteCommand.HOME)  # No-op, useful for testing without hardware
```

## Supported Roku Commands

```python
RemoteCommand.HOME          # Roku home button
RemoteCommand.BACK          # Back/previous
RemoteCommand.UP            # Navigate up
RemoteCommand.DOWN          # Navigate down
RemoteCommand.LEFT          # Navigate left
RemoteCommand.RIGHT         # Navigate right
RemoteCommand.SELECT        # Select/OK button
RemoteCommand.PLAY_PAUSE    # Play/pause button
```

Each command is mapped to a Roku NEC IR code in `RokuIRDriver.ROKU_COMMANDS`.

## Configuration in YAML

```yaml
# All IR blaster options are optional
ir_blaster_host: "192.168.1.100"
ir_blaster_port: 80
ir_blaster_type: "broadlink"           # broadlink | orvibo | custom
ir_device_id: "aabbccddeeff"
```

If `ir_blaster_host` is omitted, the system uses `LogOnlyDriver` (manual testing mode).

## Error Handling

All IR operations include proper error handling:

```python
try:
    driver.send(RemoteCommand.HOME)
except RuntimeError as e:
    print(f"IR send failed: {e}")
except ValueError as e:
    print(f"Invalid command: {e}")
```

## Extending with Additional Commands

To add new device-specific IR codes:

1. Find the NEC code for your device's remote buttons
2. Add to `RokuIRDriver.ROKU_COMMANDS` (or create a device-specific mapping):

```python
ROKU_COMMANDS = {
    RemoteCommand.HOME: "0xC23C",
    # Add device-specific code:
    # RemoteCommand.HOME: "0xE0E040BF",  # e.g. Apple TV code
}
```

For device-specific commands, extend `RemoteCommand` enum in `models.py`.

## Integration with Pipeline

The IR driver integrates into the main correlation pipeline via:

1. **Config file** specifies blaster settings and device type
2. **CLI** instantiates driver based on config
3. **Verify module** uses driver to confirm remote actions
4. **Pipeline** compares intended vs. observed state changes

See [src/screen2events/control/verify.py](../src/screen2events/control/verify.py) for verification logic.

# IR Blaster Integration Guide

## Overview

The `RokuIRDriver` class provides HTTP-based IR command transmission to Roku devices via compatible IR blasters. It supports multiple blaster types and handles command mapping automatically.

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

To add new Roku IR codes:

1. Find the Roku NEC code for the command
2. Add to `RokuIRDriver.ROKU_COMMANDS`:

```python
ROKU_COMMANDS = {
    RemoteCommand.HOME: "0xC23C",
    # Add new mapping:
    # RemoteCommand.CUSTOM: "0xABCD",
}
```

Or extend the `RemoteCommand` enum in `models.py` and add the IR code.

## Network Setup

### Requirements
- IR blaster device on same network as test machine
- Network must allow HTTP communication (port 80/8080)
- IR blaster must be powered on and responsive

### Debugging Connection
```bash
# Test connectivity
curl -X POST http://192.168.1.100:80/api/irda/send \
  -H "Content-Type: application/json" \
  -d '{"device_id":"aabbccddeeff","code":"0xC23C"}'

# Check if device responds
ping 192.168.1.100
```

## Dependencies

Requires `requests>=2.28` for HTTP communication:

```bash
# Install IR support
pip install -e '.[ir]'

# Or with everything
pip install -e '.[video,opensearch,ir,dev]'
```

If you plan to use S3-stored telemetry (recommended for low-friction demos), install the
S3 extra and follow the `examples/s3_config.yaml` example:

```bash
pip install -e '.[s3]'
```

The S3 adapter expects newline-delimited JSON (JSONL) files of `NormalizedEvent` records.
Place them under your configured `s3_prefix` and the adapter will enumerate and read them.

## Testing

Run IR driver tests:

```bash
pytest tests/test_ir.py -v
```

Tests cover:
- LogOnlyDriver (no-op mode)
- RokuIRDriver initialization
- Factory function behavior
- Command coverage
- Error handling

## Troubleshooting

### "requests library is required"
```bash
pip install requests
```

### "Failed to send IR command"
- Verify IR blaster is reachable: `ping 192.168.1.100`
- Check blaster type matches your device
- Verify device_id is correct (for Broadlink)
- Check firewall rules

### Commands not received by Roku
- Verify IR blaster can see Roku (line of sight for IR)
- Test with IR blaster's native app first
- Check IR codes are correct for your Roku model
- Ensure Roku is powered on and responsive

## Integration with Pipeline

The IR driver integrates into the main correlation pipeline via:

1. **Config file** specifies blaster settings
2. **CLI** instantiates driver based on config
3. **Verify module** uses driver to confirm remote actions
4. **Pipeline** compares intended vs. observed state changes

See [src/screen2events/control/verify.py](../src/screen2events/control/verify.py) for verification logic.

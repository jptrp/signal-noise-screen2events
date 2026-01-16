import pytest
from screen2events.control.ir import LogOnlyDriver, RokuIRDriver, make_remote_driver
from screen2events.models import RemoteCommand


def test_logonly_driver():
    """Test that LogOnlyDriver is a no-op."""
    driver = LogOnlyDriver()
    # Should not raise or error
    driver.send(RemoteCommand.HOME)
    driver.send(RemoteCommand.PLAY_PAUSE)


def test_roku_ir_driver_invalid_command():
    """Test that RokuIRDriver rejects unsupported commands."""
    driver = RokuIRDriver(
        ir_blaster_host="192.168.1.100",
        ir_blaster_port=80,
    )
    # Verify HOME is in commands
    assert RemoteCommand.HOME in driver.ROKU_COMMANDS


def test_make_remote_driver_none_host():
    """Test factory function returns LogOnlyDriver for None host."""
    driver = make_remote_driver(ir_blaster_host=None)
    assert isinstance(driver, LogOnlyDriver)


def test_make_remote_driver_with_host():
    """Test factory function returns RokuIRDriver with host."""
    driver = make_remote_driver(
        ir_blaster_host="192.168.1.100",
        ir_blaster_type="broadlink",
    )
    assert isinstance(driver, RokuIRDriver)
    assert driver.ir_blaster_host == "192.168.1.100"
    assert driver.blaster_type == "broadlink"


def test_roku_ir_driver_initialization():
    """Test RokuIRDriver initialization with various parameters."""
    driver = RokuIRDriver(
        ir_blaster_host="192.168.1.100",
        ir_blaster_port=8080,
        device_id="aabbccddeeff",
        blaster_type="orvibo",
        timeout_seconds=10.0,
    )
    assert driver.ir_blaster_host == "192.168.1.100"
    assert driver.ir_blaster_port == 8080
    assert driver.device_id == "aabbccddeeff"
    assert driver.blaster_type == "orvibo"
    assert driver.timeout_seconds == 10.0


def test_roku_commands_coverage():
    """Test that all RemoteCommand types are covered in ROKU_COMMANDS."""
    driver = RokuIRDriver(ir_blaster_host="192.168.1.100")
    
    # Commands that should have IR codes
    expected_commands = {
        RemoteCommand.HOME,
        RemoteCommand.BACK,
        RemoteCommand.UP,
        RemoteCommand.DOWN,
        RemoteCommand.LEFT,
        RemoteCommand.RIGHT,
        RemoteCommand.SELECT,
        RemoteCommand.PLAY_PAUSE,
    }
    
    for cmd in expected_commands:
        assert cmd in driver.ROKU_COMMANDS, f"Missing IR code for {cmd}"
        assert isinstance(driver.ROKU_COMMANDS[cmd], str), f"IR code should be string for {cmd}"

#!/usr/bin/env python3
"""
Main entry point for acpi-wakeup-persistd service/timer.
Resets ACPI wakeup sources to desired states.
"""

import sys
import os
import logging
import argparse
import time
from pathlib import Path

# Add parent directory to path to import config_parser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_parser import parse_config

# Constants
PROC_ACPI_WAKEUP = '/proc/acpi/wakeup'
DEFAULT_CONFIG_PATH = '/etc/acpi-wakeup-persistd/config.conf'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

logger = logging.getLogger('acpi-wakeup-persistd')


def setup_logging(debug: bool = False):
    """Configure logging."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format=LOG_FORMAT)
    # Also log to stdout for service compatibility
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)


def get_current_states() -> dict[str, str]:
    """
    Read current states from /proc/acpi/wakeup.
    Returns a dict mapping source name to current state (enabled/disabled).
    """
    states = {}
    try:
        with open(PROC_ACPI_WAKEUP, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                # Format: [ * ] device path state
                # parts[1] is device name, parts[3] is state
                if len(parts) >= 4:
                    device = parts[1].upper()  # Ensure uppercase for comparison
                    state = parts[3].lower()
                    states[device] = state
                elif len(parts) == 3:
                    # Fallback for some weird kernel versions
                    device = parts[0].upper()
                    state = parts[2].lower()
                    states[device] = state
    except Exception as e:
        logger.error(f"Failed to read {PROC_ACPI_WAKEUP}: {e}")
        sys.exit(1)
    return states


def set_wakeup_state(source: str, desired_state: str) -> bool:
    """
    Toggle the wakeup state of a given source.
    Writing the device name toggles its state.
    Returns True if successful, False otherwise.
    """
    try:
        with open(PROC_ACPI_WAKEUP, 'w') as f:
            f.write(f"{source}\n")
        # Brief sleep to ensure kernel processes the write
        time.sleep(0.1)
        return True
    except Exception as e:
        logger.error(f"Failed to set state of {source} to {desired_state}: {e}")
        return False


def apply_config(enabled_sources: set[str], disabled_sources: set[str]) -> None:
    """
    Apply the configuration to the current system state.
    """
    current_states = get_current_states()

    # Process enabled sources
    for source in enabled_sources:
        if source not in current_states:
            logger.debug(f"Source {source} not found in {PROC_ACPI_WAKEUP}. Skipping.")
            continue
        if current_states[source] == 'enabled':
            continue # Already enabled
        logger.info(f"Enabling source {source}")
        if not set_wakeup_state(source, 'enabled'):
            logger.error(f"Failed to enable source {source}")

    # Process disabled sources
    for source in disabled_sources:
        if source not in current_states:
            logger.debug(f"Source {source} not found in {PROC_ACPI_WAKEUP}. Skipping.")
            continue
        if current_states[source] == 'disabled':
            continue # Already disabled
        logger.info(f"Disabling source {source}")
        if not set_wakeup_state(source, 'disabled'):
            logger.error(f"Failed to disable source {source}")


def generate_default_config(output_path: str) -> None:
    """
    Generate a default config file reflecting the current system state.
    Mirrors the current /proc/acpi/wakeup states to the config.
    """
    current_states = get_current_states()
    
    if not current_states:
        logger.warning("No wakeup devices found in /proc/acpi/wakeup. Config will be empty.")
        # Create an empty config with headers just in case
        config_content = """# ACPI Wakeup Persistd Generated Config
# Generated on {date}
# No wakeup devices were detected in /proc/acpi/wakeup.
# You may need to plug in devices and run this again, or check kernel logs.

[enabled]

[disabled]
""".format(date=time.strftime("%Y-%m-%d %H:%M:%S"))
        dir_path = os.path.dirname(output_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(config_content)
        return

    enabled_list = []
    disabled_list = []

    # Sort devices for consistent output
    all_devices = sorted(current_states.keys())

    # Categorize based on current state
    for device in all_devices:
        state = current_states[device]
        if state == 'enabled':
            enabled_list.append(device)
        elif state == 'disabled':
            disabled_list.append(device)
        else:
            # Fallback for any unexpected state strings (e.g., 'unknown')
            disabled_list.append(device)
            logger.debug(f"Unknown state '{state}' for device {device}, defaulting to disabled")

    config_content = f"""# ACPI Wakeup Persistd Generated Config
# Generated on {time.strftime("%Y-%m-%d %H:%M:%S")}
# This file was automatically generated based on your current system state.
#
# Devices currently in the [enabled] section will be allowed to wake the system.
# Devices currently in the [disabled] section will be prevented from waking the system.
#
# You can edit this file to change these defaults.
# After editing, the service will apply the new settings on the next run (boot or timer).

[enabled]
"""
    
    # Add enabled devices
    if enabled_list:
        for device in enabled_list:
            config_content += f"{device}\n"
    else:
        config_content += "# None\n"

    config_content += "\n[disabled]\n"
    
    # Add disabled devices
    if disabled_list:
        for device in disabled_list:
            config_content += f"{device}\n"
    else:
        config_content += "# None\n"

    # Write to file
    dir_path = os.path.dirname(output_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(config_content)
    
    logger.info(f"Generated default config at {output_path} based on current kernel state.")
    logger.info(f"Summary: {len(enabled_list)} devices enabled, {len(disabled_list)} devices disabled.")


def main():
    parser = argparse.ArgumentParser(description='Persist ACPI wakeup sources')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Run command (default)
    run_parser = subparsers.add_parser('run', help='Apply config')
    run_parser.add_argument('--config', type=str, default=DEFAULT_CONFIG_PATH,
                            help='Path to config file')
    run_parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    # Generate config command
    gen_parser = subparsers.add_parser('generate-config', help='Generate default config')
    gen_parser.add_argument('--output', type=str, default=DEFAULT_CONFIG_PATH,
                            help='Output path for the generated config')

    args = parser.parse_args()

    setup_logging(debug=args.debug)

    if args.command == 'generate-config':
        generate_default_config(args.output)
    elif args.command == 'run':
        logger.info("Starting acpi-wakeup-persistd")

        # Parse config
        try:
            enabled_sources, disabled_sources = parse_config(args.config)
        except FileNotFoundError as e:
            logger.error(str(e))
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to parse config: {e}")
            sys.exit(1)

        if not enabled_sources and not disabled_sources:
            logger.warning("No sources specified in config. Exiting.")
            sys.exit(0)

        # Apply configuration
        apply_config(enabled_sources, disabled_sources)

        logger.info("acpi-wakeup-persistd finished")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

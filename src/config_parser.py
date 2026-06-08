"""
Config parser for acpi-wakeup-persistd.
Reads a config file and returns two sets: enabled_sources and disabled_sources.
"""

import configparser
import os
import logging

logger = logging.getLogger(__name__)


def parse_config(config_file: str) -> tuple[set[str], set[str]]:
    """
    Parse the config file and return two sets:
    - enabled_sources: sources to be enabled
    - disabled_sources: sources to be disabled
    """
    enabled_sources = set()
    disabled_sources = set()

    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file not found: {config_file}")

    config = configparser.ConfigParser()
    # Ignore case for section names
    config.read(config_file, encoding='utf-8')

    # Parse [enabled] section
    if config.has_section('enabled'):
        for key in config.options('enabled'):
            # Strip whitespace and ensure uppercase (kernel names are usually uppercase)
            enabled_sources.add(key.strip().upper())

    # Parse [disabled] section
    if config.has_section('disabled'):
        for key in config.options('disabled'):
            disabled_sources.add(key.strip().upper())

    logger.debug(f"Parsed config: enabled={enabled_sources}, disabled={disabled_sources}")
    return enabled_sources, disabled_sources

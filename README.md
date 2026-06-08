# ACPI Wakeup Persistd

A systemd service and timer that ensures all `/proc/acpi/wakeup` sources remain in their desired state (enabled/disabled) persistently.

## Why?

Linux often enables wakeup sources by default that you may want to disable (e.g., `USB0`, `PXSX`, `LPC`) to prevent unwanted wakeups from USB devices, PCI devices, or the LPC bus. Changes to `/proc/acpi/wakeup` are lost on reboot. This tool ensures your preferences are applied consistently.

## Features

- Runs early in the boot process via `sysinit.target`.
- **Also** runs periodically (every 5 minutes) via `systemd.timer` to catch devices probed late in the boot process.
- Reads a configuration file to determine which sources should be enabled or disabled.
- Requires root privileges (standard for `/proc` manipulation).
- Logs actions to journalctl.

## Installation

### Prerequisites

- Python 3.8+
- Systemd
- Root access

### Steps

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/acpi-wakeup-persistd.git
   cd acpi-wakeup-persistd
   ```

2. Install the package:
   ```bash
   sudo make install
   ```
   > **Note:** During installation, the tool will automatically query your current `/proc/acpi/wakeup` devices and generate a default config file at `/etc/acpi-wakeup-persistd/config.conf`. 
   >
   > **Important:** This config **mirrors your current system state**. If a device is currently enabled to wake the system, it will be listed in `[enabled]`. If you want to change these defaults, edit the file **before** enabling the service.

3. Edit the configuration file if needed:
   ```bash
   sudo nano /etc/acpi-wakeup-persistd/config.conf
   ```
   *   Move devices you want to **stop** waking the system into the `[disabled]` section.
   *   Move devices you want to **keep** waking the system into the `[enabled]` section.
   *   Remove any devices that are no longer relevant.

4. Enable and start the service and timer:
   ```bash
   sudo systemctl enable --now acpi-wakeup-persistd.service
   sudo systemctl enable --now acpi-wakeup-persistd.timer
   ```

5. Check logs to verify it applied correctly:
   ```bash
   journalctl -u acpi-wakeup-persistd.service -f
   ```

## Security

- The service runs as root. This is required to write to `/proc/acpi/wakeup`.
- The configuration file is protected with `600` permissions to prevent unauthorized modification.
- The script validates device names against the current kernel list to prevent arbitrary writes.

## License

MIT

PREFIX ?= /usr
SYSTEMD_DIR ?= $(PREFIX)/lib/systemd/system
SYS_CONF_DIR ?= $(PREFIX)/etc/acpi-wakeup-persistd

.PHONY: install uninstall test clean

install:
	# Create directories
	install -d $(DESTDIR)$(PREFIX)/lib/acpi-wakeup-persistd
	install -d $(DESTDIR)$(SYS_CONF_DIR)
	install -d $(DESTDIR)$(SYSTEMD_DIR)

	# Install Python files
	cp -r src/* $(DESTDIR)$(PREFIX)/lib/acpi-wakeup-persistd/

	# Install config
	cp configs/default.conf $(DESTDIR)$(SYS_CONF_DIR)/config.conf.example

	# Install systemd units
	cp systemd/acpi-wakeup-persistd.service $(DESTDIR)$(SYSTEMD_DIR)/
	cp systemd/acpi-wakeup-persistd.timer $(DESTDIR)$(SYSTEMD_DIR)/
	cp systemd/acpi-wakeup-persistd.path $(DESTDIR)$(SYSTEMD_DIR)/

	# Generate config if it doesn't exist
	if [ ! -f $(DESTDIR)$(SYS_CONF_DIR)/config.conf ]; then \
		echo "Generating default config based on current hardware..."; \
		/usr/bin/python3 $(DESTDIR)$(PREFIX)/lib/acpi-wakeup-persistd/main.py generate-config --output $(DESTDIR)$(SYS_CONF_DIR)/config.conf; \
	fi

	# Set config permissions (only if generated or new)
	chmod 600 $(DESTDIR)$(SYS_CONF_DIR)/config.conf

	# Reload systemd daemon
	systemctl daemon-reload 2>/dev/null || true

uninstall:
	rm -f $(DESTDIR)$(SYSTEMD_DIR)/acpi-wakeup-persistd.service
	rm -f $(DESTDIR)$(SYSTEMD_DIR)/acpi-wakeup-persistd.timer
	rm -f $(DESTDIR)$(SYSTEMD_DIR)/acpi-wakeup-persistd.path
	rm -rf $(DESTDIR)$(PREFIX)/lib/acpi-wakeup-persistd
	rm -f $(DESTDIR)$(SYS_CONF_DIR)/config.conf
	rm -f $(DESTDIR)$(SYS_CONF_DIR)/config.conf.example
	systemctl daemon-reload 2>/dev/null || true

test:
	python -m pytest tests/ -v

clean:
	rm -rf build/ dist/ *.egg-info/

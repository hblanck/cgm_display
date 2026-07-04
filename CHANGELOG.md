# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Display abstraction layer (DisplayFactory/DisplayInterface) for adding new display types
- Async/await refactoring for improved performance
- Configuration file schema for advanced settings
- Web UI dashboard (optional)

---

## [1.1.0] - 2026-07-04

### Added
- **Unified Entry Point**: Single `cgm_display.py` script supporting both Nightscout and Dexcom modes via subcommands
- **Environment Variable Support**: Dexcom credentials can now be provided via `DEXCOM_USERNAME` and `DEXCOM_PASSWORD` environment variables
- **Dexcom Data Source Class**: New `DexcomDataSource` class providing clean interface matching `NightscoutDataSource`
- **Professional Directory Structure**: Organized code into `src/` package, `assets/`, `docs/`, and `archive/` directories
- **Comprehensive Documentation**: Directory structure diagram and setup instructions in README
- **Systemd Service Example**: Sample systemd service file for running as a Linux service
- **Docker Environment Variables**: Docker usage examples with credential passing
- **Enhanced .gitignore**: Prevents accidental credential file commits
- **CHANGELOG.md**: This file documenting all changes

### Changed
- **Refactored Command-Line Interface**: Now uses subcommands (`nightscout` and `dexcom`) instead of separate scripts
- **Reorganized Directory Structure**:
  - Python modules moved to `src/` package
  - Documentation images moved to `assets/images/`
  - Loop status images moved to `assets/loop-status/`
  - Documentation moved to `docs/`
  - Obsolete code archived in `archive/`
- **Updated Dockerfile**: Uses new unified entry point with Nightscout mode
- **README Restructured**: Added sections for environment variables, systemd setup, Docker usage, and directory structure
- **Import Strategy**: All modules now use `src.*` imports for external scripts, relative imports within package

### Removed
- **cgm_display.ini**: Plaintext config file (replaced with environment variables)
- **nightscout_display.py**: Superseded by unified `cgm_display.py` entry point
- **Config File References**: Removed all `configparser` and `.ini` file handling
- **Legacy Threading Model**: Dexcom mode no longer uses threading (unified with Nightscout's cleaner model)

### Deprecated
- **Sugarmate API Support**: Use Nightscout instead (archived in `archive/sugarmate_display.py`)
- **E-ink Display Module**: Archived in `archive/e-ink_display.py` (may be refactored in future)
- **Dual-Display Variant**: Archived in `archive/cgm_display_2displays.py`

### Security
- **Removed Plaintext Credentials**: No longer stores credentials in `.ini` files
- **Environment Variable Credentials**: Credentials now passed via secure environment variables
- **Improved .gitignore**: Prevents accidental credential storage (*.ini, *.conf, credentials.txt, .env, etc.)
- **Credential Resolution Order**: CLI args > environment variables (transparent, no hidden defaults)

### Fixed
- **Image Path Resolution**: Loop status images now correctly located in `assets/loop-status/` directory
- **Module Imports**: All relative imports within `src/` package fixed to use proper relative import syntax

### Documentation
- **Added Directory Structure Diagram**: Visual layout of project organization
- **Added Environment Variable Examples**: Multiple usage methods (CLI, env vars, systemd, Docker)
- **Restored PiTFT Instructions**: Hardware setup and installation instructions retained
- **Added Import Documentation**: Explained import patterns for external scripts and package modules
- **Security Best Practices**: Documented secure credential management approaches

---

## [1.0.0] - 2026-01-09

### Added
- **Nightscout Display Mode**: Modern, refactored implementation using `PygameDisplay` class
- **Data Source Abstraction**: `Nightscout` class for clean API client interface
- **Display Abstraction**: `PygameDisplay` class encapsulating pygame rendering logic
- **Loop Status Indicators**: Support for Loop device freshness tracking with status images
- **Connection Status Badge**: Visual indicator showing Nightscout connection status
- **Error Handling**: Full-screen error display for connection failures
- **Platform Detection**: Automatic font selection based on OS (Linux vs macOS)
- **Night Mode**: Automatic display brightness adjustment (10pm-7am)
- **Command-Line Arguments**: Subcommand support for different data sources (initial version)

### Changed
- **Architecture Shift**: Moved from procedural to class-based design
- **Display Logic**: Consolidated pygame rendering into reusable `PygameDisplay` class

### Technical Details
- Python 3.10+ support
- `pygame 2.6.1+` for rendering
- `requests` library for HTTP API calls
- Docker support with Python 3.11.11

---

## Legacy Versions

### [0.x] - Pre-2025

Legacy implementations preserved in `archive/`:
- **cgm_display_legacy.py**: Original Dexcom Share API implementation with threading and config file
- **sugarmate_display.py**: Sugarmate API alternative (2023-2025)
- **e-ink_display.py**: Waveshare e-ink specific implementation (2023-2025)
- **cgm_display_2displays.py**: Dual-display variant for monitoring multiple users (2019-2025)

For historical context and archived implementations, see the `archive/` directory.

---

## Migration Guide

### From v0.x (Legacy Dexcom Implementation)

**Before** (cgm_display.py with config file):
```bash
# Configure credentials in cgm_display.ini
python cgm_display.py
```

**After** (v1.1.0 with environment variables):
```bash
export DEXCOM_USERNAME=myuser
export DEXCOM_PASSWORD=mypass
python cgm_display.py dexcom
```

### From Nightscout-Only Implementation

**Before** (nightscout_display.py):
```bash
python nightscout_display.py --nightscoutserver https://your-server.com
```

**After** (v1.1.0 unified entry point):
```bash
python cgm_display.py nightscout --nightscoutserver https://your-server.com
```

### To Run at Boot

**Systemd Service** (recommended):
```ini
[Unit]
Description=CGM Display
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/cgm_display
Environment="DEXCOM_USERNAME=myuser"
Environment="DEXCOM_PASSWORD=mypass"
ExecStart=/usr/bin/python3 /home/pi/cgm_display/cgm_display.py dexcom
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## Version Numbering

- **v1.1.0** (2026-07-04): Major refactoring - unified entry point, environment variables, clean directory structure
- **v1.0.0** (2026-01-09): Nightscout-focused implementation with modern architecture
- **v0.x** (Pre-2025): Legacy implementations (archived)

---

## Known Issues

None currently. For bug reports, please open an issue on GitHub.

---

## Contributing

When adding features or fixing bugs, update this CHANGELOG.md:

1. Add an entry under `[Unreleased]` or create a new version section
2. Use standard categories: Added, Changed, Removed, Deprecated, Fixed, Security
3. Keep entries clear and concise
4. Reference relevant pull requests or issues if applicable

---

## Backwards Compatibility

**v1.1.0 Compatibility Matrix**:

| Feature | v0.x | v1.0.0 | v1.1.0 | Notes |
|---------|------|--------|--------|-------|
| Nightscout | ✗ | ✅ | ✅ | Added in v1.0.0 |
| Dexcom | ✅ | ✗ | ✅ | Restored in v1.1.0 with env vars |
| Config File | ✅ | ✗ | ✗ | Removed, use env vars instead |
| Threading | ✅ | ✗ | ✗ | Simplified, single-threaded design |
| Entry Point | Multiple | nightscout_display.py | cgm_display.py | Unified in v1.1.0 |

**Breaking Changes in v1.1.0**:
- `.ini` config files no longer supported
- Dexcom credentials must use environment variables or CLI args
- Command structure changed to subcommands (`nightscout`/`dexcom`)

**Upgrade Path**:
- Set `DEXCOM_USERNAME` and `DEXCOM_PASSWORD` environment variables
- Update command to: `python cgm_display.py dexcom`
- For Nightscout: `python cgm_display.py nightscout --nightscoutserver <url>`

---

## Future Roadmap

### Planned for Next Release
- [ ] DisplayFactory and DisplayInterface for pluggable display types
- [ ] Async/await refactoring for improved responsiveness
- [ ] Configuration schema for advanced settings
- [ ] Enhanced error recovery and reconnection logic

### Long-Term Vision
- Web UI dashboard for remote monitoring
- Mobile app integration
- Multi-user support
- Integration with other CGM systems (Freestyle Libre, Medtronic, etc.)

---

## Resources

- [README.md](README.md) — Project overview and setup instructions
- [docs/](docs/) — Additional documentation
- [archive/](archive/) — Historical implementations
- [src/](src/) — Current source code
- [assets/](assets/) — Images and resources

---

## License

This project is licensed under the terms specified in [docs/THIRD_PARTY_NOTICES.md](docs/THIRD_PARTY_NOTICES.md).

---

**Last Updated**: 2026-07-04

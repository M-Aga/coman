# Changelog

## [1.0.0] - 2024-08-22

### Added
- Centralised Semantic Versioning metadata for the platform and modules, including helpers to query module versions. 
- Automatic mirroring of module endpoints to legacy routers with deprecation metadata and a published sunset date.

### Changed
- Core FastAPI application and module routers now expose canonical `/v1/{module}` endpoints while keeping legacy routes available.
- Default tool registry data, integration tests, and UI hints now target the versioned API paths.
- Core instrumentation sources read version information from the shared metadata module.

### Deprecated
- Unversioned module routes are now flagged as deprecated and are scheduled for removal on 2025-09-30.

### Removed
- Nothing.

### Fixed
- Improved route inclusion logic to attach both canonical and legacy routers for loaded modules.


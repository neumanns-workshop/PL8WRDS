# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0-beta.4] - 2024-01-06

### Changed
- Modularized code architecture
  - Split screens into individual components
  - Created BaseScreen class for shared functionality
  - Implemented ScreenManager for better state handling
  - Improved screen transitions and lifecycle management
- Modularized CSS structure for better maintainability
  - Split styles into component-specific files
  - Improved organization of UI-related code
- Fixed UI consistency issues
  - Unified plate display design across game over and stats screens
  - Consistent vertical alignment in about screen carousel
  - Fixed menu button interaction issues
- Completed mobile UI improvements
  - Optimized layouts for all screen sizes
  - Enhanced touch controls
  - Fixed scrolling and overflow issues

## [0.1.0-beta.3] - 2024-01-05

### Added
- Mobile support improvements
  - Added tap interaction for game menu start
  - Fixed About menu scrolling and content layout
  - Fixed font loading issues

## [0.1.0-beta.2] - 2024-01-05

### Changed
- Improved scoring card UI in About menu for better clarity and consistency
  - Aligned scoring components with controls section style
  - Clearer presentation of base points, multiplier, and combo system
  - Added visual indicator for plate change scoring
- Made version text in main menu link to CHANGELOG on GitHub
- Updated repository URLs to point to neumanns-workshop organization

## [0.1.0-beta.1] - Initial Release

### Added
- Core gameplay mechanics
- Dynamic license plate generation
- Word validation system
- Scoring system with multipliers
- Statistics tracking
- Tutorial and help screens
- Basic UI/UX implementation

# Changelog

## [0.2.0] - 2023-08-31

### Added
- Connection tracking with new `connections` table
- Real-time VPN metrics via WebSocket
- Payment system with Stripe integration
- Premium vs Free tier server differentiation

### New Endpoints
- `/vpn/connect` - Create new VPN connection with eligibility checks
- `/vpn/disconnect` - End VPN connection with usage summary
- `/ws/connection/{user_id}` - WebSocket for real-time connection metrics
- `/payments/create` - Create Stripe checkout session
- `/payments/webhook` - Handle Stripe payment webhooks

### Database Changes
- New `connections` table for tracking VPN sessions
- Added indexes on `connections(user_id)`, `vpn_servers(location, status)`
- Added `tier` column to `vpn_servers` table
- New `payment_logs` table for payment tracking

### Developer Changes
- Added comprehensive test suite with pytest
- In-memory SQLite support for local testing
- Added test coverage reporting
- Added OpenAPI documentation improvements

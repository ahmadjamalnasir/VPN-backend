# VPN Status API Curl Command

## Get VPN Connection Status
```bash
# Get status by connection ID
curl -X GET "http://localhost:8000/api/v1/vpn/status?connection_id=connection-uuid&user_id=123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get latest connection status (without connection_id)
curl -X GET "http://localhost:8000/api/v1/vpn/status?user_id=123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Response Example
```json
{
  "connection_id": "uuid",
  "status": "connected",
  "server": {
    "id": "uuid",
    "hostname": "vpn-us-east-1",
    "location": "us-east",
    "ip_address": "203.0.113.1",
    "is_premium": false
  },
  "client_ip": "10.0.123.45",
  "started_at": "2024-01-15T10:30:00Z",
  "ended_at": null,
  "duration_seconds": 3600,
  "bytes_sent": 1048576,
  "bytes_received": 2097152,
  "total_bytes": 3145728,
  "connection_speed_mbps": 6.99,
  "server_load": 0.35,
  "ping_ms": 15,
  "is_active": true
}
```
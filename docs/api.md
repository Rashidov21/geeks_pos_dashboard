# Owner Dashboard API v1

Base URL: `/api/v1/`

## Authentication
- Header 1: `Authorization: Token <token>`
- Header 2: `X-CLIENT-KEY: <client_api_key>`

## 1) Activate License
`POST /api/v1/activate/`

Request:
```json
{
  "activation_key": "key-value",
  "hardware_id": "PC-ABC-123",
  "client_meta": {"app_version": "1.0.0"}
}
```

Success Response:
```json
{
  "status": "active",
  "license_type": "monthly",
  "start_date": "2026-04-25",
  "end_date": "2026-05-25",
  "store": {"id": 1, "name": "Demo Store"}
}
```

## 2) Check Status
`GET /api/v1/check-status/?activation_key=<key>&hardware_id=<hwid>`

Success Response:
```json
{
  "status": "active",
  "license_type": "yearly",
  "start_date": "2026-04-25",
  "end_date": "2027-04-25",
  "store": {"id": 1, "name": "Demo Store"}
}
```

## 3) Sync Report
`POST /api/v1/sync-report/`

Request:
```json
{
  "activation_key": "key-value",
  "hardware_id": "PC-ABC-123",
  "events": [
    {
      "client_event_id": "evt-1",
      "event_type": "z_report_sync",
      "payload": {"report_no": 991},
      "client_timestamp": "2026-04-25T05:00:00Z",
      "device_info": "Windows POS"
    }
  ]
}
```

Success Response:
```json
{"received": 1, "created": 1}
```

## Error Codes
- `400` invalid input / inactive license
- `401` missing/invalid token
- `403` hardware mismatch or invalid client key
- `404` activation key not found
- `409` uniqueness conflict (if surfaced by client_event_id)
- `429` rate limited

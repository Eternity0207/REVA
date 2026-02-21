# REVA Server API Documentation

## Base URL
`http://localhost:8002`

## Endpoints

### Health Check
`GET /api/health`

### Permissions
`GET /api/permissions`

### Save API Key
`POST /api/key`
```json
{"api_key": "gsk_..."}
```

### Screenshot
`GET /api/screenshot`

### Execute Command
`POST /api/execute`
```json
{"command": "Open Firefox"}
```

### Command History
`GET /api/history`

# REVA Server API Documentation

## Overview
Comprehensive REST API for REVA autonomous agent.

## Endpoints

### Task Management
- POST /execute - Submit task
- GET /tasks - List tasks
- GET /tasks/{id} - Get task details

### Task Control
- PATCH /tasks/{id} - Pause/resume/cancel task

### System
- GET /health - Health check
- GET /queue - Queue status

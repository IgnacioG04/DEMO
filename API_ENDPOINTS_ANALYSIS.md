# API Endpoints Analysis for External Microservices

## 📋 Executive Summary

This document analyzes which endpoints from the Face Recognition API should be exposed to external backend services (e.g., NestJS microservices) and which should remain internal.

---

## 🔍 Current Endpoints Analysis

### 1. **POST `/register`** ✅ **EXPOSE TO EXTERNAL SERVICES**

**Purpose**: Register a new user's face embedding in the system.

**Used by**:

- ✅ GUI application (`face_app_gui.py:917`)
- ✅ External services should use this

**Rate Limit**: 5 requests/minute

**Request**:

```http
POST /register
Content-Type: multipart/form-data

file: <image file>
user_id: <string>
```

**Response**:

```json
{
  "success": true,
  "message": "Rostro registrado correctamente para 1"
}
```

**Recommendation**: **EXPOSE** - This is a core business function that external services need.

---

### 2. **POST `/verify-frame`** ✅ **EXPOSE TO EXTERNAL SERVICES**

**Purpose**: Real-time frame verification - returns ALL similarities sorted, best match, and threshold. Used for real-time recognition scenarios.

**Used by**:

- ✅ GUI application (`face_app_gui.py:791`) - for real-time login
- ✅ External services that need detailed similarity data

**Rate Limit**: 30 requests/minute

**Request**:

```http
POST /verify-frame
Content-Type: multipart/form-data

file: <image file>
```

**Response**:

```json
{
  "success": true,
  "best_match": {
    "user_id": "1",
    "similarity": 0.85
  },
  "all_similarities": [
    { "user_id": "1", "similarity": 0.85 },
    { "user_id": "2", "similarity": 0.42 },
    { "user_id": "3", "similarity": 0.38 }
  ],
  "other_similarities": [
    { "user_id": "2", "similarity": 0.42 },
    { "user_id": "3", "similarity": 0.38 }
  ],
  "threshold": 0.8
}
```

**Recommendation**: **EXPOSE** - Essential for external services that need:

- Real-time video frame processing
- Multiple similarity scores for analysis
- Best match + alternative matches
- Threshold information

**Use Case**:

- Use `/verify-frame` for: Real-time recognition, detailed analysis, multiple matches, authentication flows

---

**Note**: The `/users` endpoint has been moved to an external NestJS microservice. To list users, call `http://localhost:5001/api/users` from your NestJS service.

**Note**: The `/login` endpoint has been removed. Use `/verify-frame` for all face verification needs.

---

### 3. **GET `/health`** ⚠️ **CONDITIONAL - EXPOSE FOR ORCHESTRATION**

**Purpose**: Complete health check with database, disk, memory, and cache status.

**Used by**:

- ✅ Kubernetes/Docker orchestration systems
- ✅ Monitoring tools (Prometheus, Datadog, etc.)
- ❌ Not used by GUI or business logic

**Request**:

```http
GET /health
```

**Response**:

```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "checks": {
    "database": {
      "status": "ok",
      "pool_size": 5,
      "message": "Conexión a base de datos exitosa"
    },
    "disk_space": {
      "status": "ok",
      "free_percent": 45.2,
      "message": "45.2% de espacio libre disponible"
    },
    "memory": {
      "status": "ok",
      "used_percent": 65.3,
      "message": "65.3% de memoria en uso"
    },
    "cache": {
      "status": "ok",
      "embeddings_count": 150,
      "message": "Caché activo con 150 embeddings"
    }
  }
}
```

**Recommendation**: **EXPOSE FOR ORCHESTRATION ONLY** - Not needed by business microservices, but essential for:

- Kubernetes liveness/readiness probes
- Monitoring dashboards
- Health monitoring systems

**Best Practice**: Expose on a separate port or path (e.g., `/internal/health`) or use IP whitelisting.

---

### 4. **GET `/health/live`** ⚠️ **CONDITIONAL - EXPOSE FOR ORCHESTRATION**

**Purpose**: Liveness probe - always returns OK if server is running.

**Used by**:

- ✅ Kubernetes liveness probes
- ❌ Not used by GUI or business logic

**Request**:

```http
GET /health/live
```

**Response**:

```json
{
  "status": "alive",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Recommendation**: **EXPOSE FOR ORCHESTRATION ONLY** - Same as `/health`.

---

### 5. **GET `/health/ready`** ⚠️ **CONDITIONAL - EXPOSE FOR ORCHESTRATION**

**Purpose**: Readiness probe - checks if system is ready (database must be available).

**Used by**:

- ✅ Kubernetes readiness probes
- ❌ Not used by GUI or business logic

**Request**:

```http
GET /health/ready
```

**Response (Ready)**:

```json
{
  "status": "ready",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Response (Not Ready)**:

```json
{
  "status": "not_ready",
  "reason": "Database not available",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

Status: 503

**Recommendation**: **EXPOSE FOR ORCHESTRATION ONLY** - Same as `/health`.

---

### 6. **GET `/`** ❌ **DO NOT EXPOSE (OPTIONAL)**

**Purpose**: API information endpoint - returns available endpoints and version.

**Used by**:

- ❌ Not used by GUI
- ❌ Not used by business logic
- ⚠️ Only for API documentation/discovery

**Request**:

```http
GET /
```

**Response**:

```json
{
  "name": "Sistema de Reconocimiento Facial API",
  "version": "1.0.0",
  "endpoints": {
    "register": "/register",
    "verify-frame": "/verify-frame",
    "health": "/health",
    "health_live": "/health/live",
    "health_ready": "/health/ready"
  },
  "docs": "/docs"
}
```

**Recommendation**: **OPTIONAL** - Can expose for API discovery, but not necessary for business logic. External services should know endpoints from documentation.

---

## 📊 Summary Table

| Endpoint        | Method | Expose to External?  | Use Case               | Rate Limit |
| --------------- | ------ | -------------------- | ---------------------- | ---------- |
| `/register`     | POST   | ✅ **YES**           | Register new user face | 5/min      |
| `/verify-frame` | POST   | ✅ **YES**           | Real-time recognition  | 30/min     |
| `/health`       | GET    | ⚠️ **ORCHESTRATION** | System health check    | None       |
| `/health/live`  | GET    | ⚠️ **ORCHESTRATION** | Liveness probe         | None       |
| `/health/ready` | GET    | ⚠️ **ORCHESTRATION** | Readiness probe        | None       |
| `/`             | GET    | ❌ **OPTIONAL**      | API info               | None       |

**Notes**:

- The `/users` endpoint has been moved to an external NestJS microservice at `http://localhost:5001/api/users`.
- The `/login` endpoint has been removed. Use `/verify-frame` for all face verification needs.

---

## 🎯 Recommendations for NestJS Microservice Integration

### **Core Business Endpoints to Expose** (Required):

1. **POST `/register`** - User registration
2. **POST `/verify-frame`** - Face verification and real-time recognition (use this for all authentication and verification needs)

**Notes**:

- User listing (`GET /users`) is handled by the external NestJS microservice at `http://localhost:5001/api/users`.
- The `/login` endpoint has been removed. Use `/verify-frame` for all face verification needs.

### **Using `/verify-frame` for Authentication**:

The `/verify-frame` endpoint can be used for all face verification needs:

- **For simple authentication**: Check if `best_match.similarity >= threshold` to determine success/failure
- **For real-time recognition**: Process video frames continuously
- **For detailed analysis**: Use `all_similarities` to show alternative matches
- **For threshold validation**: The response includes the `threshold` value for client-side validation

### **Health Endpoints** (For Orchestration):

If your NestJS service is running in Kubernetes/Docker:

- Expose `/health`, `/health/live`, `/health/ready` for orchestration
- Consider using IP whitelisting or separate port for security

### **Root Endpoint** (Optional):

- `/` is informational only - not needed for business logic
- Can expose for API discovery if desired

---

## 🔒 Security Considerations

1. **Rate Limiting**: All business endpoints have rate limits. Ensure your NestJS service implements retry logic with exponential backoff.

2. **Authentication**: Consider adding API key or JWT authentication if exposing to external services.

3. **Health Endpoints**: If exposing health endpoints, consider:

   - IP whitelisting
   - Separate port
   - Internal network only

4. **Error Handling**: All endpoints use custom exceptions with proper HTTP status codes. Your NestJS service should handle:
   - `400` - Validation errors
   - `401` - Authentication failures
   - `404` - User not found
   - `409` - Duplicate user
   - `500` - Internal server errors
   - `503` - Service unavailable (rate limit, health issues)

---

## 📝 Example NestJS Service Integration

```typescript
// face-recognition.service.ts
@Injectable()
export class FaceRecognitionService {
  private readonly apiUrl = process.env.FACE_RECOGNITION_API_URL;

  async registerUser(userId: string, imageFile: Express.Multer.File) {
    const formData = new FormData();
    formData.append("file", imageFile.buffer, imageFile.originalname);
    formData.append("user_id", userId);

    const response = await axios.post(`${this.apiUrl}/register`, formData, {
      headers: formData.getHeaders(),
    });

    return response.data;
  }

  async verifyFrame(imageFile: Express.Multer.File) {
    const formData = new FormData();
    formData.append("file", imageFile.buffer, imageFile.originalname);

    const response = await axios.post(`${this.apiUrl}/verify-frame`, formData, {
      headers: formData.getHeaders(),
    });

    return response.data;
  }

  // Note: User listing is handled by external NestJS microservice
  // Call http://localhost:5001/api/users from your NestJS service instead
}
```

---

## ✅ Final Recommendation

**Expose these endpoints to your NestJS microservice:**

1. ✅ `POST /register`
2. ✅ `POST /verify-frame`

**Notes**:

- `GET /users` is handled by your NestJS microservice at `http://localhost:5001/api/users` - do not call the FastAPI service for this.
- The `/login` endpoint has been removed. Use `/verify-frame` for all face verification needs.

**Conditionally expose (for orchestration):**

- ⚠️ `GET /health/*` (if using Kubernetes/Docker)

**Do not expose (not needed):**

- ❌ `GET /` (optional, informational only)

# Analysis Module API

## Versioned endpoint
- **Method:** `POST`
- **Path:** `/v1/analysis/frequency`
- **Request body:**
  ```json
  {
    "text": "To be or not to be"
  }
  ```
- **Response body:**
  ```json
  {
    "counts": {
      "to": 2,
      "be": 2,
      "or": 1,
      "not": 1
    }
  }
  ```

### Validation errors
All validation errors use FastAPI's default error payload:
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "text"],
      "msg": "text must contain at least one non-whitespace character",
      "input": "   "
    }
  ]
}
```

## Deprecated endpoint
- **Method:** `POST`
- **Path:** `/analysis/frequency`
- **Status:** Deprecated, sunset on 2025-03-31.
- **Request body:** Same as the versioned endpoint.
- **Response body:** Same as the versioned endpoint.

Use the `/v1/analysis/frequency` endpoint for all new integrations.

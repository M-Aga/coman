# Text Module API

## Versioned endpoint
- **Method:** `POST`
- **Path:** `/v1/text/uppercase`
- **Request body:**
  ```json
  {
    "text": "Hello"
  }
  ```
- **Response body:**
  ```json
  {
    "original": "Hello",
    "uppercased": "HELLO"
  }
  ```

### Validation errors
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "text"],
      "msg": "text must contain at least one visible character",
      "input": ""
    }
  ]
}
```

## Deprecated endpoint
- **Method:** `GET`
- **Path:** `/text/uppercase`
- **Status:** Deprecated, sunset on 2025-03-31.
- **Query parameters:**
  - `text` – the string to transform.
- **Response body:** Same as the versioned endpoint.

Prefer the `/v1/text/uppercase` route for all new integrations.

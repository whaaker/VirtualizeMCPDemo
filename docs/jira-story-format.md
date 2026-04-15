# Jira Story Format

For the AI agent to reliably extract all required information, structure your
Jira user story using the template below.  The agent can work from free-form
text, but a structured story reduces ambiguity and produces better results.

---

## Recommended story template

**Summary** (Jira issue title):
```
Create virtual service for <Service Name> <HTTP Method> <endpoint path>
```

**Description:**

```
## Virtual Service Specification

**Service Name:** <human-readable name, e.g. "Payment Gateway Stub">
**Base Path:** <root path, e.g. /api/v1/payments>
**Port:** <port number, e.g. 9080>

### Endpoint(s)

#### <HTTP METHOD> <path>
- **Description:** <what this endpoint does>
- **Request Content-Type:** application/json
- **Request Body Schema:**
  ```json
  {
    "field1": "string",
    "field2": 0
  }
  ```
- **Response Status:** 200
- **Response Content-Type:** application/json
- **Response Body:**
  ```json
  {
    "status": "success",
    "transactionId": "TX-001"
  }
  ```

### Acceptance Criteria
- [ ] Virtual service is reachable at http://localhost:<port><base-path>
- [ ] Returns the specified response body for a matching request
- [ ] Service remains deployed after workflow completes
```

---

## Minimal example

**Summary:** Create virtual service for Order API GET /orders/{id}

**Description:**
```
## Virtual Service Specification

**Service Name:** Order Service Stub
**Base Path:** /api/orders
**Port:** 9081

### Endpoint(s)

#### GET /api/orders/{id}
- **Description:** Returns a single order by ID
- **Response Status:** 200
- **Response Content-Type:** application/json
- **Response Body:**
  ```json
  {
    "orderId": "12345",
    "status": "SHIPPED",
    "items": []
  }
  ```

### Acceptance Criteria
- [ ] GET /api/orders/12345 returns HTTP 200 with the body above
```

---

## Notes

- You may include multiple endpoints in a single story.
- If a port is not specified, the agent will use the Virtualize default (9080).
- If a request schema is not provided, the virtual service will match any request body.
- The agent will note any assumptions it makes in the workflow summary artifact.

# Jira Story Format

Write your Jira user story as plain prose with structured bullet points. The agent
can work from free-form text, but the patterns below reduce ambiguity and produce
consistent results.

The two most important elements are a **concrete example URL with real sample
values** and a **concrete example response body**. The example URL gives the
agent the exact full path — including any deployment prefix — without inference.
The example response body is what the virtual service will literally return;
without it the agent has to guess at field names, types, and structure.

> **What is the deployment prefix?**
> Parasoft Virtualize requires every virtual service to be grouped under a
> *deployment* — an extra path segment that is prepended to the endpoint path
> the service listens on. It is a Virtualize-internal concept that is
> independent of the real API path being simulated. For example, a deployment
> of `VirtualizeMCPDemo` and an endpoint path of
> `/parabank/services/bank/requestLoan` results in the service listening at
> `/VirtualizeMCPDemo/parabank/services/bank/requestLoan`. Deployments are
> typically used to segment virtual services by team, project, or client
> application. If the story does not specify a deployment, the agent defaults
> to the repository name.

---

## Recommended story template

**Summary:** `<short noun phrase, e.g. "Request Loan" or "Get Account Balance">`

**Description:**

```
As a user, I want <what the endpoint does>, so that <the benefit to callers>.

Service Name: <camelCase or kebab-case name, used as the virtual asset name>

* Request Method: <GET | POST | PUT | PATCH | DELETE>
* Request Content-Type: <application/json | application/x-www-form-urlencoded | omit if no body>
* Request Path Parameters:           ← omit entire section if none
    * (required) <name> (<type>)
* Request URL Query Parameters:      ← omit entire section if none
    * (required) <name> (<type>)
    * (optional) <name> (<type>)
* Request Body: <empty>              ← or omit this line and use a JSON block below

<JSON code block for request body schema — omit if body is empty>

* Example: <METHOD> http://{host}:{port}/<full-path-with-sample-values>

The service should respond with the following body structure:

<JSON code block showing a representative response body>

All responses use a <200> status code. A <500> status is only returned when <condition>.
```

---

## Examples

### POST with query parameters (no request body)

Modeled directly from a story that successfully produced a working virtual service.

**Summary:** Request Loan

**Description:**
```
As a user, I want a new API endpoint that will request a loan for client
applications, so that banking integration will be easier.

Service Name: requestLoan

* Request Method: POST
* Request Content-Type: application/json
* Request URL Query Parameters:
    * (required) customerId (integer)
    * (required) amount (number)
    * (required) downPayment (number)
    * (required) fromAccountId (integer)
* Request Body: empty
* Example: POST http://{host}:{port}/parabank/services/bank/requestLoan?customerId=12212&amount=1000.00&downPayment=100.00&fromAccountId=13344

The loan provider service should respond with the following body structure:

{
    "responseDate": "2026-04-15T22:30:56.360Z",
    "loanProviderName": "Acme Loan Company",
    "approved": true,
    "message": "Approved",
    "accountId": 13344
}

All responses, including ones where a loan is not approved, should use a 200 status
code. A 500 Internal Server Error response is only used when input validation fails.
```

---

### GET with path parameter

**Summary:** Get Account by ID

**Description:**
```
As a user, I want to retrieve account details by account ID, so that client
applications can display account information.

Service Name: getAccount

* Request Method: GET
* Request Path Parameters:
    * (required) accountId (integer)
* Request Body: empty
* Example: GET http://{host}:{port}/parabank/services/bank/accounts/12345

The service should respond with the following body structure:

{
    "id": 12345,
    "customerId": 12212,
    "type": "CHECKING",
    "balance": 1500.00
}

All responses use a 200 status code.
```

---

### POST with JSON request body

**Summary:** Create Customer

**Description:**
```
As a user, I want to create a new customer record, so that new accounts can
be opened.

Service Name: createCustomer

* Request Method: POST
* Request Content-Type: application/json
* Request Body:

{
    "firstName": "John",
    "lastName": "Doe",
    "address": "123 Main St",
    "city": "Anytown",
    "state": "OH",
    "zipCode": "12345",
    "phoneNumber": "555-1234",
    "ssn": "123-45-6789",
    "username": "johndoe",
    "password": "secret"
}

* Example: POST http://{host}:{port}/parabank/services/bank/customers/new

The service should respond with the following body structure:

{
    "id": 12345,
    "firstName": "John",
    "lastName": "Doe"
}

All responses use a 201 status code on success.
```

---

## Notes

- **Example URL is critical.** It lets the agent know the exact full endpoint
  path without guessing. Always include it with real sample values. Note that
  the example URL should reflect the *real* API path only — do **not** include
  the Virtualize deployment prefix in the example URL. The agent adds the
  deployment prefix automatically and reports the full deployed URL in the
  workflow log.
- **Example response body is equally critical.** It is the literal payload the
  virtual service will return. Without it the agent must infer field names,
  types, and nesting — which produces unreliable results. Always include a
  representative JSON (or other content-type) response body with real sample
  values.
- **Omit sections that don't apply.** A GET with only a path parameter doesn't
  need a query parameters section or a request body.
- **Service Name** is used by Virtualize as the virtual asset name. Use camelCase
  or kebab-case and keep it concise.
- **Port is optional.** If not specified, the agent defaults to port `38000`.
- **Deployment prefix is optional.** If not specified, the agent defaults to
  the repository name. You can specify one by adding a line to your story:
  `Deployment: <your-prefix>`. Use it to group virtual services by team,
  project, or client application (e.g. `Deployment: TeamA` or
  `Deployment: ParabankDemo`).
- **Multiple endpoints** can be described in a single story by repeating the
  bullet pattern for each method/path combination.
- The agent will note any assumptions it makes in the workflow step log.


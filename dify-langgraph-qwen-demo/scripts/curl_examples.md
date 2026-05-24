# Curl Examples for Testing Agent Backend

Use these curl examples to test the FastAPI agent backend endpoints manually.

## 1. Health Check

Verify if the server is running and configured correctly:

```bash
curl -X GET http://localhost:8000/health
```

**Expected Response:**

```json
{
  "status": "healthy",
  "model_configured": "qwen14b",
  "base_url": "http://localhost:8001/v1"
}
```

## 2. Quality Analysis Scenario

Test the multi-agent workflow for a manufacturing quality issue. This trigger will classify the task as `quality_analysis`, perform reasoning, and output a structured report.

```bash
curl -X POST http://localhost:8000/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "query": "A batch of machined parts has an outer diameter deviation of +0.05mm. The machine is CNC-01, the material is 45 steel, and the cutting tool was recently replaced. Please analyze possible causes and provide troubleshooting steps.",
    "user_id": "demo_user",
    "context": {}
  }'
```

## 3. Knowledge Base Query (Document QA Scenario)

Test a query that triggers the document QA flow.

```bash
curl -X POST http://localhost:8000/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Please search the standard operating manual for the maintenance schedule of CNC-01.",
    "user_id": "demo_user",
    "context": {}
  }'
```

## 4. General Chat Scenario

Test a general greeting or non-manufacturing chat query.

```bash
curl -X POST http://localhost:8000/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Hello! What can you help me with today?",
    "user_id": "demo_user",
    "context": {}
  }'
```

# Background Processing for Ticker Generation

This document describes the background processing capabilities added to the ticker generation API.

## Features

- **Parallel Processing**: Multiple ticker requests are processed simultaneously using a thread pool
- **Background Jobs**: Long-running requests can be processed asynchronously
- **Job Tracking**: Real-time status tracking for background jobs
- **Graceful Shutdown**: Proper cleanup of threads on application shutdown

## Configuration

Set the maximum number of parallel workers using the environment variable:

```bash
export MAX_WORKERS=5  # Default is 5
```

## API Endpoints

### 1. Process Generation Requests

#### Synchronous Processing (Original Behavior)

```http
POST /api/ticker-v1/generate-reports/process-generation-requests
Content-Type: application/json

{}
```

#### Background Processing

```http
POST /api/ticker-v1/generate-reports/process-generation-requests
Content-Type: application/json

{
  "background": true
}
```

**Response (Background):**

```json
{
  "success": true,
  "message": "Started background processing of 3 requests",
  "job_id": "12345678-1234-1234-1234-123456789abc",
  "background": true,
  "total_requests": 3,
  "ticker_symbols": ["AAPL", "GOOGL", "MSFT"]
}
```

### 2. Get Job Status

```http
GET /api/ticker-v1/generate-reports/job-status/{job_id}
```

**Response:**

```json
{
  "success": true,
  "job_id": "12345678-1234-1234-1234-123456789abc",
  "status": "Running",
  "created_at": "2025-10-14T10:30:00.000000",
  "updated_at": "2025-10-14T10:32:15.000000",
  "total_requests": 3,
  "completed_requests": 2,
  "failed_requests": 0,
  "progress_percentage": 66.67,
  "ticker_symbols": ["AAPL", "GOOGL", "MSFT"],
  "results": [
    {
      "request_id": "req_1",
      "ticker_symbol": "AAPL",
      "status": "Completed",
      "steps_completed": ["competition", "financial-analysis"],
      "failed_steps": [],
      "completed_at": "2025-10-14T10:31:30.000000"
    }
  ]
}
```

### 3. List All Jobs

```http
GET /api/ticker-v1/generate-reports/jobs
```

**Response:**

```json
{
  "success": true,
  "jobs": [
    {
      "job_id": "12345678-1234-1234-1234-123456789abc",
      "status": "Completed",
      "created_at": "2025-10-14T10:30:00.000000",
      "updated_at": "2025-10-14T10:35:00.000000",
      "finished_at": "2025-10-14T10:35:00.000000",
      "total_requests": 3,
      "completed_requests": 3,
      "failed_requests": 0,
      "progress_percentage": 100.0,
      "ticker_symbols": ["AAPL", "GOOGL", "MSFT"]
    }
  ],
  "total_jobs": 1
}
```

### 4. Cleanup Old Jobs

```http
POST /api/ticker-v1/generate-reports/cleanup-jobs
Content-Type: application/json

{
  "max_age_hours": 24
}
```

**Response:**

```json
{
  "success": true,
  "message": "Cleaned up 5 old jobs",
  "cleaned_jobs": 5
}
```

## Job Statuses

### Background Job Statuses

- `Queued`: Job is queued for processing
- `Running`: Job is currently being processed
- `Completed`: Job completed (may include some failed individual requests)
- `Failed`: Job failed due to system error

### Individual Request Statuses

- `NotStarted`: Request not yet started
- `InProgress`: Request is being processed
- `Completed`: Request completed successfully
- `Failed`: Request failed

## Usage Examples

### Python Client Example

```python
import requests
import time

# Start background processing
response = requests.post(
    'http://localhost:5000/api/ticker-v1/generate-reports/process-generation-requests',
    json={'background': True}
)

if response.status_code == 202:
    job_data = response.json()
    job_id = job_data['job_id']
    print(f"Started job {job_id}")

    # Poll for status
    while True:
        status_response = requests.get(
            f'http://localhost:5000/api/ticker-v1/generate-reports/job-status/{job_id}'
        )

        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"Progress: {status_data['progress_percentage']}%")

            if status_data['status'] in ['Completed', 'Failed']:
                print(f"Job {status_data['status'].lower()}")
                break

        time.sleep(5)  # Poll every 5 seconds
```

### JavaScript/TypeScript Client Example

```typescript
interface JobStatus {
  job_id: string;
  status: string;
  progress_percentage: number;
  completed_requests: number;
  total_requests: number;
}

async function processTickersInBackground() {
  // Start background job
  const response = await fetch(
    "/api/ticker-v1/generate-reports/process-generation-requests",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ background: true }),
    }
  );

  if (response.status === 202) {
    const jobData = await response.json();
    const jobId = jobData.job_id;

    console.log(`Started job ${jobId}`);

    // Poll for status
    const pollStatus = async () => {
      const statusResponse = await fetch(
        `/api/ticker-v1/generate-reports/job-status/${jobId}`
      );

      if (statusResponse.ok) {
        const status: JobStatus = await statusResponse.json();
        console.log(`Progress: ${status.progress_percentage}%`);

        if (status.status === "Completed" || status.status === "Failed") {
          console.log(`Job ${status.status.toLowerCase()}`);
          return;
        }

        // Continue polling
        setTimeout(pollStatus, 5000);
      }
    };

    pollStatus();
  }
}
```

## Performance Considerations

1. **Thread Pool Size**: Adjust `MAX_WORKERS` based on your server's resources and the backend API limits
2. **Memory Usage**: Job status is stored in memory; use cleanup endpoint to remove old jobs
3. **Timeout Handling**: Individual API calls have 300-second timeouts
4. **Graceful Shutdown**: The application will wait for running jobs to complete on shutdown

## Monitoring and Troubleshooting

1. **Check Job Status**: Use the job status endpoint to monitor progress
2. **View Logs**: Check application logs for detailed processing information
3. **List Active Jobs**: Use the jobs endpoint to see all current jobs
4. **Clean Up**: Regularly clean up old completed jobs to free memory

## Migration from Synchronous Processing

Existing clients will continue to work without changes. To enable background processing, simply add `"background": true` to the request body.

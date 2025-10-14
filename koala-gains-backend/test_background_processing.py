#!/usr/bin/env python3
"""
Test script for the background processing functionality
"""

import requests
import time
import json


def test_background_processing():
    """Test the background processing functionality"""
    base_url = "http://localhost:5000/api/ticker-v1/generate-reports"
    
    print("Testing Background Ticker Processing API")
    print("=" * 50)
    
    # Test 1: Start background processing
    print("\n1. Starting background processing...")
    response = requests.post(
        f"{base_url}/process-generation-requests",
        json={"background": True},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 202:
        job_data = response.json()
        job_id = job_data.get("job_id")
        print(f"✓ Background job started successfully")
        print(f"  Job ID: {job_id}")
        print(f"  Total requests: {job_data.get('total_requests', 0)}")
        print(f"  Ticker symbols: {job_data.get('ticker_symbols', [])}")
        
        # Test 2: Monitor job progress
        print(f"\n2. Monitoring job progress...")
        while True:
            status_response = requests.get(f"{base_url}/job-status/{job_id}")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get("status")
                progress = status_data.get("progress_percentage", 0)
                completed = status_data.get("completed_requests", 0)
                failed = status_data.get("failed_requests", 0)
                total = status_data.get("total_requests", 0)
                
                print(f"  Status: {status} | Progress: {progress}% | Completed: {completed}/{total} | Failed: {failed}")
                
                if status in ["Completed", "Failed"]:
                    print(f"✓ Job {status.lower()}")
                    break
                    
            else:
                print(f"✗ Error checking job status: {status_response.status_code}")
                break
                
            time.sleep(2)  # Check every 2 seconds for demo
            
    elif response.status_code == 200:
        # No pending requests
        result_data = response.json()
        print(f"✓ No pending requests to process")
        print(f"  Message: {result_data.get('message')}")
        
        # Test with synchronous processing instead
        print(f"\n  Testing synchronous processing...")
        sync_response = requests.post(
            f"{base_url}/process-generation-requests",
            json={},
            headers={"Content-Type": "application/json"}
        )
        
        if sync_response.status_code == 200:
            sync_data = sync_response.json()
            print(f"  ✓ Synchronous processing completed")
            print(f"    Processed: {sync_data.get('processed_count', 0)}")
            print(f"    Successful: {sync_data.get('successful', 0)}")
            print(f"    Failed: {sync_data.get('failed', 0)}")
        else:
            print(f"  ✗ Synchronous processing failed: {sync_response.status_code}")
            
    else:
        print(f"✗ Failed to start background processing: {response.status_code}")
        print(f"  Response: {response.text}")
        return
    
    # Test 3: List all jobs
    print(f"\n3. Listing all jobs...")
    jobs_response = requests.get(f"{base_url}/jobs")
    
    if jobs_response.status_code == 200:
        jobs_data = jobs_response.json()
        total_jobs = jobs_data.get("total_jobs", 0)
        print(f"✓ Found {total_jobs} jobs")
        
        for job in jobs_data.get("jobs", [])[:3]:  # Show first 3 jobs
            print(f"  Job {job.get('job_id')[:8]}... | Status: {job.get('status')} | Progress: {job.get('progress_percentage', 0)}%")
            
    else:
        print(f"✗ Failed to list jobs: {jobs_response.status_code}")
    
    # Test 4: Cleanup old jobs (optional)
    print(f"\n4. Testing job cleanup...")
    cleanup_response = requests.post(
        f"{base_url}/cleanup-jobs",
        json={"max_age_hours": 0.01},  # Clean jobs older than ~36 seconds for demo
        headers={"Content-Type": "application/json"}
    )
    
    if cleanup_response.status_code == 200:
        cleanup_data = cleanup_response.json()
        print(f"✓ Cleanup completed")
        print(f"  Cleaned jobs: {cleanup_data.get('cleaned_jobs', 0)}")
    else:
        print(f"✗ Failed to cleanup jobs: {cleanup_response.status_code}")
    
    print(f"\n" + "=" * 50)
    print("Test completed!")


if __name__ == "__main__":
    try:
        test_background_processing()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to the server.")
        print("  Make sure the Flask application is running on http://localhost:5000")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
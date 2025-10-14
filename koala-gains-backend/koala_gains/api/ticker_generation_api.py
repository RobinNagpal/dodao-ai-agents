from flask import Blueprint, jsonify, request
import requests
import logging
from typing import Dict, List, Optional
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import uuid
from collections import defaultdict
import time

ticker_generation_api = Blueprint('ticker_generation_api', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Next.js backend URL from environment
NEXTJS_BACKEND_URL = os.getenv('KOALAGAINS_BACKEND_URL', 'http://localhost:3000')
SPACE_ID = 'koala_gains'

# Background job management
MAX_WORKERS = int(os.getenv('MAX_WORKERS', '5'))  # Maximum number of parallel threads
job_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix='ticker_gen')
job_status = defaultdict(dict)  # Store job statuses by job_id
job_lock = threading.Lock()  # Thread-safe access to job_status

# Status enum matching the Next.js backend
class GenerationRequestStatus:
    NOT_STARTED = 'NotStarted'
    IN_PROGRESS = 'InProgress'
    COMPLETED = 'Completed'
    FAILED = 'Failed'

# Background job status
class BackgroundJobStatus:
    QUEUED = 'Queued'
    RUNNING = 'Running'
    COMPLETED = 'Completed'
    FAILED = 'Failed'


def update_job_status(job_id: str, status: str, details: Optional[Dict] = None):
    """Update background job status in thread-safe manner"""
    with job_lock:
        job_status[job_id]['status'] = status
        job_status[job_id]['updated_at'] = datetime.now().isoformat()
        if details:
            job_status[job_id].update(details)


def get_job_status(job_id: str) -> Optional[Dict]:
    """Get background job status"""
    with job_lock:
        return job_status.get(job_id, None)


def create_job(job_id: str, requests_count: int, ticker_symbols: List[str]) -> Dict:
    """Create a new background job entry"""
    job_info = {
        'job_id': job_id,
        'status': BackgroundJobStatus.QUEUED,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'total_requests': requests_count,
        'completed_requests': 0,
        'failed_requests': 0,
        'ticker_symbols': ticker_symbols,
        'results': []
    }
    
    with job_lock:
        job_status[job_id] = job_info
    
    return job_info

# Investor keys mapping
INVESTOR_KEYS = {
    'WARREN_BUFFETT': 'WARREN_BUFFETT',
    'CHARLIE_MUNGER': 'CHARLIE_MUNGER',
    'BILL_ACKMAN': 'BILL_ACKMAN'
}


def update_request_status(request_id: str, ticker_symbol: str, status: str) -> bool:
    """Update the generation request status"""
    try:
        url = f"{NEXTJS_BACKEND_URL}/api/{SPACE_ID}/tickers-v1/{ticker_symbol}/update-request-status"
        payload = {
            'id': request_id,
            'status': status
        }
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        logger.info(f"Updated request {request_id} status to {status}")
        return True
    except Exception as e:
        logger.error(f"Failed to update request status: {str(e)}")
        return False


def call_analysis_api(ticker_symbol: str, endpoint: str, payload: Optional[Dict] = None) -> bool:
    """Generic function to call analysis APIs"""
    try:
        url = f"{NEXTJS_BACKEND_URL}/api/{SPACE_ID}/tickers-v1/{ticker_symbol}/{endpoint}"
        logger.info(f"Calling API: {url}")
        
        if payload:
            response = requests.post(url, json=payload, timeout=300)
        else:
            response = requests.post(url, timeout=300)
        
        response.raise_for_status()
        result = response.json()
        logger.info(f"Successfully completed {endpoint} for {ticker_symbol}")
        return True
    except Exception as e:
        logger.error(f"Failed to call {endpoint} for {ticker_symbol}: {str(e)}")
        return False


def process_single_request(generation_request: Dict, job_id: Optional[str] = None) -> Dict:
    """Process a single generation request"""
    request_id = generation_request['id']
    ticker_symbol = generation_request['ticker']['symbol']
    
    logger.info(f"Processing generation request {request_id} for ticker {ticker_symbol}")
    
    # Update status to InProgress
    update_request_status(request_id, ticker_symbol, GenerationRequestStatus.IN_PROGRESS)
    
    analysis_steps = []
    failed_steps = []
    
    try:
        # Step 1: Competition Analysis (if needed)
        if generation_request.get('regenerateCompetition', False):
            analysis_steps.append('competition')
            if not call_analysis_api(ticker_symbol, 'competition'):
                failed_steps.append('competition')
        
        # Step 2: Financial Analysis (if needed)
        if generation_request.get('regenerateFinancialAnalysis', False):
            analysis_steps.append('financial-analysis')
            if not call_analysis_api(ticker_symbol, 'financial-analysis'):
                failed_steps.append('financial-analysis')
        
        # Step 3: Business and Moat (if needed)
        if generation_request.get('regenerateBusinessAndMoat', False):
            analysis_steps.append('business-and-moat')
            if not call_analysis_api(ticker_symbol, 'business-and-moat'):
                failed_steps.append('business-and-moat')
        
        # Step 4: Past Performance (if needed)
        if generation_request.get('regeneratePastPerformance', False):
            analysis_steps.append('past-performance')
            if not call_analysis_api(ticker_symbol, 'past-performance'):
                failed_steps.append('past-performance')
        
        # Step 5: Future Growth (if needed)
        if generation_request.get('regenerateFutureGrowth', False):
            analysis_steps.append('future-growth')
            if not call_analysis_api(ticker_symbol, 'future-growth'):
                failed_steps.append('future-growth')
        
        # Step 6: Fair Value (if needed)
        if generation_request.get('regenerateFairValue', False):
            analysis_steps.append('fair-value')
            if not call_analysis_api(ticker_symbol, 'fair-value'):
                failed_steps.append('fair-value')
        
        # Step 7: Future Risk (if needed)
        if generation_request.get('regenerateFutureRisk', False):
            analysis_steps.append('future-risk')
            if not call_analysis_api(ticker_symbol, 'future-risk'):
                failed_steps.append('future-risk')
        
        # Step 8: Warren Buffett Analysis (if needed)
        if generation_request.get('regenerateWarrenBuffett', False):
            analysis_steps.append('investor-analysis-warren-buffett')
            payload = {'investorKey': INVESTOR_KEYS['WARREN_BUFFETT']}
            if not call_analysis_api(ticker_symbol, 'investor-analysis', payload):
                failed_steps.append('investor-analysis-warren-buffett')
        
        # Step 9: Charlie Munger Analysis (if needed)
        if generation_request.get('regenerateCharlieMunger', False):
            analysis_steps.append('investor-analysis-charlie-munger')
            payload = {'investorKey': INVESTOR_KEYS['CHARLIE_MUNGER']}
            if not call_analysis_api(ticker_symbol, 'investor-analysis', payload):
                failed_steps.append('investor-analysis-charlie-munger')
        
        # Step 10: Bill Ackman Analysis (if needed)
        if generation_request.get('regenerateBillAckman', False):
            analysis_steps.append('investor-analysis-bill-ackman')
            payload = {'investorKey': INVESTOR_KEYS['BILL_ACKMAN']}
            if not call_analysis_api(ticker_symbol, 'investor-analysis', payload):
                failed_steps.append('investor-analysis-bill-ackman')
        
        # Step 11: Final Summary (if needed)
        if generation_request.get('regenerateFinalSummary', False):
            analysis_steps.append('final-summary')
            if not call_analysis_api(ticker_symbol, 'final-summary'):
                failed_steps.append('final-summary')
        
        # Step 12: Cached Score (if needed)
        if generation_request.get('regenerateCachedScore', False):
            analysis_steps.append('cached-score')
            if not call_analysis_api(ticker_symbol, 'cached-score'):
                failed_steps.append('cached-score')
        
        # Determine final status
        if failed_steps:
            final_status = GenerationRequestStatus.FAILED
            logger.error(f"Request {request_id} completed with failures: {failed_steps}")
        else:
            final_status = GenerationRequestStatus.COMPLETED
            logger.info(f"Request {request_id} completed successfully")
        
        # Update final status
        update_request_status(request_id, ticker_symbol, final_status)
        
        result = {
            'request_id': request_id,
            'ticker_symbol': ticker_symbol,
            'status': final_status,
            'steps_completed': analysis_steps,
            'failed_steps': failed_steps,
            'completed_at': datetime.now().isoformat()
        }
        
        # Update job status if part of background job
        if job_id:
            with job_lock:
                if job_id in job_status:
                    job_status[job_id]['results'].append(result)
                    if final_status == GenerationRequestStatus.COMPLETED:
                        job_status[job_id]['completed_requests'] += 1
                    else:
                        job_status[job_id]['failed_requests'] += 1
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing request {request_id}: {str(e)}")
        update_request_status(request_id, ticker_symbol, GenerationRequestStatus.FAILED)
        
        result = {
            'request_id': request_id,
            'ticker_symbol': ticker_symbol,
            'status': GenerationRequestStatus.FAILED,
            'error': str(e),
            'completed_at': datetime.now().isoformat()
        }
        
        # Update job status if part of background job
        if job_id:
            with job_lock:
                if job_id in job_status:
                    job_status[job_id]['results'].append(result)
                    job_status[job_id]['failed_requests'] += 1
        
        return result


def process_requests_background(requests_to_process: List[Dict], job_id: str):
    """Process multiple requests in background with parallel execution"""
    logger.info(f"Starting background job {job_id} with {len(requests_to_process)} requests")
    
    # Update job status to running
    update_job_status(job_id, BackgroundJobStatus.RUNNING)
    
    try:
        # Submit all requests to thread pool
        future_to_request = {}
        
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(requests_to_process))) as executor:
            for gen_request in requests_to_process:
                future = executor.submit(process_single_request, gen_request, job_id)
                future_to_request[future] = gen_request
            
            # Process completed futures as they finish
            for future in as_completed(future_to_request):
                gen_request = future_to_request[future]
                try:
                    result = future.result()
                    logger.info(f"Completed processing request {result['request_id']} for ticker {result['ticker_symbol']}")
                except Exception as e:
                    logger.error(f"Error processing request {gen_request['id']}: {str(e)}")
        
        # Determine final job status
        with job_lock:
            if job_id in job_status:
                job_info = job_status[job_id]
                total_processed = job_info['completed_requests'] + job_info['failed_requests']
                
                if total_processed == job_info['total_requests']:
                    if job_info['failed_requests'] == 0:
                        final_status = BackgroundJobStatus.COMPLETED
                    else:
                        final_status = BackgroundJobStatus.COMPLETED  # Completed with some failures
                else:
                    final_status = BackgroundJobStatus.FAILED
                
                update_job_status(job_id, final_status, {
                    'finished_at': datetime.now().isoformat()
                })
        
        logger.info(f"Background job {job_id} completed")
        
    except Exception as e:
        logger.error(f"Error in background job {job_id}: {str(e)}")
        update_job_status(job_id, BackgroundJobStatus.FAILED, {
            'error': str(e),
            'finished_at': datetime.now().isoformat()
        })


@ticker_generation_api.route('/process-generation-requests', methods=['POST'])
def process_generation_requests():
    """Main endpoint to process generation requests"""
    try:
        # Check if background processing is requested
        request_data = request.get_json() or {}
        background = request_data.get('background', False)
        
        # Fetch pending generation requests from Next.js backend
        url = f"{NEXTJS_BACKEND_URL}/api/{SPACE_ID}/tickers-v1/get-generation-requests"
        logger.info(f"Fetching generation requests from: {url}")
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        requests_to_process = data.get('requests', [])
        
        if not requests_to_process:
            return jsonify({
                'success': True,
                'message': 'No pending requests to process',
                'processed_count': 0
            }), 200
        
        logger.info(f"Found {len(requests_to_process)} requests to process")
        
        if background:
            # Process in background
            job_id = str(uuid.uuid4())
            ticker_symbols = [req['ticker']['symbol'] for req in requests_to_process]
            
            # Create job entry
            job_info = create_job(job_id, len(requests_to_process), ticker_symbols)
            
            # Submit to background processing
            job_executor.submit(process_requests_background, requests_to_process, job_id)
            
            return jsonify({
                'success': True,
                'message': f'Started background processing of {len(requests_to_process)} requests',
                'job_id': job_id,
                'background': True,
                'total_requests': len(requests_to_process),
                'ticker_symbols': ticker_symbols
            }), 202  # 202 Accepted for async processing
            
        else:
            # Process synchronously (original behavior)
            results = []
            for gen_request in requests_to_process:
                result = process_single_request(gen_request)
                results.append(result)
            
            # Count successes and failures
            successful = sum(1 for r in results if r['status'] == GenerationRequestStatus.COMPLETED)
            failed = sum(1 for r in results if r['status'] == GenerationRequestStatus.FAILED)
            
            return jsonify({
                'success': True,
                'processed_count': len(results),
                'successful': successful,
                'failed': failed,
                'results': results,
                'background': False
            }), 200
        
    except Exception as e:
        logger.error(f"Error in process_generation_requests: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ticker_generation_api.route('/job-status/<job_id>', methods=['GET'])
def get_job_status_endpoint(job_id: str):
    """Get the status of a background job"""
    try:
        job_info = get_job_status(job_id)
        
        if not job_info:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404
        
        # Calculate progress percentage
        total = job_info.get('total_requests', 0)
        completed = job_info.get('completed_requests', 0)
        failed = job_info.get('failed_requests', 0)
        processed = completed + failed
        progress = (processed / total * 100) if total > 0 else 0
        
        response_data = {
            'success': True,
            'job_id': job_id,
            'status': job_info.get('status'),
            'created_at': job_info.get('created_at'),
            'updated_at': job_info.get('updated_at'),
            'finished_at': job_info.get('finished_at'),
            'total_requests': total,
            'completed_requests': completed,
            'failed_requests': failed,
            'progress_percentage': round(progress, 2),
            'ticker_symbols': job_info.get('ticker_symbols', []),
            'results': job_info.get('results', [])
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ticker_generation_api.route('/jobs', methods=['GET'])
def list_jobs():
    """List all background jobs"""
    try:
        with job_lock:
            jobs_list = []
            for job_id, job_info in job_status.items():
                total = job_info.get('total_requests', 0)
                completed = job_info.get('completed_requests', 0)
                failed = job_info.get('failed_requests', 0)
                processed = completed + failed
                progress = (processed / total * 100) if total > 0 else 0
                
                jobs_list.append({
                    'job_id': job_id,
                    'status': job_info.get('status'),
                    'created_at': job_info.get('created_at'),
                    'updated_at': job_info.get('updated_at'),
                    'finished_at': job_info.get('finished_at'),
                    'total_requests': total,
                    'completed_requests': completed,
                    'failed_requests': failed,
                    'progress_percentage': round(progress, 2),
                    'ticker_symbols': job_info.get('ticker_symbols', [])
                })
        
        # Sort by creation time (newest first)
        jobs_list.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'success': True,
            'jobs': jobs_list,
            'total_jobs': len(jobs_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ticker_generation_api.route('/cleanup-jobs', methods=['POST'])
def cleanup_old_jobs():
    """Clean up old completed/failed jobs (older than 24 hours)"""
    try:
        request_data = request.get_json() or {}
        max_age_hours = request_data.get('max_age_hours', 24)
        
        current_time = datetime.now()
        cleanup_count = 0
        
        with job_lock:
            jobs_to_remove = []
            for job_id, job_info in job_status.items():
                job_status_val = job_info.get('status')
                if job_status_val in [BackgroundJobStatus.COMPLETED, BackgroundJobStatus.FAILED]:
                    created_at_str = job_info.get('created_at')
                    if created_at_str:
                        try:
                            created_at = datetime.fromisoformat(created_at_str)
                            age_hours = (current_time - created_at).total_seconds() / 3600
                            if age_hours > max_age_hours:
                                jobs_to_remove.append(job_id)
                        except ValueError:
                            # Invalid datetime format, remove it
                            jobs_to_remove.append(job_id)
            
            # Remove old jobs
            for job_id in jobs_to_remove:
                del job_status[job_id]
                cleanup_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {cleanup_count} old jobs',
            'cleaned_jobs': cleanup_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error cleaning up jobs: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
from flask import Blueprint, jsonify, request
import requests
import logging
from typing import Dict, List, Optional
import os
import threading

ticker_generation_api = Blueprint('ticker_generation_api', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Next.js backend URL from environment
NEXTJS_BACKEND_URL = os.getenv('KOALAGAINS_BACKEND_URL', 'http://localhost:3000')
SPACE_ID = 'koala_gains'

# Status enum matching the Next.js backend
class GenerationRequestStatus:
    NOT_STARTED = 'NotStarted'
    IN_PROGRESS = 'InProgress'
    COMPLETED = 'Completed'
    FAILED = 'Failed'

# Investor keys mapping
INVESTOR_KEYS = {
    'WARREN_BUFFETT': 'WARREN_BUFFETT',
    'CHARLIE_MUNGER': 'CHARLIE_MUNGER',
    'BILL_ACKMAN': 'BILL_ACKMAN'
}


def update_request_status(request_id: str, ticker_symbol: str, status: str, completed_steps: List[str] = None, failed_steps: List[str] = None, mark_started: bool = False, mark_completed: bool = False) -> bool:
    """Update the generation request status"""
    try:
        url = f"{NEXTJS_BACKEND_URL}/api/{SPACE_ID}/tickers-v1/{ticker_symbol}/update-request-status"
        payload = {
            'id': request_id,
            'status': status
        }
        
        # Add completed and failed steps to payload if provided
        if completed_steps is not None:
            payload['completed_steps'] = completed_steps
        if failed_steps is not None:
            payload['failed_steps'] = failed_steps
        
        # Add timestamp indicators if provided
        if mark_started:
            payload['mark_started'] = True
        if mark_completed:
            payload['mark_completed'] = True
            
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


def process_single_request(generation_request: Dict) -> Dict:
    """Process a single generation request"""
    request_id = generation_request['id']
    ticker_symbol = generation_request['ticker']['symbol']
    
    logger.info(f"Processing generation request {request_id} for ticker {ticker_symbol}")
    
    # Update status to InProgress and mark as started
    update_request_status(request_id, ticker_symbol, GenerationRequestStatus.IN_PROGRESS, mark_started=True)
    
    completed_steps = []
    failed_steps = []
    
    try:
        # Step 1: Competition Analysis (if needed)
        if generation_request.get('regenerateCompetition', False):
            if call_analysis_api(ticker_symbol, 'competition'):
                completed_steps.append('competition')
            else:
                failed_steps.append('competition')
            update_request_status(request_id, ticker_symbol, GenerationRequestStatus.IN_PROGRESS, completed_steps, failed_steps)
        
        # Step 2: Financial Analysis (if needed)
        if generation_request.get('regenerateFinancialAnalysis', False):
            if call_analysis_api(ticker_symbol, 'financial-analysis'):
                completed_steps.append('financial-analysis')
            else:
                failed_steps.append('financial-analysis')
            update_request_status(request_id, ticker_symbol, GenerationRequestStatus.IN_PROGRESS, completed_steps, failed_steps)
        
        # Step 3: Business and Moat (if needed)
        if generation_request.get('regenerateBusinessAndMoat', False):
            if call_analysis_api(ticker_symbol, 'business-and-moat'):
                completed_steps.append('business-and-moat')
            else:
                failed_steps.append('business-and-moat')
            update_request_status(request_id, ticker_symbol, GenerationRequestStatus.IN_PROGRESS, completed_steps, failed_steps)
        
        # Step 4: Past Performance (if needed)
        if generation_request.get('regeneratePastPerformance', False):
            if call_analysis_api(ticker_symbol, 'past-performance'):
                completed_steps.append('past-performance')
            else:
                failed_steps.append('past-performance')
            update_request_status(request_id, ticker_symbol, GenerationRequestStatus.IN_PROGRESS, completed_steps, failed_steps)
        
        # Step 5: Future Growth (if needed)
        if generation_request.get('regenerateFutureGrowth', False):
            if call_analysis_api(ticker_symbol, 'future-growth'):
                completed_steps.append('future-growth')
            else:
                failed_steps.append('future-growth')
            update_request_status(request_id, ticker_symbol, GenerationRequestStatus.IN_PROGRESS, completed_steps, failed_steps)
        
        # Step 6: Fair Value (if needed)
        if generation_request.get('regenerateFairValue', False):
            if call_analysis_api(ticker_symbol, 'fair-value'):
                completed_steps.append('fair-value')
            else:
                failed_steps.append('fair-value')
            update_request_status(request_id, ticker_symbol, GenerationRequestStatus.IN_PROGRESS, completed_steps, failed_steps)
        
        # Step 7: Future Risk (if needed)
        if generation_request.get('regenerateFutureRisk', False):
            if call_analysis_api(ticker_symbol, 'future-risk'):
                completed_steps.append('future-risk')
            else:
                failed_steps.append('future-risk')
            update_request_status(request_id, ticker_symbol, GenerationRequestStatus.IN_PROGRESS, completed_steps, failed_steps)
        
        # Step 8: Warren Buffett Analysis (if needed)
        if generation_request.get('regenerateWarrenBuffett', False):
            payload = {'investorKey': INVESTOR_KEYS['WARREN_BUFFETT']}
            if call_analysis_api(ticker_symbol, 'investor-analysis', payload):
                completed_steps.append('investor-analysis-warren-buffett')
            else:
                failed_steps.append('investor-analysis-warren-buffett')
            update_request_status(request_id, ticker_symbol, GenerationRequestStatus.IN_PROGRESS, completed_steps, failed_steps)
        
        # Step 9: Charlie Munger Analysis (if needed)
        if generation_request.get('regenerateCharlieMunger', False):
            payload = {'investorKey': INVESTOR_KEYS['CHARLIE_MUNGER']}
            if call_analysis_api(ticker_symbol, 'investor-analysis', payload):
                completed_steps.append('investor-analysis-charlie-munger')
            else:
                failed_steps.append('investor-analysis-charlie-munger')
            update_request_status(request_id, ticker_symbol, GenerationRequestStatus.IN_PROGRESS, completed_steps, failed_steps)
        
        # Step 10: Bill Ackman Analysis (if needed)
        if generation_request.get('regenerateBillAckman', False):
            payload = {'investorKey': INVESTOR_KEYS['BILL_ACKMAN']}
            if call_analysis_api(ticker_symbol, 'investor-analysis', payload):
                completed_steps.append('investor-analysis-bill-ackman')
            else:
                failed_steps.append('investor-analysis-bill-ackman')
            update_request_status(request_id, ticker_symbol, GenerationRequestStatus.IN_PROGRESS, completed_steps, failed_steps)
        
        # Step 11: Final Summary (if needed)
        if generation_request.get('regenerateFinalSummary', False):
            if call_analysis_api(ticker_symbol, 'final-summary'):
                completed_steps.append('final-summary')
            else:
                failed_steps.append('final-summary')
            update_request_status(request_id, ticker_symbol, GenerationRequestStatus.IN_PROGRESS, completed_steps, failed_steps)
        
        # Step 12: Cached Score (if needed)
        if generation_request.get('regenerateCachedScore', False):
            if call_analysis_api(ticker_symbol, 'cached-score'):
                completed_steps.append('cached-score')
            else:
                failed_steps.append('cached-score')
            update_request_status(request_id, ticker_symbol, GenerationRequestStatus.IN_PROGRESS, completed_steps, failed_steps)
        
        # Determine final status
        if failed_steps:
            final_status = GenerationRequestStatus.FAILED
            logger.error(f"Request {request_id} completed with failures: {failed_steps}")
        else:
            final_status = GenerationRequestStatus.COMPLETED
            logger.info(f"Request {request_id} completed successfully")
        
        # Update final status and mark as completed
        update_request_status(request_id, ticker_symbol, final_status, completed_steps, failed_steps, mark_completed=True)
        
        return {
            'request_id': request_id,
            'ticker_symbol': ticker_symbol,
            'status': final_status,
            'steps_completed': completed_steps,
            'failed_steps': failed_steps
        }
        
    except Exception as e:
        logger.error(f"Error processing request {request_id}: {str(e)}")
        update_request_status(request_id, ticker_symbol, GenerationRequestStatus.FAILED, mark_completed=True)
        return {
            'request_id': request_id,
            'ticker_symbol': ticker_symbol,
            'status': GenerationRequestStatus.FAILED,
            'error': str(e)
        }


@ticker_generation_api.route('/process-single-request', methods=['POST'])
def process_single_request():
    """Main endpoint to process a single generation request"""
    try:
        # Get request from body
        generation_request = request.get_json()
        
        if not generation_request:
            return jsonify({
                'success': False,
                'error': 'No generation request provided in request body'
            }), 400
        
        request_id = generation_request.get('id')
        ticker_symbol = generation_request.get('ticker', {}).get('symbol')
        
        logger.info(f"Received generation request {request_id} for ticker {ticker_symbol}")
        
        # Start background processing
        thread = threading.Thread(
            target=process_single_request,
            args=(generation_request,),
            daemon=True
        )
        thread.start()
        
        # Return immediate response
        return jsonify({
            'success': True,
            'message': f'Processing request {request_id} for ticker {ticker_symbol} in background',
            'request_id': request_id,
            'ticker_symbol': ticker_symbol,
            'status': 'accepted'
        }), 202
        
    except Exception as e:
        logger.error(f"Error in process_generation_requests: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
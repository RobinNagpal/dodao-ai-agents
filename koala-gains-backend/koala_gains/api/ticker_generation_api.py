from flask import Blueprint, jsonify, request
import requests
import logging
from typing import Dict, List, Optional
import os
from datetime import datetime

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


def process_single_request(generation_request: Dict) -> Dict:
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
        
        return {
            'request_id': request_id,
            'ticker_symbol': ticker_symbol,
            'status': final_status,
            'steps_completed': analysis_steps,
            'failed_steps': failed_steps
        }
        
    except Exception as e:
        logger.error(f"Error processing request {request_id}: {str(e)}")
        update_request_status(request_id, ticker_symbol, GenerationRequestStatus.FAILED)
        return {
            'request_id': request_id,
            'ticker_symbol': ticker_symbol,
            'status': GenerationRequestStatus.FAILED,
            'error': str(e)
        }


@ticker_generation_api.route('/process-generation-requests', methods=['POST'])
def process_generation_requests():
    """Main endpoint to process generation requests"""
    try:
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
        
        # Process each request
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
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Error in process_generation_requests: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
#!/usr/bin/env python3
from flask import Flask, request, jsonify
from src.final_lambda import lambda_handler
import json

app = Flask(__name__)

@app.route('/stock', methods=['GET'])
def get_stock_data():
    symbol = request.args.get('symbol')
    event = {
        "queryStringParameters": {
            "symbol": symbol
        } if symbol else None
    }
    resp = lambda_handler(event, {})
    return jsonify(json.loads(resp.get('body', '{}'))), resp.get('statusCode', 500)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Stock Financial Data API",
                    "usage": {"get_stock_data": "GET /stock?symbol=AAPL"}}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

from time import time
import os
import pandas as pd
from flask import Flask, request, jsonify
from pyterrier_serve._loader import load_pipeline

def create_app(pipeline=None):
    """
    Create a Flask app with the PyTerrier pipeline endpoint.
    
    Args:
        pipeline: A PyTerrier pipeline object. If None, will attempt to load from environment.
    
    Returns:
        Flask application
    """
    app = Flask(__name__)

    if pipeline is None:
        pipeline = load_pipeline()

    @app.route('/transform', methods=['POST'])
    def exec():
        try:
            data = request.get_json()
            data = pd.DataFrame(data)
            t0 = time()
            results = pipeline.transform(data)
            t1 = time()
            duration = int((t1-t0)/1000)
            results = results.to_dict('records')
            return jsonify({'took': duration, 'results': results})
        except Exception as ex:
            return jsonify({"error": str(ex)}), 500

    @app.route('/search', methods=['GET'])
    def search():
        try:
            query = request.args.get('q')
            t0 = time()
            results = pipeline.search(query)
            t1 = time()
            duration = int((t1-t0)/1000)
            results = results.to_dict('records')
            return jsonify({'took': duration, 'results': results})
        except Exception as ex:
            return jsonify({"error": str(ex)}), 500

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({"status": "ok"})

    return app

def run_server(host='0.0.0.0', port=8000, pipeline=None, debug=False):
    """
    Run the PyTerrier serve server.
    
    Args:
        host: Host to bind the server to
        port: Port to bind the server to
        pipeline: PyTerrier pipeline. If None, will load from environment.
        debug: Whether to run in debug mode
    """
    app = create_app(pipeline)
    port = int(os.environ.get('PORT', port))
    app.run(host=host, port=port, debug=debug)

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

    app.json.sort_keys = False

    @app.route('/', methods=['GET'])
    def index():
        # a basic html form that issues a /search request
        return """<html>
<head>
<title>PyTerrier Serve</title>
<style>
body { font-family: Arial, sans-serif; }
h1 { color: #333; }
form { margin: 20px 0; }
input[type="text"] { width: 300px; padding: 10px; }
input[type="submit"] { padding: 10px 20px; }
</style>
</head>
<body>
<h1>PyTerrier Serve</h1>
<form action="/search" method="get">
    <input type="text" name="q" placeholder="Enter your query" required>
    <input type="submit" value="Search">
</form>
<h2>Search Results</h2>
<div id="results"></div>
<script>
document.querySelector('form').addEventListener('submit', function(event) {
    event.preventDefault();
    const query = document.querySelector('input[name="q"]').value;
    fetch('/search?q=' + encodeURIComponent(query))
        .then(response => response.json())
        .then(data => {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '';
            if (data.results.length === 0) {
                resultsDiv.innerHTML = '<p>No results found.</p>';
            } else {
                // Create a table with the results
                const table = document.createElement('table');
                table.style.width = '100%';
                table.style.borderCollapse = 'collapse';
                const headerRow = document.createElement('tr');
                const headers = Object.keys(data.results[0]);
                headers.forEach(header => {
                    const th = document.createElement('th');
                    th.innerText = header;
                    th.style.border = '1px solid #ddd';
                    th.style.padding = '8px';
                    headerRow.appendChild(th);
                });
                table.appendChild(headerRow);
                data.results.forEach(result => {
                    const row = document.createElement('tr');
                    headers.forEach(header => {
                        const td = document.createElement('td');
                        td.innerText = result[header];
                        td.style.border = '1px solid #ddd';
                        td.style.padding = '8px';
                        row.appendChild(td);
                    });
                    table.appendChild(row);
                });
                resultsDiv.appendChild(table);
            }
        });
});
</script>
</body>
</html>
        """

    @app.route('/transform', methods=['POST'])
    def exec():
        try:
            data = request.get_json()
            data = pd.DataFrame(data)
            t0 = time()
            results = pipeline.transform(data)
            t1 = time()
            duration = int((t1-t0)*1000)
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
            duration = int((t1-t0)*1000)
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

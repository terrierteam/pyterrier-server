import os
import argparse
from pyterrier_serve import run_server


def main():
    parser = argparse.ArgumentParser(description="PyTerrier Serve CLI")
    parser.add_argument('--host', help='Host to bind the server to (or loads from PYTERRIER_SERVE_HOST). Defaults to 0.0.0.0.')
    parser.add_argument('--port', type=int, help='Port to bind the server to (or loads from PYTERRIER_SERVE_PORT). Defaults to 8000.')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--pipeline', help='Pipeline to execute (or loads from PYTERRIER_SERVE_PIPELINE)')
    args = parser.parse_args()
    if args.host is None:
        args.host = os.environ.get('PYTERRIER_SERVE_HOST', '0.0.0.0')
    if args.port is None:
        args.port = int(os.environ.get('PYTERRIER_SERVE_PORT', '8000'))
    if args.pipeline:
        os.environ['PYTERRIER_SERVE_PIPELINE'] = args.pipeline
    run_server(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()

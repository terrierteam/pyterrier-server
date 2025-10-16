import os
import pyterrier as pt
from pyterrier import inspect, model as pt_model
from dotenv import load_dotenv
import logging
import pprint
import json

load_dotenv()
logger = logging.getLogger(__name__)

def load_pipeline():
    """Load one or more PyTerrier pipelines from the ``PYTERRIER_SERVER_PIPELINE`` environment variable."""
    logger.debug("Starting load_pipeline()")
    pipeline_expr = os.environ.get('PYTERRIER_SERVER_PIPELINE')
    if not pipeline_expr:
        logger.error("PYTERRIER_SERVER_PIPELINE environment variable not set")
        raise ValueError("PYTERRIER_SERVER_PIPELINE environment variable not set")

    logger.info(f"pipeline_expr: {pipeline_expr.strip().lower()}")

    if os.path.isfile(pipeline_expr):
        import yaml
        logger.debug(f"Loading pipeline from YAML file: {pipeline_expr}")
        with open(pipeline_expr, 'r') as f:
            config = yaml.safe_load(f)

        pipelines = {}
        for function in config["functions"]:
            name = function.get("name")
            task = function.get("task", "search").lower()
            pipeline = function.get("pipeline")
            if not name or not pipeline:
                logger.warning(f"Skipping function with missing name or pipeline: {function}")
                continue

            _globals = {'pt': pt}
            _locals = {}
            try:
                exec(pipeline, _globals, _locals)
            except Exception as e:
                logger.exception(f"Error executing code for function '{name}': {e}")
                continue

            for key in ['pipeline', 'p']:
                if key in _locals:
                    extra = {
                        "description": function.get("description", "")
                    }
                    if "properties" in function:
                        extra["properties"] = function["properties"]
                    else:
                        extra["properties"] = [{**pt_model.column_info(i),**{"phrase":i}} for i in inspect.transformer_inputs(_locals[key])[0]]
                        print("extra['properties']",extra["properties"])
                    try:
                        extra["outputs"] = [{**pt_model.column_info(i),**{"phrase":i}}
                                        for i in inspect.transformer_outputs(
                                            _locals[key],
                                            inspect.transformer_inputs(_locals[key])[0]
                                        )]
                    except Exception as e:
                        logger.warning(f"Warning creating outputs params for function '{name}': {e}. Skipping outputs param.")
                    pipelines[name] = {'pipeline': _locals[key], 'task': task, **extra}
                    logger.info(f"Loaded pipeline '{name}' with task '{task}' and extra params {list(extra.keys())}")
                    break
            else:
                logger.error("No 'pipelines' section found in YAML file")
                raise ValueError("No 'pipelines' section found in YAML file")

        logger.info("Loaded pipelines:")
        logger.info(json.dumps(pipelines, indent=4, default=str))
        return pipelines

    else:
        logger.debug("Detected single pipeline mode")
        task = os.environ.get('PYTERRIER_SERVER_PIPELINE_task', 'search').lower()
        _globals = {'pt': pt}
        _locals = {}
        try:
            exec(pipeline_expr, _globals, _locals)
        except Exception as e:
            logger.exception(f"Error executing pipeline expression: {e}")
            raise

        for key in ['pipeline', 'p']:
            if key in _locals:
                logger.info(f"Single pipeline loaded with key '{key}' and task '{task}'")
                single_pipeline = {'pipeline': _locals[key], 'task': task}
                logging.info(json.dumps(single_pipeline, indent=4, default=str))
                return single_pipeline

        logger.error("pipeline not set in PYTERRIER_SERVER_PIPELINE")
        raise ValueError("pipeline not set in PYTERRIER_SERVER_PIPELINE")

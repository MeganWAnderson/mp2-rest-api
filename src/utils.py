import logging 

def setup_logging(verbose=False):
    """Configure logging for the pipeline."""
    # use logging.DEBUG when verbose is True 
    # use logging.INFO when verbose is False 
    # include time, log level, and messagge in each log entry
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%H:%M:%S"
    )
"""
Library module for utility functions for the application.
BlockTimer is a RAII timer that measures and logs execution time of a code block.

Does have test code to demonstrate usage at the bottom of the file.
"""
import time
import logging

class BlockTimer:
    """RAII timer that measures and logs execution time of a code block."""
    
    def __init__(self, block_name: str, logger: logging.Logger):
        """Initialize the timer with a name for the code block being timed.
        
        Args:
            block_name (str): Name to identify this timed block in logs
            logger (logging.Logger): Logger instance to use for output
        """
        self.block_name = block_name
        self.logger = logger
        
    def __enter__(self):
        """Start timing when entering the context."""
        self.start_time = time.perf_counter_ns()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log the elapsed time when exiting the context."""
        end_time = time.perf_counter_ns()
        duration_ms = (end_time - self.start_time) / 1_000_000  # Convert ns to ms
        self.logger.info("%s took %.2fms to execute", self.block_name, duration_ms)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    with BlockTimer("main", logger) as timer:
        print("This is a test block to measure execution time.")
        time.sleep(1)  # Simulate some work
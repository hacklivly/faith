"""
Faith - the scheduler.

Lets her speak first sometimes, on a randomized rhythm rather than a fixed
timer, so the proactive check-ins don't feel robotic.
"""
import random
import threading
import time


def start_proactive_loop(trigger_callback, min_minutes=20, max_minutes=90):
    """Calls trigger_callback() at randomized intervals."""

    def loop():
        while True:
            wait_minutes = random.uniform(min_minutes, max_minutes)
            time.sleep(wait_minutes * 60)
            if random.random() < 0.8:
                trigger_callback()

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    return thread

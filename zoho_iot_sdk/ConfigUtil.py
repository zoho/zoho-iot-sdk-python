import time
from concurrent.futures import ThreadPoolExecutor

class ConfigUtil:
    def __init__(self, timeout=5):
        self.correlation_id_map = {}
        self.timeout = timeout  # Timeout in minutes
        self.scheduler = ThreadPoolExecutor(max_workers=1)

    def put(self, correlation_id, value):
        self.correlation_id_map[correlation_id] = value
        self.scheduler.submit(self._remove_after_timeout, correlation_id)

    def get(self, correlation_id):
        return self.correlation_id_map.get(correlation_id)

    def remove(self, correlation_id):
        if correlation_id in self.correlation_id_map:
            del self.correlation_id_map[correlation_id]

    def contains_correlation_id(self, correlation_id):
        return correlation_id in self.correlation_id_map

    def _remove_after_timeout(self, correlation_id):
        time.sleep(self.timeout * 60)
        self.remove(correlation_id)

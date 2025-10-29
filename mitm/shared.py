import threading
from typing import TypedDict, Optional

AffinityMapping = TypedDict("AffinityMapping", {
    "riot_host": str,
    "riot_port": int,
    "local_host": str,
})

class AffinityMappings():
    def __init__(self):
        self.mappings: list[AffinityMapping] = []
        self.mapping_id = 1
        self._lock = threading.Lock()

    def by_local_host(self, local_host: str) -> Optional[AffinityMapping]:
        for mapping in self.mappings:
            if mapping["local_host"] == local_host:
                return mapping.copy()

    def by_riot_host(self, riot_host: str) -> Optional[AffinityMapping]:
        for mapping in self.mappings:
            if mapping["riot_host"] == riot_host:
                return mapping.copy()

    def get_or_create(self, riot_host: str, riot_port: int) -> AffinityMapping:
        with self._lock:
            existing_mapping = self.by_riot_host(riot_host)

            if existing_mapping: return existing_mapping

            new_mapping = {
                "riot_host": riot_host,
                "riot_port": riot_port,
                "local_host": f"127.0.0.{self.mapping_id}",
            }

            self.mappings.append(new_mapping)
            self.mapping_id += 1

            return new_mapping.copy()

# shared state between config mitm and xmpp mitm
affinity_mappings = AffinityMappings()
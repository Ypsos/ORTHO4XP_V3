#  ============================================================
#  CRÉDIT — AUTEUR : Roland(Ypsos). -Mars 2026
#  Ce module a été conçu et spécifié par Roland (Ypsos) pour Ortho4XP V3. Cette mention de paternité NE DOIT JAMAIS ÊTRE SUPPRIMÉE, quelle que soit l'évolution ultérieure du fichier.
#  ============================================================
# CREDIT — AUTHOR: Roland(Ypsos). -March 2026
# This module was designed and specified by Roland (Ypsos) for # Ortho4XP V3. This statement of paternity MUST NEVER BE DELETED, # regardless of the subsequent evolution of the file.
# ============================================================
from enum import Enum
from typing import Callable, Dict, Any, Set
import threading
import queue

class EventType(Enum):
    TILE_START = "tile_start"
    TILE_PROGRESS = "tile_progress"
    TILE_COMPLETE = "tile_complete"
    TILE_ERROR = "tile_error"
    PIPELINE_STEP = "pipeline_step"
    CACHE_HIT = "cache_hit"

class EventBus:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self):
        self._subscribers: Dict[EventType, Set[Callable]] = {}
        self._queue = queue.Queue()
        self._running = True
        self._worker = threading.Thread(target=self._process_queue, daemon=True)
        self._worker.start()

    def subscribe(self, event_type: EventType, callback: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()
        self._subscribers[event_type].add(callback)

    def publish(self, event_type: EventType, data: Any = None):
        self._queue.put((event_type, data))

    def _process_queue(self):
        while self._running:
            try:
                event_type, data = self._queue.get(timeout=0.1)
                if event_type in self._subscribers:
                    for cb in list(self._subscribers[event_type]):
                        try:
                            cb(data)
                        except:
                            pass
            except:
                pass

    def shutdown(self):
        self._running = False

event_bus = EventBus()
from bailiff.core.events import TranscriptionSegment
import logging
import queue
import time

from bailiff.core.events import DiarizationResult


# TODO: Add support for labeling speakers

logger = logging.getLogger("bailiff.features.diarization.merge")

class MergeService:
    def __init__(self, tx_queue, diar_queue, output_queue, merge_timeout=8.0, segment_timeout=3.0):
        self.tx_queue = tx_queue
        self.diar_queue = diar_queue
        self.output_queue = output_queue
        self.pending_segments = []       # (TranscriptionSegment, arrival_time)
        self.diar_timeline = []          # sorted DiarizationResults
        self.merge_timeout = merge_timeout  # max age for diar_timeline entries
        self.segment_timeout = segment_timeout  # max wait before forwarding as "unknown"

    def run(self):
        while True:
            try:
                diarization_result = self.diar_queue.get(timeout=0.1)
                if diarization_result is None:
                    break
                self.diar_timeline.append(diarization_result)
            except queue.Empty:
                pass

            try:
                segment = self.tx_queue.get(timeout=0.1)
                if segment is None:
                    break
                self.pending_segments.append((segment, time.time()))
            except queue.Empty:
                pass

            now = time.time()
            for segment, arrival in list(self.pending_segments):
                self._handle_segment(segment, arrival, now)

            self.prune_timeline()
    
    def _handle_segment(self, segment, arrival, now):
        """Checks if the segment matches one of the diarization results
        and forwards it to the output queue."""
        
        # Check if the segment matches a diarization result
        for diarization_result in self.diar_timeline:
            if diarization_result.start_time <= segment.start_time <= diarization_result.end_time:
                self.pending_segments = [
                    (s, a) for s, a in self.pending_segments if s is not segment
                ]
                self.output_queue.put(
                    TranscriptionSegment(
                        text=segment.text,
                        start_time=segment.start_time,
                        end_time=segment.end_time,
                        duration=segment.duration,
                        speaker=diarization_result.speaker
                    )
                )
                return
        
        # If timed out waiting for diarization, forward as unknown
        if now - arrival >= self.segment_timeout:
            self.pending_segments = [
                (s, a) for s, a in self.pending_segments if s is not segment
            ]
            self.output_queue.put(
                TranscriptionSegment(
                    text=segment.text,
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    duration=segment.duration,
                    speaker="unknown"
                )
            )

        
    def prune_timeline(self):
        """Removes diarization results that are older than the merge timeout"""
        self.diar_timeline = [dr for dr in self.diar_timeline if dr.end_time > time.time() - self.merge_timeout]

def run_merge_service(tx_queue, diar_queue, output_queue, log_file: str | None = None):
    from bailiff.core.logging import setup_logging
    from bailiff.core.config import settings
    
    setup_logging(log_file=log_file)
    service = MergeService(
        tx_queue, 
        diar_queue, 
        output_queue,
        merge_timeout=settings.diarization.merge_timeout,
        segment_timeout=settings.diarization.segment_timeout
    )
    service.run()

import time
from datetime import datetime, timezone


class FaceTracker:
    def __init__(self, max_missing_frames=10, min_iou=0.15):
        self.max_missing_frames = max_missing_frames
        self.min_iou = min_iou
        self.tracks = {}
        self.next_id = 1
        self.frame_number = 0

    @staticmethod
    def _iou(a, b):
        ax, ay, aw, ah = a
        bx, by, bw, bh = b

        left = max(ax, bx)
        top = max(ay, by)
        right = min(ax + aw, bx + bw)
        bottom = min(ay + ah, by + bh)

        intersection = (
            max(0, right - left) * max(0, bottom - top)
        )
        union = aw * ah + bw * bh - intersection

        return intersection / union if union > 0 else 0.0

    def reset(self):
        """Start a new tracking session with fresh IDs."""
        self.tracks.clear()
        self.next_id = 1
        self.frame_number = 0

    def update(self, detections, timestamp=None):
        now = time.monotonic() if timestamp is None else float(timestamp)
        utc_now = datetime.now(timezone.utc).isoformat()
        self.frame_number += 1

        # Mark existing tracks as missed until matched.
        for track in self.tracks.values():
            track["missing"] += 1

        candidates = []

        for track_id, track in self.tracks.items():
            for index, detection in enumerate(detections):
                overlap = self._iou(
                    track["bbox"], detection["bbox"]
                )
                if overlap >= self.min_iou:
                    candidates.append((overlap, track_id, index))

        candidates.sort(reverse=True)

        used_tracks = set()
        used_detections = set()
        assignments = {}

        for overlap, track_id, index in candidates:
            if track_id in used_tracks or index in used_detections:
                continue

            used_tracks.add(track_id)
            used_detections.add(index)
            assignments[index] = track_id

        for index, detection in enumerate(detections):
            bbox = tuple(int(v) for v in detection["bbox"])

            if index in assignments:
                track_id = assignments[index]
            else:
                track_id = self.next_id
                self.next_id += 1

            x, y, w, h = bbox

            self.tracks[track_id] = {
                "participant_id": f"P{track_id:04d}",
                "bbox": bbox,
                "position": (x + w // 2, y + h // 2),
                "last_seen": now,
                "missing": 0,
                "score": float(detection.get("score", 1.0)),
            }

        expired = [
            track_id
            for track_id, track in self.tracks.items()
            if track["missing"] > self.max_missing_frames
        ]

        for track_id in expired:
            del self.tracks[track_id]

        results = []

        for track in self.tracks.values():
            if track["missing"] != 0:
                continue

            results.append({
                "participant_id": track["participant_id"],
                "timestamp": now,
                "timestamp_utc": utc_now,
                "frame_number": self.frame_number,
                "bbox": track["bbox"],
                "position": track["position"],
                "score": track["score"],
            })

        return results

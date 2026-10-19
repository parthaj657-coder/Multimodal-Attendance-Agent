
import csv
import os
from datetime import datetime, timezone

import librosa
import numpy as np


class AudioAnalyzer:
    """Analyze audio chunks and estimate sound activity."""

    def __init__(
        self,
        sample_rate=16000,
        chunk_seconds=5,
        silence_threshold_db=-45.0,
        activity_threshold_db=-35.0,
    ):
        if sample_rate <= 0 or chunk_seconds <= 0:
            raise ValueError("Sample rate and chunk duration must be positive.")

        self.sample_rate = sample_rate
        self.chunk_seconds = chunk_seconds
        self.silence_threshold_db = silence_threshold_db
        self.activity_threshold_db = activity_threshold_db

        self.session_metrics = []

    def load_audio(self, audio_path):
        """Load audio, convert to mono, and resample."""
        waveform, _ = librosa.load(
            audio_path,
            sr=self.sample_rate,
            mono=True,
        )
        return waveform.astype(np.float32)

    def analyze_audio_chunk(self, audio_data, timestamp=None):
        """Calculate energy, amplitude variation, and activity estimates."""
        if audio_data is None:
            return None

        if isinstance(audio_data, (bytes, bytearray)):
            if len(audio_data) % 2:
                raise ValueError("16-bit PCM audio must have an even byte length.")

            waveform = (
                np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
                / 32768.0
            )
        else:
            waveform = np.asarray(
                audio_data, dtype=np.float32
            ).reshape(-1)

        if waveform.size == 0:
            return None

        waveform = np.nan_to_num(
            waveform, nan=0.0, posinf=0.0, neginf=0.0
        )

        rms = float(np.sqrt(np.mean(waveform ** 2)))
        peak = float(np.max(np.abs(waveform)))
        mean_amplitude = float(np.mean(np.abs(waveform)))
        amplitude_std = float(np.std(waveform))

        energy_db = float(20 * np.log10(max(rms, 1e-8)))

        # Divide the chunk into short frames and calculate frame energy.
        frame_length = min(1024, waveform.size)
        hop_length = max(1, frame_length // 2)

        if waveform.size >= frame_length:
            frame_rms = librosa.feature.rms(
                y=waveform,
                frame_length=frame_length,
                hop_length=hop_length,
            )[0]
        else:
            frame_rms = np.array([rms], dtype=np.float32)

        frame_db = 20 * np.log10(np.maximum(frame_rms, 1e-8))

        quiet_ratio = float(
            np.mean(frame_db < self.silence_threshold_db)
        )
        active_ratio = float(
            np.mean(frame_db >= self.activity_threshold_db)
        )

        if energy_db < self.silence_threshold_db:
            activity = "Silence"
        elif active_ratio >= 0.5:
            activity = "Active sound"
        else:
            activity = "Background noise"

        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        record = {
            "timestamp": timestamp,
            "sample_rate": self.sample_rate,
            "duration_seconds": round(
                waveform.size / self.sample_rate, 3
            ),
            "rms_amplitude": round(rms, 6),
            "peak_amplitude": round(peak, 6),
            "mean_absolute_amplitude": round(mean_amplitude, 6),
            "amplitude_std": round(amplitude_std, 6),
            "energy_db": round(energy_db, 2),
            "quiet_ratio": round(quiet_ratio, 3),
            "active_sound_ratio": round(active_ratio, 3),
            "activity": activity,
        }

        self.session_metrics.append(record)
        return record

    def analyze_file(self, audio_path, output_dir="audio_logs"):
        """Analyze fixed-duration chunks and save detailed metrics."""
        waveform = self.load_audio(audio_path)
        os.makedirs(output_dir, exist_ok=True)

        samples_per_chunk = int(
            self.sample_rate * self.chunk_seconds
        )

        self.session_metrics = []

        for start in range(0, waveform.size, samples_per_chunk):
            chunk = waveform[start:start + samples_per_chunk]

            self.analyze_audio_chunk(
                chunk,
                timestamp=round(start / self.sample_rate, 3),
            )

        csv_path = os.path.join(
            output_dir, "audio_analysis.csv"
        )

        fieldnames = [
            "timestamp",
            "sample_rate",
            "duration_seconds",
            "rms_amplitude",
            "peak_amplitude",
            "mean_absolute_amplitude",
            "amplitude_std",
            "energy_db",
            "quiet_ratio",
            "active_sound_ratio",
            "activity",
        ]

        with open(
            csv_path, "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.session_metrics)

        return {
            "chunks_analyzed": len(self.session_metrics),
            "sample_rate": self.sample_rate,
            "chunk_seconds": self.chunk_seconds,
            "csv_path": os.path.abspath(csv_path),
            "results": self.session_metrics,
        }

    def get_session_summary(self):
        """Summarize the analyzed chunks for later multimodal fusion."""
        if not self.session_metrics:
            return {
                "chunks_analyzed": 0,
                "average_energy_db": None,
                "average_active_sound_ratio": None,
                "activity_counts": {},
            }

        energies = [
            item["energy_db"] for item in self.session_metrics
        ]
        active_ratios = [
            item["active_sound_ratio"]
            for item in self.session_metrics
        ]

        activity_counts = {}
        for item in self.session_metrics:
            activity = item["activity"]
            activity_counts[activity] = (
                activity_counts.get(activity, 0) + 1
            )

        return {
            "chunks_analyzed": len(self.session_metrics),
            "average_energy_db": round(
                sum(energies) / len(energies), 2
            ),
            "average_active_sound_ratio": round(
                sum(active_ratios) / len(active_ratios), 3
            ),
            "activity_counts": activity_counts,
        }

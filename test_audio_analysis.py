
from backend.core.audio_analysis import AudioAnalyzer

analyzer = AudioAnalyzer(sample_rate=16000, chunk_seconds=5)

result = analyzer.analyze_file("test_audio.wav")

print("Audio analysis completed!")
print("Chunks analyzed:", result["chunks_analyzed"])
print("CSV saved to:", result["csv_path"])

for chunk in result["results"]:
    print(chunk)

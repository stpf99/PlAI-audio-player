import os
import argparse
import numpy as np
import librosa
import essentia
from essentia.standard import MonoLoader, RhythmExtractor2013, Danceability, Energy, Duration, ZeroCrossingRate

def analyze_audio_file(audio_file):
    # Wczytywanie audio za pomocą Librosa
    y, sr = librosa.load(audio_file)

    # Ekstrakcja cech za pomocą Librosa
    tempo_librosa, _ = librosa.beat.beat_track(y=y, sr=sr)
    duration_librosa = librosa.get_duration(y=y, sr=sr)
    zero_crossings_librosa = librosa.feature.zero_crossing_rate(y).mean()
    spectral_contrast_librosa = librosa.feature.spectral_contrast(y=y, sr=sr).mean(axis=1)

    # Wczytywanie audio za pomocą Essentia
    loader = MonoLoader(filename=audio_file)
    audio = loader()

    # Ekstrakcja cech za pomocą Essentia
    danceability_extractor = Danceability()
    danceability = danceability_extractor(audio)

    energy_extractor = Energy()
    energy = energy_extractor(audio)

    rhythm_extractor = RhythmExtractor2013()
    tempo_essentia, _, _, _, _ = rhythm_extractor(audio)

    duration_extractor = Duration()
    duration_essentia = duration_extractor(audio)

    zero_crossing_rate_extractor = ZeroCrossingRate()
    zero_crossing_rate = zero_crossing_rate_extractor(audio)

    return {
        'filename': os.path.basename(audio_file),
        'tempo_librosa': tempo_librosa,
        'duration_librosa': duration_librosa,
        'zero_crossings_librosa': zero_crossings_librosa,
        'spectral_contrast_librosa': spectral_contrast_librosa.tolist(),
        'danceability': danceability,
        'energy': energy,
        'tempo_essentia': tempo_essentia,
        'duration_essentia': duration_essentia,
        'zero_crossing_rate': zero_crossing_rate,
    }

def main():
    parser = argparse.ArgumentParser(description='Analyze audio files in a directory and output results to a text file.')
    parser.add_argument('directory', type=str, help='Directory containing audio files to analyze.')
    args = parser.parse_args()

    directory = args.directory
    output_file = f'scanned_db.txt'

    if not os.path.isdir(directory):
        print(f'The directory {directory} does not exist.')
        return

    results = []

    for filename in os.listdir(directory):
        if filename.endswith('.mp3') or filename.endswith('.wav') or filename.endswith('.flac'):
            audio_file = os.path.join(directory, filename)
            print(f'Analyzing {audio_file}...')
            try:
                result = analyze_audio_file(audio_file)
                results.append(result)
            except Exception as e:
                print(f'Error analyzing {audio_file}: {e}')

    with open(output_file, 'w') as f:
        for result in results:
            f.write(f"File: {result['filename']}\n")
            f.write(f"  Tempo (Librosa): {result['tempo_librosa']} BPM\n")
            f.write(f"  Duration (Librosa): {result['duration_librosa']} seconds\n")
            f.write(f"  Zero Crossing Rate (Librosa): {result['zero_crossings_librosa']}\n")
            f.write(f"  Spectral Contrast (Librosa): {result['spectral_contrast_librosa']}\n")
            f.write(f"  Danceability (Essentia): {result['danceability']}\n")
            f.write(f"  Energy (Essentia): {result['energy']}\n")
            f.write(f"  Tempo (Essentia): {result['tempo_essentia']} BPM\n")
            f.write(f"  Duration (Essentia): {result['duration_essentia']} seconds\n")
            f.write(f"  Zero Crossing Rate (Essentia): {result['zero_crossing_rate']}\n")
            f.write('\n')

    print(f'Results written to {output_file}')

if __name__ == '__main__':
    main()

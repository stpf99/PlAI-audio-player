import os
import argparse
import numpy as np
import librosa
import essentia
from essentia.standard import MonoLoader, RhythmExtractor2013, Danceability, Energy, Duration, ZeroCrossingRate
from concurrent.futures import ProcessPoolExecutor
import threading
import traceback

file_lock = threading.Lock()

def analyze_and_write_audio_file(audio_file, output_file):
    try:
        print(f"Analyzing file: {audio_file}")
        y, sr = librosa.load(audio_file)

        tempo_librosa, _ = librosa.beat.beat_track(y=y, sr=sr)
        duration_librosa = librosa.get_duration(y=y, sr=sr)
        zero_crossings_librosa = librosa.feature.zero_crossing_rate(y).mean()
        spectral_contrast_librosa = librosa.feature.spectral_contrast(y=y, sr=sr).mean(axis=1)

        audio_essentia = essentia.array(y)

        danceability_extractor = Danceability()
        danceability = danceability_extractor(audio_essentia)

        energy_extractor = Energy()
        energy = energy_extractor(audio_essentia)

        rhythm_extractor = RhythmExtractor2013()
        tempo_essentia, _, _, _, _ = rhythm_extractor(audio_essentia)

        duration_extractor = Duration()
        duration_essentia = duration_extractor(audio_essentia)

        zero_crossing_rate_extractor = ZeroCrossingRate()
        zero_crossing_rate = zero_crossing_rate_extractor(audio_essentia)

        print(f"Analysis completed for: {audio_file}")
        
        result = {
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
        
        write_result_to_file(output_file, result)
        return True
    except Exception as e:
        print(f'Error analyzing {audio_file}: {str(e)}')
        traceback.print_exc()
        return False

def write_result_to_file(output_file, result):
    with file_lock:
        with open(output_file, 'a') as f:
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
        print(f"Wrote results for {result['filename']} to {output_file}")

def process_file(args):
    file, output_file = args
    return analyze_and_write_audio_file(file, output_file)

def main():
    parser = argparse.ArgumentParser(description='Analyze audio files in a directory and output results to a text file.')
    parser.add_argument('directory', type=str, help='Directory containing audio files to analyze.')
    args = parser.parse_args()

    directory = args.directory
    output_file = 'scanned_db.txt'

    if not os.path.isdir(directory):
        print(f'The directory {directory} does not exist.')
        return

    files = [os.path.join(directory, filename) for filename in os.listdir(directory)
             if filename.endswith(('.mp3', '.wav', '.flac'))]

    print(f"Found {len(files)} audio files to process")

    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        results = list(executor.map(process_file, [(file, output_file) for file in files]))

    successful_analyses = sum(results)
    print(f'All processing completed. Analyzed {successful_analyses} out of {len(files)} files.')
    print(f'Results written to {output_file}')
    print(f'Total lines in output file: {sum(1 for line in open(output_file))}')

if __name__ == '__main__':
    main()

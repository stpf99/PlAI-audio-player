import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os
import numpy as np

class PlaylistGenerator(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Generator Playlist M3U")
        self.set_border_width(10)
        self.set_default_size(800, 600)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        self.db_chooser = Gtk.FileChooserButton(title="Wybierz plik bazy danych")
        vbox.pack_start(self.db_chooser, False, False, 0)

        filters_frame = Gtk.Frame(label="Filtry")
        vbox.pack_start(filters_frame, False, False, 0)

        filters_grid = Gtk.Grid()
        filters_grid.set_column_spacing(10)
        filters_grid.set_row_spacing(10)
        filters_frame.add(filters_grid)

        # Tempo
        filters_grid.attach(Gtk.Label(label="Tempo (BPM):"), 0, 0, 1, 1)
        self.tempo_min = Gtk.Entry()
        self.tempo_max = Gtk.Entry()
        filters_grid.attach(self.tempo_min, 1, 0, 1, 1)
        filters_grid.attach(self.tempo_max, 2, 0, 1, 1)

        # Czas trwania
        filters_grid.attach(Gtk.Label(label="Czas trwania (s):"), 0, 1, 1, 1)
        self.duration_min = Gtk.Entry()
        self.duration_max = Gtk.Entry()
        filters_grid.attach(self.duration_min, 1, 1, 1, 1)
        filters_grid.attach(self.duration_max, 2, 1, 1, 1)

        # Energia
        filters_grid.attach(Gtk.Label(label="Energia:"), 0, 2, 1, 1)
        self.energy_min = Gtk.Entry()
        self.energy_max = Gtk.Entry()
        filters_grid.attach(self.energy_min, 1, 2, 1, 1)
        filters_grid.attach(self.energy_max, 2, 2, 1, 1)

        # Danceability
        filters_grid.attach(Gtk.Label(label="Danceability:"), 0, 3, 1, 1)
        self.danceability_min = Gtk.Entry()
        self.danceability_max = Gtk.Entry()
        filters_grid.attach(self.danceability_min, 1, 3, 1, 1)
        filters_grid.attach(self.danceability_max, 2, 3, 1, 1)

        # Spectral Contrast
        filters_grid.attach(Gtk.Label(label="Spectral Contrast:"), 0, 4, 1, 1)
        self.spectral_contrast_min = Gtk.Entry()
        self.spectral_contrast_max = Gtk.Entry()
        filters_grid.attach(self.spectral_contrast_min, 1, 4, 1, 1)
        filters_grid.attach(self.spectral_contrast_max, 2, 4, 1, 1)

        # Zero Crossing Rate
        filters_grid.attach(Gtk.Label(label="Zero Crossing Rate:"), 0, 5, 1, 1)
        self.zcr_min = Gtk.Entry()
        self.zcr_max = Gtk.Entry()
        filters_grid.attach(self.zcr_min, 1, 5, 1, 1)
        filters_grid.attach(self.zcr_max, 2, 5, 1, 1)

        generate_button = Gtk.Button(label="Generuj playlistę")
        generate_button.connect("clicked", self.on_generate_clicked)
        vbox.pack_start(generate_button, False, False, 0)

    def on_generate_clicked(self, widget):
        db_file = self.db_chooser.get_filename()
        if not db_file:
            self.show_error("Wybierz plik bazy danych!")
            return

        filtered_tracks = self.filter_tracks(db_file)
        if filtered_tracks:
            self.generate_m3u(filtered_tracks)
        else:
            self.show_error("Brak utworów spełniających kryteria!")

    def filter_tracks(self, db_file):
        filtered_tracks = []
        with open(db_file, 'r') as f:
            current_track = {}
            for line in f:
                line = line.strip()
                if line.startswith("File:"):
                    if current_track:
                        self.process_track(current_track)
                        if self.track_matches_filters(current_track):
                            filtered_tracks.append(current_track)
                    current_track = {"File": line.split(": ", 1)[1]}
                elif ": " in line:
                    key, value = line.split(": ", 1)
                    current_track[key] = value

        if current_track:
            self.process_track(current_track)
            if self.track_matches_filters(current_track):
                filtered_tracks.append(current_track)

        return filtered_tracks

    def process_track(self, track):
        try:
            if 'Tempo (Librosa)' in track and 'Tempo (Essentia)' in track:
                tempo_librosa = float(track['Tempo (Librosa)'].strip('[] BPM'))
                tempo_essentia = float(track['Tempo (Essentia)'].split()[0])
                track['Tempo'] = round((tempo_librosa + tempo_essentia) / 2)

            if 'Duration (Librosa)' in track and 'Duration (Essentia)' in track:
                duration_librosa = float(track['Duration (Librosa)'].split()[0])
                duration_essentia = float(track['Duration (Essentia)'].split()[0])
                track['Duration'] = round((duration_librosa + duration_essentia) / 2, 3)

            if 'Zero Crossing Rate (Librosa)' in track and 'Zero Crossing Rate (Essentia)' in track:
                zcr_librosa = float(track['Zero Crossing Rate (Librosa)'])
                zcr_essentia = float(track['Zero Crossing Rate (Essentia)'])
                track['Zero Crossing Rate'] = round((zcr_librosa + zcr_essentia) / 2, 3)

            if 'Spectral Contrast (Librosa)' in track:
                spectral_contrast_str = track['Spectral Contrast (Librosa)'].strip('[]')
                track['Spectral Contrast'] = [round(float(x.strip()), 3) for x in spectral_contrast_str.split(',')]

            if 'Danceability (Essentia)' in track:
                danceability_str = track['Danceability (Essentia)'].split(',')[0]
                track['Danceability'] = round(float(danceability_str.strip('()')), 3)

            if 'Energy (Essentia)' in track:
                track['Energy'] = round(float(track['Energy (Essentia)']), 3)

            print(f"Processed track:")
            for key, value in track.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"Error processing track: {e}")
            print(f"Problematic track data: {track}")

    def track_matches_filters(self, track):
        if self.tempo_min.get_text() and track.get('Tempo', 0) < float(self.tempo_min.get_text()):
            return False
        if self.tempo_max.get_text() and track.get('Tempo', 0) > float(self.tempo_max.get_text()):
            return False

        if self.duration_min.get_text() and track.get('Duration', 0) < float(self.duration_min.get_text()):
            return False
        if self.duration_max.get_text() and track.get('Duration', 0) > float(self.duration_max.get_text()):
            return False

        if self.energy_min.get_text() and track.get('Energy', 0) < float(self.energy_min.get_text()):
            return False
        if self.energy_max.get_text() and track.get('Energy', 0) > float(self.energy_max.get_text()):
            return False

        if self.zcr_min.get_text() and track.get('Zero Crossing Rate', 0) < float(self.zcr_min.get_text()):
            return False
        if self.zcr_max.get_text() and track.get('Zero Crossing Rate', 0) > float(self.zcr_max.get_text()):
            return False

        if self.danceability_min.get_text() and track.get('Danceability', 0) < float(self.danceability_min.get_text()):
            return False
        if self.danceability_max.get_text() and track.get('Danceability', 0) > float(self.danceability_max.get_text()):
            return False

        if self.spectral_contrast_min.get_text() or self.spectral_contrast_max.get_text():
            target_sc_min = np.array([float(x) for x in self.spectral_contrast_min.get_text().split(',')])
            target_sc_max = np.array([float(x) for x in self.spectral_contrast_max.get_text().split(',')])
            track_sc = np.array(track.get('Spectral Contrast', []))
            if len(track_sc) > 0:
                if np.any(track_sc < target_sc_min) or np.any(track_sc > target_sc_max):
                    return False

        return True

    def generate_m3u(self, tracks):
        playlist_file = "playlist.m3u"
        with open(playlist_file, 'w') as f:
            f.write("#EXTM3U\n")
            for track in tracks:
                f.write(f"#EXTINF:-1,{os.path.basename(track['File'])}\n")
                f.write(f"{track['File']}\n")
        self.show_info(f"Playlista zapisana jako {playlist_file}")

    def show_error(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        dialog.run()
        dialog.destroy()

    def show_info(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        dialog.run()
        dialog.destroy()

win = PlaylistGenerator()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()

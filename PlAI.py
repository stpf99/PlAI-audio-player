import os
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk
import numpy as np
import gi.repository.Gst as Gst

class AudioPlayer(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Audio Player PlAI")

        self.playlist = []

        # Main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(self.main_box)

        # Button to open directory with audio files
        self.open_directory_button = Gtk.Button(label="Open Directory with Audio Files")
        self.open_directory_button.connect("clicked", self.on_open_directory_clicked)
        self.main_box.pack_start(self.open_directory_button, False, False, 0)

        # Button to open database file
        self.open_database_button = Gtk.Button(label="Open Database File")
        self.open_database_button.connect("clicked", self.on_open_database_clicked)
        self.main_box.pack_start(self.open_database_button, False, False, 0)

        # Button to load playlist
        self.load_playlist_button = Gtk.Button(label="Load Playlist")
        self.load_playlist_button.connect("clicked", self.on_load_playlist_clicked)
        self.main_box.pack_start(self.load_playlist_button, False, False, 0)

        # TreeView and ListStore for playlist
        self.liststore = Gtk.ListStore(str, float, float, float, float, float, str)
        self.treeview = Gtk.TreeView(model=self.liststore)

        # Initialize columns
        self.setup_columns()

        # Enable sorting
        for column in self.treeview.get_columns():
            column.set_sort_indicator(True)
            column.connect("clicked", self.on_column_clicked)

        self.main_box.pack_start(self.treeview, True, True, 0)

        # Button to play selected audio
        self.play_button = Gtk.Button(label="Play")
        self.play_button.connect("clicked", self.on_play_clicked)
        self.main_box.pack_start(self.play_button, False, False, 0)

        # Button to stop audio playback
        self.stop_button = Gtk.Button(label="Stop")
        self.stop_button.connect("clicked", self.on_stop_clicked)
        self.main_box.pack_start(self.stop_button, False, False, 0)

        self.audio_directory = None
        self.database_file = None

        # Initialize GStreamer
        Gst.init(None)

        # GStreamer elements
        self.player = Gst.ElementFactory.make("playbin", "player")

    def setup_columns(self):
        # Column titles and data types
        columns = [("File", str), ("Tempo", float), ("Duration", float),
                   ("Energy", float), ("Zero Crossing Rate", float),
                   ("Danceability", float), ("Spectral Contrast", str)]

        for i, (title, data_type) in enumerate(columns):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_sort_column_id(i)  # Set the column to be sortable
            self.treeview.append_column(column)

    def on_open_directory_clicked(self, widget):
        dialog = Gtk.FileChooserDialog("Please choose a directory with audio files", self,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        "Select", Gtk.ResponseType.OK))

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.audio_directory = dialog.get_filename()
            print("Selected audio directory: ", self.audio_directory)
        dialog.destroy()

    def on_open_database_clicked(self, widget):
        dialog = Gtk.FileChooserDialog("Please choose a database file", self,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.database_file = dialog.get_filename()
            print("Selected database file: ", self.database_file)
        dialog.destroy()

    def on_load_playlist_clicked(self, widget):
        if not self.audio_directory or not self.database_file:
            print("Please select both audio directory and database file first.")
            return

        self.playlist = self.read_playlist_from_file(self.database_file)
        self.update_playlist_view()

    def read_playlist_from_file(self, filename):
        playlist = []

        with open(filename, 'r') as file:
            lines = file.readlines()

        entry = {}
        for line in lines:
            line = line.strip()
            if line.startswith("File:"):
                if entry:
                    playlist.append(entry)
                entry = {'File': line[6:].strip()}
                audio_file = os.path.join(self.audio_directory, entry['File'])
                if os.path.exists(audio_file):
                    entry['File'] = audio_file  # Replace relative path with absolute path
            elif line.startswith("Tempo (Librosa)"):
                # Extract numeric value from string, handle case with brackets
                tempo_value = line.split(':')[1].strip().split()[0].lstrip('[').rstrip(']')
                entry['Tempo'] = float(tempo_value)
            elif line.startswith("Duration"):
                entry['Duration'] = float(line.split(':')[1].strip().split()[0])
            elif line.startswith("Energy"):
                entry['Energy'] = float(line.split(':')[1].strip())
            elif line.startswith("Zero Crossing Rate"):
                entry['Zero Crossing Rate'] = float(line.split(':')[1].strip())
            elif line.startswith("Danceability"):
                # Parse danceability values
                danceability_values = line.split(':')[1].strip().split(',')
                entry['Danceability'] = float(danceability_values[0].strip(' ()'))
            elif line.startswith("Spectral Contrast"):
                # Parse list of floats
                spectral_contrast_values = line.split(':')[1].strip().split(',')
                entry['Spectral Contrast'] = [float(val.strip(' []')) for val in spectral_contrast_values]

        if entry:
            playlist.append(entry)

        return playlist

    def update_playlist_view(self):
        self.liststore.clear()
        for item in self.playlist:
            # Calculate average spectral contrast
            if 'Spectral Contrast' in item:
                spectral_contrast_avg = np.mean(item['Spectral Contrast'])
            else:
                spectral_contrast_avg = 0.0

            self.liststore.append([
                item.get('File', ''),
                item.get('Tempo', 0.0),
                item.get('Duration', 0.0),
                item.get('Energy', 0.0),
                item.get('Zero Crossing Rate', 0.0),
                item.get('Danceability', 0.0),
                str(spectral_contrast_avg)  # Convert to string for display
            ])

    def on_column_clicked(self, column):
        # Handle sorting
        sort_column_id = column.get_sort_column_id()
        self.liststore.set_sort_column_id(sort_column_id, Gtk.SortType.ASCENDING)

    def on_play_clicked(self, widget):
        # Play selected audio file
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            filepath = model[treeiter][0]  # Get file path from selected row
            self.player.set_property("uri", "file://" + filepath)
            self.player.set_state(Gst.State.PLAYING)

    def on_stop_clicked(self, widget):
        # Stop audio playback
        self.player.set_state(Gst.State.NULL)

win = AudioPlayer()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()

import os
import gi
import sqlite3

gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, GLib, Pango
import gi.repository.Gst as Gst

class AudioPlayer(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Audio Player PlAI")

        self.playlist = []
        self.current_sort_column = None
        self.current_sort_order = Gtk.SortType.ASCENDING

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

        # ScrolledWindow for the TreeView
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.main_box.pack_start(self.scrolled_window, True, True, 0)

        # TreeView and ListStore for playlist
        self.liststore = Gtk.ListStore(str, str, float, float, float, float, float, str)
        self.treeview = Gtk.TreeView(model=self.liststore)
        self.scrolled_window.add(self.treeview)

        # Initialize columns
        self.setup_columns()

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
        # Column titles, data types, and max widths
        columns = [
            ("Filename", str, 200),
            ("Tempo", float, 100),
            ("Duration", float, 100),
            ("Energy", float, 100),
            ("Zero Crossing Rate", float, 150),
            ("Danceability", float, 100),
            ("Spectral Contrast", str, 200)
        ]

        for i, (title, data_type, max_width) in enumerate(columns):
            renderer = Gtk.CellRendererText()
            renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
            column = Gtk.TreeViewColumn(title, renderer, text=i+1)  # i+1 because full path is at index 0
            column.set_sort_column_id(i+1)
            column.set_resizable(True)
            column.set_min_width(50)
            column.set_max_width(max_width)
            column.connect("clicked", self.on_column_clicked)
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

        self.create_database()
        self.load_playlist_to_database()
        self.update_playlist_view()

    def create_database(self):
        self.conn = sqlite3.connect(':memory:')  # Use in-memory database for speed
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS playlist
                            (file TEXT, filename TEXT, tempo REAL, duration REAL, energy REAL,
                            zero_crossing_rate REAL, danceability REAL, spectral_contrast TEXT)''')

    def load_playlist_to_database(self):
        with open(self.database_file, 'r') as file:
            batch = []
            for line in file:
                if line.startswith("File:"):
                    if batch:
                        self.insert_entry(batch)
                        batch = []
                batch.append(line.strip())
            if batch:
                self.insert_entry(batch)
        
        self.conn.commit()

    def insert_entry(self, batch):
        entry = {}
        for line in batch:
            if line.startswith("File:"):
                full_path = os.path.join(self.audio_directory, line[6:].strip())
                entry['File'] = full_path
                entry['Filename'] = os.path.basename(full_path)
            elif line.startswith("Tempo (Librosa)"):
                entry['Tempo'] = float(line.split(':')[1].strip().split()[0].lstrip('[').rstrip(']'))
            elif line.startswith("Duration"):
                entry['Duration'] = float(line.split(':')[1].strip().split()[0])
            elif line.startswith("Energy"):
                entry['Energy'] = float(line.split(':')[1].strip())
            elif line.startswith("Zero Crossing Rate"):
                entry['Zero Crossing Rate'] = float(line.split(':')[1].strip())
            elif line.startswith("Danceability"):
                danceability_values = line.split(':')[1].strip().split(',')
                entry['Danceability'] = float(danceability_values[0].strip(' ()'))
            elif line.startswith("Spectral Contrast"):
                spectral_contrast_values = line.split(':')[1].strip().split(',')
                entry['Spectral Contrast'] = str([float(val.strip(' []')) for val in spectral_contrast_values])

        self.cursor.execute('''INSERT INTO playlist VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                            (entry.get('File', ''), entry.get('Filename', ''), entry.get('Tempo', 0.0), 
                             entry.get('Duration', 0.0), entry.get('Energy', 0.0), 
                             entry.get('Zero Crossing Rate', 0.0), entry.get('Danceability', 0.0), 
                             entry.get('Spectral Contrast', '[]')))

    def update_playlist_view(self):
        self.liststore.clear()
        order_by = ""
        if self.current_sort_column is not None:
            order_by = f"ORDER BY {self.current_sort_column + 1} {'DESC' if self.current_sort_order == Gtk.SortType.DESCENDING else 'ASC'}"
        self.cursor.execute(f'''SELECT * FROM playlist {order_by}''')
        for row in self.cursor.fetchall():
            self.liststore.append(row)

    def on_column_clicked(self, column):
        sort_column_id = column.get_sort_column_id()
        if self.current_sort_column == sort_column_id:
            self.current_sort_order = Gtk.SortType.DESCENDING if self.current_sort_order == Gtk.SortType.ASCENDING else Gtk.SortType.ASCENDING
        else:
            self.current_sort_column = sort_column_id
            self.current_sort_order = Gtk.SortType.ASCENDING

        for col in self.treeview.get_columns():
            col.set_sort_indicator(col == column)
        column.set_sort_order(self.current_sort_order)

        self.update_playlist_view()

    def on_play_clicked(self, widget):
        # Play selected audio file
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            filepath = model[treeiter][0]  # Get full file path from selected row
            self.player.set_property("uri", "file://" + filepath)
            self.player.set_state(Gst.State.PLAYING)

    def on_stop_clicked(self, widget):
        # Stop audio playback
        self.player.set_state(Gst.State.NULL)

win = AudioPlayer()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()

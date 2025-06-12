import sys
import mido
import mido.backends.rtmidi
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout, QPushButton,
    QLabel, QLineEdit, QSpinBox, QHBoxLayout
)
from PyQt5.QtCore import QTimer
from mido import Message, MidiFile, MidiTrack, bpm2tempo

DRUM_NOTES = {
    'kick': 36,
    'snare': 38,
    'closed_hat': 42,
    'open_hat': 46,
    'low_tom': 45,
    'mid_tom': 47,
    'high_tom': 50,
    'crash': 49,
    'ride': 51
}
STEPS = 16

class DrumMachine(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Drum Machine")
        self.pattern = {drum: [0]*STEPS for drum in DRUM_NOTES}
        self.outport = self.init_midi_output()
        self.step_index = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.play_step)
        self.is_playing = False
        self.init_ui()

    def init_midi_output(self):
        try:
            outputs = mido.get_output_names()
            if not outputs:
                print("No MIDI output devices found.")
                return None
            print("Available MIDI Outputs:")
            for i, name in enumerate(outputs):
                print(f"{i}: {name}")
            return mido.open_output(outputs[0])
        except Exception as e:
            print(f"Error opening MIDI output: {e}")
            return None

    def init_ui(self):
        layout = QVBoxLayout()
        grid = QGridLayout()

        self.buttons = {}
        for row, drum in enumerate(DRUM_NOTES):
            for col in range(STEPS):
                btn = QPushButton("")
                btn.setCheckable(True)
                btn.setFixedSize(30, 30)
                btn.clicked.connect(self.make_toggle(drum, col, btn))
                self.buttons[(drum, col)] = btn
                grid.addWidget(btn, row, col)
            grid.addWidget(QLabel(drum), row, STEPS)

        layout.addLayout(grid)

        bpm_layout = QVBoxLayout()
        self.bpm_input = QSpinBox()
        self.bpm_input.setRange(30, 300)
        self.bpm_input.setValue(120)
        bpm_layout.addWidget(QLabel("BPM"))
        bpm_layout.addWidget(self.bpm_input)
        layout.addLayout(bpm_layout)

        file_layout = QVBoxLayout()
        self.file_input = QLineEdit("drum_output.mid")
        file_layout.addWidget(QLabel("MIDI File Name"))
        file_layout.addWidget(self.file_input)
        layout.addLayout(file_layout)

        controls = QHBoxLayout()
        play_btn = QPushButton("▶ Play")
        play_btn.clicked.connect(self.start_playback)
        pause_btn = QPushButton("⏸ Pause")
        pause_btn.clicked.connect(self.pause_playback)
        stop_btn = QPushButton("⏹ Stop")
        stop_btn.clicked.connect(self.stop_playback)
        controls.addWidget(play_btn)
        controls.addWidget(pause_btn)
        controls.addWidget(stop_btn)
        layout.addLayout(controls)

        export_btn = QPushButton("💾 Export MIDI")
        export_btn.clicked.connect(self.export_midi)
        layout.addWidget(export_btn)

        self.setLayout(layout)

    def make_toggle(self, drum, step, btn):
        def toggle():
            self.pattern[drum][step] = int(btn.isChecked())
            if btn.isChecked():
                self.preview_note(DRUM_NOTES[drum])
        return toggle

    def preview_note(self, note):
        if self.outport:
            self.outport.send(Message('note_on', channel=9, note=note, velocity=127))
            self.outport.send(Message('note_off', channel=9, note=note, velocity=127, time=100))

    def start_playback(self):
        bpm = self.bpm_input.value()
        interval_ms = int((60 / bpm) * 1000 / 4)
        self.timer.start(interval_ms)
        self.is_playing = True

    def pause_playback(self):
        self.timer.stop()
        self.is_playing = False

    def stop_playback(self):
        self.timer.stop()
        self.step_index = 0
        self.is_playing = False

    def play_step(self):
        if self.outport:
            for drum, note in DRUM_NOTES.items():
                if self.pattern[drum][self.step_index]:
                    self.outport.send(Message('note_on', channel=9, note=note, velocity=127))
                    self.outport.send(Message('note_off', channel=9, note=note, velocity=127, time=100))
        self.step_index = (self.step_index + 1) % STEPS

    def export_midi(self):
        bpm = self.bpm_input.value()
        filename = self.file_input.text()
        mid = MidiFile()
        track = MidiTrack()
        mid.tracks.append(track)
        track.append(mido.MetaMessage('set_tempo', tempo=bpm2tempo(bpm)))

        ticks = mid.ticks_per_beat // 4
        for step in range(STEPS):
            step_written = False
            for drum, note in DRUM_NOTES.items():
                if self.pattern[drum][step]:
                    track.append(Message('note_on', channel=9, note=note, velocity=127, time=0 if step_written else ticks))
                    track.append(Message('note_off', channel=9, note=note, velocity=127, time=0))
                    step_written = True
            if not step_written:
                track.append(Message('note_off', channel=9, note=0, velocity=0, time=ticks))

        mid.save(filename)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DrumMachine()
    window.show()
    sys.exit(app.exec_())

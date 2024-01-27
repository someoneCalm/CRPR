from ctypes import c_ubyte, cast, POINTER
from numpy import array, frombuffer, int16
from sdl2.sdlmixer import (Mix_Pause, Mix_Resume, Mix_Paused, Mix_QuickLoad_RAW,
                           Mix_OpenAudio, Mix_CloseAudio, Mix_HaltChannel, Mix_PlayChannel, Mix_Volume,
                           AUDIO_S16LSB)
from tkinter.filedialog import askopenfilename, asksaveasfile
from wave import *

from io import BytesIO
from pydub import AudioSegment


class AudioPlayer:
    def __init__(self, audio):
        self.audio = audio
        self.bactive = False
        self.bplaying = False

        self.chunk = b""
        self.volume = 100

        self.start = 0.0
        self.start_index = 0
        self.end = 0.0
        self.end_index = 0
        self.current = 0.0

    def open_player(self):
        """
        Инициализация SDL аудио устройства.
        """
        if self.bactive:
            self.close_player()

        result = Mix_OpenAudio(
            self.audio.framerate, AUDIO_S16LSB, self.audio.nchannels, self.audio.chunksize
        )
        if result == 0:
            self.bactive = True

    def close_player(self):
        """
        Закрытие SDL аудио устройства.
        """
        if not self.bactive:
            return

        Mix_CloseAudio()
        self.bactive = False
        self.bplaying = False

    def pause_audio(self, event=None):
        """
        Остановка проигрывания аудио.
        :param event: событие нажатия.
        """
        self.bplaying = False
        Mix_Pause(0)

    def resume_audio(self, event=None):
        """
        Возобновление проигрывания аудио.
        :param event: событие нажатия.
        """
        if not self.bplaying:
            self.bplaying = True
            Mix_Resume(0)

    def set_time_borders(self, start, end, bload, bplay):
        """
        Установка границ области аудио.
        :param start: время начада области аудио в секудах.
        :param end: время конца области аудио в секундах.
        :param bload: флаг для загрузки области аудио в буфер.
        :param bplay: флаг для воспроизведения аудио.
        """
        self.start = start
        self.start_index = int(self.start * self.audio.framerate * self.audio.nchannels)
        self.end = end
        self.end_index = int(self.end * self.audio.framerate * self.audio.nchannels)

        if bload:
            Mix_HaltChannel(0)
            self.load_chunk(self.audio.signals_data, self.start_index, self.end_index, bplay)

    def set_time(self, start, bplay):
        """
        Установка временной отметки в области аудио.
        :param start: время линии отметки времени в секудах.
        :param bplay: флаг для воспроизведения аудио.
        """
        self.current = start
        time = int(self.current * self.audio.framerate * self.audio.nchannels)

        if time < self.start_index:
            time = self.start_index

        Mix_HaltChannel(0)
        self.load_chunk(self.audio.signals_data, time, self.end_index, bplay)

    def load_file(self, chunksize=2048):
        """
        Загрузка аудиофайла в буфер.
        :param chunksize: размер буфера, воспроизводимого в единицу времени, в байтах.
        """
        filename = askopenfilename(
            filetypes=(
                ("WAVE files", "*.wav"),
                ("MP3 files", "*.mp3"),

                ("FLV files", "*.flv"),
                ("MP4 files", "*.mp4"),
            )
        )

        try:
            if filename.endswith("wav"):
                with open(filename, "rb") as wave_sample:
                    params = wave_sample.getparams()

                    self.audio.object = None
                    self.audio.nchannels = params[0]
                    self.audio.sampwidth = params[1]
                    self.audio.framerate = params[2]
                    self.audio.nframes = params[3]
                    self.audio.comptype = params[4]
                    self.audio.compname = params[5]

                    self.audio.signals_data = array(frombuffer(wave_sample.readframes(self.audio.nframes), int16))
            else:
                self.audio.object = AudioSegment.from_file(filename, format=filename.split(".")[-1])

                self.audio.nchannels = self.audio.object.channels
                self.audio.sampwidth = self.audio.object.sample_width
                self.audio.framerate = self.audio.object.frame_rate
                self.audio.nframes = self.audio.object.frame_count()

                self.audio.signals_data = array(frombuffer(self.audio.object.raw_data, int16))

            self.audio.chunksize = chunksize
            self.audio.name = filename

            self.audio.duration = self.audio.nframes / self.audio.framerate
            self.set_time_borders(0.0, self.audio.duration, True, False)

            self.open_player()
        except:
            return

    def save_file(self):
        """
        Запись аудиофайла на компьютер.
        """
        if not self.bactive:
            return

        if self.audio.name.endswith(".wav"):
            with open(self.audio.name, "wb") as wave_sample:
                params = (
                    self.audio.nchannels, self.audio.sampwidth, self.audio.framerate, self.audio.nframes,
                    self.audio.comptype, self.audio.compname
                )
                wave_sample.setparams(params)
                wave_sample.writeframes(self.audio.signals_data.tobytes())
        else:
            self.audio.object = AudioSegment.from_file(
                BytesIO(self.audio.signals_data.tobytes()), format="raw",
                frame_rate=self.audio.framerate, channels=self.audio.nchannels,
                sample_width=self.audio.sampwidth
            )
            self.audio.object.export(self.audio.name, format=self.audio.name.split(".")[-1])

    def save_file_where(self):
        """
        Запись аудиофайла на компьютер с выбором названия и папки.
        """
        if not self.bactive:
            return

        if (self.audio.name.split(".")[-1] == "mp3" or
                self.audio.name.split(".")[-1] == "flv" or
                self.audio.name.split(".")[-1] == "mp4"):
            filetype = [("MP3 files", "*.mp3")]
        else:
            filetype = [("WAVE files", "*.wav")]

        file = asksaveasfile(
            mode="w", defaultextension=self.audio.name.split(".")[-1],
            filetypes=filetype
        )
        if file is None:
            return

        if self.audio.name.endswith(".wav"):
            file.write("")
            with open(file.name, "w") as wave_sample:
                params = (
                    self.audio.nchannels, self.audio.sampwidth, self.audio.framerate, self.audio.nframes,
                    self.audio.comptype, self.audio.compname
                )
                wave_sample.setparams(params)
                wave_sample.writeframes(self.audio.signals_data.tobytes())
        else:
            self.audio.object = AudioSegment.from_file(
                BytesIO(self.audio.signals_data.tobytes()), format="raw",
                frame_rate=self.audio.framerate, channels=self.audio.nchannels,
                sample_width=self.audio.sampwidth
            )
            if self.audio.name.split(".")[-1] != "wav":
                self.audio.object.export(file.name, format="mp3")
            else:
                self.audio.object.export(file.name, format=self.audio.name.split(".")[-1])

    def load_chunk(self, chunk, start_index, end_index, play, loops=0):
        """
        Установка аудиобуфера.
        :param chunk: аудиобуфер.
        :param start_index: индекс начала области аудио.
        :param end_index: индекс конца области аудио.
        :param play: флаг для проигрывания аудио.
        :param loops: количество циклов воспроизведения.
        """
        if len(self.audio.signals_data) == 0:
            return

        if start_index < 0:
            start_index = 0
        if end_index >= len(chunk) - 1:
            end_index = len(chunk) - 1

        buflen = len(chunk[start_index: end_index]) * self.audio.nchannels
        buffer = (c_ubyte * buflen).from_buffer_copy(chunk[start_index: end_index])

        self.chunk = Mix_QuickLoad_RAW(cast(buffer, POINTER(c_ubyte)), buflen)
        self.play_chunk(self.chunk, loops) if play else self.pause_audio()

    def play_chunk(self, chunk, loops):
        """
        Воспроизведение аудио.
        :param chunk: аудиобуфер.
        :param loops: количество циклов воспроизведения.
        """
        if len(self.audio.signals_data) == 0:
            return

        Mix_Volume(0, self.volume)
        if Mix_Paused(0):
            Mix_Resume(0)
        else:
            Mix_HaltChannel(0)
            Mix_PlayChannel(0, chunk, loops)
        self.bplaying = True

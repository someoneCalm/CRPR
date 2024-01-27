from numpy import array, int16, concatenate, zeros, copy
from command import Command


class Audio:
    def __init__(self):
        self.name = ""
        self.object = None

        self.nchannels = 0
        self.sampwidth = 0
        self.framerate = 0
        self.nframes = 0
        self.comptype = "NONE"
        self.compname = "not compressed"

        self.chunksize = 0
        self.copy_buffer = array([], dtype=int16)
        self.signals_data = array([], dtype=int16)

        self.duration = 0.0

    def copy_audio(self, start_index, end_index):
        """
        Копирование области аудио.
        :param start_index: индекс начала области аудио.
        :param end_index: индекс конца области аудио.
        """
        if len(self.signals_data) == 0:
            return

        self.copy_buffer = self.signals_data[start_index: end_index]


class CutCommand(Command):
    def __init__(self, bcopy, **kwargs):
        super().__init__(**kwargs)
        self.bcopy = bcopy

    def do(self):
        """
        Удаление области аудио.
        """
        if super().do():
            if self.bcopy:
                self.audio.copy_buffer = array(self.audio.signals_data[self.start_index: self.end_index])

            self.audio.signals_data = array(
                concatenate((
                    self.audio.signals_data[:self.start_index],
                    self.audio.signals_data[self.end_index:]
                ))
            )

            self.audio.nframes = len(self.audio.signals_data) // self.audio.nchannels
            self.audio.duration = self.audio.nframes / self.audio.framerate

    def undo(self):
        """
        Отмена удаления области аудио.
        """
        if super().undo():
            self.audio.signals_data = array(
                concatenate((
                    self.audio.signals_data[: self.start_index],
                    self.buffer,
                    self.audio.signals_data[self.start_index:]
                ))
            )

            self.audio.nframes = len(self.audio.signals_data) // self.audio.nchannels
            self.audio.duration = self.audio.nframes / self.audio.framerate


class PasteCommand(Command):
    def __init__(self, breplace, **kwargs):
        super().__init__(**kwargs)
        self.breplace = breplace

    def do(self):
        """
        Вставка области аудио.
        """
        if super().do():
            if self.breplace:
                self.audio.signals_data = array(
                    concatenate((
                        self.audio.signals_data[:self.start_index],
                        self.audio.copy_buffer,
                        self.audio.signals_data[self.end_index:]
                    ))
                )
            else:
                self.audio.signals_data = array(
                    concatenate((
                        self.audio.signals_data[:self.start_index],
                        self.audio.copy_buffer,
                        self.audio.signals_data[self.start_index:]
                    ))
                )
                self.audio.nframes = len(self.audio.signals_data) // self.audio.nchannels
                self.audio.duration = self.audio.nframes / self.audio.framerate

    def undo(self):
        """
        Отмена вставки области аудио.
        """
        if super().undo():
            if self.breplace:
                self.audio.signals_data = array(
                    concatenate((
                        self.audio.signals_data[:self.start_index],
                        self.buffer,
                        self.audio.signals_data[self.end_index:]
                    ))
                )
            else:
                self.audio.signals_data = array(
                    concatenate((
                        self.audio.signals_data[:self.start_index],
                        self.audio.signals_data[self.end_index:]
                    ))
                )
                self.audio.nframes = len(self.audio.signals_data) // self.audio.nchannels
                self.audio.duration = self.audio.nframes / self.audio.framerate


class NullifyCommand(Command):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def do(self):
        """
        Обнуление области аудио.
        """
        if super().do():
            self.audio.signals_data = array(
                concatenate((
                    self.audio.signals_data[:self.start_index],
                    array(
                        zeros(len(self.buffer), dtype=int16)
                    ),
                    self.audio.signals_data[self.end_index:]
                ))
            )

    def undo(self):
        """
        Отмена обнуления области аудио.
        """
        if super().undo():
            self.audio.signals_data = array(
                concatenate((
                    self.audio.signals_data[:self.start_index],
                    self.buffer,
                    self.audio.signals_data[self.end_index:]
                ))
            )


class FadeCommand(Command):
    def __init__(self, seconds, bout, **kwargs):
        super().__init__(**kwargs)
        self.seconds = seconds
        self.bout = bout

    def do(self):
        """
        Эффект нарастания/затухания громкости области аудио.
        """
        if super().do():
            interm_data = copy(self.buffer)
            indexes = self.seconds * self.audio.framerate * self.audio.nchannels
            if not self.bout:
                k = 0
                for index in range(0, len(interm_data)):
                    interm_data[index] *= k
                    k += 1 / indexes
                    if k >= 1:
                        break
            else:
                k = 1
                for index in range(0, len(interm_data)):
                    interm_data[index] *= k
                    k -= 1 / indexes
                    if k <= 0:
                        break
            self.audio.signals_data = array(
                concatenate((
                    self.audio.signals_data[:self.start_index],
                    interm_data,
                    self.audio.signals_data[self.end_index:]
                ))
            )
            del interm_data

    def undo(self):
        """
        Отмена эффекта нарастания/затухания громкости области аудио.
        """
        if super().undo():
            self.audio.signals_data = array(
                concatenate((
                    self.audio.signals_data[:self.start_index],
                    self.buffer,
                    self.audio.signals_data[self.end_index:]
                ))
            )


class VolumeCommand(Command):
    def __init__(self, volume, **kwargs):
        super().__init__(**kwargs)
        self.volume = volume

    def do(self):
        """
        Изменение громкости области аудио.
        """
        if super().do():
            self.audio.signals_data = array(
                concatenate((
                    self.audio.signals_data[: self.start_index],
                    (self.buffer * (self.volume / 100)).astype(dtype=int16),
                    self.audio.signals_data[self.end_index:]
                ))
            )

    def undo(self):
        """
        Отмена изменения громкости области аудио.
        """
        if super().undo():
            self.audio.signals_data = array(
                concatenate((
                    self.audio.signals_data[: self.start_index],
                    self.buffer,
                    self.audio.signals_data[self.end_index:]
                ))
            )

class CommandBuffer:
    def __init__(self):
        self.buffer = [0] * 3
        self.index = 0

    def add(self, command):
        """
        Добавление команды в буфер.
        """
        if self.index >= len(self.buffer):
            self.extend()

        self.buffer[self.index] = command
        command.do()

        if self.index < len(self.buffer) and self.buffer[self.index] is not None:
            self.clean()

    def clean(self):
        """
        Очищение буфера команд.
        """
        self.buffer[self.index:] = [0] * (len(self.buffer) - self.index)

    def extend(self):
        self.buffer = self.buffer[1:] + [0]
        self.index = len(self.buffer) - 1


command_buffer = CommandBuffer()


class Command:
    def __init__(self, audio, start_index, end_index):
        self.audio = audio

        self.start_index = start_index
        self.end_index = end_index

        self.buffer = self.audio.signals_data[self.start_index: self.end_index]

    def undo(self):
        """
        Отмена совершенного изменения аудио.
        """
        if command_buffer.index <= 0:
            return False

        command_buffer.index -= 1
        return True

    def do(self):
        """
        Совершение изменения аудио.
        """
        if command_buffer.index >= len(command_buffer.buffer):
            return False

        command_buffer.index += 1
        return True

from eline import EdgeLine
from tkinter import Canvas, Label
from tline import TimeLine
from numpy import absolute


class ScrollableCanvas(Canvas):
    def __init__(self, player, **keyargs):
        Canvas.__init__(self, **keyargs)

        self.loaded = False
        self.player = player

        self.signals = []
        self.signals_count = 1

        self.pixel_values = [
            2,
            1,
            5,
            10,
            30,
            60
        ]
        self.pixels_per_second = 60 // self.pixel_values[self.pixel_values[0]]

        self.bdrawing = False
        self.block = False

        self.s_line = EdgeLine(
            master=self.master, x=0,
            height=400, width=0, bg="grey"
        )
        self.e_line = EdgeLine(
            master=self.master, x=0,
            height=400, width=0, bg="grey"
        )
        self.t_line = TimeLine(
            player=self.player, master=self,
            s_line=self.s_line, e_line=self.e_line,
            interval=0, x=0, height=400, width=0, bg="purple"
        )
        self.labels = [0, [Label()]]
        self.pack(side="top", fill="x")

        self.bind("<ButtonPress-1>", lambda e, x=False: self.set_line(e, x))
        self.bind("<ButtonPress-3>", lambda e, x=True: self.set_line(e, x))

    def change_lines_position(self, start, end, xstart, xend, bplay):
        """
        Установка позиции линий.
        :param start: время начада области аудио в секудах.
        :param end: время конца области аудио в секудах.
        :param xstart: индекс начала области аудио.
        :param xend: индекс конца области аудио.
        :param bplay: флаг для проигрывания аудио.
        """
        self.s_line.change_position(xstart)
        self.e_line.change_position(xend)
        self.player.set_time_borders(start, end, True, bplay)

    def set_line(self, event, bend):
        """
        Событие установки позиции линий.
        :param event: событие нажатия.
        :param bend: флаг для разделения типа линий.
        """
        if self.bdrawing or self.signals_count < 1:
            return

        time = self.player.start - self.player.end if bend else self.player.end - self.player.start
        start = self.canvasx(event.x) * self.player.audio.duration / self.signals_count
        if self.block:
            end = (
                    (self.canvasx(event.x) + time * self.pixels_per_second) *
                    self.player.audio.duration / self.signals_count
            )
            if bend:
                if self.canvasx(event.x) + time * self.pixels_per_second < 0:
                    return

                self.change_lines_position(
                    end, start, self.canvasx(event.x) + time * self.pixels_per_second,
                    self.canvasx(event.x), self.player.bplaying
                )
            else:
                if self.canvasx(event.x) + time * self.pixels_per_second > self.signals_count - 4:
                    return

                self.change_lines_position(
                    start, end, self.canvasx(event.x),
                    self.canvasx(event.x) + time * self.pixels_per_second, self.player.bplaying
                )
        else:
            if bend:
                if self.s_line.x < self.canvasx(event.x):
                    self.e_line.change_position(self.canvasx(event.x))

                    self.player.set_time_borders(self.player.start, start, True, self.player.bplaying)
            else:
                if self.e_line.x > self.canvasx(event.x):
                    self.s_line.change_position(self.canvasx(event.x))

                    self.player.set_time_borders(start, self.player.end, True, self.player.bplaying)

            self.t_line.change_position(self.s_line.x, True)

        self.t_line.change_position(self.s_line.x, True)

    def draw(self, bstart=False, bend=False, btime=False):
        """
        Отрисовка аудиодорожки.
        :param bstart: флаг для сброса линии начала границы области аудио.
        :param bend: флаг для сброса линии конца границы области аудио.
        :param btime: флаг для сброса линии отметки времени области аудио.
        """
        if len(self.player.audio.signals_data) == 0:
            self.delete("all")
            if len(self.labels) > 1:
                for i in self.labels[1]:
                    i.destroy()
            self.reset_lines(bstart, bend, btime)
            return

        self.pixels_per_second = 60 // self.pixel_values[self.pixel_values[0]]
        self.signals_count = int(self.player.audio.duration * self.pixels_per_second)

        if self.signals_count < 1:
            self.signals_count = 1
            width = 0
        else:
            width = self.signals_count

        self.config(
            width=width, height=400 - 2
        )

        if not self.loaded:
            self.s_line.config(width=4)
            self.e_line.config(width=4)
            self.t_line.config(width=4)
            self.reset_lines(True, True, True)
            self.loaded = True

        self.delete("all")
        self.update()

        self.master.master.config(
            scrollregion=(
                0, 0, self.signals_count, 0
            )
        )
        self.reset_lines(bstart, bend, btime)
        self.create_line(0, 200, self.signals_count, 200, width=1, fill="white")
        self.create_line(self.signals_count - 1, 0, self.signals_count - 1, 400, width=1, fill="white")

        if self.player.audio.nchannels == 2:
            buflen = len(self.player.audio.signals_data[0::2])
        else:
            buflen = len(self.player.audio.signals_data)

        step = int(buflen // self.signals_count)

        if self.player.audio.nchannels == 2:
            self.signals = [
                self.player.audio.signals_data[0::2][i: i + step]
                for i in range(0, buflen - step, step)
            ]
        else:
            self.signals = [
                self.player.audio.signals_data[i: i + step]
                for i in range(0, buflen - step, step)
            ]

        xlineposition = 0
        if len(self.labels) > 1:
            for i in self.labels[1]:
                i.destroy()
            self.labels = [0, [0] * int(self.player.audio.duration / self.pixel_values[self.pixel_values[0]] + 1)]

        for index in range(self.signals_count):
            if index > len(self.signals) - 1:
                break

            self.bdrawing = True
            average = sum(absolute(self.signals[index])) // len(self.signals[index])
            self.create_line(xlineposition, 200 - average // 110, xlineposition, 200 + average // 110,
                             width=1, fill="white")

            if xlineposition % 12 == 0:
                if xlineposition % 60 == 0:
                    self.create_line(xlineposition, 400, xlineposition, 375, width=1, fill="white")

                    seconds = self.labels[0] * self.pixel_values[self.pixel_values[0]]
                    self.labels[1][self.labels[0]] = Label(
                        master=self, text=f"{seconds // 60}:{(seconds - (seconds // 60) * 60)}:00",
                        bg="#1E1F22", fg="white"
                    )
                    self.labels[1][self.labels[0]].place(x=xlineposition - 2, y=355)
                    self.labels[0] += 1

                self.create_line(xlineposition, 390, xlineposition, 385, width=1, fill="white")

            if xlineposition % 7 == 0:
                self.update()

            xlineposition += 1

        self.bdrawing = False

    def change_scale(self, badd):
        """
        Масштабирование аудиодорожки.
        :param badd: флаг для увеличения.
        """
        if self.signals_count == 0 or self.bdrawing:
            return

        self.pixel_values[0] += -1 if badd else 1

        if self.pixel_values[0] >= len(self.pixel_values):
            self.pixel_values[0] = len(self.pixel_values) - 1
            if not badd:
                return

        if self.pixel_values[0] < 1:
            self.pixel_values[0] = 1
            if badd:
                return

        if badd:
            xmul = self.pixel_values[self.pixel_values[0] + 1] / self.pixel_values[self.pixel_values[0]]
        else:
            xmul = 1 / (self.pixel_values[self.pixel_values[0]] / self.pixel_values[self.pixel_values[0] - 1])

        self.pixels_per_second = 60 // self.pixel_values[self.pixel_values[0]]
        self.signals_count = int(self.player.audio.duration * self.pixels_per_second)

        xend = self.e_line.x * xmul
        if xend > self.signals_count - 4:
            xend = self.signals_count - 4

        self.change_lines_position(self.player.start, self.player.end, self.s_line.x * xmul, xend, False)

        self.t_line.change_position(self.s_line.x, False)
        self.t_line.interval = self.pixel_values[self.pixel_values[0]] / 60

        self.draw(btime=True)

    def reset_lines(self, bstart, bend, btime):
        """
        Событие сброса позиции линий.
        :param bstart: флаг для сброса линии начала границы области аудио.
        :param bend: флаг для сброса линии конца границы области аудио.
        :param btime: флаг для сброса линии отметки времени области аудио.
        """
        if self.signals_count == 0:
            return

        if self.loaded:
            if bstart:
                self.s_line.change_position(0)

            if bend:
                self.e_line.change_position(self.signals_count - 4)

            if btime:
                self.t_line.pause()
                self.t_line.change_position(0, True)
                self.t_line.interval = self.pixel_values[self.pixel_values[0]] / 60

from tkinter import Frame, Label, StringVar
from threading import Thread, Event
from time import sleep


class TimeLine(Frame):
    def __init__(self, s_line, e_line, player, x, interval, **keyargs):
        Frame.__init__(self, **keyargs)

        self.s_line = s_line
        self.e_line = e_line

        self.player = player

        self.x = x
        self.place(x=self.x)

        self.time = 0.0
        self.interval = interval

        self.event = Event()
        self.event.clear()
        self.bend = False

        self.thread = Thread(target=self.movement, args=(self.event,))
        self.thread.start()

        self.label = Label(master=self.master)
        self.string = StringVar()
        self.string.set("0.0")

        self.label.place(x=5, y=330)
        self.label.config(textvariable=self.string, width=0, bg="#1E1F22", fg="white")

    def start(self):
        """
        Запуск движения линии.
        """
        self.bend = False
        self.event.set()
        if not self.player.bplaying:
            self.player.bplaying = True

    def pause(self):
        """
        Остановка движения линии.
        """
        self.event.clear()
        if self.player.bplaying:
            self.player.bplaying = False

    def change_position(self, x, bchange):
        """
        Смена позиции линии.
        :param x: координата x.
        :param bchange: флаг для смены текста надписи.
        """
        if x < self.s_line.x:
            x = self.s_line.x

        if x >= self.e_line.x:
            x = self.e_line.x
            self.bend = True
        else:
            self.bend = False

        self.x = x
        self.place(x=self.x)

        if self.master.signals_count < 1:
            xpos = 0.0
        else:
            xpos = x * self.player.audio.duration / self.master.signals_count

        self.time = xpos
        self.player.current = self.time

        if bchange:
            self.set(self.x + 5, self.time)

    def movement(self, event):
        """
        Движение линии.
        :param event: событие.
        """
        while True:
            sleep(self.interval)
            self.event.wait()

            self.set(self.x + 5, self.time)

            if self.x >= self.e_line.x:
                self.pause()
                self.bend = True
            else:
                self.change_position(self.x + 1, True)

    def set(self, x, text):
        """
        Изменение текста надписи и ее позиции.
        :param x: координата x.
        :param text: текст надписи.
        """
        dint, dloat = f"{text}".split(".")
        self.string.set(dint + "." + dloat[:1])
        self.label.place(x=x)

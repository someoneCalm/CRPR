from tkinter import Frame


class EdgeLine(Frame):
    def __init__(self, x, **keyargs):
        Frame.__init__(self, **keyargs)

        self.x = x
        self.place(x=self.x)

    def change_position(self, x):
        """
        Смена позиции линии.
        :param x: координата x.
        """
        self.x = x
        self.place(x=self.x)

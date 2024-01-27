from canvas import ScrollableCanvas
from tkinter import Tk, Frame, Canvas, Scrollbar


# Поудалять ненужные объявления?
class Window(Tk):
    def __init__(self, player):
        Tk.__init__(self)

        self.title(".wav Editor")
        self.config(bg="#1E1F22")
        self.iconbitmap("music_icon.ico")
        self.geometry(f"{self.winfo_screenwidth() - 500}x500+0+0")
        self.resizable(True, False)

        self.scrollbar = Scrollbar(master=self, orient="horizontal")
        self.scrollbar.pack(side="top", anchor="n", fill="x")

        self.canvas = Canvas(
            master=self, height=400,
            xscrollcommand=self.scrollbar.set, bg="#1E1F22"
        )
        self.scrollbar.config(command=self.canvas.xview)

        self.scrollable_frame = Frame(master=self.canvas)
        self.canvas.create_window(0, 0, window=self.scrollable_frame, anchor="nw")

        self.scrollable_canvas = ScrollableCanvas(
            player=player,
            master=self.scrollable_frame,
            width=0, height=0,
            bg="#1E1F22", bd=0,
            highlightthickness=0
        )
        self.frame = Frame(master=self, bg="#1E1F22")
        self.canvas.pack(side="top", anchor="n", fill="x")
        self.frame.pack(side="top", anchor="n", fill="both")


from audio import Audio, CutCommand, PasteCommand, NullifyCommand, VolumeCommand, FadeCommand
from audioplayer import AudioPlayer
from command import command_buffer
from sdl2.sdlmixer import Mix_Paused, Mix_Volume, Mix_Pause
from tkinter import PhotoImage, Button, Scale, Menu
from window import Window


if __name__ == "__main__":
    audio = Audio()
    player = AudioPlayer(audio)
    window = Window(player)
    canvas = window.scrollable_canvas
    t_line = canvas.t_line


    def load_file():
        """
        Событие нажатия на кнопку загрузки аудио.
        """
        player.load_file()
        canvas.draw(True, True, True)


    def play_audio():
        """
        Событие нажатия на кнопку воспроизведения аудио.
        """
        if len(audio.signals_data) == 0:
            return

        if not player.bactive:
            player.open_player()

        if not player.bplaying:
            if t_line.bend:
                t_line.change_position(canvas.s_line.x, True)
                player.set_time_borders(player.start, player.end, True, True)
            else:
                player.set_time(player.current, True)
            t_line.start()


    def stop_audio():
        """
        Событие нажатия на кнопку остановки воспроизведения аудио.
        """
        player.pause_audio()
        t_line.pause()


    def skip_audio(bback):
        """
        Событие нажатия на кнопку загрузки.
        :param bback: флаг для направления пропуска.
        """
        value = -(300 / canvas.pixel_values[canvas.pixel_values[0]]) if bback else (
                300 / canvas.pixel_values[canvas.pixel_values[0]])
        t_line.change_position(t_line.x + value, True)
        if player.current <= 0.0:
            return

        if not t_line.bend and not Mix_Paused(0):
            player.set_time(player.current, True)
            t_line.start()
        else:
            Mix_Pause(0)


    def lock_lines():
        """
        Событие нажатия на кнопку закрепления линий.
        """
        canvas.block = not canvas.block
        lock_button.config(image=bimages[8] if canvas.block else bimages[9])


    def copy_audio():
        """
        Событие нажатия на кнопку копирования области аудио.
        """
        audio.copy_audio(player.start_index, player.end_index)
        if not canvas.block:
            lock_lines()


    def cut_audio(bcopy):
        """
        Событие нажатия на кнопки удаления и выреза области аудио.
        :param bcopy: флаг для копирования области аудио.
        """
        command_buffer.add(
            CutCommand(
                audio=audio, bcopy=bcopy, start_index=player.start_index, end_index=player.end_index
            )
        )
        player.set_time_borders(0.0, audio.duration, True, False)
        canvas.draw(True, True, True)
        if canvas.block:
            lock_lines()


    def paste_audio(breplace):
        """
        Событие нажатия на кнопку вставки области аудио.
        :param breplace: флаг для замены области аудио.
        """
        command_buffer.add(
            PasteCommand(
                audio=audio, breplace=breplace, start_index=player.start_index, end_index=player.end_index,
            )
        )
        player.set_time_borders(player.start, player.end, True, False)
        canvas.draw(True, True, True)


    def nullify_audio():
        """
        Событие нажатия на кнопку обнуления области аудио.
        """
        command_buffer.add(
            NullifyCommand(
                audio=audio, start_index=player.start_index, end_index=player.end_index
            )
        )
        player.set_time_borders(player.start, player.end, True, False)
        canvas.draw(True, True, True)


    def redo():
        if command_buffer.buffer[command_buffer.index] != 0:
            command_buffer.buffer[command_buffer.index].do()

            player.set_time_borders(player.start, player.end, True, False)
            canvas.draw(True, True, True)

    def undo():
        if command_buffer.index - 1 >= 0:
            command_buffer.buffer[command_buffer.index - 1].undo()

            player.set_time_borders(player.start, player.end, True, False)
            canvas.draw(True, True, True)


    def fade_audio(bout):
        """
        Событие нажатия на кнопку нарастания/затухания области аудио.
        :param bout: флаг для затухания.
        """
        command_buffer.add(
                FadeCommand(
                    seconds=player.end - player.start, bout=bout, audio=audio,
                    start_index=player.start_index, end_index=player.end_index
                )
            )
        player.set_time_borders(player.start, player.end, True, False)
        canvas.draw(btime=True)

    def volume_audio():
        """
        Событие нажатия на кнопку изменения громкости области аудио.
        """
        volume = volume_value.get()
        if volume > 0:
            command_buffer.add(
                VolumeCommand(
                    volume=volume, audio=audio, start_index=player.start_index, end_index=player.end_index
                )
            )
        else:
            command_buffer.add(
                NullifyCommand(
                    audio=audio, start_index=player.start_index, end_index=player.end_index
                )
            )
        player.set_time_borders(player.start, player.end, True, False)
        canvas.draw(btime=True)


    def volume_player(value):
        player.volume = int(value)
        Mix_Volume(0, int(value))


    edit_menu = Menu(tearoff=0)
    edit_menu.add_command(label="Копировать", command=lambda: copy_audio())
    edit_menu.add_command(label="Удалить", command=lambda x=False: cut_audio(x))
    edit_menu.add_command(label="Вырезать", command=lambda x=True: cut_audio(x))
    edit_menu.add_command(label="Вставить", command=lambda x=False: paste_audio(x))
    edit_menu.add_command(label="Заменить", command=lambda x=True: paste_audio(x))
    edit_menu.add_command(label="Обнулить", command=lambda: nullify_audio())
    edit_menu.add_command(label="Нарастание", command=lambda x=False: fade_audio(x))
    edit_menu.add_command(label="Затухание",  command=lambda x=True: fade_audio(x))
    edit_menu.add_separator()
    edit_menu.add_command(label="Отменить", command=lambda: undo())
    edit_menu.add_command(label="Вернуть", command=lambda: redo())


    def show_edit_menu(event):
        """
        Событие вызова меню.
        :param event: событие.
        """
        if canvas.bdrawing:
            return

        edit_menu.post(x=event.x_root, y=event.y_root)


    canvas.bind("<ButtonPress-2>", show_edit_menu)

    bimages = [
        PhotoImage(file="load_button.png"),
        PhotoImage(file="save_button.png"),
        PhotoImage(file="save_loc_button.png"),
        PhotoImage(file="play_button.png"),
        PhotoImage(file="pause_button.png"),

        PhotoImage(file="skipb_button.png"),
        PhotoImage(file="skipf_button.png"),

        PhotoImage(file="volume_button.png"),

        PhotoImage(file="lock_button.png"),
        PhotoImage(file="lock2_button.png"),

        PhotoImage(file="less_button.png"),
        PhotoImage(file="more_button.png")
    ]

    load_button = Button(
        master=window,
        image=bimages[0],
        command=lambda: load_file(),
        bd=0, highlightthickness=0
    )
    load_button.place(
        relx=0, x=25, y=420, anchor="n"
    )

    save_button = Button(
        master=window,
        image=bimages[1],
        command=lambda: player.save_file(),
        bd=0, highlightthickness=0
    )
    save_button.place(
        relx=0, x=75, y=420, anchor="n"
    )

    save_as_button = Button(
        master=window,
        image=bimages[2],
        command=lambda: player.save_file_where(),
        bd=0, highlightthickness=0
    )
    save_as_button.place(
        relx=0, x=125, y=420, anchor="n"
    )

    lock_button = Button(
        master=window,
        image=bimages[9],
        command=lambda: lock_lines(),
        bd=0, highlightthickness=0
    )
    lock_button.place(
        relx=0.43, x=-41, y=420, anchor="n"
    )
    skipb_button = Button(
        master=window,
        image=bimages[5],
        command=lambda x=True: skip_audio(x),
        bd=0, highlightthickness=0
    )
    skipb_button.place(
        relx=0.43, x=0, y=420, anchor="n"
    )
    play_button = Button(
        master=window,
        image=bimages[3],
        command=lambda: play_audio(),
        bd=0, highlightthickness=0
    )
    play_button.place(
        relx=0.43, x=50, y=420, anchor="n"
    )
    pause_button = Button(
        master=window,
        image=bimages[4],
        command=lambda: stop_audio(),
        bd=0, highlightthickness=0
    )
    pause_button.place(
        relx=0.43, x=100, y=420, anchor="n"
    )
    skipf_button = Button(
        master=window,
        image=bimages[6],
        command=lambda x=False: skip_audio(x),
        bd=0, highlightthickness=0
    )
    skipf_button.place(
        relx=0.43, x=150, y=420, anchor="n"
    )

    volume_scale = Scale(
        master=window, orient="horizontal", from_=0, to=100, bg="white",
        command=lambda v: volume_player(v)
    )
    volume_scale.set(100)
    volume_scale.place(
        relx=0.43, x=228, y=420, anchor="n"
    )

    volume_value = Scale(
        master=window,
        from_=100, to=0,
        orient="horizontal", bg="white"
    )
    volume_value.set(100)
    volume_value.place(
        relx=1, x=-300, y=420, anchor="n"
    )

    volume_button = Button(
        master=window,
        image=bimages[7],
        command=lambda: volume_audio(),
        bd=0, highlightthickness=0
    )
    volume_button.place(
        relx=1, x=-233, y=420, anchor="n"
    )

    less_button = Button(
        master=window,
        image=bimages[10],
        command=lambda x=False: canvas.change_scale(x),
        bd=0, highlightthickness=0
    )
    less_button.place(
        relx=1, x=-25, y=420, anchor="n"
    )
    more_button = Button(
        master=window,
        image=bimages[11],
        command=lambda x=True: canvas.change_scale(x),
        bd=0, highlightthickness=0
    )
    more_button.place(
        relx=1, x=-75, y=420, anchor="n"
    )

    load_menu = Menu(tearoff=0)
    load_menu.add_command(label="Загрузить", command=lambda: load_file())
    load_menu.add_command(label="Сохранить", command=lambda: player.save_file())
    load_menu.add_command(label="Сохранить...", command=lambda: player.save_file_where())

    window_menu = Menu(tearoff=0)
    window_menu.add_cascade(label="Файл", menu=load_menu)
    window_menu.add_cascade(label="Редактировать", menu=edit_menu)

    window.config(menu=window_menu)
    window.mainloop()

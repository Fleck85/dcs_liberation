from tkinter import *
from game.game import *
from .styles import BG_COLOR,BG_TITLE_COLOR

class Window:
    image = None
    left_pane = None  # type: Frame
    right_pane = None  # type: Frame

    def __init__(self):
        self.tk = Tk()
        self.tk.title("DCS Liberation")
        self.tk.iconbitmap("icon.ico")
        self.tk.resizable(True, True)
        self.tk.grid_columnconfigure(0, weight=1)
        self.tk.grid_rowconfigure(0, weight=1)

        self.frame = Frame(self.tk, bg=BG_COLOR)
        self.frame.grid(column=0, row=0, sticky=NSEW)
        self.frame.grid_columnconfigure(0)
        self.frame.grid_columnconfigure(1)

        self.frame.grid_columnconfigure(0, weight=0)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_rowconfigure(0, weight=0)

        self.left_pane = Frame(self.frame, bg=BG_TITLE_COLOR)
        self.left_pane.grid(row=0, column=0, sticky=NSEW)
        self.right_pane = Frame(self.frame, bg=BG_COLOR)
        self.right_pane.grid(row=0, column=1, sticky=NSEW)

        self.tk.focus()

    def clear_right_pane(self):
        for x in self.right_pane.winfo_children():
            x.grid_remove()

    def clear(self):
        for x in self.left_pane.winfo_children():
            x.grid_remove()
        for x in self.right_pane.winfo_children():
            x.grid_remove()

    def run(self):
        self.tk.mainloop()


class Menu:
    parent = None  # type: Menu

    def __init__(self, window: Window, parent, game: Game):
        self.window = window
        self.parent = parent
        self.game = game

    def dismiss(self):
        self.parent.display()

    def display(self):
        pass

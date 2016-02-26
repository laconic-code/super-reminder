from time import *
from sys import argv
from Tkinter import *

FONT_NAME = "Arial"
FONT_SIZE = 60

"""
TODO:
    Create an actual file format
    make an actual parser for it
    take in style formatting
"""

class SuperReminder(Tk):
    def __init__(self, *args, **kwargs):
        path = kwargs.pop('path', '')
        Tk.__init__(self, *args, **kwargs)

        self.attributes('-fullscreen', True)
        self.quit_button = Button(self, text="Okay", command=self.quit)
        
        with open(path) as f:
            text = f.readlines()[1:]
        text = ''.join(text)
        self.message_label = Label(self, text=text, font=(FONT_NAME, FONT_SIZE))
        
        self.time_str = StringVar()
        self.time_label = Label(self, textvariable=self.time_str, font=(FONT_NAME, FONT_SIZE), fg="darkred")
        
        
        self.quit_button.pack(side=RIGHT, anchor=SE)        
        self.time_label.pack(side=TOP, anchor=NW)
        self.message_label.pack(side=TOP, fill="both", expand=True)
        
        self.after(100, self.update)
        
    def update(self, *args):
        self.time_str.set(strftime("%I:%M:%S %p"))
        self.after(100, self.update)

if __name__ == "__main__":
    root = SuperReminder(path=argv[1]);
    root.mainloop();


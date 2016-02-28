from time import *
from sys import argv
from Tkinter import *
import datetime

import Reminder

FONT_NAME = "Arial"
FONT_SIZE = 40

"""
TODO:

"""

class SuperReminder(Tk):
    def __init__(self, reminder, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.attributes('-fullscreen', True)

        self.button_frame = Frame(self)
        self.quit_button = Button(self.button_frame, text="Dismiss", command=self.quit)

        text = ''.join(reminder.text)
        self.message_label = Label(self, text=reminder.text, font=reminder.font)

        self.time_frame = Frame(self)
        self.time_str = StringVar()
        self.countdown_str = StringVar()
        self.time_label = Label(self.time_frame , textvariable=self.time_str, font=(FONT_NAME, FONT_SIZE), fg="darkred")
        self.countdown_label = Label(self.time_frame , textvariable=self.countdown_str, font=(FONT_NAME, FONT_SIZE), fg="darkred")
        self.out_of_time = False

        self.time_frame.pack(side=TOP, fill="x")
        self.time_label.pack(side=LEFT, anchor=NW)
        self.countdown_label.pack(side=TOP, anchor=NE)

        self.message_label.pack(fill="both", expand=True)


        self.button_frame.pack(side=BOTTOM, fill='x')
        self.quit_button.pack(side=RIGHT, anchor=SE)

        self.after(100, self.update)

    def update(self, *args):
        countdown_str = "0:00:00"
        if not self.out_of_time:
            delta = reminder.time - datetime.datetime.now()
            delta = delta - datetime.timedelta(microseconds=delta.microseconds, days=delta.days)
            if delta.total_seconds() > 0:
                countdown_str = str(delta)
            else:
                self.out_of_time = True
                for element in (self.time_frame, self.time_label, self.countdown_label, self.message_label, self.button_frame):
                    element.config(bg="darkgrey")

        self.countdown_str.set(countdown_str + " Left")
        self.time_str.set(strftime("%I:%M:%S %p"))

        self.after(100, self.update)

if __name__ == "__main__":
    reminder = Reminder.parse_file(argv[1])
    root = SuperReminder(reminder);
    root.mainloop();


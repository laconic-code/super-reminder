from time import *
from sys import argv
from Tkinter import *
import datetime
import colorsys

import Reminder

FONT_NAME = "Arial"
FONT_SIZE = 40
class COLOR_SCHEME:
    HSV = 'hsv'
    RGB = 'rgb'
    TOGGLE = 'toggle'
COLOR = COLOR_SCHEME.TOGGLE

"""
TODO:

"""

def map_yellow_to_red(percentage):
    """maps decreasing percentage to redder values"""
    if COLOR == COLOR_SCHEME.HSV:
        # 0.2 is yellow
        # 0.0 is red
        r, g, b = colorsys.hsv_to_rgb(.20 * percentage, 1.0, 1.0)
        return '#%02x%02x%02x' % (255 * r, 255 * g, 255 * b)

    if COLOR == COLOR_SCHEME.RGB:
        return '#%02x%02x%02x' % (255, 255 * percentage, 0)

    if COLOR == COLOR_SCHEME.TOGGLE:
        # yellow four-fifths, red the last fifth
        if percentage < 0.2:
            return 'red'
        return 'yellow'

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

            color = None
            if delta.total_seconds() < 300:
                # < 5 minutes
                color = map_yellow_to_red(float(delta.total_seconds() / 300.0))
                for element in (self.time_frame, self.time_label, self.countdown_label, self.button_frame):
                    element.config(bg=color)
                for element in (self.time_label, self.countdown_label):
                    element.config(fg='black')

        self.countdown_str.set(countdown_str + " Left")
        self.time_str.set(strftime("%I:%M:%S %p"))

        self.after(100, self.update)

if __name__ == "__main__":
    reminder = Reminder.parse_file(argv[1])
    root = SuperReminder(reminder);
    root.mainloop();


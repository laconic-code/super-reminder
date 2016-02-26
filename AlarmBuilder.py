#!/usr/bin/env python
from time import *
from sys import argv
from os import environ
from os.path import join
from Tix import *
from tkFileDialog import *
import tkFont

CONFIG_DIR = join(environ['HOME'], '.super_reminder/')
DAYS = 'Monday Tuesday Wednesday Thursday Friday Saturday Sunday'.split()
SIZES = [6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 21, 24, 36, 48, 60, 72, 80, 88, 96]

"""
TODO:
    Figure out style strings for alarms
        should they always be line 2?
        should they be optionally tagged onto the time line?
    opening AlarmBuilder creates the hidden directory
    opening a file in Alarm builder imports ALL of its settings
    make about page
    save as and saves actually save ALL values to the file in the correct format
        be sure to use everyday if all days are selected
        
OPTIONAL:
    maybe allow am and pm format?


"""


class CenteredText(Text):
    def __init__(self, *args, **kwargs):
        callback = kwargs.pop('callback', lambda *_, **__: None)
        Text.__init__(self, *args, **kwargs)
        self.callback = callback
        self.clear_modified()
        self.bind_all('<<Modified>>', self._modified)
        
    def _modified(self, event=None):
        if self._lock_flag:
            return
        self.clear_modified()
        self.callback(event)
        
    def clear_modified(self):
        self._lock_flag = True
        try:
            self.tk.call(self._w, 'edit', 'modified', 0)
        finally:
            self._lock_flag = False

class Builder(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        
        self.wm_title("Alarm Builder")
                    
        ############
        # Menu Bar #
        ############
        
        self.menu_bar = Menu(self)
        
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="New", command=self.new)
        file_menu.add_separator()
        file_menu.add_command(label="Open", command=self.open)
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=self.save)
        file_menu.add_command(label="Save As", comman=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.quit)
        self.file_menu = file_menu
        
        help_menu = Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.about)
        self.help_menu = help_menu
        
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.config(menu=self.menu_bar)
        
        ###########
        # Widgets #
        ###########
        
        self.entry_frame = Frame(self)
        self.entry_centered_frame = Frame(self.entry_frame)
        
        self.hour = StringVar()
        self.minute = StringVar()
        self.hour_entry = ComboBox(self.entry_centered_frame, label="Hour: ", variable=self.hour, dropdown=1, editable=1)
        self.minute_entry = ComboBox(self.entry_centered_frame, label="Minute: ", variable=self.minute, dropdown=1, editable=1)
        
        self.day_chooser = Listbox(self.entry_centered_frame, selectmode=EXTENDED, height=7, width=(len(max(DAYS, key=len)) + 1))
        
        fonts = sorted([x for x in tkFont.families() if not x.startswith('@')])
        self.font_name = StringVar()
        self.font_size = StringVar()
        self.font_name_chooser = ComboBox(self.entry_centered_frame, label="Font: ", dropdown=1, editable=0, variable=self.font_name)
        self.font_size_chooser = ComboBox(self.entry_centered_frame, label="Size:  ", dropdown=1, editable=1, variable=self.font_size)
        
        ############
        # Defaults #
        ############

        self.hour.set('12')
        self.minute.set('00')
        self.font_name.set(fonts[0])
        self.font_size.set('12')
        for day in DAYS:
            self.day_chooser.insert(END, day)
        for hour in range(0,24):
            self.hour_entry.insert(END, str(hour).zfill(2))
        for minute in range(0, 60):
            self.minute_entry.insert(END, str(minute).zfill(2))
        for font in fonts:
            self.font_name_chooser.insert(END, font)
        for size in SIZES:
            self.font_size_chooser.insert(END, size)
        
        ###########################
        # Text Entry Box Specific #
        ###########################
        
        self.message_entry_frame = Frame(self)
        self.message_entry_frame.grid_propagate(False)
        self.message_entry_frame.grid_rowconfigure(0, weight=1)
        self.message_entry_frame.grid_columnconfigure(0, weight=1)
        
        self.message_entry = CenteredText(self.message_entry_frame, callback=self._recenter)
        self.message_entry.tag_configure("center-tag", justify='center')
        self.message_entry.tag_add("center-tag", 1.0, END)
        
        ###########
        # Packing #
        ###########
        
        self.entry_frame.pack(side=TOP, expand=False, fill="both")
        self.message_entry_frame.pack(side=TOP, expand=True, fill="both")

        self.entry_centered_frame.pack()
        
        self.day_chooser.grid(      row=0, column=0, sticky="nsew", rowspan=2)
        self.hour_entry.grid(       row=0, column=1, sticky="nsew", padx=10)
        self.minute_entry.grid(     row=0, column=2, sticky="nsew", padx=10)
        self.font_name_chooser.grid(row=1, column=1, sticky="nsew", padx=10)
        self.font_size_chooser.grid(row=1, column=2, sticky="nsew", padx=10)
        
        self.message_entry.grid(row=0, column=0, sticky="nsew")
        
        #############
        # Callbacks #
        #############
        
        self.font_name.trace("w", self._font_change)
        self.font_size.trace("w", self._font_change)
        self.hour.trace("w", self._time_change)
        self.minute.trace("w", self._time_change)
        
    def new(self, *args, **kwargs):
        self.message_entry.delete(1.0, END)
        self._current_file = None
        self.wm_title("Alarm Builder: *Untitled*")
        
    def open(self, *args, **kwargs):
        file_path = askopenfilename(initialdir=CONFIG_DIR)
        if file_path:
            self.message_entry.delete(1.0, END)
            with open(file_path) as f:
                contents = f.readlines()
            message = ''.join(contents[1:])
            self.message_entry.insert(1.0, message, 'center-tag')
            self._current_file = file_path
            self.wm_title("Alarm Builder: %s" % self._current_file)
        
    def save(self, *args, **kwargs):
        if self._current_file:
            pass
        else:
            self.save_as(*args, **kwargs)
        
    def save_as(self, *args, **kwargs):
        file_path = asksaveasfilename(initialdir=CONFIG_DIR)
        with open(file_path, 'w+') as f:
            contents = text.get(1.0, END)
            f.write(contents)
        self._current_file = file_path
        self.wm_title("Alarm Builder: %s" % self._current_file)

    def about(self, *args, **kwargs):
        pass
 
    def _font_change(self, *args, **kwargs):
        if not self.font_size.get().isdigit():
            self.font_size.set('12')
        self.message_entry.config(font=(self.font_name.get(), int(self.font_size.get())))
        
    def _recenter(self, *args, **kwargs):
        self.message_entry.tag_remove("center-tag", 1.0, "end")
        self.message_entry.tag_add("center-tag", 1.0, "end")
        
    def _time_change(self, *args, **kwargs):
        for var in (self.hour, self.minute):
            if not var.get().isdigit():
                var.set('00')
            if len(var.get()) != 2:
                var.set(var.get()[-2:].zfill(2))
  
 
if __name__ == "__main__":
    root = Builder()
    root.minsize(800, 600)
    root.mainloop()

#!/usr/bin/env python
from time import *
from sys import argv
from os import environ
from os.path import join
from Tix import *
from tkFileDialog import *
import Reminder
from Reminder import FONTS
import tkMessageBox

CONFIG_DIR = join(environ['HOME'], '.super_reminder/')
DAYS = 'Monday Tuesday Wednesday Thursday Friday Saturday Sunday'.split()
SIZES = [6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 21, 24, 36, 48, 60, 72, 80, 88, 96]

"""
TODO:
    make about page
    warn if quiting and unsaved
    show if edited but unsaved
        
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
        self._current_file = None
        
        ############
        # Menu Bar #
        ############
        
        self.menu_bar = Menu(self)
        
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="New", command=self.new, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Open", command=self.open, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=self.save, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", comman=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.quit, accelerator="Ctrl+Q")
        self.file_menu = file_menu
        
        edit_menu = Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", command=lambda: self.focus_get().event_generate('<<Undo>>'), accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=lambda: self.focus_get().event_generate('<<Redo>>'), accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=lambda: self.focus_get().event_generate('<<Cut>>'), accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", comman=lambda: self.focus_get().event_generate('<<Copy>>'), accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", comman=lambda: self.focus_get().event_generate('<<Paste>>'), accelerator="Ctrl+V")
        self.edit_menu = file_menu
        
        help_menu = Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.about)
        self.help_menu = help_menu
        
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.config(menu=self.menu_bar)
        
        #################
        # Menu Keybinds #
        #################
        
        self.bind_all('<Control-n>', self.new)
        self.bind_all('<Control-o>', self.open)
        self.bind_all('<Control-s>', self.save)
        self.bind_all('<Control-q>', lambda *_: self.quit())
        
        ###########
        # Widgets #
        ###########
        
        self.entry_frame = Frame(self)
        self.entry_centered_frame = Frame(self.entry_frame)
        
        self.hour = StringVar()
        self.minute = StringVar()
        self.hour_entry = ComboBox(self.entry_centered_frame, label="Hour: ", variable=self.hour, dropdown=1, editable=1)
        self.minute_entry = ComboBox(self.entry_centered_frame, label="Minute: ", variable=self.minute, dropdown=1, editable=1)
        
        self.day_chooser = Listbox(self.entry_centered_frame, selectmode=EXTENDED, exportselection=0, height=7, width=(len(max(DAYS, key=len)) + 1))
        
        self.font_name = StringVar()
        self.font_size = StringVar()
        self.font_name_chooser = ComboBox(self.entry_centered_frame, label="Font: ", dropdown=1, editable=0, variable=self.font_name)
        self.font_size_chooser = ComboBox(self.entry_centered_frame, label="Size:  ", dropdown=1, editable=1, variable=self.font_size)
        
        self.warning_time = StringVar()
        self.warning_time_chooser = ComboBox(self.entry_centered_frame, label="Warning Minutes", dropdown=1, editable=1, variable=self.warning_time)
        
        ############
        # Defaults #
        ############

        self.hour.set('12')
        self.minute.set('00')
        self.font_name.set(FONTS[0])
        self.font_size.set('12')
        self.warning_time.set('5')
        for day in DAYS:
            self.day_chooser.insert(END, day)
        for hour in range(0,24):
            self.hour_entry.insert(END, str(hour).zfill(2))
        for minute in range(0, 60):
            self.minute_entry.insert(END, str(minute).zfill(2))
        for font in FONTS:
            self.font_name_chooser.insert(END, font)
        for size in SIZES:
            self.font_size_chooser.insert(END, size)
        for minute in range(0, 121):
            self.warning_time_chooser.insert(END, str(minute))
        
        ###########################
        # Text Entry Box Specific #
        ###########################
        
        self.message_entry_frame = Frame(self)
        self.message_entry_frame.grid_propagate(False)
        self.message_entry_frame.grid_rowconfigure(0, weight=1)
        self.message_entry_frame.grid_columnconfigure(0, weight=1)
        
        self.message_entry = CenteredText(self.message_entry_frame, callback=self._recenter, wrap=WORD, undo=True)
        self.message_entry.tag_configure("center-tag", justify='center')
        self.message_entry.tag_add("center-tag", 1.0, END)
        
        ###########
        # Packing #
        ###########
        
        self.entry_frame.pack(side=TOP, expand=False, fill="both")
        self.message_entry_frame.pack(side=TOP, expand=True, fill="both")

        self.entry_centered_frame.pack()
        
        self.day_chooser.grid(         row=0, column=0, sticky="nsew", rowspan=3)
        self.hour_entry.grid(          row=0, column=1, sticky="nsew", padx=10)
        self.minute_entry.grid(        row=0, column=2, sticky="nsew", padx=10)
        self.font_name_chooser.grid(   row=1, column=1, sticky="nsew", padx=10)
        self.font_size_chooser.grid(   row=1, column=2, sticky="nsew", padx=10)
        self.warning_time_chooser.grid(row=2, column=1, sticky="nsew", padx=10)
        
        self.message_entry.grid(row=0, column=0, sticky="nsew")
        
        #############
        # Callbacks #
        #############
        
        self.font_name.trace("w", self._font_change)
        self.font_size.trace("w", self._font_change)
        self.hour.trace("w", self._time_change)
        self.minute.trace("w", self._time_change)
        self.warning_time.trace("w", self._warning_time_change)
        
    def new(self, *args, **kwargs):
        self.message_entry.delete(1.0, END)
        self._current_file = None
        self.wm_title("Alarm Builder: *Untitled*")
        
    def open(self, *args, **kwargs):
        file_path = askopenfilename(initialdir=CONFIG_DIR)
        if not file_path:
            return
        
        self.message_entry.delete(1.0, END)
        reminder = Reminder.parse_file(file_path)
        
        self.message_entry.insert(1.0, reminder.text, 'center-tag')
        
        self.hour.set(str(reminder.time.hour).zfill(2))
        self.minute.set(str(reminder.time.minute).zfill(2))
        
        self.day_chooser.selection_clear(0, END)
        for day in reminder.days:
            self.day_chooser.selection_set(DAYS.index(day.capitalize()))
        
        self.font_name.set(reminder.font[0])
        self.font_size.set(reminder.font[1])
        
        self.warning_time.set(str(reminder.warn))
        
        self._current_file = file_path
        self.wm_title("Alarm Builder: %s" % self._current_file)
    
    def save(self, *args, **kwargs):
        if not self._current_file:
            self.save_as()
            return

        hours = int(self.hour.get())
        minutes = int(self.minute.get())
        time = Reminder.make_time(hours, minutes)
        
        selection = map(int, self.day_chooser.curselection())
        days = [self.day_chooser.get(day) for day in selection]
        
        text = self.message_entry.get(1.0, END)
        warn = int(self.warning_time.get())
        font = (self.font_name.get(), int(self.font_size.get()))
        
        if not days:
            tkMessageBox.showerror("Save file", "Cannt save without at least 1 day selected")
            return
        
        reminder = Reminder.Reminder(time, days, text, warn, font)
        Reminder.serialize_file(reminder, self._current_file)
        
    def save_as(self, *args, **kwargs):
        file_path = asksaveasfilename(initialdir=CONFIG_DIR)

        if not file_path:
            return
            
        self._current_file = file_path
        self.wm_title("Alarm Builder: %s" % self._current_file)
        
        self.save()

    def about(self, *args, **kwargs):
        pass
 
    def _font_change(self, *args, **kwargs):
        if not self.font_size.get().isdigit():
            self.font_size.set('12')
        size = int(self.font_size.get())
        if size < 8:
            self.font_size.set('8')
        self.message_entry.config(font=(self.font_name.get(), int(self.font_size.get())))
        
    def _recenter(self, *args, **kwargs):
        self.message_entry.tag_remove("center-tag", 1.0, "end")
        self.message_entry.tag_add("center-tag", 1.0, "end")
        
    def _time_change(self, *args, **kwargs):
        for var in (self.hour, self.minute):
            # by extension checks if < 0
            if not var.get().isdigit():
                var.set('00')
            if len(var.get()) != 2:
                var.set(var.get()[-2:].zfill(2))
        hour = int(self.hour.get())
        minute = int(self.minute.get())
        if hour > 23:
            self.hour.set('23')
        if minute > 59:
            self.minute.set('59')
                
    def _warning_time_change(self, *args, **kwargs):
        # by extension checks if < 0
        if not self.warning_time.get().isdigit():
            self.warning_time.set('5')
                
                
if __name__ == "__main__":
    try:
        mkdir(GLOBALS['config_path'])
    except:
        pass
    root = Builder()
    root.minsize(800, 600)
    root.mainloop()

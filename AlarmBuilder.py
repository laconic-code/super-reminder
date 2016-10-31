#!/usr/bin/env python
from time import *
from sys import argv
from os import environ
from os.path import join
from Tkinter import *
from ttk import Combobox
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
    Logging
"""


class LabelEntry(Frame):
    def __init__(self, root, *args, **kwargs):
        label = kwargs.pop('label', '')
        Frame.__init__(self, root, *args, **kwargs)
        self.label = Label(self, text=label)
        self.entry = Entry(self)
        self.label.pack(side=LEFT)
        self.entry.pack(side=RIGHT)

class ComboBox(Frame):
    def __init__(self, root, *args, **kwargs):
        label_kwargs = dict(text=kwargs.pop('label', ''))
        combobox_kwargs = dict()
        combobox_kwargs['state'] = kwargs.pop('state', 'normal')
        combobox_kwargs['textvariable'] = kwargs.pop('textvariable', None)

        Frame.__init__(self, root, *args, **kwargs)

        self.label = Label(self, **label_kwargs)
        self.combobox = Combobox(self, **combobox_kwargs)
        self.values = list()

        self.label.pack(side=LEFT)
        self.combobox.pack(side=RIGHT)

    def insert(self, position, value):
        if position.lower() == 'end':
          self.values.append(value)
        else:
          self.values.insert(int(position), value)
        self.combobox['values'] = self.values


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

        ############
        # Menu Bar #
        ############

        self.menu_bar = Menu(self)

        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="New", command=self.New, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Open", command=self.Open, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=self.Save, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", comman=self.Save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.Quit, accelerator="Ctrl+Q")
        self.file_menu = file_menu

        edit_menu = Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", command=lambda: self.focus_get().event_generate('<<Undo>>'), accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=lambda: self.focus_get().event_generate('<<Redo>>'), accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=lambda: self.focus_get().event_generate('<<Cut>>'), accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", comman=lambda: self.focus_get().event_generate('<<Copy>>'), accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", comman=lambda: self.focus_get().event_generate('<<Paste>>'), accelerator="Ctrl+V")
        self.edit_menu = file_menu

        self.use_24hr_format = BooleanVar()
        settings_menu = Menu(self.menu_bar, tearoff=0)
        settings_menu.add_checkbutton(label="Default to 24hr format", variable=self.use_24hr_format)
        self.settings_menu = settings_menu

        help_menu = Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.About)
        self.help_menu = help_menu

        self.menu_bar.add_cascade(label="File", menu=file_menu)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        self.menu_bar.add_cascade(label="Settings", menu=settings_menu)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=self.menu_bar)

        #################
        # Menu Keybinds #
        #################

        self.bind_all('<Control-n>', self.New)
        self.bind_all('<Control-o>', self.Open)
        self.bind_all('<Control-s>', self.Save)
        self.bind_all('<Control-q>', self.Quit)
        self.protocol("WM_DELETE_WINDOW", self.Quit)

        ###########
        # Widgets #
        ###########

        self.entry_frame = Frame(self)
        self.entry_centered_frame = Frame(self.entry_frame)

        self.status_bar_text = StringVar()
        self.status_bar = Label(textvariable=self.status_bar_text, fg='gray')

        self.time = StringVar()
        self.time_entry = LabelEntry(self.entry_centered_frame, label="Time: ")
        self.time_entry.entry.config(textvariable=self.time)
        self.time_entry_background_default = self.time_entry.entry.cget("bg")
        self.time_entry.entry.bind("<Enter>", lambda event : self.status_bar_text.set("24 or 12 hour format: HH:MM [am/pm]"))
        self.time_entry.entry.bind("<Leave>", lambda event : self.status_bar_text.set(""))

        self.day_chooser = Listbox(self.entry_centered_frame, selectmode=EXTENDED, exportselection=0, height=7, width=(len(max(DAYS, key=len)) + 1))
        self.day_chooser.bind("<Enter>", lambda event : self.status_bar_text.set("ctrl click or shift click to select multiple days"))
        self.day_chooser.bind("<Leave>", lambda event : self.status_bar_text.set(""))

        self.font_name = StringVar()
        self.font_size = StringVar()
        self.font_name_chooser = ComboBox(self.entry_centered_frame, label="Font: ", state="readonly", textvariable=self.font_name)
        self.font_size_chooser = ComboBox(self.entry_centered_frame, label="Size: ", state="normal", textvariable=self.font_size)

        self.warning_time = StringVar()
        self.warning_time_chooser = ComboBox(self.entry_centered_frame, label="Warning Minutes: ", state='normal', textvariable=self.warning_time)
        self.warning_time_chooser.bind("<Enter>", lambda event : self.status_bar_text.set("The number of minutes before hand to start the reminder"))
        self.warning_time_chooser.bind("<Leave>", lambda event : self.status_bar_text.set(""))

        ############
        # Defaults #
        ############

        self.time.set('10:00 am')
        self.font_name.set(FONTS[0])
        self.font_size.set('12')
        self.warning_time.set('5')
        for day in DAYS:
            self.day_chooser.insert(END, day)
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
        self.status_bar.pack()

        self.day_chooser.grid(         row=0, column=0, sticky="nsew", rowspan=3)
        self.time_entry.grid(          row=0, column=1, sticky="ew", padx=10)
        self.font_name_chooser.grid(   row=1, column=1, sticky="nsew", padx=10)
        self.font_size_chooser.grid(   row=1, column=2, sticky="nsew", padx=10)
        self.warning_time_chooser.grid(row=2, column=1, sticky="nsew", padx=10)

        self.message_entry.grid(row=0, column=0, sticky="nsew")

        #############
        # Callbacks #
        #############

        self.font_name.trace("w", self._font_change)
        self.font_size.trace("w", self._font_change)
        self.time.trace("w", self._time_change)
        self.warning_time.trace("w", self._warning_time_change)

        #########
        # Setup #
        #########

        self.New()
        self._edited(False)

    def New(self, *args, **kwargs):
        self.message_entry.delete(1.0, END)
        self._current_file = None
        self.wm_title("Alarm Builder: Untitled")

        self._edited(True)

    def Open(self, *args, **kwargs):
        file_path = askopenfilename(initialdir=CONFIG_DIR)
        if not file_path:
            return

        try:
            reminder = Reminder.parse_file(file_path)
        except Exception as e:
            tkMessageBox.showerror("Open file", e)
            return

        self.message_entry.delete(1.0, END)
        self.message_entry.insert(1.0, reminder.text, 'center-tag')

        if self.use_24hr_format.get():
            self.time.set(reminder.time.strftime('%H:%M') )
        else:
            self.time.set(reminder.time.strftime('%I:%M %p'))

        self.day_chooser.selection_clear(0, END)
        for day in reminder.days:
            self.day_chooser.selection_set(DAYS.index(day.capitalize()))

        self.font_name.set(reminder.font[0])
        self.font_size.set(reminder.font[1])

        self.warning_time.set(str(reminder.warn))

        self._current_file = file_path
        self.wm_title("Alarm Builder: %s" % self._current_file)

        self._edited(False)

    def Save(self, *args, **kwargs):
        if not self._current_file:
            self.Save_as()
            return

        time = Reminder._parse_hours_minutes(self.time.get())

        selection = map(int, self.day_chooser.curselection())
        days = [self.day_chooser.get(day) for day in selection]

        text = self.message_entry.get(1.0, END)
        warn = int(self.warning_time.get())
        font = (self.font_name.get(), int(self.font_size.get()))

        if not days:
            tkMessageBox.showerror("Save file", "Can not save without at least 1 day selected")
            return

        reminder = Reminder.Reminder(time, days, text, warn, font)
        Reminder.serialize_file(reminder, self._current_file)

        self._edited(False)

    def Save_as(self, *args, **kwargs):
        file_path = asksaveasfilename(initialdir=CONFIG_DIR)

        if not file_path:
            return

        self._current_file = file_path
        self.wm_title('Alarm Builder: %s' % self._current_file)

        self.Save()

    def Quit(self, *args, **kwargs):
        if self._edited():
            choice = tkMessageBox.showwarning(
                type=tkMessageBox.YESNOCANCEL,
                default=tkMessageBox.CANCEL,
                message='Save file "%s"?' % self._current_file,
                title='Save?')
            if choice == 'cancel':
                return
            if choice == 'yes':
                self.Save()
        self.quit()

    def About(self, *args, **kwargs):
        pass

    def _font_change(self, *args, **kwargs):
        if not self.font_size.get().isdigit():
            self.font_size.set('12')
        size = int(self.font_size.get())
        if size < 8:
            self.font_size.set('8')
        if size > 200:
            self.font_size.set('200')
        self.message_entry.config(font=(self.font_name.get(), int(self.font_size.get())))
        self._edited(True)

    def _recenter(self, *args, **kwargs):
        self.message_entry.tag_remove("center-tag", 1.0, "end")
        self.message_entry.tag_add("center-tag", 1.0, "end")
        self._edited(True)

    def _time_change(self, *args, **kwargs):
        try:
            Reminder._parse_hours_minutes(self.time.get())
            self.time_entry.entry.config(bg=self.time_entry_background_default)
        except ValueError:
            self.time_entry.entry.config(bg='salmon1')
        self._edited(True)

    def _warning_time_change(self, *args, **kwargs):
        # by extension checks if < 0
        if not self.warning_time.get().isdigit():
            self.warning_time.set('5')
        self._edited(True)

    def _edited(self, edited=None):
        """Set or remove window asterisks if edited given, else return if has been edited"""
        title = self.wm_title()
        has_asterisks = title.startswith('* ') and title.endswith(' *')
        if edited is None:
            return has_asterisks
        if edited and not has_asterisks:
            self.wm_title('* %s *' % title)
        if not edited and has_asterisks:
            self.wm_title(title[2:-2])




if __name__ == "__main__":
    try:
        mkdir(GLOBALS['config_path'])
    except:
        pass
    root = Builder()
    root.minsize(800, 600)
    root.mainloop()

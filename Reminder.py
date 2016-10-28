import datetime
import md5
import tkFont
import Tkinter as tk

"""
TODO:
     Implement once command
     Implement get full datetime
     Logging
"""


# getting Tkinter fonts requires a root object but we don't want it hanging
# around after
def _get_font_families():
    temp = tk.Tk()
    fonts = sorted([x for x in tkFont.families() if not x.startswith('@')])
    temp.destroy()
    return fonts

DAYS = ('monday tuesday wednesday thursday friday saturday sunday '
        'mon tue wed thu fri sat sun '
        'mo tu we th fr sa su').split()
MONTHS = ('january february march april may june july august september october november december '
          'jan feb mar apr may jun jul aug sep oct nov dec').split()
COMMANDS = 'time text font warn'.split()
FONTS = _get_font_families()


class ArgumentError(Exception):
    pass


class Reminder(object):
    def __init__(self, time, days, text, warn=None, font=None):
        for arg in 'time days text warn font'.split():
            is_valid = getattr(self, "_is_valid_%s" % arg)
            error_string =  is_valid(locals()[arg])
            if error_string:
                raise ArgumentError(error_string)

        if warn is None:
            warn = 5
        if not font:
            font_family = 'Arial' if 'Arial' in FONTS else FONTS[0]
            font = (font_family, '30')

        self.__dict__.update(dict(time=time, days=days, text=text, warn=warn, font=font))

    def _is_valid_time(self, time):
        if not isinstance(time, datetime.datetime):
            return 'time (%s) is not a datetime' % time

    def _is_valid_days(self, days):
        if not isinstance(days, list):
            return 'days (%s) is not a list' % days
        if days == []:
            return 'days cannot be empty'
        for day in days:
            if not isinstance(day, str):
                return '%s in days is not a string' % day
            if not day.lower() in DAYS:
                return '%s in days is not one of: %s' % (day, ' '.join(DAYS))

    def _is_valid_text(self, _):
        return

    def _is_valid_warn(self, warn):
        if warn is None:
            return
        if not isinstance(warn, int):
            return 'warn (%s) is not an integer or None' % warn

    def _is_valid_font(self, font):
        if font is None:
            return
        if not isinstance(font, tuple):
            return 'font (%s) is not a tuple or None' % font
        if not isinstance(font[0], str):
            return 'font family name (%s) is not a string' % font[0]
        if not font[0] in FONTS:
            return 'font family name (%s) is not installed on this system' % font[0]
        if not isinstance(font[1], int):
            return 'font size (%s) is not an integer' % font[1]

    def __repr__(self):
        return "time: %s\ndays: %s\nfont: %s\nwarn: %s\ntext: %s\n" % \
               (self.time, self.days, self.font, self.warn, self.text)


def make_time(hours=None, minutes=None):
    """Create a date time on Jan 1st, 2000 with variable hours and minutes

    If hours or minutes are not provided, the current time is used
    """
    if hours is None or minutes is None:
        now = datetime.datetime.now()
        hours = now.hour
        minutes = now.minute
    return datetime.datetime(year=2000, month=1, day=1, hour=hours, minute=minutes)

def _standardize_day(day_of_week_string):
    return DAYS[DAYS.index(day_of_week_string) % 7]

def _parse_time(time_string):
    """Parse a day and time string
    String should be of the form
    <day ... day> <hour>:<minute> [am/pm]

    Where:
      day:    is the day's full name, 3 letter abbreviation, or 2 letter abbreviation
              or one of: all, everyday, every, always
      hour:   is 24 or 12 hour format
              using 12 hour then requires that am/pm be given
      minute: two digit second
      am/pm:  is either am or pm ONLY if using 12 hour format

    Examples:
      everyday     6:00 pm
      Tue Wed Fri 14:00
      Monday Fri   4:00 am
      Fr Th Sa    23:59

    Returns:
      datetime.datetime, ['list', 'of', 'days']
      The date time will always have Jan 1st, 2000 as the day

    TODO:
      * support d/m/y with no day
    """
    tokens = [x.lower().strip() for x in time_string.split()]

    days = []
    i = 0
    # check if it repeats every day
    if tokens[i] in ['everyday', 'every', 'all', 'always']:
        for day in DAYS[:7]:
            days.append(day)
        i += 1
    # maybe it repeats only on certain days
    elif tokens[i] in DAYS:
        while tokens[i] in DAYS:
            days.append(_standardize_day(tokens[i]))
            i += 1
    # maybe it is only a certain day
    elif '/' in tokens[i]:
        raise NotImplemented('Only certain days is not currently implemented')
    # just assume it is every day
    else:
        for day in DAYS[:7]:
            days.append(day)

    # remove the days, months, years etc so that all we have left is the time
    time = _parse_hours_minutes(' '.join(tokens[i:]))

    return time, days

def _parse_hours_minutes(time_string):
    for time_format in ("%I:%M %p", "%H:%M"):
        try:
            dt = datetime.datetime.strptime(time_string.lower(), time_format)
            return make_time(dt.hour, dt.minute)
        except ValueError:
            pass

    raise ValueError('Invalid time format, must be 12hr or 24hr format HH:MM [am/pm]')

def _parse_font(font_string):
    """Parse font

    string should be of the form:
    <font family name> <font size>
    """
    if not font_string:
        return None
    return (' '.join(font_string.split()[:-1]), int(font_string.split()[-1]))

def _parse_warn(warn_string):
    """Parse warning time line

    string should be of the form:
    <warning minute number>
    """
    if not warn_string:
        return None
    if not warn_string.isdigit():
        raise ArgumentError('warning minutes is not an integer')
    return int(warn_string)

def parse_file(file_path):
    """Parse a reminder file and return a representative object"""
    with open(file_path) as f:
        reminder_string = f.read()
    return parse(reminder_string)

def parse(reminder_string):
    """Parse a reminder string and return a representative object

    File Format:
      time: <day ... day | everyday> hour:minute [am/pm if using 12 hour format]
      font: <font family name> <font_size>
      warn: <minutes before warning>
      message goes here
      everything is taken literally

    Required File Lines:
      # time: ...
      Message Contents

    Returns
      Reminder
        time: datetime.datetime
        days: ['list', 'of', 'days']
        font: ("font name", int(font_size))
        warn: <minutes before warning occurs>
        text: "multiline message contents"

      The date time will always have Jan 1st, 2000 as the day
    """
    contents = reminder_string.splitlines(True)

    text = ""
    commands = {}
    for line in contents:
        tokens = line.split()
        if not tokens:
            # empty line
            text += line
            continue
        possible_command = tokens[0].rstrip(':').lower()
        if possible_command in COMMANDS:
            commands[possible_command] = ' '.join(tokens[1:])
        else:
            # text
            text += line

    # strip the trailing newline
    text = text[:-1]

    if not commands.get('time'):
        raise ArgumentError('time section required in file')

    time, days = _parse_time(commands['time'])
    font = _parse_font(commands.get('font'))
    warn = _parse_warn(commands.get('warn'))

    return Reminder(time, days, text, warn, font)


def serialize_file(reminder, file_path):
    with open(file_path, 'w+') as f:
        f.write(serialize(reminder))

def serialize(reminder):
    """Serialize a reminder object

    time will always be changed to 24 hour format

    TODO: do simplification with days (all days selected -> everyday)
    """
    if not isinstance(reminder, Reminder):
        raise ArgumentError("reminder is not a reminder object")

    contents = ""

    days_s = ' '.join(reminder.days)
    time_s = '%s:%s' % (reminder.time.hour, reminder.time.minute)
    contents += 'time: %s %s\n' % (days_s, time_s)

    if reminder.font:
        contents += 'font: %s %s\n' % (reminder.font[0], reminder.font[1])

    if reminder.warn != None and reminder.warn >= 0:
        contents += 'warn: %s\n' % reminder.warn

    contents += reminder.text

    return contents

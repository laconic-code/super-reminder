#!/usr/bin/env python
from os import listdir, mkdir, environ
from os.path import isfile, join, abspath
from sched import *
import subprocess
import time
import datetime

GLOBALS = dict()
GLOBALS['scheduler'] = scheduler(time.time, time.sleep)
GLOBALS['config_path'] = abspath('%s/.super_reminder/' % environ['HOME'])

"""
TODO:
    Use schedule to set timers for when to display a specific reminder INSTEAD of polling every minute
    Maybe allow variable REMIND_BEFORE, maybe it needs to be in the file format?

"""



# Minutes before alarm to start warning
WARN_BEFORE_MINUTES = 5
# Minutes after alarm time to stop warming
STOP_REMIND_AFTER_MINUTES = 20
# time between reloading the config files
RELOAD_AFTER_MINUTES = 5
# time between checking alarms
CHECK_AFTER_MINUTES = 1

DAYS = ('monday tuesday wednesday thursday friday saturday sunday '
        'mon tue wed thu fri sat sun '
        'mo tu we th fr sa su').split()
MONTHS = ('january february march april may june july august september october november december '
          'jan feb mar apr may jun jul aug sep oct nov dec').split()

def make_time(hours=None, minutes=None):
    """Create a date time on Jan 1st, 2000 with variable hours and minutes
    
    If hours or minutes are not provided, the current time is used
    """
    if hours is None or minutes is None:
        now = datetime.datetime.now()
        hours = now.hour
        minutes = now.minute
    return datetime.datetime(year=2000, month=1, day=1, hour=hours, minute=minutes)

def standardize_day(day_of_week_string):
    return DAYS[DAYS.index(day_of_week_string) % 7]

def parse_time(time_string):
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
      datetime.datetime, list_of_days
      
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
    # maybe it repeats only on certain days
    elif tokens[i] in Days:
        while tokens[i] in DAYS:
            days.append(standardize_day(tokens[i]))
            i += 1
    # maybe it is only a certain day
    elif '/' in tokens[i]:
        raise NotImplemented('Only certain days is not currently implemented')
    # just assume it is every day
    else:
        for days in DAYS[:7]:
            days.append(day)
    
    # remove the days, months, years etc so that all we have left is the time
    tokens = tokens[i:]
    
    # determine if 12 hour or not
    use_12_hour = False
    if tokens[-1] in ['am', 'pm']:
        use_12_hour = True
    
    time_split = tokens[-2 if use_12_hour else -1].split(':')
    if len(time_split) > 2:
        raise NotImplemented('Seconds not supported')
    hour, minute = int(time_split[0]), int(time_split[1])
    
    # account for 12 hour clock
    if use_12_hour and tokens[-1] == 'pm':
        hour = (hour + 12) % 24
        
    return make_time(hour, minute), days

def reload_configs():
    # grab all the config files
    configs_path = GLOBALS['config_path']
    files = [join(configs_path, f) for f
             in listdir(configs_path)
             if isfile(join(configs_path, f))]

    alarms = dict()
    for path in files:
        with open(path) as f:
            # the first line contains the time string
            # we don't care about the rest of it
            time = f.readlines()[0]
            time, days = parse_time(time)

        # maybe the alarm was triggered already today
        old_alarm = GLOBALS.get('alarms', {}).get(time)
        triggered = old_alarm['triggered'] if old_alarm else False
        
        alarms[time] = dict(path=path, days=days, triggered=triggered)

    # swap out the reloaded alarms
    GLOBALS['alarms'] = alarms
    
    # reload every n minutes
    GLOBALS['scheduler'].enter(60 * RELOAD_AFTER_MINUTES, 1, check_alarms, ())

def check_alarms():
    now = make_time() + datetime.timedelta(minutes=WARN_BEFORE_MINUTES)

    day_of_week = DAYS[datetime.datetime.now().weekday()]

    for alarm, data in GLOBALS['alarms'].iteritems():
        days, path, triggered = data['days'], data['path'], data['triggered']
        
        # skip days we do not care about
        if not day_of_week in days:
            continue

        # stop reminding people after this time
        stop_remind_time = alarm + datetime.timedelta(minutes=STOP_REMIND_AFTER_MINUTES)

        # pop up reminder and note as triggered for today
        if alarm <= now and not triggered and not stop_remind_time < now:
            subprocess.call(["python", "SuperReminder.py", path])
            GLOBALS['alarms'][alarm]['triggered'] = True

        # unset triggered after wait time
        if stop_remind_time < now and triggered:
            GLOBALS['alarms'][alarm]['triggered'] = False
            
    # check every n minutes
    GLOBALS['scheduler'].enter(60 * CHECK_AFTER_MINUTES, 1, check_alarms, ())
    
    
if __name__ == "__main__":
    try:
        mkdir(GLOBALS['config_path'])
    except:
        pass
    reload_configs()
    GLOBALS['scheduler'].enter(1, 1, check_alarms, ())
    GLOBALS['scheduler'].run()

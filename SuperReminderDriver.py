#!/usr/bin/env python
from os import listdir, mkdir, environ
from os.path import isfile, join, abspath
from sched import *
import subprocess
import time
import datetime
import Reminder
import hashlib

CONFIG_DIR = abspath('%s/.super_reminder/' % environ['HOME'])
RELOAD_AFTER_MINUTES = 0.1

class ReminderScheduler(scheduler):
    def __init__(self, config_dir, reload_after_minutes, *args, **kwargs):
        scheduler.__init__(self, *args, **kwargs)

        self.alarms = dict()
        self.config_dir = config_dir
        self.reload_after_minutes = reload_after_minutes

    def _file_checksum(self, path):
        with open(path) as f:
            stamp = hashlib.sha256(f.read())
        return stamp.hexdigest()

    def reload_configs(self):
        now = datetime.datetime.now()

        # grab all the config files
        files = [join(self.config_dir, f) for f
                 in listdir(self.config_dir)
                 if isfile(join(self.config_dir, f))]

        for path in files:
            checksum = self._file_checksum(path)

            old_alarm = self.alarms.get(path)
            if old_alarm:
                # skip unchanged alarm files
                # TODO: Maybe this should be last access time, it would be cheaper
                if old_alarm['checksum'] == checksum:
                    continue

                # otherwise it changed and we need to unschedule to old alarm
                try:
                    self.cancel(old_alarm['event'])
                except ValueError as e:
                    # the event is already out of the queue (already ran)
                    pass

            reminder = Reminder.parse_file(path)

            event = None
            if Reminder.DAYS[now.weekday()] in reminder.days:
                event = self.try_schedule(reminder, path)

            self.alarms[path] = dict(checksum=checksum, reminder=reminder,
                                event=event)

        # reload every n minutes
        self.enter(60 * self.reload_after_minutes, 1, self.reload_configs, ())

    def show_reminder(self, path):
        now = datetime.datetime.now()
        subprocess.call(["python", "SuperReminder.py", path])
        import pdb; pdb.set_trace()

        alarm = self.alarms[path]
        reminder = alarm['reminder']
        days_in_week = 7

        today_string = Reminder.DAYS[now.weekday()]

        # get the next day to run the alarm
        next_day = reminder.days[(reminder.days.index(today_string) + 1)
                                 % len(reminder.days)]

        # get a list of days starting from tomorrow
        # ex if today is Friday ['Saturday', 'Sunday', 'Monday', ..., 'Friday']
        days = [Reminder.DAYS[(now.weekday() + i + 1) % days_in_week]
                for i in range(days_in_week)]
        days_until_next_day = days.index(next_day) + 1

        event = self.try_schedule(reminder, path, days_until_next_day)
        alarm['event'] = event

    def try_schedule(self, reminder, path, days_offset=0):
        now = datetime.datetime.now()
        warning_minutes = datetime.timedelta(minutes=reminder.warn)
        days_offset = datetime.timedelta(days=days_offset)
        target_time = (reminder.time - warning_minutes) + days_offset
        target_time = target_time
        current_time = Reminder.make_time().replace(second=now.second)

        time_to_reminder =  (target_time - current_time).total_seconds()
        if time_to_reminder > 0:
            print "Next update in %s" % (target_time - current_time)
            return self.enter(time_to_reminder, 1, self.show_reminder, (path,))

        return None

if __name__ == "__main__":
    try:
        mkdir(CONFIG_DIR)
    except:
        pass
    reminder_scheduler = ReminderScheduler(CONFIG_DIR, RELOAD_AFTER_MINUTES,
                                           time.time, time.sleep)
    reminder_scheduler.reload_configs()
    reminder_scheduler.run()

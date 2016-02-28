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

"""
TODO:
    Logging
"""

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

            alarm = dict(checksum=checksum, reminder=reminder,
                                event=None, path=path)

            alarm['event'] = self.schedule(alarm, False)

            self.alarms[path] = alarm

        # reload every n minutes
        self.enter(60 * self.reload_after_minutes, 1, self.reload_configs, ())

    def show_reminder(self, alarm):
        subprocess.call(["python", "SuperReminder.py", alarm['path']])
        alarm['event'] = self.schedule(alarm, True)

    def _days_until_next_alarm(self, alarm):
        days_in_week = 7
        now = datetime.datetime.now()
        reminder = alarm['reminder']

        today_string = Reminder.DAYS[now.weekday()]

        # get a list of days starting from tomorrow
        # ex if today is Friday ['Saturday', 'Sunday', 'Monday', ..., 'Friday']
        days = [Reminder.DAYS[(now.weekday() + i + 1) % days_in_week]
                for i in range(days_in_week)]

        # get the next day to run the alarm
        for day in days:
            if day in reminder.days:
                day_index = reminder.days.index(day)
                next_day = reminder.days[(day_index + 1) % len(reminder.days)]
                break


        return days.index(next_day) + 1

    def _seconds_to_next_reminder(self, alarm, days_offset=0):
        now = datetime.datetime.now()
        reminder = alarm['reminder']

        warning_minutes = datetime.timedelta(minutes=reminder.warn)
        days_offset = datetime.timedelta(days=days_offset)
        target_time = (reminder.time - warning_minutes) + days_offset
        target_time = target_time
        current_time = Reminder.make_time().replace(second=now.second)

        return (target_time - current_time).total_seconds()

    def schedule(self, alarm, run_today):
        # get the seconds to the next reminder, assuming it is today
        seconds_to_next_reminder = self._seconds_to_next_reminder(alarm)
        today = Reminder.DAYS[datetime.datetime.now().weekday()]
        can_run_today = today in alarm['reminder'].days

        if not run_today and can_run_today:
            # The alarm may be run later today
            if seconds_to_next_reminder > 0:
                print "Next update in %s for %s" % (datetime.timedelta(seconds=seconds_to_next_reminder), alarm['path'])
                return self.enter(seconds_to_next_reminder, 1,
                                  self.show_reminder, (alarm,))

            # maybe we just started up and are in the warning window for this reminder
            if abs(seconds_to_next_reminder) < (alarm['reminder'].warn * 60):
                return self.enter(1, 1, self.show_reminder, (alarm,))

        # otherwise, we have missed/run this reminder and need to schedule
        #  the next occurance of the alarm far into the future
        days_offset = self._days_until_next_alarm(alarm)
        seconds_to_next_reminder = \
            self._seconds_to_next_reminder(alarm, days_offset=days_offset)
        print "Next update in %s for %s" % (datetime.timedelta(seconds=seconds_to_next_reminder), alarm['path'])
        return self.enter(seconds_to_next_reminder, 1,
                          self.show_reminder, (alarm,))




if __name__ == "__main__":
    try:
        mkdir(CONFIG_DIR)
    except:
        pass
    reminder_scheduler = ReminderScheduler(CONFIG_DIR, RELOAD_AFTER_MINUTES,
                                           time.time, time.sleep)
    reminder_scheduler.reload_configs()
    reminder_scheduler.run()

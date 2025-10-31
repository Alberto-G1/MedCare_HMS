from django import template

register = template.Library()

@register.filter
def filter_by_day(availability_slots, day):
    """Filter availability slots by day of the week"""
    return [slot for slot in availability_slots if slot.day_of_week == day]

@register.filter
def get_day_name(day_number):
    """Convert day number to day name"""
    days = {
        0: 'Monday',
        1: 'Tuesday',
        2: 'Wednesday',
        3: 'Thursday',
        4: 'Friday',
        5: 'Saturday',
        6: 'Sunday'
    }
    return days.get(day_number, 'Unknown')

@register.filter
def get_day_short_name(day_number):
    """Convert day number to short day name"""
    days = {
        0: 'Mon',
        1: 'Tue',
        2: 'Wed',
        3: 'Thu',
        4: 'Fri',
        5: 'Sat',
        6: 'Sun'
    }
    return days.get(day_number, 'Unknown')
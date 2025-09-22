from django import template

register = template.Library()

@register.filter
def first_if_not(queryset, user):
    """
    A custom template filter that returns the first item in a queryset
    that is NOT equal to the provided user.
    
    This is useful for finding the "other person" in a two-person chat thread.
    
    Usage in template: {{ thread.participants.all|first_if_not:request.user }}
    """
    for item in queryset:
        if item != user:
            return item
    return None # Return None if no other user is found
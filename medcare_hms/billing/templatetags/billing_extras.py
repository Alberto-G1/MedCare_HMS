from django import template
import locale

register = template.Library()

@register.filter
def currency_ugx(value):
    """
    Formats a number as Ugandan Shilling currency.
    Example: 50000 -> UGX 50,000
    """
    try:
        # Using locale for proper comma separation
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        # Since UGX has no subdivision, we format as an integer
        return f"UGX {locale.format_string('%d', int(value), grouping=True)}"
    except (ValueError, TypeError):
        return value
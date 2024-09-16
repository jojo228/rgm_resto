from django import template
register = template.Library()

@register.filter
def cfa(price):
    return f'{price}f cfa'
from django import template
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag(takes_context=True)
def update_query_params(context, **kwargs):
    """
    Обновляет параметры запроса в URL, сохраняя существующие
    """
    request = context['request']
    query_dict = request.GET.copy()
    
    for key, value in kwargs.items():
        if value is None:
            if key in query_dict:
                del query_dict[key]
        else:
            query_dict[key] = value
    
    if query_dict:
        return urlencode(query_dict)
    return ''
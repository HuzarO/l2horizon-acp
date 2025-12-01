from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
import json
import html
from apps.lineage.games.models import BoxItem
from apps.lineage.games.choices import RARITY_CHOICES


register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_item_list_json(box_type):
    box_items = BoxItem.objects.filter(box__box_type=box_type).select_related('item')
    if not box_items.exists():
        return mark_safe(json.dumps([]))

    unique_items = {bi.item for bi in box_items}

    items_data = []
    for item in unique_items:
        image_url = None
        if item.image:
            try:
                image_url = str(item.image.url)
            except (AttributeError, ValueError):
                pass
        
        items_data.append({
            'name': str(item.name) if item.name else '',
            'rarity': str(item.rarity) if item.rarity else '',
            'rarity_display': str(dict(RARITY_CHOICES).get(item.rarity, item.rarity)),
            'enchant': int(item.enchant) if item.enchant is not None else 0,
            'image_url': image_url
        })
    
    # json.dumps já escapa corretamente as strings, então podemos usar mark_safe
    # O JSON será usado em um atributo HTML com aspas simples, então está seguro
    return mark_safe(json.dumps(items_data, ensure_ascii=False))


@register.filter
def json_escape(value):
    """
    Escapa JSON para uso seguro em atributos HTML.
    Escapa apenas aspas e &, mantendo o JSON válido.
    """
    if value is None:
        return ''
    json_str = str(value)
    # Escapa apenas os caracteres necessários para atributos HTML
    # Substitui " por &quot; e & por &amp;
    escaped = json_str.replace('&', '&amp;').replace('"', '&quot;')
    return mark_safe(escaped)



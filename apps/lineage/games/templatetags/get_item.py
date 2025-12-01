from django import template
import json
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
        return json.dumps([])

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
    
    return json.dumps(items_data, ensure_ascii=False)



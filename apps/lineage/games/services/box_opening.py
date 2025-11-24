import random
import logging
from apps.lineage.games.models import *

logger = logging.getLogger(__name__)

def open_box(user, box_id):
    logger.info(f"[BOX_OPEN] Iniciando abertura da caixa {box_id} para usuário {user.username}")
    
    try:
        box = Box.objects.get(id=box_id)
        logger.info(f"[BOX_OPEN] Caixa {box_id} encontrada. Tipo: {box.box_type.name}")
    except Box.DoesNotExist:
        logger.error(f"[BOX_OPEN] Caixa {box_id} não encontrada")
        return None, "Caixa não encontrada."

    # Conta todos os boosters antes
    total_items = box.items.count()
    opened_items_before = box.items.filter(opened=True).count()
    closed_items_before = box.items.filter(opened=False).count()
    logger.info(f"[BOX_OPEN] Estado ANTES: Total={total_items}, Abertos={opened_items_before}, Fechados={closed_items_before}")

    # Pega apenas boosters que ainda não foram usados
    items = list(box.items.filter(opened=False))
    logger.info(f"[BOX_OPEN] Boosters disponíveis para abrir: {len(items)}")
    
    if not items:
        logger.warning(f"[BOX_OPEN] Sem boosters disponíveis na caixa {box_id}")
        return None, "Sem boosters disponíveis na caixa."

    # Sorteia um booster com base na probabilidade
    selected_item = random.choices(
        items,
        weights=[item.probability for item in items],
        k=1
    )[0]
    logger.info(f"[BOX_OPEN] Booster selecionado: ID={selected_item.id}, Item={selected_item.item.name}, Opened={selected_item.opened}")

    # Marca o booster como usado usando update() para garantir que seja salvo
    updated_count = BoxItem.objects.filter(id=selected_item.id).update(opened=True)
    logger.info(f"[BOX_OPEN] Update executado. Linhas afetadas: {updated_count}")
    
    # Verifica se foi atualizado corretamente
    selected_item.refresh_from_db()
    logger.info(f"[BOX_OPEN] Após refresh_from_db: ID={selected_item.id}, Opened={selected_item.opened}")
    
    # Verifica o estado após a atualização
    opened_items_after = box.items.filter(opened=True).count()
    closed_items_after = box.items.filter(opened=False).count()
    logger.info(f"[BOX_OPEN] Estado DEPOIS: Abertos={opened_items_after}, Fechados={closed_items_after}")

    # Garante que o usuário tem uma bag
    bag, created = Bag.objects.get_or_create(user=user)

    # Adiciona o item à bag
    bag_item, created = BagItem.objects.get_or_create(
        bag=bag,
        item_id=selected_item.item.item_id,
        enchant=selected_item.item.enchant,
        defaults={
            'item_name': selected_item.item.name,
            'quantity': 1,
        }
    )

    if not created:
        bag_item.quantity += 1
        bag_item.save()

    # Registro no histórico
    BoxItemHistory.objects.create(
        user=user,
        item=selected_item.item,
        box=box,
        rarity=selected_item.item.rarity,
        enchant=selected_item.item.enchant
    )

    return selected_item.item, None

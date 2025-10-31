from celery import shared_task
from .utils import reconciliar_pendentes_mercadopago


@shared_task(name='apps.lineage.payment.tasks.reconciliar_pendentes_mp')
def reconciliar_pendentes_mp(cutoff_minutes: int = 5) -> int:
	return reconciliar_pendentes_mercadopago(cutoff_minutes=cutoff_minutes)

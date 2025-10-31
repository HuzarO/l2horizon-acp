from django.core.management.base import BaseCommand
from apps.lineage.payment.utils import reconciliar_pendentes_mercadopago


class Command(BaseCommand):
	help = 'Reconcilia pagamentos pendentes do Mercado Pago (pull)'

	def add_arguments(self, parser):
		parser.add_argument('--cutoff-minutes', type=int, default=5, help='Minutos mínimos desde a criação para tentar conciliar')

	def handle(self, *args, **options):
		cutoff = options.get('cutoff_minutes', 5)
		reconciliados = reconciliar_pendentes_mercadopago(cutoff_minutes=cutoff)
		self.stdout.write(self.style.SUCCESS(f'Reconciliados: {reconciliados}'))

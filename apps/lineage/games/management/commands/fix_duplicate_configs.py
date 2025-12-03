from django.core.management.base import BaseCommand
from apps.lineage.games.models import (
    SlotMachineConfig, DiceGameConfig, FishingGameConfig
)


class Command(BaseCommand):
    help = 'Remove configurações duplicadas dos jogos, mantendo apenas uma de cada'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 Corrigindo configurações duplicadas...'))
        
        # Slot Machine Config
        slot_configs = SlotMachineConfig.objects.all()
        if slot_configs.count() > 1:
            # Manter a primeira ativa, ou a primeira se nenhuma ativa
            active_config = slot_configs.filter(is_active=True).first()
            if active_config:
                keep_config = active_config
            else:
                keep_config = slot_configs.first()
            
            # Deletar as outras
            deleted_count = slot_configs.exclude(id=keep_config.id).delete()[0]
            self.stdout.write(self.style.WARNING(f'  🎰 Slot Machine: Removidas {deleted_count} configurações duplicadas'))
        else:
            self.stdout.write(self.style.SUCCESS('  🎰 Slot Machine: OK'))
        
        # Dice Game Config
        dice_configs = DiceGameConfig.objects.all()
        if dice_configs.count() > 1:
            # Manter a primeira ativa, ou a primeira se nenhuma ativa
            active_config = dice_configs.filter(is_active=True).first()
            if active_config:
                keep_config = active_config
            else:
                keep_config = dice_configs.first()
            
            # Deletar as outras
            deleted_count = dice_configs.exclude(id=keep_config.id).delete()[0]
            self.stdout.write(self.style.WARNING(f'  🎲 Dice Game: Removidas {deleted_count} configurações duplicadas'))
        else:
            self.stdout.write(self.style.SUCCESS('  🎲 Dice Game: OK'))
        
        # Fishing Game Config
        fishing_configs = FishingGameConfig.objects.all()
        if fishing_configs.count() > 1:
            # Manter a primeira ativa, ou a primeira se nenhuma ativa
            active_config = fishing_configs.filter(is_active=True).first()
            if active_config:
                keep_config = active_config
            else:
                keep_config = fishing_configs.first()
            
            # Deletar as outras
            deleted_count = fishing_configs.exclude(id=keep_config.id).delete()[0]
            self.stdout.write(self.style.WARNING(f'  🎣 Fishing Game: Removidas {deleted_count} configurações duplicadas'))
        else:
            self.stdout.write(self.style.SUCCESS('  🎣 Fishing Game: OK'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Correção concluída!'))


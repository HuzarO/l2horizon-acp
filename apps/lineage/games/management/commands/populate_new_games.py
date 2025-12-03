from django.core.management.base import BaseCommand
from apps.lineage.games.models import (
    SlotMachineConfig, SlotMachineSymbol, SlotMachinePrize,
    DiceGameConfig, FishingGameConfig, Fish, FishingBait, Item
)


class Command(BaseCommand):
    help = 'Popula os novos jogos com configurações iniciais'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando população dos novos jogos...'))
        
        # Slot Machine
        self.populate_slot_machine()
        
        # Dice Game
        self.populate_dice_game()
        
        # Fishing Game
        self.populate_fishing_game()
        
        self.stdout.write(self.style.SUCCESS('✅ População concluída com sucesso!'))

    def populate_slot_machine(self):
        self.stdout.write('🎰 Configurando Slot Machine...')
        
        # Criar configuração
        config, created = SlotMachineConfig.objects.get_or_create(
            name='Slot Machine Principal',
            defaults={
                'cost_per_spin': 1,
                'is_active': True,
                'jackpot_amount': 1000,
                'jackpot_chance': 0.1
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ Configuração criada'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠ Configuração já existe'))
        
        # Criar símbolos
        symbols_data = [
            {'symbol': 'sword', 'weight': 15, 'icon': '⚔️'},
            {'symbol': 'shield', 'weight': 15, 'icon': '🛡️'},
            {'symbol': 'potion', 'weight': 20, 'icon': '🧪'},
            {'symbol': 'gem', 'weight': 10, 'icon': '💎'},
            {'symbol': 'gold', 'weight': 25, 'icon': '🪙'},
            {'symbol': 'armor', 'weight': 12, 'icon': '🥋'},
            {'symbol': 'bow', 'weight': 13, 'icon': '🏹'},
            {'symbol': 'staff', 'weight': 8, 'icon': '🪄'},
            {'symbol': 'jackpot', 'weight': 1, 'icon': '💰'},
        ]
        
        symbols_created = 0
        for symbol_data in symbols_data:
            symbol, created = SlotMachineSymbol.objects.get_or_create(
                symbol=symbol_data['symbol'],
                defaults={
                    'weight': symbol_data['weight'],
                    'icon': symbol_data['icon']
                }
            )
            if created:
                symbols_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {symbols_created} símbolos criados'))
        
        # Criar prêmios básicos
        prizes_data = [
            {'symbol': 'jackpot', 'matches': 3, 'fichas': 10000},
            {'symbol': 'gem', 'matches': 3, 'fichas': 500},
            {'symbol': 'staff', 'matches': 3, 'fichas': 300},
            {'symbol': 'armor', 'matches': 3, 'fichas': 200},
            {'symbol': 'bow', 'matches': 3, 'fichas': 150},
            {'symbol': 'sword', 'matches': 3, 'fichas': 100},
            {'symbol': 'shield', 'matches': 3, 'fichas': 100},
            {'symbol': 'gold', 'matches': 3, 'fichas': 50},
            {'symbol': 'potion', 'matches': 3, 'fichas': 30},
            {'symbol': 'gem', 'matches': 2, 'fichas': 50},
            {'symbol': 'sword', 'matches': 2, 'fichas': 20},
            {'symbol': 'shield', 'matches': 2, 'fichas': 20},
        ]
        
        prizes_created = 0
        for prize_data in prizes_data:
            symbol = SlotMachineSymbol.objects.filter(symbol=prize_data['symbol']).first()
            if symbol:
                prize, created = SlotMachinePrize.objects.get_or_create(
                    config=config,
                    symbol=symbol,
                    matches_required=prize_data['matches'],
                    defaults={
                        'fichas_prize': prize_data['fichas']
                    }
                )
                if created:
                    prizes_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {prizes_created} prêmios criados'))

    def populate_dice_game(self):
        self.stdout.write('🎲 Configurando Dice Game...')
        
        # Verificar se já existe alguma configuração
        existing_config = DiceGameConfig.objects.first()
        if existing_config:
            self.stdout.write(self.style.WARNING('  ⚠ Configuração já existe'))
            created = False
        else:
            config = DiceGameConfig.objects.create(
                min_bet=1,
                max_bet=100,
                is_active=True,
                specific_number_multiplier=5.0,
                even_odd_multiplier=2.0,
                high_low_multiplier=2.0
            )
            self.stdout.write(self.style.SUCCESS('  ✓ Configuração criada'))
            created = True

    def populate_fishing_game(self):
        self.stdout.write('🎣 Configurando Fishing Game...')
        
        # Criar configuração
        config, created = FishingGameConfig.objects.get_or_create(
            name='Fishing Game Principal',
            defaults={
                'cost_per_cast': 1,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ Configuração criada'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠ Configuração já existe'))
        
        # Criar peixes
        fishes_data = [
            # Peixes Comuns (Level 1+)
            {'name': 'Peixinho', 'rarity': 'common', 'icon': '🐟', 'min_level': 1, 'weight': 50, 'xp': 10, 'fichas': 5},
            {'name': 'Sardinha', 'rarity': 'common', 'icon': '🐠', 'min_level': 1, 'weight': 45, 'xp': 12, 'fichas': 6},
            {'name': 'Carpa', 'rarity': 'common', 'icon': '🐡', 'min_level': 1, 'weight': 40, 'xp': 15, 'fichas': 8},
            
            # Peixes Raros (Level 3+)
            {'name': 'Atum', 'rarity': 'rare', 'icon': '🐟', 'min_level': 3, 'weight': 25, 'xp': 30, 'fichas': 20},
            {'name': 'Salmão', 'rarity': 'rare', 'icon': '🐠', 'min_level': 3, 'weight': 20, 'xp': 35, 'fichas': 25},
            {'name': 'Dourado', 'rarity': 'rare', 'icon': '🐡', 'min_level': 3, 'weight': 18, 'xp': 40, 'fichas': 30},
            
            # Peixes Épicos (Level 5+)
            {'name': 'Tubarão', 'rarity': 'epic', 'icon': '🦈', 'min_level': 5, 'weight': 10, 'xp': 80, 'fichas': 50},
            {'name': 'Golfinho', 'rarity': 'epic', 'icon': '🐬', 'min_level': 5, 'weight': 8, 'xp': 90, 'fichas': 60},
            {'name': 'Baleia', 'rarity': 'epic', 'icon': '🐋', 'min_level': 5, 'weight': 6, 'xp': 100, 'fichas': 70},
            
            # Peixes Lendários (Level 7+)
            {'name': 'Dragão Marinho', 'rarity': 'legendary', 'icon': '🐉', 'min_level': 7, 'weight': 3, 'xp': 200, 'fichas': 150},
            {'name': 'Kraken Bebê', 'rarity': 'legendary', 'icon': '🦑', 'min_level': 7, 'weight': 2, 'xp': 250, 'fichas': 200},
            {'name': 'Sereia Dourada', 'rarity': 'legendary', 'icon': '🧜', 'min_level': 10, 'weight': 1, 'xp': 500, 'fichas': 500},
        ]
        
        fishes_created = 0
        for fish_data in fishes_data:
            fish, created = Fish.objects.get_or_create(
                name=fish_data['name'],
                defaults={
                    'rarity': fish_data['rarity'],
                    'icon': fish_data['icon'],
                    'min_rod_level': fish_data['min_level'],
                    'weight': fish_data['weight'],
                    'experience_reward': fish_data['xp'],
                    'fichas_reward': fish_data['fichas']
                }
            )
            if created:
                fishes_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {fishes_created} peixes criados'))
        
        # Criar iscas
        baits_data = [
            {
                'name': 'Isca Comum',
                'description': 'Aumenta a chance de pegar peixes comuns',
                'price': 20,
                'rarity_boost': 'common',
                'boost_percentage': 50.0,
                'duration_minutes': 30
            },
            {
                'name': 'Isca Rara',
                'description': 'Aumenta a chance de pegar peixes raros',
                'price': 50,
                'rarity_boost': 'rare',
                'boost_percentage': 50.0,
                'duration_minutes': 30
            },
            {
                'name': 'Isca Épica',
                'description': 'Aumenta a chance de pegar peixes épicos',
                'price': 100,
                'rarity_boost': 'epic',
                'boost_percentage': 50.0,
                'duration_minutes': 30
            },
            {
                'name': 'Isca Lendária',
                'description': 'Aumenta a chance de pegar peixes lendários',
                'price': 200,
                'rarity_boost': 'legendary',
                'boost_percentage': 50.0,
                'duration_minutes': 60
            },
        ]
        
        baits_created = 0
        for bait_data in baits_data:
            bait, created = FishingBait.objects.get_or_create(
                name=bait_data['name'],
                defaults=bait_data
            )
            if created:
                baits_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {baits_created} iscas criadas'))


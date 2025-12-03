from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.main.home.models import User
from core.models import BaseModel
from django.templatetags.static import static
import random
from django.utils import timezone
from datetime import timedelta
from .choices import *


class Prize(BaseModel):    
    # Novo: vínculo com Item para evitar duplicidade (fase de migração: manter campos legados por enquanto)
    item = models.ForeignKey('Item', on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Item"))
    # Legado
    name = models.CharField(max_length=255, verbose_name=_("Prize Name"))
    image = models.ImageField(upload_to='prizes/', null=True, blank=True, verbose_name=_("Image"))
    weight = models.PositiveIntegerField(default=1, help_text=_("Quanto maior o peso, maior a chance de ser sorteado."), verbose_name=_("Weight"))
    legacy_item_code = models.IntegerField(verbose_name=_("Item ID"))
    enchant = models.IntegerField(default=0, verbose_name=_("Enchant Level"))
    rarity = models.CharField(max_length=15, choices=RARITY_CHOICES, default='COMUM', verbose_name=_("Rarity"))
    
    # Método para retornar a URL da imagem
    def get_image_url(self):
        try:
            if self.item and self.item.image:
                return self.item.image.url
            if self.image:
                return self.image.url
        except (AttributeError, ValueError):
            pass
        return static("roulette/images/default.png")

    def __str__(self):
        display_name = self.item.name if self.item else self.name
        return f'{display_name} ({self.rarity})'

    class Meta:
        verbose_name = _("Prize")
        verbose_name_plural = _("Prizes")


class SpinHistory(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    prize = models.ForeignKey(Prize, on_delete=models.CASCADE, verbose_name=_("Prize"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    # Auditoria do giro
    seed = models.BigIntegerField(null=True, blank=True, verbose_name=_("Random Seed"))
    fail_chance = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Fail Chance (%)"))
    weights_snapshot = models.TextField(null=True, blank=True, verbose_name=_("Weights Snapshot (JSON)"))

    def __str__(self):
        return f'{self.user.username} won {self.prize.name}'

    class Meta:
        verbose_name = _("Spin History")
        verbose_name_plural = _("Spin Histories")


class GameConfig(BaseModel):
    """Configurações do módulo de jogos (roleta, etc)."""
    fail_chance = models.PositiveIntegerField(default=20, verbose_name=_("Fail Chance (%)"))

    class Meta:
        verbose_name = _("Game Config")
        verbose_name_plural = _("Game Configs")

    def __str__(self):
        return f"GameConfig (fail_chance={self.fail_chance}%)"


class Bag(BaseModel):
    user = models.OneToOneField(User, related_name='bag', on_delete=models.CASCADE, verbose_name=_("User"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    def __str__(self):
        return f"Bag de {self.user.username}"

    class Meta:
        verbose_name = _("Bag")
        verbose_name_plural = _("Bags")


class BagItem(BaseModel):
    bag = models.ForeignKey(Bag, related_name='items', on_delete=models.CASCADE, verbose_name=_("Bag"))
    item_id = models.IntegerField(verbose_name=_("Item ID"))
    item_name = models.CharField(max_length=100, verbose_name=_("Item Name"))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Quantity"))
    enchant = models.IntegerField(default=0, verbose_name=_("Enchant Level"))
    added_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Added At"))

    class Meta:
        unique_together = ('bag', 'item_id', 'enchant')
        verbose_name = _("Bag Item")
        verbose_name_plural = _("Bag Items")

    def __str__(self):
        return f"{self.item_name} +{self.enchant} x{self.quantity} (Bag)"


class Item(BaseModel):
    name = models.CharField(max_length=100, verbose_name=_("Item Name"))
    enchant = models.IntegerField(default=0, verbose_name=_("Enchant Level"))
    item_id = models.IntegerField(verbose_name=_("Item ID"))
    image = models.ImageField(upload_to='items/', verbose_name=_("Image"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, verbose_name=_("Rarity"))
    can_be_populated = models.BooleanField(default=True, verbose_name=_("Can Be Populated"))
    
    def __str__(self):
        return f"{self.name} ({self.get_rarity_display()})"

    class Meta:
        verbose_name = _("Item")
        verbose_name_plural = _("Items")


class BoxType(BaseModel):
    name = models.CharField(max_length=100, verbose_name=_("Box Type Name"))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Price"))
    boosters_amount = models.PositiveIntegerField(default=5, verbose_name=_("Boosters Amount"))
    
    # Probabilidades por raridade (em %)
    chance_common = models.FloatField(default=60, verbose_name=_("Chance of Common"))
    chance_rare = models.FloatField(default=25, verbose_name=_("Chance of Rare"))
    chance_epic = models.FloatField(default=10, verbose_name=_("Chance of Epic"))
    chance_legendary = models.FloatField(default=5, verbose_name=_("Chance of Legendary"))

    max_epic_items = models.IntegerField(default=0, verbose_name=_("Max Epic Items"))
    max_legendary_items = models.IntegerField(default=0, verbose_name=_("Max Legendary Items"))
    allowed_items = models.ManyToManyField(Item, blank=True, related_name='allowed_in_boxes')

    def __str__(self):
        return self.name

    def get_rarity_by_chance(self):
        roll = random.uniform(0, 100)
        if roll <= self.chance_legendary:
            return 'legendary'
        elif roll <= self.chance_legendary + self.chance_epic:
            return 'epic'
        elif roll <= self.chance_legendary + self.chance_epic + self.chance_rare:
            return 'rare'
        return 'common'

    def get_highest_rarity(self):
        """Retorna a maior raridade disponível na caixa baseada nas chances"""
        if self.chance_legendary > 0:
            return 'legendary'  # Nome correto do arquivo
        elif self.chance_epic > 0:
            return 'epic'
        elif self.chance_rare > 0:
            return 'rare'
        return 'common'

    class Meta:
        verbose_name = _("Box Type")
        verbose_name_plural = _("Box Types")


class Box(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    box_type = models.ForeignKey(BoxType, on_delete=models.CASCADE, verbose_name=_("Box Type"))
    opened = models.BooleanField(default=False, verbose_name=_("Opened"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    def __str__(self):
        return f"Box de {self.box_type.name} - {self.user.username}"

    class Meta:
        verbose_name = _("Box")
        verbose_name_plural = _("Boxes")


class BoxItem(BaseModel):
    box = models.ForeignKey(Box, on_delete=models.CASCADE, related_name='items', verbose_name=_("Box"))
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name=_("Item"))
    probability = models.FloatField(default=1.0, verbose_name=_("Probability"))
    opened = models.BooleanField(default=False, verbose_name=_("Opened"))

    def __str__(self):
        return f"{self.item.name} ({'Aberto' if self.opened else 'Fechado'})"

    class Meta:
        verbose_name = _("Box Item")
        verbose_name_plural = _("Box Items")


class BoxItemHistory(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='box_item_history', verbose_name=_("User"))
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name=_("Item"))
    box = models.ForeignKey(Box, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Box"))
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, verbose_name=_("Rarity"))
    enchant = models.IntegerField(default=0, verbose_name=_("Enchant Level"))
    obtained_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Obtained At"))

    def __str__(self):
        return f"{self.user.username} ganhou {self.item.name} +{self.enchant} [{self.rarity}]"

    class Meta:
        verbose_name = _("Box Item History")
        verbose_name_plural = _("Box Item Histories")


class Recompensa(BaseModel):
    TIPO_CHOICES = [
        ('NIVEL', _('Por Nível')),
        ('CONQUISTA', _('Por Conquista')),
        ('CONQUISTAS_MULTIPLAS', _('Por Quantidade de Conquistas')),
    ]

    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, verbose_name=_("Tipo de Recompensa"))
    referencia = models.CharField(max_length=100, verbose_name=_("Referência"))  # nível ou código conquista
    item_id = models.IntegerField(verbose_name=_("Item ID"))
    item_name = models.CharField(max_length=100, verbose_name=_("Item Name"))
    enchant = models.IntegerField(default=0, verbose_name=_("Enchant"))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Quantidade"))

    class Meta:
        verbose_name = _("Recompensa")
        verbose_name_plural = _("Recompensas")

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.referencia} => {self.item_name} +{self.enchant} x{self.quantity}"
    
    @property
    def referencia_como_inteiro(self):
        try:
            return int(self.referencia)
        except (ValueError, TypeError):
            return None


class RecompensaRecebida(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recompensas_recebidas_games", verbose_name=_("User"))
    recompensa = models.ForeignKey(Recompensa, on_delete=models.CASCADE, verbose_name=_("Reward"))
    data = models.DateTimeField(auto_now_add=True, verbose_name=_("Date"))

    class Meta:
        unique_together = ('user', 'recompensa')
        verbose_name = _("Received Reward")
        verbose_name_plural = _("Received Rewards")

    def __str__(self):
        return f"{self.user.username} - {self.recompensa}"


class EconomyWeapon(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"))
    level = models.IntegerField(default=0, verbose_name=_("Level"))  # +0 a +10
    fragments = models.IntegerField(default=0, verbose_name=_("Fragments"))

    class Meta:
        verbose_name = _("Economy Weapon")
        verbose_name_plural = _("Economy Weapons")

    def __str__(self):
        return f"{self.user.username} [+{self.level}] ({self.fragments} frags)"


class Monster(BaseModel):
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    level = models.IntegerField(verbose_name=_("Level"))
    required_weapon_level = models.IntegerField(verbose_name=_("Required Weapon Level"))
    fragment_reward = models.IntegerField(verbose_name=_("Fragment Reward"))
    image = models.ImageField(upload_to='monsters/', null=True, blank=True, verbose_name=_("Image"))
    respawn_seconds = models.PositiveIntegerField(default=60, verbose_name=_("Respawn Time (seconds)"))
    last_defeated_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Last Defeated At"))

    # Atributos básicos
    attack = models.IntegerField(default=10, verbose_name=_("Attack"))
    defense = models.IntegerField(default=5, verbose_name=_("Defense"))
    hp = models.IntegerField(default=100, verbose_name=_("HP"))

    class Meta:
        verbose_name = _("Monster")
        verbose_name_plural = _("Monsters")

    @property
    def is_alive(self):
        if not self.last_defeated_at:
            return True
        return timezone.now() >= self.last_defeated_at + timedelta(seconds=self.respawn_seconds)

    def __str__(self):
        return f"{self.name} (Level {self.level})"


class RewardItem(BaseModel):
    # Transição: manter campos legados e adicionar FK opcional para Item
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    legacy_item_code = models.PositiveIntegerField(verbose_name=_("Item ID"))
    enchant = models.PositiveIntegerField(default=0, verbose_name=_("Enchant"))
    amount = models.PositiveIntegerField(default=1, verbose_name=_("Amount"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    # Novo
    item = models.ForeignKey('Item', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Item"))

    class Meta:
        verbose_name = _("Reward Item")
        verbose_name_plural = _("Reward Items")

    def __str__(self):
        base = self.item.name if self.item else self.name
        ench = self.item.enchant if self.item else self.enchant
        return f"{base} +{ench}"


# ==============================
# Daily Bonus System
# ==============================

class DailyBonusSeason(BaseModel):
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    is_active = models.BooleanField(default=False, verbose_name=_("Is Active"))
    reset_hour_utc = models.PositiveSmallIntegerField(default=3, verbose_name=_("Reset Hour (UTC)"))

    class Meta:
        verbose_name = _("Daily Bonus Season")
        verbose_name_plural = _("Daily Bonus Seasons")

    def __str__(self):
        return f"{self.name} ({'active' if self.is_active else 'inactive'})"

    def save(self, *args, **kwargs):
        if self.is_active:
            DailyBonusSeason.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class DailyBonusPoolEntry(BaseModel):
    season = models.ForeignKey(DailyBonusSeason, on_delete=models.CASCADE, related_name='pool_entries', verbose_name=_("Season"))
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name=_("Item"))
    weight = models.PositiveIntegerField(default=1, verbose_name=_("Weight"))

    class Meta:
        verbose_name = _("Daily Bonus Pool Entry")
        verbose_name_plural = _("Daily Bonus Pool Entries")

    def __str__(self):
        return f"{self.item.name} (w={self.weight})"


class DailyBonusDay(BaseModel):
    MODE_CHOICES = (
        ('FIXED', _("Fixed Item")),
        ('RANDOM', _("Random from Pool")),
    )
    season = models.ForeignKey(DailyBonusSeason, on_delete=models.CASCADE, related_name='days', verbose_name=_("Season"))
    day_of_month = models.PositiveSmallIntegerField(verbose_name=_("Day of Month"))
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='RANDOM', verbose_name=_("Mode"))
    fixed_item = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_("Fixed Item"))

    class Meta:
        unique_together = ('season', 'day_of_month')
        verbose_name = _("Daily Bonus Day")
        verbose_name_plural = _("Daily Bonus Days")

    def __str__(self):
        return f"{self.season.name} - Day {self.day_of_month} ({self.mode})"


class DailyBonusClaim(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_bonus_claims', verbose_name=_("User"))
    season = models.ForeignKey(DailyBonusSeason, on_delete=models.CASCADE, related_name='claims', verbose_name=_("Season"))
    day_of_month = models.PositiveSmallIntegerField(verbose_name=_("Day of Month"))
    claimed_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Claimed At"))

    class Meta:
        unique_together = ('user', 'season', 'day_of_month')
        verbose_name = _("Daily Bonus Claim")
        verbose_name_plural = _("Daily Bonus Claims")

    def __str__(self):
        return f"{self.user.username} claimed day {self.day_of_month} of {self.season.name}"

class BattlePassSeason(BaseModel):
    name = models.CharField(max_length=100)
    start_date = models.DateTimeField(verbose_name=_("Start Date"))
    end_date = models.DateTimeField(verbose_name=_("End Date"))
    is_active = models.BooleanField(default=False, verbose_name=_("Is Active"))
    premium_price = models.PositiveIntegerField(default=50, verbose_name=_("Premium Price"))

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_active:
            BattlePassSeason.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class BattlePassLevel(BaseModel):
    season = models.ForeignKey(BattlePassSeason, on_delete=models.CASCADE, verbose_name=_("Season"))
    level = models.PositiveIntegerField(verbose_name=_("Level"))
    required_xp = models.PositiveIntegerField(verbose_name=_("Required XP"))

    class Meta:
        unique_together = ('season', 'level')
        verbose_name = _("Battle Pass Level")
        verbose_name_plural = _("Battle Pass Levels")

    def __str__(self):
        return f"Level {self.level} - {self.season}"


class BattlePassReward(BaseModel):
    level = models.ForeignKey(BattlePassLevel, on_delete=models.CASCADE, verbose_name=_("Level"))
    description = models.CharField(max_length=255, verbose_name=_("Description"))
    is_premium = models.BooleanField(default=False, verbose_name=_("Is Premium"))
    # Campos para itens
    item_id = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Item ID"))
    item_name = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("Item Name"))
    item_enchant = models.PositiveIntegerField(default=0, verbose_name=_("Item Enchant"))
    item_amount = models.PositiveIntegerField(default=1, verbose_name=_("Item Amount"))

    class Meta:
        verbose_name = _("Battle Pass Reward")
        verbose_name_plural = _("Battle Pass Rewards")

    def __str__(self):
        return f"{self.description} ({_('Premium') if self.is_premium else _('Free')})"

    def add_to_user_bag(self, user):
        if self.item_id and self.item_name:
            bag = Bag.objects.get(user=user)
            bag_item, created = BagItem.objects.get_or_create(
                bag=bag,
                item_id=self.item_id,
                enchant=self.item_enchant,
                defaults={
                    'item_name': self.item_name,
                    'quantity': self.item_amount,
                }
            )
            if not created:
                bag_item.quantity += self.item_amount
                bag_item.save()
            return bag_item
        return None


class UserBattlePassProgress(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    season = models.ForeignKey(BattlePassSeason, on_delete=models.CASCADE, verbose_name=_("Season"))
    xp = models.PositiveIntegerField(default=0, verbose_name=_("XP"))
    claimed_rewards = models.ManyToManyField(BattlePassReward, blank=True, verbose_name=_("Claimed Rewards"))
    has_premium = models.BooleanField(default=False, verbose_name=_("Has Premium"))

    class Meta:
        unique_together = ('user', 'season')
        verbose_name = _("User Battle Pass Progress")
        verbose_name_plural = _("User Battle Pass Progresses")

    def get_current_level(self):
        return self.season.battlepasslevel_set.filter(required_xp__lte=self.xp).order_by('-level').first()

    def add_xp(self, amount):
        self.xp += amount
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.season} (XP: {self.xp})"


class BattlePassItemExchange(BaseModel):
    item_id = models.PositiveIntegerField(verbose_name=_("Item ID"))
    item_name = models.CharField(max_length=100, verbose_name=_("Item Name"))
    item_enchant = models.PositiveIntegerField(default=0, verbose_name=_("Item Enchant"))
    xp_amount = models.PositiveIntegerField(verbose_name=_("XP Amount"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    max_exchanges = models.PositiveIntegerField(default=0, verbose_name=_("Max Exchanges"), 
        help_text=_("0 = sem limite"))
    current_exchanges = models.PositiveIntegerField(default=0, verbose_name=_("Current Exchanges"))

    class Meta:
        verbose_name = _("Battle Pass Item Exchange")
        verbose_name_plural = _("Battle Pass Item Exchanges")

    def __str__(self):
        return f"{self.item_name} +{self.item_enchant} -> {self.xp_amount} XP"

    def can_exchange(self):
        if not self.is_active:
            return False
        if self.max_exchanges == 0:
            return True
        return self.current_exchanges < self.max_exchanges

    def exchange(self, user, quantity=1):
        if not self.can_exchange():
            return False, _("Esta troca não está mais disponível.")

        try:
            bag = Bag.objects.get(user=user)
            bag_item = BagItem.objects.get(
                bag=bag,
                item_id=self.item_id,
                enchant=self.item_enchant
            )

            if bag_item.quantity < quantity:
                return False, _("Você não possui quantidade suficiente deste item.")

            # Remove os itens da bag
            bag_item.quantity -= quantity
            if bag_item.quantity == 0:
                bag_item.delete()
            else:
                bag_item.save()

            # Adiciona XP ao progresso do Battle Pass
            progress = UserBattlePassProgress.objects.get(
                user=user,
                season=BattlePassSeason.objects.filter(is_active=True).first()
            )
            total_xp = self.xp_amount * quantity
            progress.add_xp(total_xp)

            # Incrementa o contador de trocas
            self.current_exchanges += quantity
            self.save()

            return True, _("Troca realizada com sucesso! Você recebeu {} XP.").format(total_xp)

        except Bag.DoesNotExist:
            return False, _("Você não possui uma bag.")
        except BagItem.DoesNotExist:
            return False, _("Você não possui este item.")
        except UserBattlePassProgress.DoesNotExist:
            return False, _("Você não possui progresso no Battle Pass atual.")
        except Exception as e:
            return False, str(e)


# ==============================
# Slot Machine System
# ==============================

class SlotMachineConfig(BaseModel):
    """Configuração da Slot Machine"""
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    cost_per_spin = models.PositiveIntegerField(default=1, verbose_name=_("Cost per Spin (Fichas)"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    jackpot_amount = models.PositiveIntegerField(default=0, verbose_name=_("Jackpot Amount"))
    jackpot_chance = models.FloatField(default=0.1, verbose_name=_("Jackpot Chance (%)"))

    class Meta:
        verbose_name = _("Slot Machine Config")
        verbose_name_plural = _("Slot Machine Configs")

    def __str__(self):
        return self.name


class SlotMachineSymbol(BaseModel):
    """Símbolos disponíveis na Slot Machine"""
    SYMBOL_CHOICES = [
        ('sword', _('Espada')),
        ('shield', _('Escudo')),
        ('potion', _('Poção')),
        ('gem', _('Gema')),
        ('gold', _('Ouro')),
        ('armor', _('Armadura')),
        ('bow', _('Arco')),
        ('staff', _('Cajado')),
        ('jackpot', _('Jackpot')),
    ]
    
    symbol = models.CharField(max_length=20, choices=SYMBOL_CHOICES, unique=True, verbose_name=_("Symbol"))
    weight = models.PositiveIntegerField(default=10, verbose_name=_("Weight"))
    icon = models.CharField(max_length=50, default='🎰', verbose_name=_("Icon/Emoji"))
    
    class Meta:
        verbose_name = _("Slot Machine Symbol")
        verbose_name_plural = _("Slot Machine Symbols")

    def __str__(self):
        return f"{self.get_symbol_display()} ({self.icon})"


class SlotMachinePrize(BaseModel):
    """Prêmios da Slot Machine baseados em combinações"""
    config = models.ForeignKey(SlotMachineConfig, on_delete=models.CASCADE, related_name='prizes', verbose_name=_("Config"))
    symbol = models.ForeignKey(SlotMachineSymbol, on_delete=models.CASCADE, verbose_name=_("Symbol"))
    matches_required = models.PositiveIntegerField(default=3, verbose_name=_("Matches Required"))
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Item"))
    fichas_prize = models.PositiveIntegerField(default=0, verbose_name=_("Fichas Prize"))
    
    class Meta:
        verbose_name = _("Slot Machine Prize")
        verbose_name_plural = _("Slot Machine Prizes")
        unique_together = ('config', 'symbol', 'matches_required')

    def __str__(self):
        return f"{self.matches_required}x {self.symbol.get_symbol_display()}"


class SlotMachineHistory(BaseModel):
    """Histórico de jogadas na Slot Machine"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    config = models.ForeignKey(SlotMachineConfig, on_delete=models.CASCADE, verbose_name=_("Config"))
    symbols_result = models.CharField(max_length=100, verbose_name=_("Symbols Result"))
    prize_won = models.ForeignKey(SlotMachinePrize, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Prize Won"))
    is_jackpot = models.BooleanField(default=False, verbose_name=_("Is Jackpot"))
    fichas_won = models.PositiveIntegerField(default=0, verbose_name=_("Fichas Won"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Slot Machine History")
        verbose_name_plural = _("Slot Machine Histories")

    def __str__(self):
        return f"{self.user.username} - {self.symbols_result}"


# ==============================
# Dice Game System
# ==============================

class DiceGameConfig(BaseModel):
    """Configuração do Dice Game"""
    min_bet = models.PositiveIntegerField(default=1, verbose_name=_("Minimum Bet"))
    max_bet = models.PositiveIntegerField(default=100, verbose_name=_("Maximum Bet"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    
    # Multiplicadores
    specific_number_multiplier = models.FloatField(default=5.0, verbose_name=_("Specific Number Multiplier"))
    even_odd_multiplier = models.FloatField(default=2.0, verbose_name=_("Even/Odd Multiplier"))
    high_low_multiplier = models.FloatField(default=2.0, verbose_name=_("High/Low Multiplier"))
    
    class Meta:
        verbose_name = _("Dice Game Config")
        verbose_name_plural = _("Dice Game Configs")

    def __str__(self):
        return f"Dice Game Config (Min: {self.min_bet}, Max: {self.max_bet})"


class DiceGamePrize(BaseModel):
    """Prêmios especiais para o Dice Game"""
    name = models.CharField(max_length=100, verbose_name=_("Prize Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    drop_chance = models.FloatField(default=5.0, verbose_name=_("Drop Chance (%)"),
                                     help_text=_("Chance de ganhar este prêmio em uma vitória"))
    fichas_bonus = models.PositiveIntegerField(default=0, verbose_name=_("Bonus Fichas"))
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Item"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    
    class Meta:
        verbose_name = _("Dice Game Prize")
        verbose_name_plural = _("Dice Game Prizes")
    
    def __str__(self):
        return f"{self.name} ({self.drop_chance}%)"


class DiceGameHistory(BaseModel):
    """Histórico de jogadas no Dice Game"""
    BET_TYPE_CHOICES = [
        ('number', _('Número Específico')),
        ('even', _('Par')),
        ('odd', _('Ímpar')),
        ('high', _('Alto (4-6)')),
        ('low', _('Baixo (1-3)')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    bet_type = models.CharField(max_length=10, choices=BET_TYPE_CHOICES, verbose_name=_("Bet Type"))
    bet_value = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Bet Value"))
    bet_amount = models.PositiveIntegerField(verbose_name=_("Bet Amount (Fichas)"))
    dice_result = models.PositiveIntegerField(verbose_name=_("Dice Result"))
    won = models.BooleanField(default=False, verbose_name=_("Won"))
    prize_amount = models.PositiveIntegerField(default=0, verbose_name=_("Prize Amount"))
    bonus_prize = models.ForeignKey('DiceGamePrize', on_delete=models.SET_NULL, null=True, blank=True, 
                                     verbose_name=_("Bonus Prize Won"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Dice Game History")
        verbose_name_plural = _("Dice Game Histories")

    def __str__(self):
        return f"{self.user.username} - {self.get_bet_type_display()} - {'Won' if self.won else 'Lost'}"


# ==============================
# Fishing Game System
# ==============================

class FishingGameConfig(BaseModel):
    """Configuração do Fishing Game"""
    name = models.CharField(max_length=100, default="Fishing Game", verbose_name=_("Name"))
    cost_per_cast = models.PositiveIntegerField(default=1, verbose_name=_("Cost per Cast (Fichas)"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    
    class Meta:
        verbose_name = _("Fishing Game Config")
        verbose_name_plural = _("Fishing Game Configs")
    
    def __str__(self):
        return f"{self.name} - {'Active' if self.is_active else 'Inactive'}"


class FishingRod(BaseModel):
    """Vara de pesca do jogador"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"))
    level = models.PositiveIntegerField(default=1, verbose_name=_("Level"))
    experience = models.PositiveIntegerField(default=0, verbose_name=_("Experience"))
    
    class Meta:
        verbose_name = _("Fishing Rod")
        verbose_name_plural = _("Fishing Rods")

    def __str__(self):
        return f"{self.user.username} - Rod Level {self.level}"

    def add_experience(self, amount):
        """Adiciona experiência e verifica se sobe de nível"""
        self.experience += amount
        # A cada 100 XP sobe um nível
        while self.experience >= (self.level * 100):
            self.experience -= (self.level * 100)
            self.level += 1
        self.save()


class Fish(BaseModel):
    """Tipos de peixes disponíveis"""
    RARITY_CHOICES = [
        ('common', _('Comum')),
        ('rare', _('Raro')),
        ('epic', _('Épico')),
        ('legendary', _('Lendário')),
    ]
    
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, verbose_name=_("Rarity"))
    icon = models.CharField(max_length=10, default='🐟', verbose_name=_("Icon"), blank=True)
    image = models.ImageField(upload_to='fish/', null=True, blank=True, verbose_name=_("Image"))
    min_rod_level = models.PositiveIntegerField(default=1, verbose_name=_("Min Rod Level"))
    weight = models.PositiveIntegerField(default=10, verbose_name=_("Catch Weight"))
    experience_reward = models.PositiveIntegerField(default=10, verbose_name=_("Experience Reward"))
    item_reward = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Item Reward"))
    fichas_reward = models.PositiveIntegerField(default=0, verbose_name=_("Fichas Reward"))
    
    class Meta:
        verbose_name = _("Fish")
        verbose_name_plural = _("Fishes")

    def get_display_image(self):
        """Retorna URL da imagem ou ícone como fallback"""
        if self.image:
            return self.image.url
        return None

    def __str__(self):
        return f"{self.icon if self.icon else '🐟'} {self.name} ({self.get_rarity_display()})"


class FishingHistory(BaseModel):
    """Histórico de pescarias"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    fish = models.ForeignKey(Fish, on_delete=models.CASCADE, verbose_name=_("Fish"))
    rod_level = models.PositiveIntegerField(verbose_name=_("Rod Level"))
    success = models.BooleanField(default=True, verbose_name=_("Success"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Fishing History")
        verbose_name_plural = _("Fishing Histories")

    def __str__(self):
        return f"{self.user.username} caught {self.fish.name}"


class FishingBait(BaseModel):
    """Iscas especiais para aumentar chances"""
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    description = models.TextField(verbose_name=_("Description"))
    price = models.PositiveIntegerField(verbose_name=_("Price (Fichas)"))
    rarity_boost = models.CharField(max_length=20, choices=Fish.RARITY_CHOICES, verbose_name=_("Rarity Boost"))
    boost_percentage = models.FloatField(default=10.0, verbose_name=_("Boost Percentage"))
    duration_minutes = models.PositiveIntegerField(default=30, verbose_name=_("Duration (minutes)"))
    
    class Meta:
        verbose_name = _("Fishing Bait")
        verbose_name_plural = _("Fishing Baits")

    def __str__(self):
        return self.name


class UserFishingBait(BaseModel):
    """Iscas ativas do usuário"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    bait = models.ForeignKey(FishingBait, on_delete=models.CASCADE, verbose_name=_("Bait"))
    activated_at = models.DateTimeField(verbose_name=_("Activated At"))
    expires_at = models.DateTimeField(verbose_name=_("Expires At"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        verbose_name = _("User Fishing Bait")
        verbose_name_plural = _("User Fishing Baits")

    def __str__(self):
        return f"{self.user.username} - {self.bait.name}"

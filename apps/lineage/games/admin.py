from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import *
from core.admin import BaseModelAdmin
from .forms import BoxTypeAdminForm


@admin.register(Prize)
class PrizeAdmin(BaseModelAdmin):
    list_display = ('display_name', 'image_preview', 'weight', 'display_item_id', 'display_enchant', 'rarity', 'created_at', 'updated_at')
    search_fields = ('name', 'item__name', 'legacy_item_code')
    list_filter = ('created_at', 'rarity', 'enchant')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('name',)
    
    fieldsets = (
        (_('Informações do Prêmio'), {
            'fields': ('item', 'name', 'image', 'weight', 'enchant', 'rarity', 'legacy_item_code')
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        return format_html(
            '<img src="{}" width="50" height="50" style="object-fit: contain; border: 1px solid #ccc; border-radius: 6px;" />',
            obj.get_image_url()
        )
    image_preview.short_description = _('Imagem')

    def display_name(self, obj):
        return obj.item.name if obj.item else obj.name
    display_name.short_description = _('Nome')

    def display_item_id(self, obj):
        return obj.item.item_id if obj.item else obj.legacy_item_code
    display_item_id.short_description = _('Item ID')

    def display_enchant(self, obj):
        return obj.item.enchant if obj.item else obj.enchant
    display_enchant.short_description = _('Enchant')


@admin.register(SpinHistory)
class SpinHistoryAdmin(BaseModelAdmin):
    list_display = ('user', 'prize', 'created_at', 'fail_chance', 'get_prize_rarity')
    search_fields = ('user__username', 'prize__name')
    list_filter = ('created_at', 'prize__rarity', 'fail_chance')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('Usuário e Prêmio'), {
            'fields': ('user', 'prize')
        }),
        (_('Auditoria'), {
            'fields': ('fail_chance', 'seed', 'weights_snapshot'),
            'classes': ('collapse',)
        }),
        (_('Data'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_prize_rarity(self, obj):
        rarity_colors = {
            'common': '#6c757d',
            'rare': '#007bff',
            'epic': '#6f42c1',
            'legendary': '#fd7e14'
        }
        color = rarity_colors.get(obj.prize.rarity, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.prize.get_rarity_display()
        )
    get_prize_rarity.short_description = _('Raridade')


@admin.register(GameConfig)
class GameConfigAdmin(BaseModelAdmin):
    list_display = ('fail_chance', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Bag)
class BagAdmin(BaseModelAdmin):
    list_display = ('user', 'get_items_count', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('Usuário'), {
            'fields': ('user',)
        }),
        (_('Data'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_items_count(self, obj):
        return obj.items.count()
    get_items_count.short_description = _('Itens')


@admin.register(BagItem)
class BagItemAdmin(BaseModelAdmin):
    list_display = ('bag', 'item_name', 'enchant', 'quantity', 'added_at')
    search_fields = ('item_name', 'bag__user__username')
    list_filter = ('enchant', 'added_at', 'quantity')
    readonly_fields = ('added_at',)
    ordering = ('-added_at',)
    
    fieldsets = (
        (_('Bag e Item'), {
            'fields': ('bag', 'item_name', 'enchant', 'quantity')
        }),
        (_('Data'), {
            'fields': ('added_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Item)
class ItemAdmin(BaseModelAdmin):
    list_display = ('name', 'item_id', 'enchant', 'rarity', 'can_be_populated', 'description')
    list_editable = ('can_be_populated',)
    search_fields = ('name', 'item_id', 'description')
    list_filter = ('rarity', 'enchant', 'can_be_populated')
    ordering = ('name',)
    
    fieldsets = (
        (_('Informações do Item'), {
            'fields': ('name', 'item_id', 'enchant', 'rarity', 'description', 'image')
        }),
        (_('Configurações'), {
            'fields': ('can_be_populated',),
            'description': _('Define se o item pode ser populado automaticamente')
        }),
    )


@admin.register(BoxType)
class BoxTypeAdmin(BaseModelAdmin):
    form = BoxTypeAdminForm
    
    list_display = (
        'name', 'price', 'boosters_amount',
        'chance_common', 'chance_rare', 'chance_epic', 'chance_legendary',
        'max_epic_items', 'max_legendary_items', 'get_items_count'
    )
    search_fields = ('name',)
    list_filter = ('price', 'boosters_amount', 'chance_legendary')
    ordering = ('name',)
    filter_horizontal = ('allowed_items',)

    fieldsets = (
        (_('Informações Básicas'), {
            'fields': (
                'name', 'price', 'boosters_amount',
                'allowed_items'
            )
        }),
        (_('Chances de Raridade (%)'), {
            'fields': (
                'chance_common', 'chance_rare',
                'chance_epic', 'chance_legendary'
            ),
            'description': _('Configure as chances de cada raridade (total deve ser 100%)')
        }),
        (_('Limites por Raridade'), {
            'fields': (
                'max_epic_items', 'max_legendary_items',
            ),
            'description': _('Limite máximo de itens por raridade')
        }),
    )
    
    def get_items_count(self, obj):
        return obj.allowed_items.count()
    get_items_count.short_description = _('Itens Permitidos')


@admin.register(Box)
class BoxAdmin(BaseModelAdmin):
    list_display = ('user', 'box_type', 'opened', 'created_at', 'get_prize_info')
    search_fields = ('user__username', 'box_type__name')
    list_filter = ('opened', 'created_at', 'box_type')
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('Usuário e Tipo'), {
            'fields': ('user', 'box_type')
        }),
        (_('Status'), {
            'fields': ('opened',),
            'description': _('Se a caixa foi aberta')
        }),
        (_('Data'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_prize_info(self, obj):
        if obj.opened:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
                _('Aberta')
            )
        return format_html(
            '<span style="background: #ffc107; color: black; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            _('Fechada')
        )
    get_prize_info.short_description = _('Status')


@admin.register(BoxItem)
class BoxItemAdmin(BaseModelAdmin):
    list_display = ('box', 'item', 'opened', 'probability', 'created_at')
    search_fields = ('box__user__username', 'item__name')
    list_filter = ('opened', 'created_at')
    ordering = ('box', 'item')
    
    fieldsets = (
        (_('Box e Item'), {
            'fields': ('box', 'item')
        }),
        (_('Configurações'), {
            'fields': ('opened', 'probability'),
            'description': _('Probabilidade de obter este item')
        }),
    )


@admin.register(BoxItemHistory)
class BoxItemHistoryAdmin(BaseModelAdmin):
    list_display = ('user', 'item', 'enchant', 'rarity', 'box', 'obtained_at', 'get_rarity_badge')
    list_filter = ('rarity', 'obtained_at', 'enchant')
    search_fields = ('user__username', 'item__name')
    ordering = ('-obtained_at',)
    readonly_fields = ('user', 'item', 'box', 'rarity', 'enchant', 'obtained_at')
    
    fieldsets = (
        (_('Usuário e Item'), {
            'fields': ('user', 'item', 'enchant', 'rarity')
        }),
        (_('Box'), {
            'fields': ('box',)
        }),
        (_('Data'), {
            'fields': ('obtained_at',),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
    
    def get_rarity_badge(self, obj):
        rarity_colors = {
            'common': '#6c757d',
            'rare': '#007bff',
            'epic': '#6f42c1',
            'legendary': '#fd7e14'
        }
        color = rarity_colors.get(obj.rarity, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_rarity_display()
        )
    get_rarity_badge.short_description = _('Raridade')


@admin.register(Recompensa)
class RecompensaAdmin(BaseModelAdmin):
    list_display = ('tipo', 'referencia', 'item_name', 'quantity', 'enchant', 'created_at')
    list_filter = ('tipo', 'enchant', 'created_at')
    search_fields = ('referencia', 'item_name')
    ordering = ('tipo', 'referencia')
    
    fieldsets = (
        (_('Informações da Recompensa'), {
            'fields': ('tipo', 'referencia', 'item_name', 'quantity', 'enchant')
        }),
    )


@admin.register(RecompensaRecebida)
class RecompensaRecebidaAdmin(BaseModelAdmin):
    list_display = ('user', 'recompensa', 'data', 'created_at')
    list_filter = ('data', 'created_at', 'recompensa__tipo')
    search_fields = ('user__username', 'recompensa__item_name', 'recompensa__tipo')
    ordering = ('-data',)
    readonly_fields = ('data',)
    
    fieldsets = (
        (_('Usuário e Recompensa'), {
            'fields': ('user', 'recompensa')
        }),
        (_('Informações da Recompensa'), {
            'fields': ('data',),
            'description': _('Data automaticamente definida quando a recompensa é recebida'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EconomyWeapon)
class EconomyWeaponAdmin(BaseModelAdmin):
    list_display = ('user', 'level', 'fragments', 'created_at')
    search_fields = ('user__username',)
    list_filter = ('level', 'created_at')
    ordering = ('-level',)
    
    fieldsets = (
        (_('Usuário'), {
            'fields': ('user',)
        }),
        (_('Progresso'), {
            'fields': ('level', 'fragments'),
            'description': _('Nível atual e fragmentos coletados')
        }),
    )


@admin.register(Monster)
class MonsterAdmin(BaseModelAdmin):
    list_display = ('name', 'level', 'required_weapon_level', 'fragment_reward', 'respawn_seconds', 'is_alive_display', 'created_at')
    readonly_fields = ('last_defeated_at',)
    search_fields = ('name',)
    list_filter = ('level', 'required_weapon_level', 'created_at')
    ordering = ('level', 'name')
    
    fieldsets = (
        (_('Informações do Monstro'), {
            'fields': ('name', 'level', 'required_weapon_level')
        }),
        (_('Recompensas'), {
            'fields': ('fragment_reward', 'respawn_seconds'),
            'description': _('Fragmentos ganhos e tempo de respawn')
        }),
        (_('Status'), {
            'fields': ('last_defeated_at',),
            'classes': ('collapse',)
        }),
    )

    def is_alive_display(self, obj):
        return obj.is_alive
    is_alive_display.boolean = True
    is_alive_display.short_description = _("Disponível para Luta")


@admin.register(RewardItem)
class RewardItemAdmin(BaseModelAdmin):
    list_display = ('item', 'amount', 'created_at')
    search_fields = ('item__name', 'item__item_id')
    list_filter = ('created_at',)
    ordering = ('-created_at',)

    fieldsets = (
        (_('Informações do Item'), {
            'fields': ('item', 'amount')
        }),
    )


# ==============================
# Daily Bonus Admin
# ==============================

@admin.register(DailyBonusSeason)
class DailyBonusSeasonAdmin(BaseModelAdmin):
    list_display = ('name', 'is_active', 'allow_retroactive_claim', 'start_date', 'end_date', 'reset_hour_utc', 'created_at')
    list_filter = ('is_active', 'allow_retroactive_claim', 'start_date', 'end_date')
    search_fields = ('name',)
    ordering = ('-is_active', '-start_date')
    fieldsets = (
        (_('Informações'), {'fields': ('name', 'is_active', 'start_date', 'end_date', 'reset_hour_utc')}),
        (_('Configurações'), {'fields': ('allow_retroactive_claim',)}),
        (_('Datas'), {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DailyBonusPoolEntry)
class DailyBonusPoolEntryAdmin(BaseModelAdmin):
    list_display = ('season', 'item', 'weight', 'created_at')
    list_filter = ('season', 'item__rarity')
    search_fields = ('item__name', 'season__name')
    ordering = ('season', '-weight')


@admin.register(DailyBonusDay)
class DailyBonusDayAdmin(BaseModelAdmin):
    list_display = ('season', 'day_of_month', 'mode', 'fixed_item')
    list_filter = ('season', 'mode')
    search_fields = ('season__name', 'fixed_item__name')
    ordering = ('season', 'day_of_month')
    fieldsets = (
        (_('Dia do Mês'), {'fields': ('season', 'day_of_month', 'mode', 'fixed_item')}),
    )


@admin.register(DailyBonusClaim)
class DailyBonusClaimAdmin(BaseModelAdmin):
    list_display = ('user', 'season', 'day_of_month', 'claimed_at')
    list_filter = ('season', 'claimed_at')
    search_fields = ('user__username', 'season__name')
    ordering = ('-claimed_at',)


@admin.register(BattlePassSeason)
class BattlePassSeasonAdmin(BaseModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active', 'get_duration')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('name',)
    ordering = ('-start_date',)
    
    fieldsets = (
        (_('Informações da Temporada'), {
            'fields': ('name', 'start_date', 'end_date')
        }),
        (_('Status'), {
            'fields': ('is_active',),
            'description': _('Se a temporada está ativa')
        }),
    )
    
    def get_duration(self, obj):
        if obj.start_date and obj.end_date:
            duration = obj.end_date - obj.start_date
            return f"{duration.days} dias"
        return _('N/A')
    get_duration.short_description = _('Duração')


class BattlePassRewardInline(admin.TabularInline):
    model = BattlePassReward
    extra = 1
    fields = ('description', 'is_premium', 'item_id', 'item_name', 'item_enchant', 'item_amount')


@admin.register(BattlePassLevel)
class BattlePassLevelAdmin(BaseModelAdmin):
    list_display = ('season', 'level', 'required_xp', 'get_rewards_count')
    list_filter = ('season', 'level')
    ordering = ('season', 'level')
    inlines = [BattlePassRewardInline]
    
    fieldsets = (
        (_('Informações do Nível'), {
            'fields': ('season', 'level', 'required_xp')
        }),
    )

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            instance.level = form.instance
            instance.save()
        formset.save_m2m()
    
    def get_rewards_count(self, obj):
        return obj.battlepassreward_set.count()
    get_rewards_count.short_description = _('Recompensas')


@admin.register(BattlePassReward)
class BattlePassRewardAdmin(BaseModelAdmin):
    list_display = ('level', 'description', 'is_premium', 'item_name', 'item_amount', 'item_enchant', 'get_premium_badge')
    list_filter = ('is_premium', 'level__season', 'item_enchant')
    search_fields = ('description', 'item_name')
    ordering = ('level__season', 'level__level')
    
    fieldsets = (
        (_('Informações da Recompensa'), {
            'fields': ('level', 'description', 'is_premium')
        }),
        (_('Item da Recompensa'), {
            'fields': ('item_id', 'item_name', 'item_enchant', 'item_amount'),
            'classes': ('collapse',)
        }),
    )
    
    def get_premium_badge(self, obj):
        if obj.is_premium:
            return format_html(
                '<span style="background: #fd7e14; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
                _('Premium')
            )
        return format_html(
            '<span style="background: #6c757d; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            _('Gratuita')
        )
    get_premium_badge.short_description = _('Tipo')


@admin.register(UserBattlePassProgress)
class UserBattlePassProgressAdmin(BaseModelAdmin):
    list_display = ('user', 'season', 'xp', 'has_premium', 'get_level', 'created_at')
    list_filter = ('season', 'has_premium', 'created_at')
    search_fields = ('user__username',)
    filter_horizontal = ('claimed_rewards',)
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('Usuário e Temporada'), {
            'fields': ('user', 'season')
        }),
        (_('Progresso'), {
            'fields': ('xp', 'has_premium'),
            'description': _('XP atual e status premium')
        }),
        (_('Recompensas Reclamadas'), {
            'fields': ('claimed_rewards',),
            'description': _('Recompensas já reclamadas pelo usuário')
        }),
    )
    
    def get_level(self, obj):
        # Calcular nível baseado no XP
        level = 1
        for bp_level in obj.season.battlepasslevel_set.order_by('level'):
            if obj.xp >= bp_level.required_xp:
                level = bp_level.level
            else:
                break
        return level
    get_level.short_description = _('Nível')


# Mensagem na área administrativa para o Daily Bonus
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib import messages as dj_messages

@receiver(user_logged_in)
def notify_daily_bonus(sender, request, user, **kwargs):
    try:
        from .models import DailyBonusSeason, DailyBonusClaim
        from .views.views import _current_bonus_day
        season = DailyBonusSeason.objects.filter(is_active=True).first()
        if not season:
            return
        today_day = _current_bonus_day(season.reset_hour_utc)
        if 1 <= today_day <= 31 and not DailyBonusClaim.objects.filter(user=user, season=season, day_of_month=today_day).exists():
            dj_messages.info(request, _('Você tem um bônus diário disponível!'))
    except Exception:
        # nunca quebrar o login por causa de notificação
        pass


@admin.register(BattlePassItemExchange)
class BattlePassItemExchangeAdmin(BaseModelAdmin):
    list_display = ('item_name', 'item_enchant', 'xp_amount', 'is_active', 'current_exchanges', 'max_exchanges', 'created_at')
    list_filter = ('is_active', 'item_enchant', 'created_at')
    search_fields = ('item_name',)
    readonly_fields = ('current_exchanges',)
    ordering = ('item_name',)
    
    fieldsets = (
        (_('Informações do Item'), {
            'fields': ('item_id', 'item_name', 'item_enchant', 'xp_amount', 'is_active')
        }),
        (_('Limites de Troca'), {
            'fields': ('max_exchanges', 'current_exchanges'),
            'description': _('Defina 0 em max_exchanges para trocas ilimitadas')
        }),
    )


# ==============================
# Slot Machine Admin
# ==============================

@admin.register(SlotMachineConfig)
class SlotMachineConfigAdmin(BaseModelAdmin):
    list_display = ('name', 'cost_per_spin', 'is_active', 'jackpot_amount', 'jackpot_chance', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    ordering = ('-is_active', 'name')
    
    fieldsets = (
        (_('Informações'), {
            'fields': ('name', 'cost_per_spin', 'is_active')
        }),
        (_('Jackpot'), {
            'fields': ('jackpot_amount', 'jackpot_chance'),
            'description': _('Configure o jackpot progressivo')
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SlotMachineSymbol)
class SlotMachineSymbolAdmin(BaseModelAdmin):
    list_display = ('symbol', 'icon', 'weight', 'created_at')
    list_filter = ('symbol', 'weight')
    search_fields = ('symbol',)
    ordering = ('symbol',)
    
    fieldsets = (
        (_('Informações do Símbolo'), {
            'fields': ('symbol', 'icon', 'weight')
        }),
    )


@admin.register(SlotMachinePrize)
class SlotMachinePrizeAdmin(BaseModelAdmin):
    list_display = ('config', 'symbol', 'matches_required', 'item', 'fichas_prize', 'created_at')
    list_filter = ('config', 'matches_required', 'symbol')
    search_fields = ('symbol__symbol', 'item__name')
    ordering = ('config', 'matches_required')
    
    fieldsets = (
        (_('Configuração e Símbolo'), {
            'fields': ('config', 'symbol', 'matches_required')
        }),
        (_('Prêmios'), {
            'fields': ('item', 'fichas_prize'),
            'description': _('Item ou fichas como prêmio')
        }),
    )


@admin.register(SlotMachineHistory)
class SlotMachineHistoryAdmin(BaseModelAdmin):
    list_display = ('user', 'config', 'symbols_result', 'prize_won', 'is_jackpot', 'fichas_won', 'created_at')
    list_filter = ('is_jackpot', 'created_at', 'config')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('Usuário e Configuração'), {
            'fields': ('user', 'config', 'symbols_result')
        }),
        (_('Resultado'), {
            'fields': ('prize_won', 'is_jackpot', 'fichas_won')
        }),
        (_('Data'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# ==============================
# Dice Game Admin
# ==============================

@admin.register(DiceGameConfig)
class DiceGameConfigAdmin(BaseModelAdmin):
    list_display = ('min_bet', 'max_bet', 'is_active', 'specific_number_multiplier', 'even_odd_multiplier', 'high_low_multiplier')
    list_filter = ('is_active',)
    
    fieldsets = (
        (_('Configurações de Aposta'), {
            'fields': ('min_bet', 'max_bet', 'is_active')
        }),
        (_('Multiplicadores'), {
            'fields': ('specific_number_multiplier', 'even_odd_multiplier', 'high_low_multiplier'),
            'description': _('Configure os multiplicadores de cada tipo de aposta')
        }),
    )


@admin.register(DiceGamePrize)
class DiceGamePrizeAdmin(BaseModelAdmin):
    list_display = ('name', 'drop_chance', 'fichas_bonus', 'item', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('-drop_chance',)
    
    fieldsets = (
        (_('Informações do Prêmio'), {
            'fields': ('name', 'description', 'is_active')
        }),
        (_('Chance e Recompensas'), {
            'fields': ('drop_chance', 'fichas_bonus', 'item')
        }),
    )


@admin.register(DiceGameHistory)
class DiceGameHistoryAdmin(BaseModelAdmin):
    list_display = ('user', 'bet_type', 'bet_value', 'bet_amount', 'dice_result', 'won', 'prize_amount', 'bonus_prize', 'created_at')
    list_filter = ('bet_type', 'won', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('Usuário e Aposta'), {
            'fields': ('user', 'bet_type', 'bet_value', 'bet_amount')
        }),
        (_('Resultado'), {
            'fields': ('dice_result', 'won', 'prize_amount', 'bonus_prize')
        }),
        (_('Data'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# ==============================
# Fishing Game Admin
# ==============================

@admin.register(FishingGameConfig)
class FishingGameConfigAdmin(BaseModelAdmin):
    list_display = ('name', 'cost_per_cast', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    ordering = ('-is_active', 'name')
    
    fieldsets = (
        (_('Configurações'), {
            'fields': ('name', 'cost_per_cast', 'is_active')
        }),
    )


@admin.register(FishingRod)
class FishingRodAdmin(BaseModelAdmin):
    list_display = ('user', 'level', 'experience', 'created_at')
    search_fields = ('user__username',)
    list_filter = ('level', 'created_at')
    ordering = ('-level', '-experience')
    
    fieldsets = (
        (_('Usuário'), {
            'fields': ('user',)
        }),
        (_('Progresso'), {
            'fields': ('level', 'experience'),
            'description': _('Nível e experiência da vara de pesca')
        }),
    )


@admin.register(Fish)
class FishAdmin(BaseModelAdmin):
    list_display = ('name', 'image_preview', 'rarity', 'min_rod_level', 'weight', 'experience_reward', 'fichas_reward', 'item_reward')
    list_filter = ('rarity', 'min_rod_level')
    search_fields = ('name',)
    ordering = ('rarity', 'min_rod_level', 'name')
    
    fieldsets = (
        (_('Informações do Peixe'), {
            'fields': ('name', 'image', 'icon', 'rarity', 'min_rod_level')
        }),
        (_('Captura'), {
            'fields': ('weight',),
            'description': _('Peso para chance de captura')
        }),
        (_('Recompensas'), {
            'fields': ('experience_reward', 'fichas_reward', 'item_reward'),
            'description': _('Recompensas ao capturar o peixe')
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 8px;" />',
                obj.image.url
            )
        return obj.icon or '🐟'
    image_preview.short_description = _('Imagem')


@admin.register(FishingHistory)
class FishingHistoryAdmin(BaseModelAdmin):
    list_display = ('user', 'fish', 'rod_level', 'success', 'created_at')
    list_filter = ('success', 'fish__rarity', 'created_at')
    search_fields = ('user__username', 'fish__name')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('Usuário e Peixe'), {
            'fields': ('user', 'fish', 'rod_level')
        }),
        (_('Resultado'), {
            'fields': ('success',)
        }),
        (_('Data'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(FishingBait)
class FishingBaitAdmin(BaseModelAdmin):
    list_display = ('name', 'price', 'rarity_boost', 'boost_percentage', 'duration_minutes', 'created_at')
    list_filter = ('rarity_boost', 'duration_minutes')
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    fieldsets = (
        (_('Informações da Isca'), {
            'fields': ('name', 'description', 'price')
        }),
        (_('Bônus'), {
            'fields': ('rarity_boost', 'boost_percentage', 'duration_minutes'),
            'description': _('Configure o bônus de captura da isca')
        }),
    )


@admin.register(UserFishingBait)
class UserFishingBaitAdmin(BaseModelAdmin):
    list_display = ('user', 'bait', 'activated_at', 'expires_at', 'is_active')
    list_filter = ('is_active', 'activated_at', 'expires_at')
    search_fields = ('user__username', 'bait__name')
    readonly_fields = ('activated_at',)
    ordering = ('-activated_at',)
    
    fieldsets = (
        (_('Usuário e Isca'), {
            'fields': ('user', 'bait', 'is_active')
        }),
        (_('Duração'), {
            'fields': ('activated_at', 'expires_at'),
            'description': _('Período de ativação da isca')
        }),
    )

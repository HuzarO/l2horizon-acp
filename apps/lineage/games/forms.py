from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (
    Prize, Item, Box, BoxType, SlotMachineConfig, SlotMachineSymbol, 
    SlotMachinePrize, DiceGameConfig, DiceGamePrize, FishingGameConfig, Fish, FishingBait,
    DailyBonusSeason, DailyBonusPoolEntry, DailyBonusDay,
    Monster, RewardItem
)


class PrizeForm(forms.ModelForm):
    item = forms.ModelChoiceField(
        queryset=Item.objects.filter(can_be_populated=True),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Item')
    )
    
    class Meta:
        model = Prize
        fields = ['item', 'weight']
        widgets = {
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
        labels = {
            'weight': _('Peso (Chance)'),
        }


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'enchant', 'item_id', 'image', 'description', 'rarity', 'can_be_populated']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'enchant': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'item_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'rarity': forms.Select(attrs={'class': 'form-select'}),
            'can_be_populated': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': _('Nome'),
            'enchant': _('Nível de Encantamento'),
            'item_id': _('ID do Item'),
            'image': _('Imagem'),
            'description': _('Descrição'),
            'rarity': _('Raridade'),
            'can_be_populated': _('Pode ser Populado'),
        }


class BoxTypeAdminForm(forms.ModelForm):
    allowed_items = forms.ModelMultipleChoiceField(
        queryset=Item.objects.filter(can_be_populated=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=_('Itens Permitidos'),
        help_text=_('Selecione os itens que podem aparecer neste tipo de caixa')
    )
    
    class Meta:
        model = BoxType
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Caixa Premium'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'boosters_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '5'
            }),
            'chance_common': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': '60.00'
            }),
            'chance_rare': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': '25.00'
            }),
            'chance_epic': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': '10.00'
            }),
            'chance_legendary': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': '5.00'
            }),
            'max_epic_items': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'max_legendary_items': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
        }
        labels = {
            'name': _('Nome do Tipo de Caixa'),
            'price': _('Preço (R$)'),
            'boosters_amount': _('Quantidade de Boosters'),
            'chance_common': _('Chance de Comum (%)'),
            'chance_rare': _('Chance de Raro (%)'),
            'chance_epic': _('Chance de Épico (%)'),
            'chance_legendary': _('Chance de Lendário (%)'),
            'max_epic_items': _('Máximo de Itens Épicos'),
            'max_legendary_items': _('Máximo de Itens Lendários'),
        }
        help_texts = {
            'name': _('Nome que será exibido para os usuários'),
            'price': _('Valor em reais que a caixa custará'),
            'boosters_amount': _('Quantidade de itens que o jogador receberá'),
            'chance_common': _('Probabilidade de receber itens comuns'),
            'chance_rare': _('Probabilidade de receber itens raros'),
            'chance_epic': _('Probabilidade de receber itens épicos'),
            'chance_legendary': _('Probabilidade de receber itens lendários'),
            'max_epic_items': _('Limite máximo de itens épicos por caixa (0 = ilimitado)'),
            'max_legendary_items': _('Limite máximo de itens lendários por caixa (0 = ilimitado)'),
        }

    def clean(self):
        cleaned_data = super().clean()
        chance_common = cleaned_data.get('chance_common', 0)
        chance_rare = cleaned_data.get('chance_rare', 0)
        chance_epic = cleaned_data.get('chance_epic', 0)
        chance_legendary = cleaned_data.get('chance_legendary', 0)

        total = chance_common + chance_rare + chance_epic + chance_legendary
        if abs(total - 100) > 0.01:
            raise forms.ValidationError(
                f'A soma das chances deve ser 100%. Atual: {total}%'
            )

        return cleaned_data


# Alias for backward compatibility
BoxTypeForm = BoxTypeAdminForm


class BoxForm(forms.ModelForm):
    class Meta:
        model = Box
        fields = ['user', 'box_type', 'opened']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'box_type': forms.Select(attrs={'class': 'form-select'}),
            'opened': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'user': _('Usuário'),
            'box_type': _('Tipo de Caixa'),
            'opened': _('Aberto'),
        }


# ==============================
# Slot Machine Forms
# ==============================

class SlotMachineConfigForm(forms.ModelForm):
    class Meta:
        model = SlotMachineConfig
        fields = ['name', 'cost_per_spin', 'is_active', 'jackpot_amount', 'jackpot_chance']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'cost_per_spin': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'jackpot_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'jackpot_chance': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100', 'step': '0.1'}),
        }


class SlotMachineSymbolForm(forms.ModelForm):
    class Meta:
        model = SlotMachineSymbol
        fields = ['symbol', 'weight', 'icon']
        widgets = {
            'symbol': forms.Select(attrs={'class': 'form-select'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '🎰'}),
        }


class SlotMachinePrizeForm(forms.ModelForm):
    item = forms.ModelChoiceField(
        queryset=Item.objects.filter(can_be_populated=True),
        required=False,
        empty_label=_('-- Nenhum item --'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Item (Prêmio Extra)')
    )
    
    class Meta:
        model = SlotMachinePrize
        fields = ['symbol', 'matches_required', 'item', 'fichas_prize']
        widgets = {
            'symbol': forms.Select(attrs={'class': 'form-select'}),
            'matches_required': forms.NumberInput(attrs={'class': 'form-control', 'min': '2', 'max': '3'}),
            'fichas_prize': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }
        labels = {
            'symbol': _('Símbolo'),
            'matches_required': _('Combinações Necessárias'),
            'fichas_prize': _('Fichas'),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get('item')
        fichas_prize = cleaned_data.get('fichas_prize', 0)
        
        if not item and fichas_prize == 0:
            raise forms.ValidationError(
                _('Você deve definir pelo menos fichas OU um item como prêmio!')
            )
        
        return cleaned_data


# ==============================
# Dice Game Forms
# ==============================

class DiceGameConfigForm(forms.ModelForm):
    class Meta:
        model = DiceGameConfig
        fields = ['min_bet', 'max_bet', 'is_active', 'specific_number_multiplier', 
                  'even_odd_multiplier', 'high_low_multiplier']
        widgets = {
            'min_bet': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'max_bet': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'specific_number_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '0.1'}),
            'even_odd_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '0.1'}),
            'high_low_multiplier': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '0.1'}),
        }
        labels = {
            'min_bet': _('Aposta Mínima'),
            'max_bet': _('Aposta Máxima'),
            'is_active': _('Ativo'),
            'specific_number_multiplier': _('Multiplicador Número Específico'),
            'even_odd_multiplier': _('Multiplicador Par/Ímpar'),
            'high_low_multiplier': _('Multiplicador Alto/Baixo'),
        }


class DiceGamePrizeForm(forms.ModelForm):
    item = forms.ModelChoiceField(
        queryset=Item.objects.filter(can_be_populated=True),
        required=False,
        empty_label=_('-- Nenhum item --'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Item (Opcional)')
    )
    
    class Meta:
        model = DiceGamePrize
        fields = ['name', 'description', 'drop_chance', 'fichas_bonus', 'item', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'drop_chance': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100', 'step': '0.1'}),
            'fichas_bonus': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': _('Nome do Prêmio'),
            'description': _('Descrição'),
            'drop_chance': _('Chance de Drop (%)'),
            'fichas_bonus': _('Fichas Bônus'),
            'item': _('Item'),
            'is_active': _('Ativo'),
        }


# ==============================
# Fishing Game Forms
# ==============================

class FishingGameConfigForm(forms.ModelForm):
    class Meta:
        model = FishingGameConfig
        fields = ['name', 'cost_per_cast', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'cost_per_cast': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': _('Nome da Configuração'),
            'cost_per_cast': _('Custo por Lançamento (Fichas)'),
            'is_active': _('Ativo'),
        }


class FishForm(forms.ModelForm):
    item_reward = forms.ModelChoiceField(
        queryset=Item.objects.filter(can_be_populated=True),
        required=False,
        empty_label=_('-- Nenhum item --'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Item Recompensa (Opcional)')
    )
    
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        label=_('Imagem do Peixe (Opcional)')
    )
    
    class Meta:
        model = Fish
        fields = ['name', 'image', 'rarity', 'min_rod_level', 'weight', 
                  'experience_reward', 'fichas_reward', 'item_reward']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'rarity': forms.Select(attrs={'class': 'form-select'}),
            'min_rod_level': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'experience_reward': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'fichas_reward': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }
        labels = {
            'name': _('Nome do Peixe'),
            'rarity': _('Raridade'),
            'min_rod_level': _('Nível Mínimo de Vara'),
            'weight': _('Peso (Chance de Captura)'),
            'experience_reward': _('XP Recompensa'),
            'fichas_reward': _('Fichas Recompensa'),
        }


class FishingBaitForm(forms.ModelForm):
    class Meta:
        model = FishingBait
        fields = ['name', 'description', 'price', 'rarity_boost', 'boost_percentage', 'duration_minutes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'rarity_boost': forms.Select(attrs={'class': 'form-select'}),
            'boost_percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '0.1'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
        labels = {
            'name': _('Nome da Isca'),
            'description': _('Descrição'),
            'price': _('Preço (Fichas)'),
            'rarity_boost': _('Raridade Beneficiada'),
            'boost_percentage': _('Percentual de Bônus'),
            'duration_minutes': _('Duração (minutos)'),
        }


# ==============================
# Daily Bonus Forms
# ==============================

class DailyBonusSeasonForm(forms.ModelForm):
    class Meta:
        model = DailyBonusSeason
        fields = ['name', 'start_date', 'end_date', 'is_active', 'reset_hour_utc']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'reset_hour_utc': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '23'}),
        }


class DailyBonusPoolEntryForm(forms.ModelForm):
    item = forms.ModelChoiceField(
        queryset=Item.objects.filter(can_be_populated=True),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Item')
    )
    
    class Meta:
        model = DailyBonusPoolEntry
        fields = ['item', 'weight']
        widgets = {
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }


class DailyBonusDayForm(forms.ModelForm):
    fixed_item = forms.ModelChoiceField(
        queryset=Item.objects.filter(can_be_populated=True),
        required=False,
        empty_label=_('-- Nenhum item fixo --'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Item Fixo')
    )
    
    class Meta:
        model = DailyBonusDay
        fields = ['day_of_month', 'mode', 'fixed_item']
        widgets = {
            'day_of_month': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '31'}),
            'mode': forms.Select(attrs={'class': 'form-select'}),
        }


# ==============================
# Economy Game Forms
# ==============================

class MonsterManagerForm(forms.ModelForm):
    class Meta:
        model = Monster
        fields = ['name', 'level', 'required_weapon_level', 'fragment_reward', 
                  'image', 'respawn_seconds', 'attack', 'defense', 'hp']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'required_weapon_level': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'fragment_reward': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'respawn_seconds': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'attack': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'defense': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'hp': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }


class RewardItemManagerForm(forms.ModelForm):
    item = forms.ModelChoiceField(
        queryset=Item.objects.filter(can_be_populated=True),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Item')
    )
    
    class Meta:
        model = RewardItem
        fields = ['item', 'amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
        labels = {
            'amount': _('Quantidade'),
        }


# ==============================
# Roulette Forms
# ==============================

class PrizeManagerForm(forms.ModelForm):
    item = forms.ModelChoiceField(
        queryset=Item.objects.filter(can_be_populated=True),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label=_('Item'),
        help_text=_('Selecione o item que será adicionado à roleta')
    )
    
    weight = forms.IntegerField(
        initial=1,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'value': '1',
            'placeholder': '1'
        }),
        label=_('Peso (Chance)'),
        help_text=_('Quanto maior o peso, maior a chance do item sair na roleta')
    )
    
    class Meta:
        model = Prize
        fields = ['item', 'weight']
        labels = {
            'item': _('Item'),
            'weight': _('Peso (Chance)'),
        }

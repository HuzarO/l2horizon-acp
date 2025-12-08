from django.urls import path
from .views import (
    views, manager_box_views, battle_pass, economy_game_view, 
    daily_bonus_manager, roulette_manager, economy_manager, 
    slot_machine_views, dice_game_views, fishing_game_views,
    slot_machine_manager, dice_game_manager, fishing_game_manager,
    battle_pass_manager, battle_pass_quests, achievement_rewards_manager
)


app_name = "games"


urlpatterns = [
    path('buy-tokens/', views.comprar_fichas, name='comprar_fichas'),

    path('roulette/', views.roulette_page, name='roulette_page'),
    path('roulette/spin-ajax/', views.spin_ajax, name='spin_ajax'),
    
    path('bag/dashboard/', views.bag_dashboard, name='bag_dashboard'),
    path('bag/transfer/', views.transferir_item_bag, name='transferir_item_bag'),
    path('bag/empty/', views.esvaziar_bag_para_inventario, name='esvaziar_bag_para_inventario'),

    path('box/dashboard/', views.box_dashboard_view, name='box_user_dashboard'),
    path('box/opening/', views.box_opening_home, name='box_opening_home'),
    path('box/buy/<int:box_type_id>/', views.buy_box_view, name='box_buy'),
    path('box/buy-and-open/<int:box_type_id>/', views.buy_and_open_box_view, name='box_buy_and_open'),
    path('box/result/', views.open_box_view, name='box_user_open_box'),
    path('box/open-ajax/<int:box_id>/', views.open_box_ajax, name='box_open_ajax'),
    path('box/reset/<int:box_id>/', views.reset_box_view, name='box_reset'),

    path('box/manager/dashboard/', manager_box_views.dashboard, name='box_manager_dashboard'),
    path('box/manager/boxes/', manager_box_views.box_list_view, name='box_list'),
    path('box/manager/box/create/', manager_box_views.box_create_view, name='box_create'),
    path('box/manager/box/edit/<int:pk>/', manager_box_views.box_edit_view, name='box_edit'),
    path('box/manager/box/delete/<int:pk>/', manager_box_views.box_delete_view, name='box_delete'),
    path('box/manager/box-types/', manager_box_views.box_type_list_view, name='box_type_list'),
    path('box/manager/box-type/create/', manager_box_views.box_type_create_view, name='box_type_create'),
    path('box/manager/box-type/edit/<int:pk>/', manager_box_views.box_type_edit_view, name='box_type_edit'),
    path('box/manager/box-type/delete/<int:pk>/', manager_box_views.box_type_delete_view, name='box_type_delete'),
    path('box/manager/items/', manager_box_views.item_list_view, name='item_list'),
    path('box/manager/item/create/', manager_box_views.item_create_view, name='item_create'),
    path('box/manager/item/edit/<int:pk>/', manager_box_views.item_edit_view, name='item_edit'),
    path('box/manager/item/delete/<int:pk>/', manager_box_views.item_delete_view, name='item_delete'),

    # Daily Bonus
    path('daily-bonus/', views.daily_bonus_dashboard, name='daily_bonus_dashboard'),
    path('daily-bonus/claim/', views.daily_bonus_claim, name='daily_bonus_claim'),
    path('daily-bonus/manager/', daily_bonus_manager.manager_dashboard, name='daily_bonus_manager'),
    path('roulette/manager/', roulette_manager.dashboard, name='roulette_manager'),

    path("economy-game/", economy_game_view.economy_game, name="economy-game"),
    path('economy-game/manager/', economy_manager.dashboard, name='economy_manager'),
    path("economy-game/fight/<int:monster_id>/", economy_game_view.fight_monster, name="fight-monster"),
    path("economy-game/enchant/", economy_game_view.enchant_weapon, name="enchant-weapon"),
    path("economy-game/monster/<int:monster_id>/is_alive/", economy_game_view.is_monster_alive, name="monster-is-alive"),

    path('battle-pass/', battle_pass.battle_pass_view, name='battle_pass'),
    path('battle-pass/claim/<int:reward_id>/', battle_pass.claim_reward, name='claim_reward'),
    path('battle-pass/buy-premium/', battle_pass.buy_battle_pass_premium_view, name='buy_battle_pass_premium'),
    path('battle-pass/exchange/', battle_pass.exchange_items_view, name='exchange_items'),
    path('battle-pass/exchange/<int:exchange_id>/', battle_pass.exchange_item, name='exchange_item'),
    path('battle-pass/quests/', battle_pass_quests.quests_view, name='quests'),
    path('battle-pass/quests/<int:quest_id>/complete/', battle_pass_quests.complete_quest, name='complete_quest'),
    path('battle-pass/history/', battle_pass.battle_pass_history_view, name='battle_pass_history'),
    path('battle-pass/statistics/', battle_pass.battle_pass_statistics_view, name='battle_pass_statistics'),
    path('battle-pass/toggle-auto-claim/', battle_pass.toggle_auto_claim, name='toggle_auto_claim'),

    # Slot Machine
    path('slot-machine/', slot_machine_views.slot_machine_page, name='slot_machine_page'),
    path('slot-machine/spin/', slot_machine_views.slot_machine_spin, name='slot_machine_spin'),
    path('slot-machine/leaderboard/', slot_machine_views.slot_machine_leaderboard, name='slot_machine_leaderboard'),

    # Dice Game
    path('dice-game/', dice_game_views.dice_game_page, name='dice_game_page'),
    path('dice-game/play/', dice_game_views.dice_game_play, name='dice_game_play'),
    path('dice-game/leaderboard/', dice_game_views.dice_game_leaderboard, name='dice_game_leaderboard'),
    path('dice-game/statistics/', dice_game_views.dice_game_statistics, name='dice_game_statistics'),

    # Fishing Game
    path('fishing/', fishing_game_views.fishing_game_page, name='fishing_game_page'),
    path('fishing/cast/', fishing_game_views.fishing_game_cast, name='fishing_game_cast'),
    path('fishing/buy-bait/', fishing_game_views.fishing_buy_bait, name='fishing_buy_bait'),
    path('fishing/leaderboard/', fishing_game_views.fishing_leaderboard, name='fishing_leaderboard'),
    path('fishing/collection/', fishing_game_views.fishing_collection, name='fishing_collection'),

    # Managers
    path('slot-machine/manager/', slot_machine_manager.dashboard, name='slot_machine_manager'),
    path('dice-game/manager/', dice_game_manager.dashboard, name='dice_game_manager'),
    path('fishing/manager/', fishing_game_manager.dashboard, name='fishing_game_manager'),
    
    # Battle Pass Manager
    path('battle-pass/manager/', battle_pass_manager.dashboard, name='battle_pass_manager'),
    path('battle-pass/manager/seasons/', battle_pass_manager.season_list, name='battle_pass_manager_season_list'),
    path('battle-pass/manager/season/create/', battle_pass_manager.season_create, name='battle_pass_manager_season_create'),
    path('battle-pass/manager/season/<int:season_id>/', battle_pass_manager.season_detail, name='battle_pass_manager_season_detail'),
    path('battle-pass/manager/season/<int:season_id>/edit/', battle_pass_manager.season_edit, name='battle_pass_manager_season_edit'),
    path('battle-pass/manager/season/<int:season_id>/delete/', battle_pass_manager.season_delete, name='battle_pass_manager_season_delete'),
    path('battle-pass/manager/season/<int:season_id>/level/create/', battle_pass_manager.level_create, name='battle_pass_manager_level_create'),
    path('battle-pass/manager/level/<int:level_id>/edit/', battle_pass_manager.level_edit, name='battle_pass_manager_level_edit'),
    path('battle-pass/manager/level/<int:level_id>/delete/', battle_pass_manager.level_delete, name='battle_pass_manager_level_delete'),
    path('battle-pass/manager/level/<int:level_id>/reward/create/', battle_pass_manager.reward_create, name='battle_pass_manager_reward_create'),
    path('battle-pass/manager/reward/<int:reward_id>/edit/', battle_pass_manager.reward_edit, name='battle_pass_manager_reward_edit'),
    path('battle-pass/manager/reward/<int:reward_id>/delete/', battle_pass_manager.reward_delete, name='battle_pass_manager_reward_delete'),
    path('battle-pass/manager/exchanges/', battle_pass_manager.exchange_list, name='battle_pass_manager_exchange_list'),
    path('battle-pass/manager/exchange/create/', battle_pass_manager.exchange_create, name='battle_pass_manager_exchange_create'),
    path('battle-pass/manager/exchange/<int:exchange_id>/edit/', battle_pass_manager.exchange_edit, name='battle_pass_manager_exchange_edit'),
    path('battle-pass/manager/exchange/<int:exchange_id>/delete/', battle_pass_manager.exchange_delete, name='battle_pass_manager_exchange_delete'),
    # Quest Management
    path('battle-pass/manager/quests/', battle_pass_manager.quest_list, name='battle_pass_manager_quest_list'),
    path('battle-pass/manager/quest/create/', battle_pass_manager.quest_create, name='battle_pass_manager_quest_create'),
    path('battle-pass/manager/quest/<int:quest_id>/edit/', battle_pass_manager.quest_edit, name='battle_pass_manager_quest_edit'),
    path('battle-pass/manager/quest/<int:quest_id>/delete/', battle_pass_manager.quest_delete, name='battle_pass_manager_quest_delete'),
    # Milestone Management
    path('battle-pass/manager/season/<int:season_id>/milestones/', battle_pass_manager.milestone_list, name='battle_pass_manager_milestone_list'),
    path('battle-pass/manager/season/<int:season_id>/milestone/create/', battle_pass_manager.milestone_create, name='battle_pass_manager_milestone_create'),
    path('battle-pass/manager/milestone/<int:milestone_id>/edit/', battle_pass_manager.milestone_edit, name='battle_pass_manager_milestone_edit'),
    path('battle-pass/manager/milestone/<int:milestone_id>/delete/', battle_pass_manager.milestone_delete, name='battle_pass_manager_milestone_delete'),
    
    # Achievement Rewards Manager
    path('achievement-rewards/manager/', achievement_rewards_manager.dashboard, name='achievement_rewards_manager'),
    path('achievement-rewards/manager/rewards/', achievement_rewards_manager.reward_list, name='achievement_rewards_manager_reward_list'),
    path('achievement-rewards/manager/reward/create/', achievement_rewards_manager.reward_create, name='achievement_rewards_manager_reward_create'),
    path('achievement-rewards/manager/reward/<int:reward_id>/edit/', achievement_rewards_manager.reward_edit, name='achievement_rewards_manager_reward_edit'),
    path('achievement-rewards/manager/reward/<int:reward_id>/delete/', achievement_rewards_manager.reward_delete, name='achievement_rewards_manager_reward_delete'),
]

from django.urls import path
from .views import WorldDetailView, WorldCreateView, GrantAbilityPointsView, GrantItemView, QuickGiveChestView, \
    AcceptInviteView, WorldInviteLinkView, GMGrantSpellView, get_characters_hp, WorldUpdateView, WorldDeleteView

app_name = "worlds"

urlpatterns = [
    path("<int:pk>/", WorldDetailView.as_view(), name="detail"),
    path("create/", WorldCreateView.as_view(), name="create"),
    path("update/<int:pk>/", WorldUpdateView.as_view(), name="update"),
    path("delete/<int:pk>/", WorldDeleteView.as_view(), name="delete"),
    path("world/<int:world_pk>/character/<int:char_pk>/grant-points/", GrantAbilityPointsView.as_view(),
         name="world-grant-points"),
    path("world/<int:world_pk>/character/<int:char_pk>/grant-item/", GrantItemView.as_view(), name="world-grant-item"),
    path('worlds/<int:world_pk>/give/', QuickGiveChestView.as_view(), name='quick-give-chest'),
    path('worlds/<int:pk>/invite/', WorldInviteLinkView.as_view(), name='world-invite'),
    path('invite/<uuid:token>/', AcceptInviteView.as_view(), name='accept-invite'),
    path(
        'worlds/<int:world_pk>/chars/<int:char_pk>/grant-spell/',
        GMGrantSpellView.as_view(),
        name='gm-grant-spell'
    ),
    path('<int:world_id>/character-hp/', get_characters_hp, name='worlds:get_characters_hp'),

]


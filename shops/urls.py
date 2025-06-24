from django.urls import path

from shops.views import ajax_sell_item, ShopCreateView, ShopDetailView, ShopUpdateView, buy_item_from_shop, \
    update_price_multiplier, add_item_to_shop, update_item_price, update_item_quantity, remove_item_from_shop

app_name = "shops"

urlpatterns = [
    path("world/<int:world_id>/shops/create/", ShopCreateView.as_view(), name="shop-create"),
    path("shops/<int:pk>/", ShopDetailView.as_view(), name="shop-detail"),
    path("shops/<int:pk>/edit/", ShopUpdateView.as_view(), name="shop-edit"),
    path("shops/<int:character_id>/ajax/sell/<int:item_id>/", ajax_sell_item, name="ajax-sell-item"),
    path('<int:pk>/update-multiplier/', update_price_multiplier, name='shop-edit-multiplier'),
    path('<int:pk>/add-item/', add_item_to_shop, name='shop-add-item'),
    path('update-price/<int:entry_id>/', update_item_price, name='shop-update-price'),
    path('update-quantity/<int:entry_id>/', update_item_quantity, name='shop-update-quantity'),
    path('remove-item/<int:entry_id>/', remove_item_from_shop, name='shop-remove-item'),
    path('buy/<int:item_id>/', buy_item_from_shop, name='shop-buy-item'),

]

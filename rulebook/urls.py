from django.urls import path
from .views import FolderListView, ArticleListView, ArticleDetailView


urlpatterns = [
    path("", FolderListView.as_view(), name="folder_list"),
    path("folder/<slug:slug>/", ArticleListView.as_view(), name="article_list"),
    path("article/<slug:slug>/", ArticleDetailView.as_view(), name="article_detail"),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.ListBookView.as_view(), name='list-book'),
    path('book/<int:pk>/detail/', views.DetailBookView.as_view(), name='detail-book'),
    path('book/create/', views.CreateBookView.as_view(), name='create-book'),
    path('book/<int:pk>/delete/', views.DeleteBookView.as_view(), name='delete-book'),
    path('book/<int:pk>/update/', views.UpdateBookView.as_view(), name='update-book'),
    path('book/<int:book_id>/review/', views.CreateReviewView.as_view(), name='review'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('favorites/', views.FavoriteBooksView.as_view(), name='favorite-books'),
    path('book/<int:book_id>/toggle-favorite/', views.toggle_favorite, name='toggle-favorite'),
]
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

# Create your views here.
from django.views import generic
from .models import Shelf, Review
from .forms import ShelfForm, ReviewForm
from django.core.exceptions import PermissionDenied
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Q
from django.core.paginator import Paginator

class ListBookView(generic.ListView):
    template_name = 'book/book_list.html'
    model = Shelf
    context_object_name = 'Shelf'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Shelf.objects.all().order_by('-created_at')
        
        # 検索機能
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(text__icontains=search_query) |
                Q(category__icontains=search_query)
            )
        
        # カテゴリフィルタ
        category = self.request.GET.get('category', '')
        if category:
            queryset = queryset.filter(category=category)
        
        # ソート機能
        sort_by = self.request.GET.get('sort', 'newest')
        if sort_by == 'rating':
            queryset = queryset.annotate(avg_rating=Avg('review__rate')).order_by('-avg_rating')
        elif sort_by == 'title':
            queryset = queryset.order_by('title')
        elif sort_by == 'oldest':
            queryset = queryset.order_by('created_at')
        else:  # newest
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # レビュー平均でソートして上位3冊を取得
        ranking_list = (
            Shelf.objects.annotate(avg_rating=Avg('review__rate')).order_by('-avg_rating')[:3]
        )
        context['ranking_list'] = ranking_list
        context['categories'] = dict(Shelf._meta.get_field('category').choices)
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['sort_by'] = self.request.GET.get('sort', 'newest')
        return context

class DetailBookView(generic.DetailView):
    template_name = 'book/book_detail.html'
    model = Shelf
    context_object_name = 'Shelf'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 本に関連するレビューを取得
        reviews = Review.objects.filter(book=self.object).order_by('-created_at')
        paginator = Paginator(reviews, 5)  # 1ページに5件表示
        page_number = self.request.GET.get('page')
        context['reviews'] = paginator.get_page(page_number)
        context['similar_books'] = self.object.get_similar_books()
        context['is_favorited'] = self.object.is_favorited_by(self.request.user)
        return context

class CreateBookView(LoginRequiredMixin, generic.CreateView):
    template_name = 'book/book_create.html'
    model = Shelf
    form_class = ShelfForm
    context_object_name = 'Shelf'
    success_url = reverse_lazy('list-book')

    def form_valid(self, form):
        form.instance.user = self.request.user  # ログイン中のユーザーを設定
        return super().form_valid(form)
    

class DeleteBookView(LoginRequiredMixin, generic.DeleteView):
    template_name = 'book/book_confirm_delete.html'
    model = Shelf
    context_object_name = 'Shelf'
    success_url = reverse_lazy('list-book')
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != self.request.user:
            raise PermissionDenied('削除権限がありません。')
        return super(DeleteBookView, self).dispatch(request, *args, **kwargs)

class UpdateBookView(LoginRequiredMixin, generic.UpdateView):
    template_name = 'book/book_update.html'
    model = Shelf
    form_class = ShelfForm
    context_object_name = 'Shelf'
    success_url = reverse_lazy('list-book')
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != self.request.user:
            raise PermissionDenied('編集権限がありません。')
        return super(UpdateBookView, self).dispatch(request, *args, **kwargs)

class CreateReviewView(LoginRequiredMixin, generic.CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'book/review_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['book'] = Shelf.objects.get(pk=self.kwargs['book_id'])
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('detail-book', kwargs={'pk':self.object.book.id})

class DashboardView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'book/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # ユーザーの統計情報
        context['total_books'] = Shelf.objects.filter(user=user).count()
        context['total_reviews'] = Review.objects.filter(user=user).count()
        context['favorite_books'] = user.favorite_books.all()[:5]
        context['recent_books'] = Shelf.objects.filter(user=user).order_by('-created_at')[:5]
        context['recent_reviews'] = Review.objects.filter(user=user).order_by('-created_at')[:5]
        
        # カテゴリ別統計
        category_stats = {}
        category_choices = Shelf._meta.get_field('category').choices
        for category_code, category_name in category_choices:
            count = Shelf.objects.filter(user=user, category=category_code).count()
            category_stats[category_name] = count
        context['category_stats'] = category_stats
        
        return context

@login_required
@require_POST
def toggle_favorite(request, book_id):
    """お気に入り登録/解除"""
    book = get_object_or_404(Shelf, id=book_id)
    user = request.user
    
    if book.favorites.filter(id=user.id).exists():
        book.favorites.remove(user)
        is_favorited = False
    else:
        book.favorites.add(user)
        is_favorited = True
    
    return JsonResponse({
        'is_favorited': is_favorited,
        'favorite_count': book.favorites.count()
    })

class FavoriteBooksView(LoginRequiredMixin, generic.ListView):
    template_name = 'book/favorite_books.html'
    context_object_name = 'books'
    paginate_by = 12
    
    def get_queryset(self):
        return self.request.user.favorite_books.all().order_by('-created_at')
    

from django import forms
from .models import Shelf, Review

class ShelfForm(forms.ModelForm):
    class Meta:
        model = Shelf
        fields = ['title', 'text', 'category', 'thumbnail']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '書籍タイトルを入力してください'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '書籍の説明を入力してください'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['book', 'title', 'text', 'rate']
        widgets = {
            'book': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'レビュータイトルを入力してください'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'レビュー内容を入力してください'}),
            'rate': forms.Select(attrs={'class': 'form-select'}),
        } 
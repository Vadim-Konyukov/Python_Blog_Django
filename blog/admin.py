from django.contrib import admin
from .models import Post, Comment


@admin.register(Post)  #admin.site.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'author', 'publish', 'status']  # показывает поля модели на сайте админа
    list_filter = ['status', 'created', 'publish', 'author']  # фильтрация по полям модели
    search_fields = ['title', 'body']  # поля для поиска по модели
    prepopulated_fields = {'slug': ('title',)}  # автозаполнение поля slug при создании или редактировании нового поста
    raw_id_fields = ['author']  # виджет для отбора ассоциированных объектов для поля author модели Post
    date_hierarchy = 'publish'  # группировка по дате публикации
    ordering = ['status', 'publish']  # сортировка постов по статусу и дате публикации


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'post', 'created', 'active']  # показывает поля модели на сайте админа
    list_filter = ['active', 'created', 'updated']  # фильтрация по полям модели
    search_fields = ['name', 'email', 'body']  # поля для поиска по модели

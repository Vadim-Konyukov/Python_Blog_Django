
from django.core.mail import send_mail
from django.core.mail.backends import console
from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm, SearchForm
from .models import Post, Comment
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity




def post_list(request, tag_slug=None):
    post_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])
    # Постраничная разбивка с 3 постами на страницу
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        # Если page_number не целое число то выдать первую страницу
        posts = paginator.page(1)
    except EmptyPage:
        # Если page_number находится вне диапазона, то выдать последнюю страницу результата
        posts = paginator.page(paginator.num_pages)
    return render(request,
                 'blog/post/list.html',
                 {'posts': posts,
                  'tag': tag})


def post_detail(request, year, month, day, post):

    post = get_object_or_404(Post,
                             status=Post.Status.PUBLISHED,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)    # функция сокращенного доступа - извлекать желаемый пост
    # Список активных комментариев к этому посту
    comments = post.comments.filter(active=True)
    # Форма для добавления нового комментария
    form = CommentForm()

    # Список схожих постов
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids)\
                              .exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags'))\
                              .order_by('-same_tags', '-publish')[:4]


     # Возвращаем представление с информацией о пост
    return render(request, 'blog/post/detail.html',
                  {'post': post, 'comments': comments, 'form': form, 'similar_posts': similar_posts})

class PostListView(ListView):
    # Альтернативное представление post_list
    queryset = Post.published.all()     # model=Post
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'

def post_share(request, post_id):
    # Извлечь пост по индификатору id
    post = get_object_or_404(Post, id=post_id,
                             status=Post.Status.PUBLISHED)
    sent = False
    if request.method == 'POST':
        # форма была передана на обработку
        form = EmailPostForm(request.POST)
        if form.is_valid():     #  метод проверяет допустимостьвведеныых данных
            #  сохраняем данные формы
            cd = form.cleaned_data
            # ....  отправить электронное письмо
            post_url = request.build_absolute_url(
                post.get_absolute_url()
            )
            subject = f"{cd['name']} recommends you read" \
                      f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n"\
                      f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, console.Email.Backend,
                      [cd['to']])
            sent = True
    else:
        form = EmailPostForm() # GET запрос, когда открывает в первый раз
        return render(request,'blog/post/share.html', {'post': post, 'form': form, 'sent': sent})


@require_POST    # разрешает запрос POST только для этого представления
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    # Комментарий был отправлен
    form = CommentForm(data=request.POST)
    if form.is_valid():
        # Создать объект класса Comment, не сохраняя его в БД
        new_comment = form.save(commit=False)
        # Назначить пост комментарии
        new_comment.post = post
        # Сохранить комментарий в БД
        new_comment.save()
    return render(request, 'blog/post/comment.html',
                  {'post': post, 'form': form, 'comment': comment})


def post_search(request):
    # Поиск по тексту, заголовку с использованием Postgres'овского векторного поиска
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']

            # search_vector = SearchVector('title', weight='A') + \
            #                 SearchVector('body', weight='B', config='spanish')
            # search_query = SearchQuery(query, config='spanish')   # транслирует термины в объект поискового запроса, получая оптимальные совпадения
            # results = Post.published.annotate(
            #     search=search_vector, rank=SearchRank(search_vector,search_query)
            # ).filter(rank__gte=0.3).order_by('-rank') # упорядочивает результаты по релевантности

            # Поиск с использованием TrigramSimilarity триграммный поиск
            results = Post.published.annotate(
                similarity=TrigramSimilarity('title', query),
            ).filter(similarity__gt=0.1).order_by('-similarity')

    return render(request, 'blog/post/search.html', {'form': form, 'query': query, 'results': results})


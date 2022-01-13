from datetime import datetime
import random

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from News.forms import PostEditForm
from News.models import Post, Ad, Category, Comment

ImportantNewsCount = 3
LatestNewsCount = 10
PopularNewsCount = 10
NewsPerPage = 12
AdsCount = 3
PaginationCount = 7
NewsOrders = ['publish_date', 'accepted_comments', 'visits', 'importance']
for i in range(0, len(NewsOrders)):
    NewsOrders.append('-' + NewsOrders[i])


def DateFromStrOrDefault(string: str, date_format: str, default: datetime) -> datetime:
    try:
        return datetime.strptime(string, date_format)
    except ValueError:
        return default


def Index(request):
    important_news = Post.objects.order_by('-publish_date__day', '-importance', '-visits')[:ImportantNewsCount]
    for news in important_news:
        news.summary = news.GetSummary(75)

    most_popular_news = Post.objects.order_by('-visits') \
        .filter(publish_date__month=datetime.now().month)[0]
    most_popular_news.summary = most_popular_news.GetSummary(100)
    popular_news = Post.objects.order_by('-visits') \
                       .exclude(id__in=important_news) \
                       .exclude(id=most_popular_news.id)[:PopularNewsCount]
    for news in popular_news:
        news.summary = news.GetSummary(50)

    latest_news = Post.objects.order_by('-publish_date') \
                      .exclude(id__in=important_news) \
                      .exclude(id__in=popular_news) \
                      .exclude(id=most_popular_news.id)[:LatestNewsCount]
    for news in latest_news:
        news.summary = news.GetSummary(50)

    ads = list(Ad.objects.all()[:AdsCount])
    random.shuffle(ads)

    return render(request, 'News/index.html', context={
        'important_news': important_news,
        'latest_news': latest_news,
        'popular_news': popular_news,
        'most_popular_news': most_popular_news,
        'ads': ads,
    })


def NewsArchive(request):
    today = datetime.now()
    start_date = DateFromStrOrDefault(request.GET.get('start_date', ''), '%Y-%m-%d', datetime.min)
    end_date = DateFromStrOrDefault(request.GET.get('end_date', ''), '%Y-%m-%d', today) \
        .replace(hour=23, minute=59, second=59, microsecond=999999)

    category = request.GET.get('category', '')

    search_for = request.GET.get('search', '')

    order = request.GET.get('order', '')
    if order not in NewsOrders:
        order = '-publish_date'

    page_number = request.GET.get('page', '')

    try:
        int(page_number)
    except ValueError:
        page_number = 1

    news = Post.objects.all()
    if 'comment' in order:
        news = news.annotate(accepted_comments=Count('comments', filter=Q(comments__is_accepted=True)))
    news = news.order_by(order).filter(
        Q(publish_date__gte=start_date) &
        Q(publish_date__lte=end_date) &
        (Q(title__icontains=search_for) | Q(article__icontains=search_for))
    )

    categories = Category.objects.all()
    if category and categories.filter(url_name=category).exists():
        news = news.filter(categories__url_name=category)

    filters = ''
    if order != '-publish_date':
        filters += f"&order={order}"
    if start_date != datetime.min:
        filters += f"&start_date={start_date.strftime('%Y-%m-%d')}"
    if end_date.date() != today.date():
        filters += f"&end_date={end_date.strftime('%Y-%m-%d')}"
    if category:
        f"&category={category}"
    if search_for:
        f"&search={search_for}"

    paginator = Paginator(news, NewsPerPage)
    page = paginator.get_page(page_number)
    for post in page:
        post.summary = post.GetSummary(250)

    ads = list(Ad.objects.all()[:AdsCount])
    random.shuffle(ads)

    return render(request, 'News/news-archive.html', context={
        'page': page,
        'filters': filters.rstrip('&'),
        'categories': categories,
        'ads': ads,
    })


def FullNews(request, news_id: int):
    post = get_object_or_404(Post, id=news_id)
    post.visits += 1
    post.save()

    category: Category = post.categories.first()
    if category:
        other_posts = category.posts.order_by('-publish_date')[:10]
    else:
        other_posts = Post.objects.order_by('-publish_date')[:10]

    ads = list(Ad.objects.all()[:AdsCount])
    random.shuffle(ads)

    return render(request, 'News/full-news.html', context={
        'post': post,
        'category': category,
        'other_posts': other_posts,
        'ads': ads,
    })


def SignUp(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        email = request.POST['email']
        username = request.POST['username']
        if form.is_valid():
            form.save()
            password = form.cleaned_data['password1']
            user = authenticate(request, username=username, password=password)
            user.first_name = firstname
            user.last_name = lastname
            user.email = email
            user.save()
            login(request, user)
            return redirect('index')

        else:
            return render(request, 'News/signup.html', context={
                'firstname': firstname,
                'lastname': lastname,
                'email': email,
                'username': username,
                'error': 'ثبت نام با خطا مواجه شد. لطفا دوباره امتحان کنید.',
            })

    return render(request, 'News/signup.html')


def Login(request):
    redirect_path = request.GET.get('next')
    if not redirect_path or redirect_path == reverse('index'):
        redirect_path = 'profile'

    if request.user.is_authenticated:
        return redirect(redirect_path)

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(redirect_path)
        else:
            return render(request, 'News/login.html', context={
                'login_failed': True,
                'username': username,
            })

    return render(request, 'News/login.html')


def Logout(request):
    redirect_path = request.GET.get('next')
    if not redirect_path or redirect_path == reverse('profile'):
        redirect_path = 'index'
    if request.user.is_authenticated:
        logout(request)
    return redirect(redirect_path)


@login_required
def Profile(request):
    user = request.user
    latest_posts = user.posts.order_by('-publish_date')[:20]
    latest_comments_on_posts = \
        Comment.objects.filter(post__author_id=user.id, is_accepted=False)[:20]
    return render(request, 'News/profile.html', context={
        'user': user,
        'posts': latest_posts,
        'comments_on_posts': latest_comments_on_posts,
    })


@login_required
def NewPost(request):
    error = False
    if request.method == 'POST':
        form = PostEditForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()
            return HttpResponseRedirect(reverse('full_news', args=[post.id]))
        else:
            error = True

    form = PostEditForm()
    return render(request, 'News/post-editor.html', context={
        'form': form,
        'error': error,
    })


@login_required
def EditPost(request, news_id: int):
    error = False
    post = get_object_or_404(Post, id=news_id)
    if request.method == 'POST':
        form = PostEditForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save()
            return HttpResponseRedirect(reverse('full_news', args=[post.id]))
        else:
            error = True

    form = PostEditForm(instance=post)
    return render(request, 'News/post-editor.html', context={
        'form': form,
        'error': error,
    })


@login_required
def DeletePost(request, news_id: int):
    post = get_object_or_404(Post, id=news_id)
    post.delete()
    redirect('profile')

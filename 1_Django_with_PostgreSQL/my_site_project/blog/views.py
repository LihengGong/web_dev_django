from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from django.core.paginator import Paginator, EmptyPage,\
    PageNotAnInteger
from django.db.models import Count
from django.core.mail import send_mail
from django.contrib.postgres.search import SearchVector
from .forms import EmailPostForm, CommentForm, SearchForm
from .models import Post


# Create your views here.
def post_list(request, tag_slug=None):
    # posts = Post.published.all()
    # return render(request,
    #               'blog/post/list.html',
    #               {'posts': posts})
    object_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])

    paginator = Paginator(object_list, 3)
    print(request.GET)
    page = request.GET.get('page')
    print('post_list, page=', page)
    try:
        posts = paginator.page(page)
        print('normal, page=', page)
    except PageNotAnInteger:
        print('PageNotAnInteger: page=', page)
        posts = paginator.page(1)
    except EmptyPage:
        print('emptypage: page=', page)
        posts = paginator.page(paginator.num_pages)
    return render(request,
                  'blog/post/list.html',
                  {'page': page,
                   'posts': posts,
                   'tag': tag})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post,
                             status='published',
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)

    comments = post.comments.filter(active=True)

    new_comment = None

    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            # Foreign key
            new_comment.post = post
            new_comment.save()
    else:
        comment_form = CommentForm()

    # List of similar posts
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = post.published.filter(tags__in=post_tags_ids)\
        .exclude(id=post.id).annotate(same_tags=Count('tags'))\
        .order_by('-same_tags', '-publish')[:4]

    return render(request,
                  'blog/post/detail.html',
                  {'post': post,
                   'comments': comments,
                   'new_comment': new_comment,
                   'comment_form': comment_form,
                   'similar_posts': similar_posts})


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_share(request, post_id):
    # Retrieve post by id
    post = get_object_or_404(Post, id=post_id, status='published')
    mail_sent = False

    if request.method == 'POST':
        # Form was submitted
        print('in post_share: request.POST=', request.POST)
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # TODO send mail...
            post_url = request.build_absolute_uri(
                post.get_absolute_url())
            subject = '{}({}) recommends you reading"\
            {}"'.format(cd['name'], cd['email'], post.title)
            message = 'read'
            send_mail('test', 'test', 'liheng.gong@outlook.com', ['407137855@qq.com'])
            mail_sent = True
        else:
            print('errors are: ', form.errors)
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html',
                  {'post': post,
                   'form': form,
                   'sent': mail_sent})


def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        print(request.GET)
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            results = Post.objects.annotate(
                search=SearchVector('title', 'body'),
            ).filter(search=query)
    return render(request,
                  'blog/post/search.html',
                  {'form': form,
                   'query': query,
                   'results': results})

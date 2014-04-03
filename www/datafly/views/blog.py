import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pytz import utc
from bottle import Bottle, request, response, abort
from jinja2.filters import do_truncate
from feedgen.feed import FeedGenerator

from datafly.core import g, template
from datafly.models.page import Page

from config import Config, db

# PUBLIC

public_app = Bottle()

@public_app.get('/blog')
@public_app.get('/blog/<slug>')
@public_app.get('/blog/page/<page:int>')
@public_app.get('/blog/archive/<year:int>/<month:int>')
@public_app.get('/blog/archive/<year:int>/<month:int>/page/<page:int>')
def show_posts(page=1, slug=None, year=None, month=None):
    c = template_context = dict(
        addthis_id = public_app.config.get('addthis_id'),
        fb_id = public_app.config.get('fb_id')
    )
    page = int(page)

    query = {
        'id': { '$regex': 'blog' },
        'current': True,
        'meta.hide': { '$ne': True }
    }

    c['latest_posts'] = db.pages.find(query).sort('meta.created', -1)[0:5]

    c['query'] = search = request.query.get('q', '')
    c['author'] = author = request.query.get('author', None)

    if author:
        query['meta.author'] = author
        posts = db.pages.find(query).sort('meta.created', -1)
    elif len(search):
        # posts from search
        regex = re.compile(search, re.IGNORECASE)
        query['content'] = { '$regex': regex }
        posts = db.pages.find(query).sort('meta.created', -1)
    elif slug:
        # single post
        c['single_post'] = True
        c['slug'] = slug        
        post = Page.get_latest('blog/' + slug)
        hidden = post['meta'].get('hide', False)
        if hidden == True:
            return abort(404, "Page not found")
        c['posts'] = [post]
        c['page'] = post
    elif year and month:
        # from archive
        date_from = datetime(year, month, 1)
        c['month_link'] = '/archive/%s/%s' % (year, month)
        c['month'] = date_from.strftime('%B %Y')
        date_to = date_from + relativedelta(months=+1)
        query['meta.created'] = {
            '$gte': date_from,
            '$lt': date_to
        }
        posts = db.pages.find(query).sort('meta.created', -1)
    else:
        # list
        posts = db.pages.find(query).sort('meta.created', -1)

    if slug is None:
        # pagination
        c['current_page'] = page
        per_page = 5
        skip = (page-1) * per_page
        c['count'] = count = posts.count()
        c['posts'] = posts[skip:skip+per_page]
        c['pages'] = count // 5 + 1 if (count % 5 == 0) else count // 5 + 2

    c['home'] = Page.get_latest('home')

    return template('blog.html', **template_context)

@public_app.get('/blog/rss.xml')
def rss():    
    config = public_app.config['feed']
    fg = FeedGenerator()
    fg.id('%s/blog' % Config.BASE_URL)
    fg.title(config['title'])
    fg.author( {'name': config['author'],'email': config['email']} )
    fg.description(config['desc'])
    fg.link( href=Config.BASE_URL, rel='alternate' )
    query = {
        'id': { '$regex': 'blog' },
        'current': True,
        'meta.hide': { '$ne': True }
    }
    posts = db.pages.find(query).sort('meta.created', -1)[:20]
    for post in posts:
        fe = fg.add_entry()
        fe.title(post['meta']['title'])
        if 'author' in post['meta']:
            fe.author( {'name': post['meta']['author'],'email': config['email']} )
        else:
            fe.author( {'name': config['author'],'email': config['email']} )
        fe.description(do_truncate(post['content'], 300))
        fe.link(href="%s/%s" % (Config.BASE_URL, post['id']), rel='alternate')
        fe.pubdate(utc.localize(post['meta']['created']))
        fe.content(post['content'])    
    response.headers['Content-Type'] = 'application/rss+xml'
    return fg.rss_str(pretty=True)

# ADMIN

admin_app = Bottle()

@admin_app.get('/admin/blog')
def blog():
    posts = (
        db.pages
          .find({ 'id': { '$regex': 'blog' }, 'current': True })
          .sort('meta.created', -1)
    )
    return template('admin/blog.html', posts=posts)

@admin_app.get('/admin/blog/:page')
def edit_blog_post(page):
    return template('admin/blog-post.html',
                    editor = True,
                    page = Page.get_latest(g.page_id))
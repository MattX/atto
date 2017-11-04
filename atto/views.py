import time
import os
from flask import url_for, abort, g

from . import app
from .helpers import url_from_path, get_posts, split_categories, render_with_defaults, make_feed
from .post import Post

cfg = app.config['atto_config']


def get_post_or_404(path):
    """
    Gets a given post, renders its content into the rendered_content field, and returns it. If
    the post is not found, a 404 page is rendered (and this function does not return).
    :param path: The page of the page to open
    :return: A Post object
    """
    try:
        return Post(path)
    except FileNotFoundError:
        abort(404)


@app.route('/')
def list_articles():
    print("Loaded list articles")
    posts = get_posts(app)

    categories = dict()
    for post in posts:
        cat = post.category
        if cat not in categories:
            categories[cat] = list()
        categories[cat].append({"title": post.title,
                                "url": url_for('show_post', name=url_from_path(post.path, cfg.content_root)),
                                "date": post.date})

    if None in categories:
        categories["Uncategorized"] = categories[None]
        del categories[None]

    # Arrange categories for two-column even layout.
    cols = split_categories(categories.items(), 2)

    if cfg.main_page:
        main_post = get_post_or_404(cfg.main_page)
        title = main_post.title
        content = main_post.render(cfg.markdown_extras)
    else:
        title = ""
        content = ""

    return render_with_defaults("index.html", app, columns=cols, title=title, content=content)


@app.route('/post/<path:name>/')
def show_post(name):
    p = get_post_or_404(os.path.join(cfg.content_root, name))
    content = p.render(cfg.markdown_extras)

    return render_with_defaults("post.html", app, title=p.title, date=p.date, category=p.category,
                                content=content, meta=p.meta, toc=content.toc_html)


@app.route('/rss/')
def rss():
    if cfg.generate_feeds:
        return make_feed(app).rss_str()
    else:
        abort(404)


@app.route('/atom/')
def atom():
    if cfg.generate_feeds:
        return make_feed(app).atom_str()
    else:
        abort(404)


@app.errorhandler(404)
def page_not_found(_):
    return render_with_defaults("error.html", app, title="404", descr="The page you were looking for was not found."), 404


@app.before_request
def before_request():
    request_start_time = time.time()
    g.request_time = lambda: "{:.3f}".format(time.time() - request_start_time)

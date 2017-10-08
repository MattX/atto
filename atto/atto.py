import os
import datetime, time
from post import Post
import config
import markdown2
from feedgen.feed import FeedGenerator
from flask import Flask, render_template, url_for, abort, g

CONFIG_FILE_PATH = "config.yaml"

app = Flask(__name__)
cfg = config.read_config(CONFIG_FILE_PATH)
app.config['atto_config'] = cfg
app.config['SERVER_NAME'] = cfg['server_name']
app.cache = None


def url_from_path(path):
    """
    :param path: The path of a post. It must be a subpath of the content_root path.
    :return: The url corresponding to that post.
    """
    root = cfg['content_root']
    if not path.startswith(root):
        raise RuntimeError("Cannot make URL from path {}: not a subpath of {}.".format(path, root))

    return path.replace(root, '', 1).strip('/')


def build_post_list():
    """
    Collects all posts from the content directory.
    :return: A list of post objects containing all posts in the content directory and its
    subdirectories.
    """
    post_paths = []
    for (dirpath, _, filenames) in os.walk(cfg['content_root']):
        post_paths.extend([os.path.join(dirpath, fn) for fn in filenames])

    posts = []
    for post_path in post_paths:
        post = Post(post_path)
        posts.append(post)

    return posts


def get_posts(include_hidden=False):
    """
    Returns a list of posts, either from cache or by finding all appropriate files
    :param include_hidden: The function will include hidden posts in the returned list iff this is set to true.
    :return: A list of post objects containing all posts in the content directory and its
    subdirectories.
    """
    if cfg['cache_marker']:
        if app.cache is None or not os.path.exists(cfg['cache_marker']):
            app.logger.info("Cache marker deleted, rebuilding cache")
            posts = build_post_list()
            app.cache = posts
            with open(cfg['cache_marker'], 'w'):
                pass
        else:
            posts = app.cache
    else:
        posts = build_post_list()

    if include_hidden:
        return posts
    else:
        return [p for p in posts if not p.get_hiding()]


def render_with_defaults(template, **kwargs):
    """
    Like render_template, but will automatically add the site_name parameter to the template
    arguments.
    :param template: The remplate to render
    :param kwargs: Any other arguments to pass through to render_template
    :return: A rendered template
    """
    return render_template(template, site_name=cfg['site_name'], **kwargs)


def get_post_or_404(path):
    """
    Gets a given post, renders its content into the rendered_content field, and returns it. If
    the post is not found, a 404 page is rendered (and this function does not return).
    :param path: The page of the page to open
    :return: A Post object, including a rendered_content field.
    """
    try:
        post = Post(path)
    except FileNotFoundError:
        abort(404)

    post.rendered_content = markdown2.markdown(post.get_content(), extras=cfg['markdown_extras'])
    return post


def split_categories(categories, nb_cols):
    categories = sorted(categories, key=lambda x: len(x[1]), reverse=True)
    assigned = [list() for _ in range(nb_cols)]
    totals = [0 for _ in range(nb_cols)]

    for category in categories:
        smallest_col = min(range(nb_cols), key=lambda i: totals[i])
        assigned[smallest_col].append(category)
        totals[smallest_col] += len(category[1]) + 2 # Category title height

    # Reorder the columns by date of most recent post
    return [sorted(col, key=lambda cat: max([post['date'] for post in cat[1]]), reverse=True) for col in assigned]


@app.route('/')
def list_articles():
    print("Loaded list articles")
    posts = get_posts()

    categories = dict()
    for post in posts:
        if post.get_meta().get("Hiding", False):
            continue

        cat = post.get_category()
        if cat not in categories:
            categories[cat] = list()
        categories[cat].append({"title": post.get_title(),
                                "url": url_for('show_post', name=url_from_path(post.path)),
                                "date": post.get_date()})

    if None in categories:
        categories["Uncategorized"] = categories[None]
        del categories[None]

    # Arrange categories for two-column even layout.
    cols = split_categories(categories.items(), 2)

    if cfg["main_page"]:
        main_post = get_post_or_404(cfg["main_page"])
        title = main_post.get_title()
        content = main_post.rendered_content
    else:
        title = ""
        content = ""

    return render_with_defaults("index.html", columns=cols, title=title, content=content)


@app.route('/post/<path:name>/')
def show_post(name):
    p = get_post_or_404(os.path.join(cfg['content_root'], name))

    return render_with_defaults("post.html", title=p.get_title(), date=p.get_date(), category=p.get_category(),
                                content=p.rendered_content, meta=p.get_meta())


def make_feed():
    feed_generator = FeedGenerator()
    feed_generator.title(cfg["site_name"])
    feed_generator.link({'href': url_for('list_articles', _external=True)})
    feed_generator.id("I don't really know what Atom IDs are supposed to be.")
    feed_generator.description(" ")

    posts = get_posts()
    for post in sorted(posts, key=lambda p: p.get_date(), reverse=True)[:10]:
        feed_entry = feed_generator.add_entry()
        feed_entry.id(url_from_path(post.path))
        feed_entry.link({'href': url_for('show_post', name=url_from_path(post.path), _external=True), 'rel': "alternate"})
        feed_entry.title(post.get_title())
        # Need the date to have tzinfo and be a datetime object.
        full_date = datetime.datetime.combine(post.get_date(),
                                              datetime.time(0, 0, 0, 0).replace(tzinfo=datetime.timezone.utc))
        feed_entry.pubdate(full_date)
        feed_entry.updated(full_date)

    return feed_generator


@app.route('/rss/')
def rss():
    if cfg['generate_feeds']:
        return make_feed().rss_str()
    else:
        abort(404)


@app.route('/atom/')
def atom():
    if cfg['generate_feeds']:
        return make_feed().atom_str()
    else:
        abort(404)


@app.errorhandler(404)
def page_not_found(_):
    return render_with_defaults("error.html", title="404", descr="The page you were looking for was not found."), 404


@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: "{:.3f}".format(time.time() - g.request_start_time)

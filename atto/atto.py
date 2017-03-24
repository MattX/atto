import os
import datetime, time
import post
import config
import markdown2
from feedgen.feed import FeedGenerator
from flask import Flask, render_template, url_for, abort, g

CONFIG_FILE_PATH = "config.yaml"


app = Flask(__name__)
cfg = config.read_config(CONFIG_FILE_PATH)
app.config['atto_config'] = cfg
app.config['SERVER_NAME'] = cfg['server_name']


def url_from_path(path):
    """
    :param path: The path of a post. It must be a subpath of the content_root path.
    :return: The url corresponding to that post.
    """
    root = cfg['content_root']
    if not os.path.commonpath([root, path]):
        raise RuntimeError("Cannot make URL from path {}: not a subpath of {}.".format(path, root))

    return path.replace(root, '', 1).strip('/')


def get_posts(include_hidden=False):
    post_paths = []
    for (dirpath, _, filenames) in os.walk(cfg['content_root']):
        post_paths.extend([os.path.join(dirpath, fn) for fn in filenames])

    posts = []
    for pp in post_paths:
        p = post.Post(pp)
        if include_hidden or not p.get_meta().get("Hiding", False):
            posts.append(p)

    return posts


def render_with_defaults(template, **kwargs):
    return render_template(template, site_name=cfg['site_name'], **kwargs)


@app.route('/')
def list_articles():
    posts = get_posts()

    categories = dict()
    for p in posts:
        if p.get_meta().get("Hiding", False):
            continue

        cat = p.get_category()
        if cat not in categories:
            categories[cat] = list()
        categories[cat].append({"title": p.get_title(),
                                "url": url_for('show_post', name=url_from_path(p.path)),
                                "date": p.get_date()})

    if None in categories:
        categories["Uncategorized"] = categories[None]
        del categories[None]

    categories = sorted(categories.items())

    return render_with_defaults("index.html", categories=categories)


@app.route('/post/<path:name>/')
def show_post(name):
    try:
        p = post.Post(os.path.join(cfg['content_root'], name))
    except FileNotFoundError as e:
        abort(404)
    rendered_content = markdown2.markdown(p.get_content(), extras=cfg['markdown_extras'])
    return render_with_defaults("post.html", title=p.get_title(), date=p.get_date(), category=p.get_category(),
                                content=rendered_content, meta=p.get_meta())


def make_feed():
    fg = FeedGenerator()
    fg.title(cfg["site_name"])
    fg.link({'href': url_for('list_articles', _external=True)})
    fg.id("I don't really know what Atom IDs are supposed to be.")
    fg.description(" ")

    posts = get_posts()
    for p in sorted(posts, key=lambda p: p.get_date(), reverse=True)[:10]:
        fe = fg.add_entry()
        fe.id(url_from_path(p.path))
        fe.link({'href': url_for('show_post', name=url_from_path(p.path), _external=True), 'rel': "alternate"})
        fe.title(p.get_title())
        # Need the date to have tzinfo and be a datetime object.
        full_date = datetime.datetime.combine(p.get_date(), datetime.time(0, 0, 0, 0).replace(tzinfo=datetime.timezone.utc))
        fe.pubdate(full_date)
        fe.updated(full_date)

    return fg


@app.route('/rss/')
def rss():
    return make_feed().rss_str()


@app.route('/atom/')
def atom():
    return make_feed().atom_str()


with app.app_context():
    url_for('static', filename='style.css')
    url_for('static', filename='favicon.ico')


@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: "%.5fs" % (time.time() - g.request_start_time)

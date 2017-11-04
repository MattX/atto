import os
from flask import render_template, url_for
from feedgen.feed import FeedGenerator
import datetime

from .post import Post


def url_from_path(path, content_root):
    """
    :param path: The path of a post. It must be a subpath of the content_root path.
    :return: The url corresponding to that post.
    """
    if not path.startswith(content_root):
        raise RuntimeError("Cannot make URL from path {}: not a subpath of {}.".format(path, content_root))

    return path.replace(content_root, '', 1).strip('/')


def build_post_list(content_root):
    """
    Collects all posts from the content directory.
    :return: A list of post objects containing all posts in the content directory and its
    subdirectories.
    """
    post_paths = []
    for (dirpath, _, filenames) in os.walk(content_root):
        post_paths.extend([os.path.join(dirpath, fn) for fn in filenames])

    posts = []
    for post_path in post_paths:
        post = Post(post_path)
        posts.append(post)

    return posts


def get_posts(app, include_hidden=False):
    """
    Returns a list of posts, either from cache or by finding all appropriate files
    :param include_hidden: The function will include hidden posts in the returned list iff this is set to true.
    :return: A list of post objects containing all posts in the content directory and its
    subdirectories.
    """
    cache_marker = app.config['atto_config'].cache_marker
    if cache_marker:
        if app.cache is None or not os.path.exists(cache_marker):
            app.logger.info("Cache marker deleted, rebuilding cache")
            posts = build_post_list(app.config['atto_config'].content_root)
            app.cache = posts
            with open(cache_marker, 'w'):
                pass
        else:
            posts = app.cache
    else:
        posts = build_post_list(app.config['atto_config'].content_root)

    if include_hidden:
        return posts
    else:
        return [p for p in posts if not p.hiding]


def render_with_defaults(template, app, **kwargs):
    """
    Like render_template, but will automatically add the site_name parameter to the template
    arguments.
    :param template: The remplate to render
    :param kwargs: Any other arguments to pass through to render_template
    :return: A rendered template
    """
    return render_template(template, site_name=app.config['atto_config'].site_name, **kwargs)


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


def make_feed(app):
    cfg = app.config['atto_config']

    feed_generator = FeedGenerator()
    feed_generator.title(cfg.site_name)
    feed_generator.link({'href': url_for('list_articles', _external=True)})
    feed_generator.id("I don't really know what Atom IDs are supposed to be.")
    feed_generator.description(" ")

    posts = get_posts(app)
    for post in sorted(posts, key=lambda p: p.get_date(), reverse=True)[:10]:
        feed_entry = feed_generator.add_entry()
        feed_entry.id(url_from_path(post.path, cfg.content_root))
        feed_entry.link({'href': url_for('show_post', name=url_from_path(post.path, cfg.content_root),
                                         _external=True),
                         'rel': "alternate"})
        feed_entry.title(post.get_title())
        # Need the date to have tzinfo and be a datetime object.
        full_date = datetime.datetime.combine(post.get_date(),
                                              datetime.time(0, 0, 0, 0).replace(tzinfo=datetime.timezone.utc))
        feed_entry.pubdate(full_date)
        feed_entry.updated(full_date)

    return feed_generator

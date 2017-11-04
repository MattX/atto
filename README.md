# Atto

A simple file-based CMS inspired by [Pico](http://picocms.org/).

## Usage

### Installation

Atto runs on Python 3.4+ and has a few dependencies, notably
[Flask](http://flask.pocoo.org/).

Run `pip install -r requirements.txt` to install everything you need.
You can the run Atto locally with `FLASK_APP=atto/atto.py flask run`,
or have a look at the [Flask manual](http://flask.pocoo.org/docs/0.12/deploying/)
for deployment options.

### Writing pages

Atto expects pages in Markdown format, with an optional YAML formatted
header.

The header can be delimited in two ways:

```
---
<header contents>
---
```

or

```
<!---
<header contents>
-->
```

The second method is recommended since it plays nicer with Markdown
editors. The first method is supported mainly for compatibility with
Pico. The delimiters (`---`, `<!---` and `-->`) must be alone on their
line, and the Atto parser is fairly butthurt about this.

Field names in the header are case-insensitive.

The `title`, `date`, `category`, `hiding` and `markdown_extras` fields
are natively supported. `hiding` is a boolean value that decides whether
the article should appear in the homepage and feed listings. The post
will still be accessible at its full URL. `markdown_extras` determines
which extra options to use with [markdown2](https://github.com/trentm/python-markdown2).

These options have the following defaults:

  * `title`: file name without the extension,
  * `date`: file creation time,
  * `category`: None (uncategorized)
  * `hiding`: false.
  * `markdown_extras`: `[]`

All other header flags will be passed to the page template as the
dictionary `meta`. For instance, the default template will print the
content of the `notes` header in the sidebar, if it is present.

### Configuration

There are several ways to extend Atto. The configuration file (`config.yaml`) supports the following options:

  * `content_root` (required): a path where the pages live. Atto will ignore directory structure in this path and recursively scan it for articles.
  * `site_name` (required): the name of the website.
  * `server_name` (required): the name of the server the app is running on.
  * `markdown_extras` (optional): a list of extra options to give to [markdown2](https://github.com/trentm/python-markdown2) when rendering a page.
  * `main_page` (optional): if set, Atto will render this file before the article listing on the main page.
  * `cache_marker` (optional): if set, Atto will keep an in-memory cache of the list of articles, and rebuild it every time the specified file is deleted (see the Performance section below).
  * `generate_feeds` (optional, defaults to false): if true, RSS and Atom feed of the latest posts will be accessible at `/rss/` and `/atom/`, respectively.

You should also probably adapt templates and CSS files the way you want.

## Performance

Because it's file-based, <small>and because the YAML library is slow,</small> Atto doesn't scale very well for any operation
that requires listing all posts. For now, that's just generating the
index pages and feeds. According to my tests, it takes ~1s to generate
a list of 1000 posts on a reasonably fast laptop with an SSD.

If the `cache_marker` option is set to a (possibly nonexistent) file path,
Atto will keep an in-memory cache of the post headers and recreate it
everytime it detects the file has been deleted. It will touch the file
again when the index has been recreated. This considerably speeds up
index generation, and Atto can still be easily controlled through a
simple FTP or SFTP connection.

## Issues and pull requests

Issues and pull requests are happily accepted :)

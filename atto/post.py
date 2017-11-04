import markdown2
import os
import yaml
import datetime

# Open and close headers must match in these lists.
HEADER_OPEN = ["<!---\n", "---\n"]
HEADER_CLOSE = ["-->\n", "---\n"]


def get_and_remove_or_default(dict, key, default):
    """
    Get an item from a dictionary, then deletes the item from the dictionary.
    If the item is not found, return a default value.
    :return: The value corresponding to the key in the dictionary, or the default value if it wasn't found.
    """
    if key in dict:
        ret = dict[key]
        del dict[key]
        return ret
    else:
        return default


def get_header_kind(header_opener):
    """
    Returns the type of header closing tag to expect, based on the opening tag.
    :return: The index of the header type in the HEADER_OPEN and HEADER_CLOSE lists.
    """
    try:
        return HEADER_OPEN.index(header_opener)
    except ValueError:
        return -1


class Post:
    """
    Class to read posts and their metadata
    :param path: The path of a post or page
    :param header: If passed, must be a dictionary that will be used to prefill header info.
    It must have the following fields: has_header, title, date, category, hiding, meta.
    """
    def __init__(self, path, header=None):
        if not os.path.isfile(path):
            raise FileNotFoundError("Could not find post at path {}".format(path))

        self.path = path

        if header:
            self.read_header = True
            self.has_header = header['has_header']
            self._title = header['title']
            self._date = header['date']
            self._category = header['category']
            self._hiding = header['hiding']
            self._meta = header['meta']
        else:
            self.read_header = False
            self.has_header = None
            self._title = None
            self._date = None
            self._category = None
            self._hiding = None
            self._meta = None

        self.read_content = False
        self._content = None

    def header_dict(self):
        """
        :return: a header dictionary that can be read by __init__.
        """
        self.ensure_header()
        return {'has_header': self.has_header, 'title': self._title, 'date': self._date, 'category': self._category,
                'hiding': self._hiding, 'meta': self._meta}

    def _read_header(self):
        with open(self.path) as post_file:
            first_line = post_file.readline()
            kind = get_header_kind(first_line)

            if kind < 0:
                # No header was found
                self.has_header = False
                header_text = ""

            else:
                self.has_header = True
                lines = []
                for line in post_file:
                    if line == HEADER_CLOSE[kind]:
                        break
                    lines.append(line)
                header_text = "".join(lines)

        header_dict = yaml.load(header_text) or dict()
        lowercase_header = {k.lower(): v for (k, v) in header_dict.items()}

        self._title = get_and_remove_or_default(lowercase_header, "title",
                                                os.path.splitext(os.path.basename(self.path))[0].capitalize())

        self._date = get_and_remove_or_default(lowercase_header, "date",
                                               datetime.datetime.fromtimestamp(os.path.getctime(self.path)).date())

        self._category = get_and_remove_or_default(lowercase_header, "category", None)

        self._hiding = get_and_remove_or_default(lowercase_header, "hiding", False)

        self._meta = lowercase_header

        self.read_header = True

    def _ensure_header(self):
        """
        Populates the header field. Calls __read_header, which will only read the header.
        """
        if not self.read_header:
            self._read_header()

    def _read_content(self):
        self._ensure_header()
        with open(self.path) as post_file:
            content = post_file.readlines()

        if self.has_header:
            # 1st line is guaranteed to be a header separator, find second and remove anything before that.
            header_type = get_header_kind(content[0])
            header_end = content.index(HEADER_CLOSE[header_type], 1)
            content = content[header_end+1:]

        self._content = "".join(content)
        self.read_content = True

    def _ensure_content(self):
        """
        Populates the content field
        """
        if not self.read_content:
            self._read_content()

    def render(self, markdown_extras):
        """
        Renders the post

        TODO: When using TOCs, generated IDs can collide with

        :param markdown_extras: Markdown extensions to use when rendering the post.
        :return: A string representing the rendered post.
        """
        extras = {e: None for e in markdown_extras + self.meta.get("markdown_extras", [])}
        if "toc" in extras:
            extras["header-ids"] = "_post_"
        return markdown2.markdown(self.content, extras=extras)

    @property
    def title(self):
        self._ensure_header()
        return self._title

    @property
    def date(self):
        self._ensure_header()
        return self._date

    @property
    def category(self):
        self._ensure_header()
        return self._category

    @property
    def hiding(self):
        self._ensure_header()
        return self._hiding

    @property
    def meta(self):
        self._ensure_header()
        return self._meta

    @property
    def content(self):
        self._ensure_content()
        return self._content

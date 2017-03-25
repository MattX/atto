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
            self.title = header['title']
            self.date = header['date']
            self.category = header['category']
            self.hiding = header['hiding']
            self.meta = header['meta']
        else:
            self.read_header = False
            self.has_header = None
            self.title = None
            self.date = None
            self.category = None
            self.hiding = None
            self.meta = None

        self.read_content = False
        self.content = None

    def header_dict(self):
        """
        :return: a header dictionary that can be read by __init__.
        """
        self.ensure_header()
        return {'has_header': self.has_header, 'title': self.title, 'date': self.date, 'category': self.category,
                'hiding': self.hiding, 'meta': self.meta}

    def __read_header(self):
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

        header_dict = yaml.load(header_text)
        if not header_dict:
            self.meta = dict()
        else:
            self.meta = header_dict

        self.title = get_and_remove_or_default(self.meta, "Title",
                                               os.path.splitext(os.path.basename(self.path))[0].capitalize())

        self.date = get_and_remove_or_default(self.meta, "Date",
                                              datetime.datetime.fromtimestamp(os.path.getctime(self.path)).date())

        self.category = get_and_remove_or_default(self.meta, "Category", None)

        self.hiding = get_and_remove_or_default(self.meta, "Hiding", False)

        self.read_header = True

    def ensure_header(self):
        """
        Populates the header field. Calls __read_header, which will only read the header.
        """
        if not self.read_header:
            self.__read_header()

    def __read_content(self):
        self.ensure_header()
        with open(self.path) as post_file:
            content = post_file.readlines()

        if self.has_header:
            # 1st line is guaranteed to be a header separator, find second and remove anything
            # before that.
            header_type = get_header_kind(content[0])
            header_end = content.index(HEADER_CLOSE[header_type], 1)
            content = content[header_end+1:]

        self.content = "".join(content)
        self.read_content = True

    def ensure_content(self):
        """
        Populates the content field
        """
        if not self.read_content:
            self.__read_content()

    def get_title(self):
        self.ensure_header()
        return self.title

    def get_date(self):
        self.ensure_header()
        return self.date

    def get_category(self):
        self.ensure_header()
        return self.category

    def get_hiding(self):
        self.ensure_header()
        return self.hiding

    def get_meta(self):
        self.ensure_header()
        return self.meta

    def get_content(self):
        self.ensure_content()
        return self.content

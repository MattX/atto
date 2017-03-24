import os
import yaml
import datetime

HEADER_SEP = "---\n"

# TODO: support HTML <!---  ...  --> headers


def get_and_remove_or_default(dict, key, default):
    if key in dict:
        ret = dict[key]
        del dict[key]
        return ret
    else:
        return default


class Post:
    """
    Class to read posts and their metadata
    """
    def __init__(self, path):
        if not os.path.isfile(path):
            raise FileNotFoundError("Could not find post at path {}".format(path))

        self.path = path

        self.read_header = False
        self.has_header = None
        self.title = None
        self.date = None
        self.category = None
        self.meta = None

        self.read_content = False
        self.content = None

    def __read_header(self):
        with open(self.path) as post_file:
            if post_file.readline() != HEADER_SEP:
                print("No header found for post at {}".format(self.path))
                self.has_header = False
                header_text = ""

            else:
                lines = []
                for line in post_file:
                    if line == HEADER_SEP:
                        break
                    lines.append(line)
                header_text = "".join(lines)

        header_dict = yaml.load(header_text)
        if not header_dict:
            self.meta = dict()
        else:
            self.meta = header_dict

        self.title = get_and_remove_or_default(self.meta, "Title", os.path.basename(self.path))

        self.date = get_and_remove_or_default(self.meta, "Date", datetime.date.today())

        self.category = get_and_remove_or_default(self.meta, "Category", None)

        self.has_header = True
        self.read_header = True

    def ensure_header(self):
        if not self.read_header:
            self.__read_header()

    def __read_content(self):
        self.ensure_header()
        with open(self.path) as post_file:
            content = post_file.readlines()

        if self.has_header:
            # 1st line is guaranteed to be a header separator, find second and remove anything
            # before that.
            header_end = content.index(HEADER_SEP, 1)
            content = content[header_end+1:]

        self.content = "".join(content)
        self.read_content = True

    def ensure_content(self):
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

    def get_meta(self):
        self.ensure_header()
        return self.meta

    def get_content(self):
        self.ensure_content()
        return self.content

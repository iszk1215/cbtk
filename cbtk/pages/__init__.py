import datetime
import os
import shutil


class PageMaker:

    def __init__(self, path, env, output_dir):
        self.path = path
        self.env = env
        self.base_dir = os.path.join(output_dir, path)
        os.makedirs(self.base_dir, exist_ok=True)

    def get_template(self, name):
        return self.env.get_template(name)

    def copy_file(self, config, src_file, dest_file=None):
        src = os.path.join(config.resource_dir, src_file)
        dst = os.path.join(self.base_dir, dest_file or src_file)
        shutil.copy(src, dst)

    def render_page(self, config, **kwargs):
        extras = {"base_url": config.base_url}
        if "generated_at" not in kwargs:
            extras["generated_at"] = datetime.datetime.now().strftime("%c")

        template = self.get_template("index.html")
        return template.render(**kwargs, **extras)

    def write(self, filename, contents):
        path = os.path.join(self.base_dir, filename)
        with open(path, "w") as f:
            f.write(contents)


def make_home_page(path, env, output_dir, configs, records):
    from cbtk.pages.home import make_page
    make_page(PageMaker(path, env, output_dir), configs, records)


def make_timeline_page(path, env, output_dir, configs, records):
    from cbtk.pages.timeline import make_page
    make_page(PageMaker(path, env, output_dir), configs, records)


def make_runners_page(path, env, output_dir, configs, records):
    from cbtk.pages.runners import make_page
    make_page(PageMaker(path, env, output_dir), configs, records)

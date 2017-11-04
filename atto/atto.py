from . import app

from .config import Parameter, Config


CONFIG_FILE_PATH = "config.yaml"


cfg = Config([Parameter('content_root', False, None),
              Parameter('site_name', False, None),
              Parameter('server_name', False, None),
              Parameter('markdown_extras', True, []),
              Parameter('main_page', True, None),
              Parameter('cache_marker', True, None),
              Parameter('generate_feeds', True, False)],
             CONFIG_FILE_PATH)
app.config['atto_config'] = cfg
app.config['SERVER_NAME'] = cfg.server_name
app.cache = None

from . import views

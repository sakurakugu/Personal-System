"""数据库模型注册入口。"""

from app.modules.announcements import models as announcements_models  # noqa: F401
from app.modules.articles import models as articles_models  # noqa: F401
from app.modules.bills import models as bills_models  # noqa: F401
from app.modules.collections import models as collections_models  # noqa: F401
from app.modules.feed import models as feed_models  # noqa: F401
from app.modules.files import models as files_models  # noqa: F401
from app.modules.friend_links import models as friend_links_models  # noqa: F401
from app.modules.moments import models as moments_models  # noqa: F401
from app.modules.stats import models as stats_models  # noqa: F401
from app.modules.system import models as system_models  # noqa: F401
from app.modules.todos import models as todos_models  # noqa: F401
from app.modules.users import models as users_models  # noqa: F401

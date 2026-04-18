"""友链管理权限测试。"""

from __future__ import annotations

import unittest

from fastapi.routing import APIRoute

from app.shared.auth.deps import require_admin, require_super_admin
from app.shared.db.session import get_db
from app.modules.friend_links.api import router


def build_route_map() -> dict[tuple[str, str], APIRoute]:
    """构造友链路由映射。"""
    route_map: dict[tuple[str, str], APIRoute] = {}
    for route in router.routes:
        if not isinstance(route, APIRoute):
            continue
        method = next(iter(route.methods or set()), "")
        route_map[(method, route.path)] = route
    return route_map


class FriendLinkPermissionsTest(unittest.TestCase):
    """友链管理权限断言。"""

    def test_管理接口仅允许超级管理员(self) -> None:
        route_map = build_route_map()
        protected_routes = {
            ("GET", "/friend-links"),
            ("GET", "/friend-links/categories"),
            ("GET", "/friend-links/{friend_link_id}"),
            ("POST", "/friend-links"),
            ("PATCH", "/friend-links/{friend_link_id}"),
            ("DELETE", "/friend-links/{friend_link_id}"),
            ("POST", "/friend-links/{friend_link_id}/approve"),
            ("POST", "/friend-links/{friend_link_id}/reject"),
        }

        for key in protected_routes:
            route = route_map[key]
            dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
            self.assertIn(require_super_admin, dependency_calls)
            self.assertNotIn(require_admin, dependency_calls)
            self.assertIn(get_db, dependency_calls)

    def test_公开接口不要求超级管理员(self) -> None:
        route_map = build_route_map()
        public_routes = {
            ("GET", "/friend-links/public"),
            ("POST", "/friend-links/exchange"),
        }

        for key in public_routes:
            route = route_map[key]
            dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
            self.assertNotIn(require_super_admin, dependency_calls)


if __name__ == "__main__":
    unittest.main()

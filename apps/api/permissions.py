import os

from rest_framework.permissions import BasePermission


class HasValidClientKey(BasePermission):
    message = "Invalid X-CLIENT-KEY header."

    def has_permission(self, request, view):
        expected = os.getenv("CLIENT_API_KEY", "")
        if not expected:
            return True
        return request.headers.get("X-CLIENT-KEY") == expected

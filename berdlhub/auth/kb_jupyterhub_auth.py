import logging
import os
from datetime import datetime, timezone
from urllib.parse import quote

from jupyterhub.auth import Authenticator
from jupyterhub.handlers import BaseHandler
from traitlets import List
from tornado import web

from berdlhub.auth.kb_auth import (
    KBaseAuth,
    MissingTokenError,
    InvalidTokenError,
    MissingAccessRoleError,
    AdminPermission,
)

logger = logging.getLogger(__name__)


def kbase_origin():
    """Get the KBase origin from environment variable."""
    return os.environ.get("KBASE_ORIGIN", "narrative.kbase.us")


class KBaseAuthenticator(Authenticator):
    """
    Custom JupyterHub Authenticator for KBase.
    Authenticates users by verifying the 'kbase_session' cookie
    against the KBase Auth2 API.

    This requires `c.Authenticator.enable_auth_state` to be set to True in JupyterHub config.
    This also requires JUPYTERHUB_CRYPT_KEY to be set in the environment.
    """

    SESSION_COOKIE_NAME = "kbase_session"
    SESSION_COOKIE_BACKUP = "kbase_session_backup"

    kbase_auth_url = os.environ["KBASE_AUTH_URL"]

    auth_full_admin_roles = List(
        default_value=[role.strip() for role in os.getenv("AUTH_FULL_ADMIN_ROLES", "").split(",") if role.strip()],
        config=True,
        help="Comma-separated list of KBase roles with full administrative access to JupyterHub.",
    )

    approved_roles = List(
        default_value=[role.strip() for role in os.getenv("APPROVED_ROLES", "").split(",") if role.strip()],
        config=True,
        help="Comma-separated list of KBase roles approved to login to JupyterHub.",
    )

    async def authenticate(self, handler, data=None) -> dict:
        """
        Authenticate user using KBase session cookie and API validation

        """
        session_token = handler.get_cookie(self.SESSION_COOKIE_NAME)

        if not session_token:
            session_token = handler.get_cookie(self.SESSION_COOKIE_BACKUP)

        if not session_token:
            raise MissingTokenError(
                f"Authentication required - missing {self.SESSION_COOKIE_NAME} and {self.SESSION_COOKIE_BACKUP} cookie."
            )

        kb_auth = KBaseAuth(self.kbase_auth_url, self.auth_full_admin_roles, self.approved_roles)

        try:
            kb_user = await kb_auth.validate_token(session_token)
        except MissingAccessRoleError as e:
            logger.warning(f"User {e.username} missing required access role")
            redirect_url = f"/access-request?username={quote(e.username)}"
            handler.redirect(redirect_url)
            return None

        # Validate MFA requirement - only allow Used status
        if kb_user.mfa_status != "Used":
            logger.warning(f"User {kb_user.user} denied access due to MFA status: {kb_user.mfa_status}")
            # Redirect to MFA requirement page
            mfa_status = kb_user.mfa_status or "Unknown"
            redirect_url = f"/mfa-required?mfa_status={mfa_status}"
            handler.redirect(redirect_url)
            return None

        logger.info(f"Authenticated user: {kb_user.user} with MFA status: {kb_user.mfa_status}")
        return {
            "name": str(kb_user.user),
            "admin": kb_user.admin_perm == AdminPermission.FULL,
            "auth_state": {
                "kbase_token": session_token,
                "token_expires": kb_user.expires.isoformat() if kb_user.expires else None,
                "mfa_status": kb_user.mfa_status,
            },
        }

    async def pre_spawn_start(self, user, spawner) -> None:
        """
        Pass KBase authentication token to spawner environment
        """
        auth_state = await user.get_auth_state() or {}
        kbase_auth_token = auth_state.get("kbase_token")

        if not kbase_auth_token:
            raise MissingTokenError("Missing KBase authentication token in auth state")

        spawner.environment["KBASE_AUTH_TOKEN"] = kbase_auth_token

    async def refresh_user(self, user, handler, **kwargs):
        """
        Refresh user authentication by validating token against KBase auth2/token endpoint.
        This is called periodically to ensure tokens are still valid.
        """
        auth_state = await user.get_auth_state() or {}
        kbase_token = auth_state.get("kbase_token")

        if not kbase_token:
            logger.warning(f"No token found for user {user.name} during refresh")
            return False

        try:
            kb_auth = KBaseAuth(self.kbase_auth_url, self.auth_full_admin_roles, self.approved_roles)
            kb_user = await kb_auth.validate_token(kbase_token)

            # Check MFA status - if not Used, invalidate the session
            if kb_user.mfa_status != "Used":
                logger.warning(f"Token refresh failed for user {user.name}: MFA status is {kb_user.mfa_status}")
                return False

            # Update auth_state with fresh token information
            auth_state.update(
                {
                    "kbase_token": kbase_token,
                    "token_expires": kb_user.expires.isoformat() if kb_user.expires else None,
                    "mfa_status": kb_user.mfa_status,
                }
            )

            user.db.auth_state = auth_state
            self.db.commit()

            logger.info(f"Successfully refreshed token for user {user.name} with MFA status: {kb_user.mfa_status}")
            return True

        except (InvalidTokenError, MissingTokenError) as e:
            logger.warning(f"Token validation failed for user {user.name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during token refresh for user {user.name}: {e}")
            return False


class TokenRefreshHandler(BaseHandler):
    """
    API endpoint to force refresh of current user's token validation.
    """

    @web.authenticated
    async def post(self):
        """
        Force refresh of current user's token by re-validating against KBase.
        """
        try:
            user = self.current_user
            authenticator = self.authenticator

            # Use the authenticator's refresh_user method
            success = await authenticator.refresh_user(user, self)

            if success:
                # Get updated auth state
                auth_state = await user.get_auth_state() or {}
                expires_str = auth_state.get("token_expires")

                expires_in_seconds = None
                if expires_str:
                    expires = datetime.fromisoformat(expires_str)
                    now = datetime.now(timezone.utc)
                    expires_in_seconds = max(0, int((expires - now).total_seconds()))

                self.write(
                    {
                        "success": True,
                        "message": "Token refreshed successfully",
                        "expires": expires_str,
                        "expires_in_seconds": expires_in_seconds,
                    }
                )
            else:
                self.write({"success": False, "error": "Token refresh failed - please log in again"})

        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            raise web.HTTPError(500, "Internal server error refreshing token")


class MfaRequiredHandler(BaseHandler):
    """
    Handler for MFA requirement page.
    """

    async def get(self):
        """
        Display MFA requirement page.
        """
        mfa_status = self.get_argument("mfa_status", "Unknown")

        html = await self.render_template(
            "mfa-required.html", mfa_status=mfa_status, kbase_origin=f"https://{kbase_origin()}"
        )
        self.finish(html)


class AccessRequestHandler(BaseHandler):
    """
    Handler for access request page when user lacks required role.
    """

    async def get(self):
        """
        Display access request form.
        """
        username = self.get_argument("username", "Unknown")

        html = await self.render_template(
            "access-request.html",
            username=username,
            kbase_origin=kbase_origin(),
            xsrf_token=self.xsrf_token.decode("utf-8") if isinstance(self.xsrf_token, bytes) else self.xsrf_token,
        )
        self.finish(html)

    async def post(self):
        """
        Process access request form submission.
        """
        from berdl_notebook_utils.access_requests import request_berdl_access

        username = self.get_body_argument("username", "Unknown")
        institution = self.get_body_argument("institution", "")
        reason = self.get_body_argument("reason", "")

        logger.info(f"Access request from user={username}, institution={institution}, reason={reason}")

        try:
            result = request_berdl_access(
                username=username,
                institution=institution,
                reason=reason,
            )
            logger.info(f"Access request submitted: {result}")
        except Exception as e:
            logger.error(f"Failed to submit access request: {e}")
            # Still show success page to user - request was logged

        html = await self.render_template(
            "access-request-submitted.html",
            kbase_origin=kbase_origin(),
        )
        self.finish(html)


class AdminAccessRequestsHandler(BaseHandler):
    """
    Admin page to view access requests.
    """

    @web.authenticated
    async def get(self):
        """
        Display list of access requests (admin only).
        """
        user = self.current_user
        if not user.admin:
            raise web.HTTPError(403, "Admin access required")

        from berdl_notebook_utils.access_requests import list_access_requests

        requests = []
        error = None

        try:
            requests = list_access_requests()
        except Exception as e:
            logger.error(f"Failed to fetch access requests: {e}")
            error = str(e)

        html = await self.render_template(
            "admin-access-requests.html",
            requests=requests,
            error=error,
        )
        self.finish(html)

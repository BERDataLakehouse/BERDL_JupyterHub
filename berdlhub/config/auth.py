"""Authentication configuration."""

from berdlhub.auth.kb_jupyterhub_auth import (
    KBaseAuthenticator,
    TokenRefreshHandler,
    MfaRequiredHandler,
    AccessRequestHandler,
    AdminAccessRequestsHandler,
)


def configure_auth(c):
    """Configure JupyterHub authentication."""

    c.JupyterHub.authenticator_class = KBaseAuthenticator
    c.Authenticator.enable_auth_state = True

    # Token refresh configuration for KBase authentication
    # This controls how often JupyterHub calls the authenticator's refresh_user() method
    # to validate tokens against the KBase auth2/token endpoint.
    # Set to 120 seconds (2 minutes) to provide timely detection of token expiration
    # while balancing API call frequency to the KBase auth service.
    # ref: https://jupyterhub.readthedocs.io/en/stable/reference/config-reference.html#Authenticator.auth_refresh_age
    c.Authenticator.auth_refresh_age = 120

    # Add custom API handlers for token monitoring, MFA requirement, and access requests
    c.JupyterHub.extra_handlers = [
        (r"/api/refresh-token", TokenRefreshHandler),
        (r"/mfa-required", MfaRequiredHandler),
        (r"/access-request", AccessRequestHandler),
        (r"/admin/access-requests", AdminAccessRequestsHandler),
    ]

    # TODO: Consider adding user allowlist for production
    c.Authenticator.allow_all = True

    # Could add admin users
    # c.Authenticator.admin_users = {'admin', 'joe'}

    # Could add allowed users/groups
    # c.Authenticator.allowed_users = set()
    # c.Authenticator.allowed_groups = {'data-scientists', 'researchers'}

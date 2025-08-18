"""Authentication configuration."""

from berdlhub.auth.kb_jupyterhub_auth import KBaseAuthenticator


def configure_auth(c):
    """Configure JupyterHub authentication."""

    c.JupyterHub.authenticator_class = KBaseAuthenticator
    c.Authenticator.enable_auth_state = True

    # TODO: Consider adding user allowlist for production
    c.Authenticator.allow_all = True

    # Could add admin users
    # c.Authenticator.admin_users = {'admin', 'joe'}

    # Could add allowed users/groups
    # c.Authenticator.allowed_users = set()
    # c.Authenticator.allowed_groups = {'data-scientists', 'researchers'}

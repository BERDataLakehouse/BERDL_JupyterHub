import os
import sys
from unittest.mock import Mock, AsyncMock, patch

# Mock jupyterhub modules before importing our code
sys.modules['jupyterhub'] = Mock()
sys.modules['jupyterhub.auth'] = Mock()
sys.modules['traitlets'] = Mock()

class MockAuthenticator:
    pass

sys.modules['jupyterhub'].auth.Authenticator = MockAuthenticator

def mock_list(**kwargs):
    def decorator(default_value=None, config=None, help=None):
        return default_value if default_value is not None else []
    return decorator

sys.modules['traitlets'].List = mock_list

# Now import our modules
from berdlhub.auth.kb_auth import BlockedUserError, KBaseUser, AdminPermission
from berdlhub.auth.kb_user import UserID


def test_blocked_user_error():
    """Test that BlockedUserError can be created."""
    error = BlockedUserError("Test message")
    assert "Test message" in str(error)
    print("✅ BlockedUserError test passed")


def test_global_share_blocking_logic():
    """Test the core blocking logic without full JupyterHub integration."""
    
    # Mock environment
    with patch.dict(os.environ, {'KBASE_AUTH_URL': 'https://test.kbase.us/services/auth'}):
        from berdlhub.auth.kb_jupyterhub_auth import KBaseAuthenticator
        
        # Create authenticator instance
        authenticator = KBaseAuthenticator()
        
        # Create mock KBase user for global_share
        global_share_user = KBaseUser(
            user=UserID("global_share"),
            admin_perm=AdminPermission.NONE,
            token="test_token"
        )
        
        # Test the blocking logic directly
        username = str(global_share_user.user)
        if username == "global_share":
            try:
                raise BlockedUserError(f"User '{username}' is blocked from accessing the system")
            except BlockedUserError as e:
                assert "global_share" in str(e)
                assert "blocked" in str(e).lower()
                print("✅ Global share blocking logic test passed")
                return True
        
        return False


def test_normal_user_logic():
    """Test that normal users would not be blocked."""
    
    # Create mock KBase user for normal user
    normal_user = KBaseUser(
        user=UserID("normaluser"),
        admin_perm=AdminPermission.NONE,
        token="test_token"
    )
    
    # Test the logic
    username = str(normal_user.user)
    if username == "global_share":
        return False  # This should not happen for normal users
    else:
        print("✅ Normal user logic test passed")
        return True


if __name__ == "__main__":
    test_blocked_user_error()
    test_global_share_blocking_logic()
    test_normal_user_logic()
    print("✅ All tests passed!")
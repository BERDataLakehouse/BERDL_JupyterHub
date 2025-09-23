import os
from unittest.mock import Mock, patch


# Mock the dependencies that are not available in test environment
with patch.dict(
    "sys.modules",
    {
        "berdlhub.api_utils.spark_utils": Mock(),
        "spark_manager_client": Mock(),
    },
):
    from berdlhub.config.hooks import modify_pod_hook


class TestModifyPodHook:
    """Test suite for modify_pod_hook function."""

    def test_modify_pod_hook_basic_env_vars(self):
        """Test that basic environment variables are added to the pod."""
        # Setup
        spawner = Mock()
        spawner.log = Mock()

        pod = Mock()
        pod.spec = Mock()
        pod.spec.containers = [Mock()]
        pod.spec.containers[0].env = []

        # Execute
        result = modify_pod_hook(spawner, pod)

        # Verify basic environment variables are added
        env_vars = result.spec.containers[0].env
        env_var_names = [env_var.name for env_var in env_vars]

        expected_env_vars = [
            "BERDL_POD_IP",
            "BERDL_POD_NAME",
            "BERDL_CPU_REQUEST",
            "BERDL_CPU_LIMIT",
            "BERDL_MEMORY_REQUEST",
            "BERDL_MEMORY_LIMIT",
        ]

        for expected_var in expected_env_vars:
            assert expected_var in env_var_names

        # Verify pod is returned
        assert result == pod

    def test_modify_pod_hook_no_tolerations(self):
        """Test that no tolerations are added when BERDL_TOLERATIONS is not set."""
        # Setup
        spawner = Mock()
        spawner.log = Mock()

        pod = Mock()
        pod.spec = Mock()
        pod.spec.containers = [Mock()]
        pod.spec.containers[0].env = []

        # Clear environment
        with patch.dict(os.environ, {}, clear=True):
            # Execute
            result = modify_pod_hook(spawner, pod)

            # Verify tolerations are not set on the spec
            # Since we're using Mocks, we need to check if tolerations was assigned
            # We can do this by checking if pod.spec.tolerations was assigned a list
            # If it wasn't assigned, it should still be a Mock, not a list
            assert not isinstance(result.spec.tolerations, list)

    def test_modify_pod_hook_single_toleration(self):
        """Test that a single toleration is correctly parsed and added."""
        # Setup
        spawner = Mock()
        spawner.log = Mock()

        pod = Mock()
        pod.spec = Mock()
        pod.spec.containers = [Mock()]
        pod.spec.containers[0].env = []

        # Set environment variable
        with patch.dict(os.environ, {"BERDL_TOLERATIONS": "environments=dev:NoSchedule"}):
            # Execute
            result = modify_pod_hook(spawner, pod)

            # Verify toleration is added
            assert hasattr(result.spec, "tolerations")
            assert len(result.spec.tolerations) == 1

            toleration = result.spec.tolerations[0]
            assert toleration.key == "environments"
            assert toleration.operator == "Equal"
            assert toleration.value == "dev"
            assert toleration.effect == "NoSchedule"

    def test_modify_pod_hook_multiple_tolerations(self):
        """Test that multiple tolerations are correctly parsed and added."""
        # Setup
        spawner = Mock()
        spawner.log = Mock()

        pod = Mock()
        pod.spec = Mock()
        pod.spec.containers = [Mock()]
        pod.spec.containers[0].env = []

        # Set environment variable with multiple tolerations
        tolerations_str = "environments=dev:NoSchedule,environments=prod:NoSchedule"
        with patch.dict(os.environ, {"BERDL_TOLERATIONS": tolerations_str}):
            # Execute
            result = modify_pod_hook(spawner, pod)

            # Verify tolerations are added
            assert hasattr(result.spec, "tolerations")
            assert len(result.spec.tolerations) == 2

            # Check first toleration
            toleration1 = result.spec.tolerations[0]
            assert toleration1.key == "environments"
            assert toleration1.operator == "Equal"
            assert toleration1.value == "dev"
            assert toleration1.effect == "NoSchedule"

            # Check second toleration
            toleration2 = result.spec.tolerations[1]
            assert toleration2.key == "environments"
            assert toleration2.operator == "Equal"
            assert toleration2.value == "prod"
            assert toleration2.effect == "NoSchedule"

    def test_modify_pod_hook_tolerations_with_spaces(self):
        """Test that tolerations with extra spaces are handled correctly."""
        # Setup
        spawner = Mock()
        spawner.log = Mock()

        pod = Mock()
        pod.spec = Mock()
        pod.spec.containers = [Mock()]
        pod.spec.containers[0].env = []

        # Set environment variable with spaces
        tolerations_str = " environments=dev:NoSchedule , environments=prod:NoSchedule "
        with patch.dict(os.environ, {"BERDL_TOLERATIONS": tolerations_str}):
            # Execute
            result = modify_pod_hook(spawner, pod)

            # Verify tolerations are added correctly despite spaces
            assert hasattr(result.spec, "tolerations")
            assert len(result.spec.tolerations) == 2

    def test_modify_pod_hook_invalid_toleration_format(self):
        """Test handling of invalid toleration formats."""
        # Setup
        spawner = Mock()
        spawner.log = Mock()

        pod = Mock()
        pod.spec = Mock()
        pod.spec.containers = [Mock()]
        pod.spec.containers[0].env = []

        # Set environment variable with invalid format
        with patch.dict(os.environ, {"BERDL_TOLERATIONS": "invalid_format,environments=dev:NoSchedule"}):
            # Execute
            result = modify_pod_hook(spawner, pod)

            # Verify warning is logged for invalid format
            spawner.log.warning.assert_called_once()
            warning_call = spawner.log.warning.call_args
            assert "Invalid toleration format" in warning_call[0][0]
            assert "invalid_format" in warning_call[0][0]

            # Verify valid toleration is still added
            assert hasattr(result.spec, "tolerations")
            assert len(result.spec.tolerations) == 1
            assert result.spec.tolerations[0].value == "dev"

    def test_modify_pod_hook_all_invalid_tolerations(self):
        """Test handling when all tolerations are invalid."""
        # Setup
        spawner = Mock()
        spawner.log = Mock()

        pod = Mock()
        pod.spec = Mock()
        pod.spec.containers = [Mock()]
        pod.spec.containers[0].env = []

        # Set environment variable with all invalid formats
        with patch.dict(os.environ, {"BERDL_TOLERATIONS": "invalid1,invalid2"}):
            # Execute
            result = modify_pod_hook(spawner, pod)

            # Verify warnings are logged
            assert spawner.log.warning.call_count == 2

            # Verify no tolerations are added (tolerations should not be a list)
            assert not isinstance(result.spec.tolerations, list)

    def test_modify_pod_hook_different_effects(self):
        """Test tolerations with different effects."""
        # Setup
        spawner = Mock()
        spawner.log = Mock()

        pod = Mock()
        pod.spec = Mock()
        pod.spec.containers = [Mock()]
        pod.spec.containers[0].env = []

        # Set environment variable with different effects
        tolerations_str = "tier=frontend:NoExecute,zone=us-west:PreferNoSchedule"
        with patch.dict(os.environ, {"BERDL_TOLERATIONS": tolerations_str}):
            # Execute
            result = modify_pod_hook(spawner, pod)

            # Verify tolerations with different effects
            assert hasattr(result.spec, "tolerations")
            assert len(result.spec.tolerations) == 2

            effects = [t.effect for t in result.spec.tolerations]
            assert "NoExecute" in effects
            assert "PreferNoSchedule" in effects

    def test_modify_pod_hook_kubernetes_client_call(self):
        """Test that Kubernetes client V1Toleration is called correctly."""
        # Setup
        spawner = Mock()
        spawner.log = Mock()

        pod = Mock()
        pod.spec = Mock()
        pod.spec.containers = [Mock()]
        pod.spec.containers[0].env = []

        # Set environment variable
        with patch.dict(os.environ, {"BERDL_TOLERATIONS": "environments=dev:NoSchedule"}):
            # Execute
            result = modify_pod_hook(spawner, pod)

            # Verify toleration was added correctly
            assert isinstance(result.spec.tolerations, list)
            assert len(result.spec.tolerations) == 1

            toleration = result.spec.tolerations[0]
            assert toleration.key == "environments"
            assert toleration.operator == "Equal"
            assert toleration.value == "dev"
            assert toleration.effect == "NoSchedule"

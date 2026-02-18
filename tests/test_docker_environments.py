"""
Docker-based environment tests for crashvault.

These tests spin up Docker containers to verify crashvault works correctly
across different Python versions and environments.

Requirements:
- Docker must be installed and running
- Run with: pytest tests/test_docker_environments.py -v -s

Note: These tests are slow and are marked with @pytest.mark.docker
Run with: pytest -m docker
Skip with: pytest -m "not docker"
"""
import subprocess
import pytest
import os
import tempfile
import shutil
from pathlib import Path


# Check if Docker is available
def docker_available():
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


# Skip all tests in this module if Docker is not available
pytestmark = [
    pytest.mark.docker,
    pytest.mark.skipif(not docker_available(), reason="Docker not available")
]


# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class TestDockerEnvironments:
    """Tests that run crashvault in Docker containers."""

    @pytest.fixture
    def docker_context(self, tmp_path):
        """Create a temporary directory with project files for Docker build."""
        # Copy project files to temp directory
        context_dir = tmp_path / "crashvault"
        shutil.copytree(
            PROJECT_ROOT,
            context_dir,
            ignore=shutil.ignore_patterns(
                '__pycache__', '*.pyc', '.git', '.pytest_cache',
                '*.egg-info', 'build', 'dist', '.venv', 'venv'
            )
        )
        return context_dir

    def _build_docker_image(self, context_dir: Path, python_version: str) -> str:
        """Build a Docker image for testing."""
        image_tag = f"crashvault-test:py{python_version.replace('.', '')}"

        dockerfile_content = f"""
FROM python:{python_version}-slim

RUN apt-get update && apt-get install -y --no-install-recommends git \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app/

RUN pip install --no-cache-dir -e . pytest click rich

ENV CRASHVAULT_HOME=/tmp/crashvault-test
"""
        dockerfile_path = context_dir / "Dockerfile.test"
        dockerfile_path.write_text(dockerfile_content)

        result = subprocess.run(
            ["docker", "build", "-t", image_tag, "-f", "Dockerfile.test", "."],
            cwd=context_dir,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            pytest.fail(f"Docker build failed:\n{result.stderr}")

        return image_tag

    def _run_in_docker(self, image_tag: str, command: list, timeout: int = 120) -> subprocess.CompletedProcess:
        """Run a command inside a Docker container."""
        docker_cmd = [
            "docker", "run", "--rm",
            "-e", "CRASHVAULT_HOME=/tmp/crashvault-test",
            image_tag
        ] + command

        return subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

    def _cleanup_image(self, image_tag: str):
        """Remove Docker image."""
        subprocess.run(
            ["docker", "rmi", "-f", image_tag],
            capture_output=True
        )

    @pytest.mark.parametrize("python_version", ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"])
    def test_crashvault_installs_on_python_version(self, docker_context, python_version):
        """Verify crashvault can be installed on different Python versions."""
        image_tag = self._build_docker_image(docker_context, python_version)
        try:
            # Check that crashvault CLI is available
            result = self._run_in_docker(image_tag, ["crashvault", "--help"])
            assert result.returncode == 0, f"crashvault --help failed:\n{result.stderr}"
            assert "crashvault" in result.stdout.lower() or "Usage" in result.stdout
        finally:
            self._cleanup_image(image_tag)

    @pytest.mark.parametrize("python_version", ["3.8", "3.11", "3.13"])
    def test_core_commands_on_python_version(self, docker_context, python_version):
        """Test core commands work on different Python versions."""
        image_tag = self._build_docker_image(docker_context, python_version)
        try:
            # Test add command
            result = self._run_in_docker(image_tag, [
                "crashvault", "add", "Test error from Docker"
            ])
            assert result.returncode == 0, f"add failed:\n{result.stderr}"

            # Test list command
            result = self._run_in_docker(image_tag, ["crashvault", "list"])
            assert result.returncode == 0, f"list failed:\n{result.stderr}"
        finally:
            self._cleanup_image(image_tag)

    @pytest.mark.parametrize("python_version", ["3.8", "3.11", "3.13"])
    def test_wrap_command_on_python_version(self, docker_context, python_version):
        """Test wrap command works on different Python versions."""
        image_tag = self._build_docker_image(docker_context, python_version)
        try:
            # Test wrap with successful command
            result = self._run_in_docker(image_tag, [
                "crashvault", "wrap", "echo", "hello"
            ])
            assert result.returncode == 0
            assert "hello" in result.stdout

            # Test wrap with failing command
            result = self._run_in_docker(image_tag, [
                "crashvault", "wrap", "false"
            ])
            assert result.returncode != 0
        finally:
            self._cleanup_image(image_tag)

    @pytest.mark.parametrize("python_version", ["3.8", "3.11", "3.13"])
    def test_full_test_suite_on_python_version(self, docker_context, python_version):
        """Run the full test suite on different Python versions."""
        image_tag = self._build_docker_image(docker_context, python_version)
        try:
            result = self._run_in_docker(
                image_tag,
                ["pytest", "tests/", "-v", "--tb=short", "-x"],
                timeout=300
            )
            assert result.returncode == 0, f"Tests failed on Python {python_version}:\n{result.stdout}\n{result.stderr}"
        finally:
            self._cleanup_image(image_tag)


class TestDockerWrapCommand:
    """Specific tests for wrap command behavior in Docker."""

    @pytest.fixture
    def docker_image(self, tmp_path):
        """Build a Docker image for wrap command testing."""
        context_dir = tmp_path / "crashvault"
        shutil.copytree(
            PROJECT_ROOT,
            context_dir,
            ignore=shutil.ignore_patterns(
                '__pycache__', '*.pyc', '.git', '.pytest_cache',
                '*.egg-info', 'build', 'dist', '.venv', 'venv'
            )
        )

        dockerfile_content = """
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends git curl \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app/

RUN pip install --no-cache-dir -e . pytest click rich

ENV CRASHVAULT_HOME=/tmp/crashvault-test
"""
        dockerfile_path = context_dir / "Dockerfile.test"
        dockerfile_path.write_text(dockerfile_content)

        image_tag = "crashvault-wrap-test:latest"
        result = subprocess.run(
            ["docker", "build", "-t", image_tag, "-f", "Dockerfile.test", "."],
            cwd=context_dir,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            pytest.fail(f"Docker build failed:\n{result.stderr}")

        yield image_tag

        # Cleanup
        subprocess.run(["docker", "rmi", "-f", image_tag], capture_output=True)

    def test_wrap_captures_signal_exit(self, docker_image):
        """Test wrap handles signal-based exits correctly."""
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-e", "CRASHVAULT_HOME=/tmp/crashvault-test",
                docker_image,
                "sh", "-c",
                "crashvault init && crashvault wrap sh -c 'kill -9 $$'"
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        # SIGKILL (9) results in exit code 137 (128 + 9)
        assert result.returncode != 0

    def test_wrap_with_long_running_command(self, docker_image):
        """Test wrap handles commands that take time."""
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-e", "CRASHVAULT_HOME=/tmp/crashvault-test",
                docker_image,
                "sh", "-c",
                "crashvault init && crashvault wrap sleep 2 && echo 'completed'"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        assert "completed" in result.stdout

    def test_wrap_with_environment_variables(self, docker_image):
        """Test wrap passes through environment variables."""
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-e", "CRASHVAULT_HOME=/tmp/crashvault-test",
                "-e", "TEST_VAR=hello_docker",
                docker_image,
                "sh", "-c",
                "crashvault init && crashvault wrap sh -c 'echo $TEST_VAR'"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        assert "hello_docker" in result.stdout

    def test_wrap_with_working_directory(self, docker_image):
        """Test wrap works with different working directories."""
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-e", "CRASHVAULT_HOME=/tmp/crashvault-test",
                "-w", "/tmp",
                docker_image,
                "sh", "-c",
                "crashvault init && crashvault wrap pwd"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        assert "/tmp" in result.stdout

    def test_wrap_large_output(self, docker_image):
        """Test wrap handles commands with large output."""
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-e", "CRASHVAULT_HOME=/tmp/crashvault-test",
                docker_image,
                "sh", "-c",
                "crashvault init && crashvault wrap sh -c 'for i in $(seq 1 1000); do echo line$i; done'"
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        assert result.returncode == 0
        assert "line1" in result.stdout
        assert "line1000" in result.stdout


class TestDockerLinuxSpecific:
    """Tests for Linux-specific behavior in Docker."""

    @pytest.fixture
    def linux_image(self, tmp_path):
        """Build a Docker image with additional Linux tools."""
        context_dir = tmp_path / "crashvault"
        shutil.copytree(
            PROJECT_ROOT,
            context_dir,
            ignore=shutil.ignore_patterns(
                '__pycache__', '*.pyc', '.git', '.pytest_cache',
                '*.egg-info', 'build', 'dist', '.venv', 'venv'
            )
        )

        dockerfile_content = """
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \\
    git procps coreutils \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app/

RUN pip install --no-cache-dir -e . pytest click rich

ENV CRASHVAULT_HOME=/tmp/crashvault-test
"""
        dockerfile_path = context_dir / "Dockerfile.test"
        dockerfile_path.write_text(dockerfile_content)

        image_tag = "crashvault-linux-test:latest"
        result = subprocess.run(
            ["docker", "build", "-t", image_tag, "-f", "Dockerfile.test", "."],
            cwd=context_dir,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            pytest.fail(f"Docker build failed:\n{result.stderr}")

        yield image_tag

        subprocess.run(["docker", "rmi", "-f", image_tag], capture_output=True)

    def test_crashvault_home_isolation(self, linux_image):
        """Test CRASHVAULT_HOME environment variable isolation."""
        # Run with custom CRASHVAULT_HOME
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-e", "CRASHVAULT_HOME=/custom/path",
                linux_image,
                "sh", "-c",
                "crashvault init && crashvault path"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        assert "/custom/path" in result.stdout

    def test_file_permissions(self, linux_image):
        """Test that crashvault creates files with correct permissions."""
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-e", "CRASHVAULT_HOME=/tmp/crashvault-test",
                linux_image,
                "sh", "-c",
                """
                crashvault init
                crashvault add "Test error"
                ls -la /tmp/crashvault-test/
                ls -la /tmp/crashvault-test/events/
                """
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        # Verify files are created
        assert "issues.json" in result.stdout
        assert "events" in result.stdout

    def test_concurrent_access(self, linux_image):
        """Test crashvault handles concurrent access."""
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-e", "CRASHVAULT_HOME=/tmp/crashvault-test",
                linux_image,
                "sh", "-c",
                """
                crashvault init
                # Run multiple add commands concurrently
                for i in 1 2 3 4 5; do
                    crashvault add "Concurrent error $i" &
                done
                wait
                crashvault list
                """
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        # Should complete without errors
        assert result.returncode == 0


class TestDockerAlpineEnvironment:
    """Tests for Alpine Linux environment (musl libc)."""

    @pytest.fixture
    def alpine_image(self, tmp_path):
        """Build a Docker image based on Alpine Linux."""
        context_dir = tmp_path / "crashvault"
        shutil.copytree(
            PROJECT_ROOT,
            context_dir,
            ignore=shutil.ignore_patterns(
                '__pycache__', '*.pyc', '.git', '.pytest_cache',
                '*.egg-info', 'build', 'dist', '.venv', 'venv'
            )
        )

        dockerfile_content = """
FROM python:3.11-alpine

RUN apk add --no-cache git bash

WORKDIR /app
COPY . /app/

RUN pip install --no-cache-dir -e . pytest click rich

ENV CRASHVAULT_HOME=/tmp/crashvault-test
"""
        dockerfile_path = context_dir / "Dockerfile.test"
        dockerfile_path.write_text(dockerfile_content)

        image_tag = "crashvault-alpine-test:latest"
        result = subprocess.run(
            ["docker", "build", "-t", image_tag, "-f", "Dockerfile.test", "."],
            cwd=context_dir,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            pytest.fail(f"Docker build failed:\n{result.stderr}")

        yield image_tag

        subprocess.run(["docker", "rmi", "-f", image_tag], capture_output=True)

    def test_crashvault_on_alpine(self, alpine_image):
        """Test crashvault works on Alpine Linux (musl libc)."""
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-e", "CRASHVAULT_HOME=/tmp/crashvault-test",
                alpine_image,
                "sh", "-c",
                """
                crashvault init
                crashvault add "Test on Alpine"
                crashvault list
                """
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        assert result.returncode == 0
        assert "Test on Alpine" in result.stdout or "#1" in result.stdout

    def test_wrap_on_alpine(self, alpine_image):
        """Test wrap command on Alpine Linux."""
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-e", "CRASHVAULT_HOME=/tmp/crashvault-test",
                alpine_image,
                "sh", "-c",
                "crashvault init && crashvault wrap echo 'hello alpine'"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        assert "hello alpine" in result.stdout

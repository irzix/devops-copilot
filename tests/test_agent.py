"""Tests for the agent module: command classification and safety heuristics."""

import pytest

from app.modules.chat.agent import is_write_command


class TestIsWriteCommand:
    """Test the heuristic that classifies commands as read-only or state-modifying."""

    # ── Read-only commands (should return False) ──

    @pytest.mark.parametrize("cmd", [
        "df -h",
        "free -m",
        "uptime",
        "uname -a",
        "whoami",
        "hostname",
        "ps aux",
        "top -bn1",
        "cat /etc/hostname",
        "ls -la /var/log",
        "grep error /var/log/syslog",
        "tail -n 50 /var/log/nginx/access.log",
        "head -n 10 /etc/hosts",
        "stat /etc/nginx/nginx.conf",
        "systemctl status nginx",
    ])
    def test_read_only_commands(self, cmd):
        assert is_write_command(cmd) is False, f"'{cmd}' should be read-only"

    # ── Write commands (should return True) ──

    @pytest.mark.parametrize("cmd", [
        "rm -rf /tmp/old_logs",
        "systemctl restart nginx",
        "apt-get update",
        "yum install httpd",
        "docker stop container_name",
        "reboot",
        "shutdown -h now",
        "mv /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak",
        "cp /etc/hosts /etc/hosts.bak",
        "echo 'test' > /tmp/file.txt",
        "chmod 755 /var/www",
        "chown www-data:www-data /var/www",
        "mkdir -p /opt/app",
        "useradd newuser",
    ])
    def test_write_commands(self, cmd):
        assert is_write_command(cmd) is True, f"'{cmd}' should be a write command"

    # ── Edge cases ──

    def test_read_command_with_redirect_is_write(self):
        """A normally read-only command that redirects output is state-modifying."""
        assert is_write_command("cat /etc/hosts > /tmp/hosts_copy") is True

    def test_piped_read_commands_are_safe(self):
        """Piping between read-only commands should be safe."""
        assert is_write_command("ps aux | grep nginx") is False

    def test_chained_with_write_is_dangerous(self):
        """If any sub-command in a chain is write, the whole thing is write."""
        assert is_write_command("df -h && systemctl restart nginx") is True

    def test_empty_command(self):
        """Empty command should not crash."""
        assert is_write_command("") is False

    def test_whitespace_only(self):
        assert is_write_command("   ") is False

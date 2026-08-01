def test_ssh_change_password_result():
    """测试 SSHChangePasswordResult 模型"""
    from src.ssh.first_connect import SSHChangePasswordResult

    result = SSHChangePasswordResult(success=True, message="改密成功", backup_path="backups/test")
    assert result.success is True
    assert result.message == "改密成功"
    assert result.backup_path == "backups/test"


def test_ssh_first_connect_get_summary():
    """测试 SSHFirstConnect.get_summary 方法"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.1", username="admin")
    connector = SSHFirstConnect(device)
    summary = connector.get_summary()
    assert "192.168.1.1" in summary
    assert "SSHFirstConnect" in summary


def test_ssh_first_connect_is_connected():
    """测试 SSHFirstConnect.is_connected 属性"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.1", username="admin")
    connector = SSHFirstConnect(device)
    # 初始状态未连接
    assert connector.is_connected is False


def test_ssh_first_connect_get_connection_info():
    """测试 SSHFirstConnect.get_connection_info 方法"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.1", username="admin", port=22)
    connector = SSHFirstConnect(device)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.1"
    assert info["port"] == 22
    assert info["connected"] is False


def test_ssh_first_connect_get_connection_info_detailed():
    """测试 SSHFirstConnect.get_connection_info 返回详细结构"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="10.0.0.1", username="admin", port=2222)
    connector = SSHFirstConnect(device)
    info = connector.get_connection_info()
    assert "host" in info
    assert "port" in info
    assert "username" in info
    assert "connected" in info
    assert info["username"] == "admin"


def test_ssh_first_connect_get_connection_info_with_custom_port():
    """测试 SSHFirstConnect.get_connection_info 支持自定义端口"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="172.16.0.1", username="admin", port=2222)
    connector = SSHFirstConnect(device)
    info = connector.get_connection_info()
    assert info["port"] == 2222


def test_ssh_first_connect_get_connection_info_structure():
    """测试 SSHFirstConnect.get_connection_info 返回结构完整性"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.100.1", username="admin", port=22)
    connector = SSHFirstConnect(device)
    info = connector.get_connection_info()
    expected_keys = {"host", "port", "username", "connected"}
    assert set(info.keys()) == expected_keys


def test_ssh_first_connect_get_connection_info_with_different_user():
    """测试 SSHFirstConnect.get_connection_info 支持不同用户名"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.100", username="root", port=22)
    connector = SSHFirstConnect(device)
    info = connector.get_connection_info()
    assert info["username"] == "root"


def test_ssh_first_connect_get_connection_info_default_values():
    """测试 SSHFirstConnect.get_connection_info 默认值"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.50")
    connector = SSHFirstConnect(device)
    info = connector.get_connection_info()
    assert info["username"] == "admin"
    assert info["port"] == 22


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"


def test_ssh_first_connect_get_connection_info_with_custom_timeout():
    """测试 SSHFirstConnect.get_connection_info 支持自定义超时"""
    from src.ssh.first_connect import SSHFirstConnect, SSHDevice

    device = SSHDevice(host="192.168.1.60", username="admin", port=22)
    connector = SSHFirstConnect(device, timeout=30)
    info = connector.get_connection_info()
    assert info["host"] == "192.168.1.60"

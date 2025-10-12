def test_basic():
    """Простой тест без Django зависимостей"""
    assert 1 + 1 == 2


def test_strings():
    """Тест строковых операций"""
    assert "hello".upper() == "HELLO"
    assert "test".replace("t", "b") == "besb"
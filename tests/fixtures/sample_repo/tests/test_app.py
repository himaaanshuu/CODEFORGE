"""Test module for the sample application."""

from app import add, multiply, subtract, Calculator


def test_add_basic():
    """Test basic addition."""
    assert add(2, 3) == 5
    assert add(0, 0) == 0
    assert add(-1, 1) == 0


def test_add_negative():
    """Test addition with negative numbers."""
    assert add(-5, -3) == -8
    assert add(5, -3) == 2


def test_multiply_basic():
    """Test basic multiplication."""
    assert multiply(2, 3) == 6
    assert multiply(0, 5) == 0


def test_subtract_basic():
    """Test basic subtraction."""
    assert subtract(5, 3) == 2
    assert subtract(3, 5) == -2
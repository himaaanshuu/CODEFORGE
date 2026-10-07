"""Sample application module."""

def add(x: int, y: int) -> int:
    """Add two numbers and return the result.

    Args:
        x: First integer to add.
        y: Second integer to add.

    Returns:
        The sum of x and y.
    """
    return x + y


def multiply(x: int, y: int) -> int:
    """Multiply two numbers and return the result.

    Args:
        x: First integer to multiply.
        y: Second integer to multiply.

    Returns:
        The product of x and y.
    """
    return x * y


def subtract(x: int, y: int) -> int:
    """Subtract the second number from the first.

    Args:
        x: The minuend.
        y: The subtrahend.

    Returns:
        The difference (x - y).
    """
    return x - y


class Calculator:
    """A simple calculator class."""

    def __init__(self, initial_value: int = 0) -> None:
        self.value = initial_value

    def add_to(self, amount: int) -> None:
        """Add an amount to the current value.

        Args:
            amount: The amount to add.
        """
        self.value += amount

    def multiply_by(self, factor: int) -> None:
        """Multiply the current value by a factor.

        Args:
            factor: The multiplication factor.
        """
        self.value *= factor

    def reset(self) -> None:
        """Reset the value to zero."""
        self.value = 0
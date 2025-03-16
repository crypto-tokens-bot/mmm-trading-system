import abc


class OrderExecutor(abc.ABC):
    """
    Abstract base class for all order executors.
    Subclasses must implement the execute_order method.
    """

    @abc.abstractmethod
    def execute_order(self, order_id: str):
        """
        Execute an order given its ID.

        Parameters:
            order_id (str): Unique identifier of the order to be executed.

        Raises:
            Exception: In case of execution failure.
        """
        pass

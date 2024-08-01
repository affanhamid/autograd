import numpy as np
from typing import List, NamedTuple, Callable, Optional, Union


class Dependency(NamedTuple):
    tensor: "Tensor"
    grad_fn: Callable[[np.ndarray], np.ndarray]


Arrayable = Union[float, list, np.ndarray]


def ensure_array(arrayable: Arrayable) -> np.ndarray:
    if isinstance(arrayable, np.ndarray):
        return arrayable
    else:
        return np.array(arrayable)


Tensorable = Union["Tensor", float, np.ndarray]


def ensure_tensor(tensorable: Tensorable) -> "Tensor":
    if isinstance(tensorable, Tensor):
        return tensorable
    else:
        return Tensor(tensorable)


class Tensor:
    def __init__(
        self,
        data: Arrayable,
        requires_grad: bool = False,
        depends_on: List[Dependency] = [],
    ) -> None:
        self._data = ensure_array(data)
        self.requires_grad = requires_grad
        self.depends_on = depends_on

        self.shape = self._data.shape
        self.grad: Optional["Tensor"] = None

        if self.requires_grad:
            self.zero_grad()

    @property
    def data(self) -> np.ndarray:
        return self._data

    @data.setter
    def data(self, new_data: np.ndarray) -> None:
        self._data = new_data
        self.grad = None

    def zero_grad(self) -> None:
        self.grad = Tensor(data=np.zeros_like(self.data))

    def __repr__(self) -> str:
        return f"Tensor({self.data}, requires_grad={self.requires_grad})"

    def __add__(self, other) -> "Tensor":
        from .operations import _add

        return _add(self, ensure_tensor(other))

    def __radd__(self, other) -> "Tensor":
        return self + other

    def __iadd__(self, other) -> "Tensor":
        self.data = self.data + ensure_tensor(other).data
        return self

    def __isub__(self, other) -> "Tensor":
        self.data = self.data - ensure_tensor(other).data
        return self

    def __imul__(self, other) -> "Tensor":
        self.data = self.data * ensure_tensor(other).data
        return self

    def __mul__(self, other) -> "Tensor":
        from .operations import _mul

        return _mul(self, ensure_tensor(other))

    def __rmul__(self, other) -> "Tensor":
        return self * other

    def __matmul__(self, other) -> "Tensor":
        from .operations import _matmul

        return _matmul(self, other)

    def __neg__(self) -> "Tensor":
        from .operations import _neg

        return _neg(self)

    def __sub__(self, other) -> "Tensor":
        return self + -other

    def __rsub__(self, other) -> "Tensor":
        return -(self - other)

    def __getitem__(self, idxs) -> "Tensor":
        from .operations import _slice

        return _slice(self, idxs)

    def backward(self, grad: "Tensor" = None) -> None:
        assert (
            self.requires_grad
        ), "Called backwards on a tensor that doesn't require grad"

        if grad is None:
            if self.shape == ():
                grad = Tensor(1)
            else:
                raise RuntimeError("grad must be specificied for non-zero tensor")

        self.grad.data += grad.data  # type: ignore
        for dependency in self.depends_on:
            backward_grad = dependency.grad_fn(grad.data)
            dependency.tensor.backward(Tensor(backward_grad))

    def sum(self, axis=0) -> "Tensor":
        from .operations import _tensor_sum

        return _tensor_sum(self, axis)

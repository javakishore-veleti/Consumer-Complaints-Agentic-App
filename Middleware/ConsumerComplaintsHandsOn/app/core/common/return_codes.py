"""Integer codes returned by every method that takes a ctx. More can be added later."""

SUCCESS = 0
FAILURE = 1
NOT_FOUND = 2
INVALID_INPUT = 3
CONFLICT = 4  # the request is valid but not allowed in the current state (for example an out-of-order status)

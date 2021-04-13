"""
Pietro Jomini
13.04.2021

To run two clients simultaneously  use the `scripts/clients.sh` script.
The `examples` directory contains examples of output from various scenarios .
"""

from typing import Any, Dict

import requests


def get(
    path: str,
    api: str = "http://127.0.0.1:5000/api/v1",
    **data: Dict[str, Any],
) -> Dict[str, Any]:
    """Perform a GET request with `data` as json body"""

    # Adjust the path.
    path = path if path.startswith("/") else "/" + path

    # Perform the HTTP request.
    return requests.get(api + path, json=data).json()


if __name__ == "__main__":

    # Connect to the server.
    sid = get("connect").get("sid")
    print(f"Connected with sid={sid}")

    while True:

        # Queue to solve an operation.
        response = get("queue", sid=sid)

        # If there has been a problem alert the user and break.
        if not response.get("ok"):
            error = response.get("error")
            print(f"\tError wile queueing {error}")
            break

        # If theere are no more operations to solve
        # the server send an halt alert.
        elif response.get("halt") is True:
            print("\tServer requested halt")
            break

        # Fetch the operation from the response body.
        operation = response.get("operation")
        print(f"\tQueued for operation {operation}")

        # Solve the evaluation.
        result = eval(operation)
        print(f"\t\tSolved operation {operation} as {result}")

        # Send the result to the server,
        response = get("complete", sid=sid, operation=operation, result=result)

        # If there has been a problem alert the user and break.
        if response.get("ok") is False:
            print(f"\t\tError while queueing {response.get('error')}")
            break

        # Notify the user that the solution has been submitted.
        print("\t\tSolution submitted")

    # Disconnect from the server.
    response = get("disconnect", sid=sid)
    print(f"Disconnected with status={response.get('ok')}")

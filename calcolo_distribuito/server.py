"""
Pietro Jomini
13.04.2021
"""

import sqlite3
import uuid
from typing import Any, Optional

from flask import Flask, redirect, request


def run_sql(sql, params):
    """`sqlite3` wrapper"""

    # Create a connection and a cursor to the database.
    conn = sqlite3.connect("db/operations.db")
    cursor = conn.cursor()

    # Execute the sql query.
    cursor.execute(sql, params)

    # Fetch the result of the query.
    res = cursor.fetchall()

    # Commit the changes.
    conn.commit()

    # Close the cursor and the connection.
    cursor.close()
    conn.close()

    return res


class Session:
    """Basic session utility"""

    def __init__(self):

        # Each session instance holds a list of all logged users.
        # In a real-world application this should be
        # also inside a database, probably in a cache-like
        # database (eg. redis).
        # For sake of semplicity I putted it here.
        self.clients = []

    def connect(self) -> str:
        """Connect a client to the session"""

        # Generate a new client id.
        sid = str(uuid.uuid4())

        # Add the new id to the list of connected users.
        self.clients.append(sid)
        return sid

    def get_sid(self) -> Optional[str]:
        """Get sid from body"""

        # Extract "sid" from request body.
        body = request.json or {}
        return body.get("sid")

    def disconnect(self, sid: Optional[str] = None) -> bool:
        """Disconnect a client from the session"""

        # Fetch the client id
        sid = sid or self.get_sid()

        # If the client isn't connected, return False
        # to express an error.
        if not self.is_connected(sid):
            return False

        # Remove the client id from the list of connected clients.
        self.clients = [c for c in self.clients if c != sid]

        # Return True to express the succesfull disconnection.
        return True

    def is_connected(self, sid: Optional[str] = None) -> bool:
        """Check if a client has a session open"""

        # Fetch the client id.
        sid = sid or self.get_sid()

        # Check if the client id exists and if it is included
        # in the list of connected clients.
        return sid is not None and sid in self.clients


class Manager:
    """Basic task manager utility"""

    def __init__(self):

        # Clean the list of results, to avoid
        # duplications when testing repeatedly.
        run_sql("DELETE FROM results", ())

        # Fetch the operations from the db.
        self.operations = run_sql("SELECT id, operation FROM operations", ())

        # Instantiate a queue to hold operation currently
        # being solved by a client.
        # Like `Session.clients` it should be held in
        # a cache-like db, but for simplicity sake
        # i kept it here.
        self.queue = []

    def enqueue(self, sid: str) -> Optional[str]:
        """Queue a client as solving an operation"""

        # Check if there's operations left to solve.
        if len(self.operations) == 0:
            return

        # Pop an operation from the local list.
        # Note that this don't actually change
        # the data held in the database.
        operation = self.operations.pop()

        # Queue the operation with the id of the client
        # solving it.
        self.queue.append((sid, operation))

        # Return the literal operation, so that it
        # can be solved by the client.
        return operation[1]

    def solve(self, sid: str, operation: str, result: Any) -> bool:
        """Mark an operation as completed"""

        # Check if the operation solved is present in the queue
        # and if it should be solved by the actual client.
        op = [o for c, o in self.queue if o[1] == operation and c == sid]

        # If not, return False,
        # to express an error.
        if len(op) == 0:
            return False

        # Extract the queue instance from the list of candidates.
        # (it shouldn't contain more that one element...).
        op = op[0]

        # Remove the instance from the queue.
        self.queue = [q for q in self.queue if q != (sid, op)]

        # Finally insert the result record into the database.
        # This table holds only the id of the unsolved operations,
        # to join all together run the query located at `scripts/results.sql`.
        run_sql(
            "INSERT INTO results (client, operation, result) VALUES (?, ?, ?)",
            (sid, op[0], result),
        )

        # Return True to express the successfull
        # marking of the operation as completed.
        return True


# -------------------
# Globals variables.

server = Flask(__name__)
session = Session()
manager = Manager()

# Api route base path
api = "/api/v1"

# -------------------


@server.route("/")
def index():
    """Webapp index. Usually there is some sort of front-end,
    but in this situation it just redirects to the entry point of the api."""

    return redirect(api)


@server.route(api + "/")
def api_ep():
    """Api entry point"""

    # Return some sort of "documentation" of the api.
    endpoints = [
        ("", "Api root"),
        ("connect", "Connect a client and get a clientId"),
        ("disconnect", "Disconnect a client"),
        ("queue", "Request an operation to compute"),
        ("complete", "Return the result of the operation"),
    ]

    # Format the list of endpoints as a list of dict, to work better as json.
    endpoints = [dict(path=api + "/" + p, help=h) for p, h in endpoints]

    # Send the list of endpoints as json.
    return dict(ok=True, endpoints=endpoints)


@server.route(api + "/connect")
def connect():
    """Create a client session"""

    return dict(sid=session.connect())


@server.route(api + "/disconnect")
def disconnect():
    """Delete a client session"""

    if not session.disconnect():

        # If the client is not connected send an error.
        return dict(ok=False, error="Client not connected")

    return dict(ok=True)


@server.route(api + "/queue")
def queue():
    """Queue a client as solving an operation"""

    # Check if the client is connected.
    if not session.is_connected():
        return dict(ok=False, error="Client not connected")

    # Add the operation to the local queue.
    operation = manager.enqueue(session.get_sid())

    # If the local list of operation to solve is empty the Mmanager.enqueue`
    # method returns `None`, ence if the value of `operation` is `None`
    # the client should stop.
    return dict(ok=True, operation=operation, halt=operation is None)


@server.route(api + "/complete")
def complete():
    """Mark a solution as completed"""

    # Check if the client is connected.
    if not session.is_connected():
        return dict(ok=False, error="Client not connected")

    # Extract the result ftom the request body.
    body = request.json or {}
    result = body.get("result")
    operation = body.get("operation")

    # Mark the operation as solved.
    if manager.solve(session.get_sid(), operation, result):
        return dict(ok=True)

    return dict(ok=False, error="Operation not queued by this client")


if __name__ == "__main__":

    # Start the server, listening at 127.0.0.1:500.
    server.run("127.0.0.1", 5000, debug=False)

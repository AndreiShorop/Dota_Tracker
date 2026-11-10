"""Run the web application on the local loopback interface."""

import uvicorn


def main() -> None:
    """Start the local web server."""
    uvicorn.run("dota_tracker.presentation.web.app:app", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()

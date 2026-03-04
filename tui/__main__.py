"""Entry point: uv run python -m tui"""

from tui.app import AcmMonitorApp


def main() -> None:
    app = AcmMonitorApp()
    app.run()


if __name__ == "__main__":
    main()

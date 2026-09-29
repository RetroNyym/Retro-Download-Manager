"""python -m download_manager ile arayuzu baslatir."""

import sys


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    from .gui import run
    return run(argv)


if __name__ == "__main__":
    raise SystemExit(main())

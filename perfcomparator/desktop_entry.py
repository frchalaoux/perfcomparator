"""Point d’entrée sans console pour le lanceur Web Windows."""

import ctypes


def main() -> None:
    try:
        from .cli import _start_web_pair

        _start_web_pair()
    except Exception as error:  # noqa: BLE001 - aucun terminal n'est ouvert par pythonw
        ctypes.windll.user32.MessageBoxW(  # type: ignore[attr-defined]
            None,
            f"PerfComparator n’a pas pu démarrer son interface Web :\n{error}",
            "PerfComparator",
            0x10,
        )
    except SystemExit as error:
        ctypes.windll.user32.MessageBoxW(  # type: ignore[attr-defined]
            None,
            f"PerfComparator n’a pas pu démarrer son interface Web (code {error.code}).",
            "PerfComparator",
            0x10,
        )


if __name__ == "__main__":
    main()

"""Fenêtre graphique minimale pour lancer une campagne de benchmarks."""

from __future__ import annotations

import queue
import threading
import webbrowser
from pathlib import Path
from tkinter import BOTH, LEFT, Label, StringVar, Tk, W, messagebox, ttk

from . import __version__
from .benchmarks import DEFINITIONS
from .models import BenchmarkFailure, BenchmarkResult
from .repository import JsonReportRepository
from .service import BenchmarkService
from .system_info import machine_readiness


class BenchmarkWindow:
    """Interface simple qui laisse le moteur travailler dans un thread séparé."""

    def __init__(self, root: Tk) -> None:
        self.root = root
        root.title(f"PerfComparator {__version__}")
        root.minsize(480, 300)

        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.profile = StringVar(value="standard")
        self.label = StringVar()
        self.status = StringVar(value="Prêt à mesurer cette machine.")
        self.last_report: Path | None = None
        self.run_button: ttk.Button
        self.open_button: ttk.Button
        self.progress: ttk.Progressbar

        body = ttk.Frame(root, padding=20)
        body.pack(fill=BOTH, expand=True)
        ttk.Label(body, text="Mesurer les performances", font=("TkDefaultFont", 16, "bold")).pack(
            anchor=W, pady=(0, 14)
        )

        ttk.Label(body, text="Nom de la machine (facultatif)").pack(anchor=W)
        ttk.Entry(body, textvariable=self.label).pack(fill="x", pady=(4, 12))

        ttk.Label(body, text="Durée de la mesure").pack(anchor=W)
        profile_row = ttk.Frame(body)
        profile_row.pack(anchor=W, pady=(4, 12))
        for value, title in (
            ("quick", "Rapide"),
            ("standard", "Standard"),
            ("thorough", "Complet"),
        ):
            ttk.Radiobutton(profile_row, text=title, value=value, variable=self.profile).pack(
                side=LEFT, padx=(0, 12)
            )

        Label(body, textvariable=self.status, anchor=W, justify=LEFT, wraplength=430).pack(
            fill="x", pady=(4, 8)
        )
        self.progress = ttk.Progressbar(body, mode="determinate", maximum=len(DEFINITIONS))
        self.progress.pack(fill="x", pady=(0, 14))

        actions = ttk.Frame(body)
        actions.pack(fill="x")
        self.run_button = ttk.Button(actions, text="Lancer la mesure", command=self.start)
        self.run_button.pack(side=LEFT)
        self.open_button = ttk.Button(
            actions, text="Ouvrir le rapport", command=self.open_report, state="disabled"
        )
        self.open_button.pack(side=LEFT, padx=(8, 0))
        ttk.Label(
            body,
            text="Les mesures sont enregistrées dans Documents/PerfComparator.",
            wraplength=430,
        ).pack(anchor=W, pady=(18, 0))
        ttk.Label(body, text=f"Version {__version__}").pack(anchor=W, pady=(8, 0))
        root.after(100, self.process_events)

    def start(self) -> None:
        self.run_button.configure(state="disabled")
        self.open_button.configure(state="disabled")
        self.progress.configure(value=0)
        self.status.set("Vérification de l’état de la machine…")
        profile = self.profile.get()
        label = self.label.get().strip() or None
        thread = threading.Thread(target=self.run_benchmarks, args=(profile, label), daemon=True)
        thread.start()

    def run_benchmarks(self, profile: str, label: str | None) -> None:
        output = Path.home() / "Documents" / "PerfComparator"
        service = BenchmarkService(JsonReportRepository(output))

        def progress(
            benchmark_id: str,
            outcome: BenchmarkResult | BenchmarkFailure | None,
        ) -> None:
            self.events.put(("progress", (benchmark_id, outcome)))

        try:
            _, report_path = service.run(
                profile_name=profile,
                label=label,
                repetitions=3,
                readiness=machine_readiness(),
                progress=progress,
            )
        except Exception as error:  # noqa: BLE001 - erreurs de plateforme affichées dans la fenêtre
            self.events.put(("error", str(error)))
        else:
            self.events.put(("complete", report_path))

    def process_events(self) -> None:
        try:
            while True:
                event, payload = self.events.get_nowait()
                if event == "progress":
                    benchmark_id, outcome = payload  # type: ignore[misc]
                    index = next(
                        (
                            i
                            for i, definition in enumerate(DEFINITIONS)
                            if definition.benchmark_id == benchmark_id
                        ),
                        0,
                    )
                    if outcome is None:
                        self.status.set(
                            f"Mesure en cours : {benchmark_id} ({index + 1}/{len(DEFINITIONS)})"
                        )
                    else:
                        self.progress.configure(value=index + 1)
                elif event == "complete":
                    self.last_report = payload  # type: ignore[assignment]
                    self.status.set(f"Mesure terminée. Rapport enregistré dans :\n{payload}")
                    self.run_button.configure(state="normal")
                    self.open_button.configure(state="normal")
                else:
                    self.status.set(f"La mesure n’a pas pu démarrer : {payload}")
                    self.run_button.configure(state="normal")
                    messagebox.showerror("Erreur PerfComparator", str(payload), parent=self.root)
        except queue.Empty:
            pass
        self.root.after(100, self.process_events)

    def open_report(self) -> None:
        if self.last_report is not None:
            webbrowser.open(self.last_report.resolve().as_uri())


def launch() -> None:
    """Ouvre l’interface graphique."""
    root = Tk()
    BenchmarkWindow(root)
    root.mainloop()

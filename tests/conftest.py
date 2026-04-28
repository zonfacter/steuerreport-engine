from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

import anyio.to_thread

os.environ.setdefault("STEUERREPORT_ENV", "testing")
os.environ.setdefault("STEUERREPORT_DB_PATH", "/tmp/steuerreport/steuerreport_test.db")


async def _run_sync_inline(
    func: Callable[..., Any],
    *args: Any,
    abandon_on_cancel: bool = False,
    cancellable: bool | None = None,
    limiter: Any = None,
) -> Any:
    _ = abandon_on_cancel, cancellable, limiter
    return func(*args)


anyio.to_thread.run_sync = _run_sync_inline

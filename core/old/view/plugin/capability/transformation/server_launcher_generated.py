import json
import os
import re
import secrets
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc.view.adapter.surface.document import set_state_marker
from ontobdc.view.adapter.surface.transformation import SurfaceTransformationAdapter
from ontobdc.view.domain.machine.surface_state import SurfaceGenerationProcessState
from ontobdc.view.plugin.check.is_server_launcher_generated.check import (
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
    DYNAMIC_PORT_MAX,
    DYNAMIC_PORT_MIN,
    SERVER_LAUNCHER_FILENAME,
    SERVER_REFERENCE_SCRIPT_ID,
    expected_launcher_text,
    generated_html_paths,
    main as check_server_launcher_generated,
    read_launcher_reference,
)


_SERVER_REFERENCE_SCRIPT_RE = re.compile(
    rf"<script\b[^>]*\bid=[\"']{re.escape(SERVER_REFERENCE_SCRIPT_ID)}[\"'][^>]*>"
    rf".*?</script>",
    re.IGNORECASE | re.DOTALL,
)


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f".{path.name}.",
    )
    try:
        with os.fdopen(
            fd,
            "w",
            encoding="utf-8",
            newline="",
        ) as handle:
            handle.write(content)
            handle.flush()
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def _random_server_port() -> int:
    width = DYNAMIC_PORT_MAX - DYNAMIC_PORT_MIN + 1
    return DYNAMIC_PORT_MIN + secrets.randbelow(width)


def _browser_host(host: str) -> str:
    normalized = str(host or "").strip()
    if not normalized or normalized in {"0.0.0.0", "::"}:
        return DEFAULT_SERVER_HOST
    return normalized


def _context_port(context: CliContextPort) -> Optional[int]:
    raw = context.get_parameter_value("server_port")
    if raw is None or str(raw).strip() == "":
        return None
    try:
        port = int(raw)
    except (TypeError, ValueError):
        return None
    return port if 1 <= port <= 65535 else None


def _resolve_server_reference(
    context: CliContextPort,
    launcher_path: Path,
) -> Tuple[str, int]:
    existing = read_launcher_reference(launcher_path)
    explicit_host = str(
        context.get_parameter_value("server_host") or ""
    ).strip()
    host = _browser_host(
        explicit_host or (existing[0] if existing is not None else DEFAULT_SERVER_HOST)
    )

    explicit_port = _context_port(context)
    if explicit_port is not None:
        port = explicit_port
    elif existing is not None:
        port = existing[1]
    else:
        port = _random_server_port()

    # The state is the owner of the generated server reference. Commands that
    # execute the normal Surface machine consume these values after the state
    # completes rather than inventing a second default of their own.
    context.set_parameter_value("server_host", host)
    context.set_parameter_value("server_port", port)
    return host, port


def _server_reference_script(host: str, port: int) -> str:
    generated = json.dumps(
        {"host": host, "port": int(port)},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    fallback = json.dumps(
        {"host": DEFAULT_SERVER_HOST, "port": DEFAULT_SERVER_PORT},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    template = '''<script id="__SERVER_REFERENCE_SCRIPT_ID__">
(() => {
  const GENERATED = Object.freeze(__GENERATED__);
  const FALLBACK = Object.freeze(__FALLBACK__);
  const NAMES = Object.freeze(["host", "port"]);
  const current = () => new URLSearchParams(location.search);
  const value = (name) => current().get(name) ?? GENERATED[name] ?? FALLBACK[name] ?? null;

  const previousState = window.ontobdcUrlState || null;
  const previousDecorate = previousState && typeof previousState.decorate === "function"
    ? previousState.decorate.bind(previousState)
    : null;
  const previousValue = previousState && typeof previousState.value === "function"
    ? previousState.value.bind(previousState)
    : null;

  function decorate(href) {
    try {
      const inherited = previousDecorate ? previousDecorate(href) : href;
      const target = new URL(inherited, location.href);
      for (const name of NAMES) {
        if (target.searchParams.has(name)) continue;
        const carried = value(name);
        if (carried !== null && carried !== undefined && carried !== "") {
          target.searchParams.set(name, String(carried));
        }
      }
      return target.href;
    } catch {
      return href;
    }
  }

  function ensureReference() {
    const url = new URL(location.href);
    let changed = false;
    for (const name of NAMES) {
      if (url.searchParams.has(name)) continue;
      const generatedValue = GENERATED[name] ?? FALLBACK[name];
      if (generatedValue === null || generatedValue === undefined || generatedValue === "") continue;
      url.searchParams.set(name, String(generatedValue));
      changed = true;
    }
    if (!changed) return;
    try {
      history.replaceState(history.state, "", url.href);
    } catch {
      location.replace(url.href);
    }
  }

  if (previousState) {
    previousState.defaults = {
      ...(previousState.defaults || {}),
      host: String(GENERATED.host ?? FALLBACK.host),
      port: String(GENERATED.port ?? FALLBACK.port),
    };
    previousState.names = Array.from(new Set([...(previousState.names || []), ...NAMES]));
    previousState.value = (name) => NAMES.includes(name)
      ? value(name)
      : (previousValue ? previousValue(name) : current().get(name));
    previousState.decorate = decorate;
  }

  ensureReference();

  const serverReference = Object.freeze({
    generated: GENERATED,
    fallback: FALLBACK,
    names: [...NAMES],
    current,
    value,
    decorate,
    origin: () => `http://${value("host") || FALLBACK.host}:${value("port") || FALLBACK.port}`,
  });
  window.ontobdcServerReference = serverReference;

  const runtimeNames = [
    "OntoBDCWorkStreamViewRuntime",
    "OntoBDCGanttViewRuntime",
  ];

  function activeRuntime() {
    for (const name of runtimeNames) {
      const runtime = window[name];
      if (runtime) return runtime;
    }
    return null;
  }

  function pageT(runtime, key) {
    if (runtime && typeof runtime.t === "function") {
      try { return runtime.t(key); } catch {}
    }
    try {
      const node = document.getElementById("ontobdc-i18n");
      const catalog = node ? JSON.parse(node.textContent || "{}") : {};
      const locale = document.documentElement.lang || document.documentElement.dataset.language || "en";
      const table = catalog[locale] || catalog.en || {};
      return table[key] ?? key;
    } catch {
      return key;
    }
  }

  function setConnectLabel(runtime, key) {
    const text = pageT(runtime, key);
    if (runtime && typeof runtime.setConnectButtonLabel === "function") {
      runtime.setConnectButtonLabel(text);
      return;
    }
    const button = document.querySelector(".connect-btn");
    if (!button) return;
    const label = button.querySelector(".connect-btn__label");
    if (label) label.textContent = text;
    else button.textContent = text;
  }

  function setConnectionStatus(runtime, status) {
    if (runtime && typeof runtime.setConnectionStatus === "function") {
      runtime.setConnectionStatus(status);
      return;
    }
    const dot = document.querySelector(".connect-btn .connection-status, .connection-status");
    if (dot) dot.dataset.status = status;
  }

  function setProjectActionsConnected(runtime, connected) {
    if (runtime) {
      runtime.state = runtime.state || {};
      runtime.state.serverConnected = Boolean(connected);
      runtime.state.serverHost = String(serverReference.value("host") || FALLBACK.host);
      runtime.state.serverPort = Number(serverReference.value("port") || FALLBACK.port);
      if (typeof runtime.setProjectActionsDisabled === "function") {
        runtime.setProjectActionsDisabled(!connected);
      }
    }
  }

  async function probeServer() {
    const controller = typeof AbortController === "function" ? new AbortController() : null;
    const timer = controller
      ? window.setTimeout(() => controller.abort(), 1500)
      : null;
    try {
      await fetch(serverReference.origin() + "/", {
        method: "GET",
        mode: "no-cors",
        cache: "no-store",
        signal: controller ? controller.signal : undefined,
      });
      return true;
    } finally {
      if (timer !== null) window.clearTimeout(timer);
    }
  }

  async function connectContainer(silent) {
    const runtime = activeRuntime();
    const button = document.querySelector(".connect-btn");
    if (!button) return false;

    button.disabled = true;
    setConnectionStatus(runtime, "connecting");
    setConnectLabel(runtime, "connecting");
    try {
      await probeServer();
      setProjectActionsConnected(runtime, true);
      setConnectionStatus(runtime, "connected");
      setConnectLabel(runtime, "connectedFolder");
      return true;
    } catch (error) {
      setProjectActionsConnected(runtime, false);
      if (silent) {
        setConnectionStatus(runtime, "idle");
        setConnectLabel(runtime, "connectFolder");
      } else {
        setConnectionStatus(runtime, "error");
        setConnectLabel(runtime, "serverUnavailable");
        window.setTimeout(() => {
          if (runtime && runtime.state && runtime.state.serverConnected) return;
          setConnectionStatus(runtime, "idle");
          setConnectLabel(runtime, "connectFolder");
        }, 4000);
      }
      return false;
    } finally {
      button.disabled = false;
    }
  }

  // Connection now means "the OntoBDC server is reachable". Register on
  // window capture so this supersedes the legacy folder-picker click handler
  // without depending on the order in which the Page runtime files load.
  window.addEventListener("click", (event) => {
    const target = event.target instanceof Element
      ? event.target.closest(".connect-btn")
      : null;
    if (!target) return;
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    void connectContainer(false);
  }, true);

  function probeOnLoad() {
    if (!document.querySelector(".connect-btn")) return;
    void connectContainer(true);
  }

  if (document.readyState === "complete") {
    window.setTimeout(probeOnLoad, 0);
  } else {
    window.addEventListener("load", probeOnLoad, { once: true });
  }

  window.ontobdcConnectContainer = connectContainer;
})();
</script>'''
    return (
        template
        .replace("__SERVER_REFERENCE_SCRIPT_ID__", SERVER_REFERENCE_SCRIPT_ID)
        .replace("__GENERATED__", generated)
        .replace("__FALLBACK__", fallback)
    )


def _embed_server_reference(document: str, host: str, port: int) -> str:
    script = _server_reference_script(host, port)
    if _SERVER_REFERENCE_SCRIPT_RE.search(document):
        return _SERVER_REFERENCE_SCRIPT_RE.sub(lambda _: script, document, count=1)
    closing_head = "</head>"
    if closing_head not in document:
        raise ValueError("Generated HTML is missing </head>.")
    return document.replace(closing_head, f"  {script}\n{closing_head}", 1)


class ServerLauncherGeneratedCapability(TransformationCapability):
    """Generate the Windows launcher and publish the server reference.

    A generated random high port is stable for the container: reruns reuse
    the port already written to ``server.cmd`` unless the caller explicitly
    supplied ``server_port``. The exact same host/port pair is embedded into
    index.html and every generated HTML page, and internal URL decoration
    carries ``host`` and ``port`` between those pages. Runtime query-string
    values win; the browser-only fallback is always 127.0.0.1:8080.
    """

    METADATA = CapabilityMetadata(
        id=(
            "org.ontobdc.view.plugin.capability.transformation.target."
            "server_launcher_generated"
        ),
        version="1.0.0",
        name="Server Launcher Generated",
        description=(
            "Generate server.cmd and publish one shared host/port reference "
            "into every generated HTML page."
        ),
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=[
            "view",
            "surface",
            "server",
            "launcher",
            "windows",
            "cmd",
            "host",
            "port",
            "transformation",
        ],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {
                "en": (
                    "The Windows server launcher and shared HTML server "
                    "reference were generated."
                ),
            },
            "debug_entry": {
                "en": (
                    "Generating server.cmd, choosing the server reference, "
                    "and publishing it into generated HTML pages."
                ),
            },
        },
    )

    def __init__(self) -> None:
        self._surface = SurfaceTransformationAdapter()

    def label(self, lang: str = "en") -> str:
        return SurfaceGenerationProcessState.SERVER_LAUNCHER_GENERATED.label(lang)

    def description(self, lang: str = "en") -> str:
        return SurfaceGenerationProcessState.SERVER_LAUNCHER_GENERATED.description(lang)

    def check(self, context: CliContextPort) -> bool:
        return self._surface.check(context, check_server_launcher_generated)

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        surface_path = self._surface.path(context)
        launcher_path = surface_path.parent / SERVER_LAUNCHER_FILENAME
        host, port = _resolve_server_reference(context, launcher_path)

        _atomic_write_text(
            launcher_path,
            expected_launcher_text(host, port),
        )

        html_paths = list(generated_html_paths(surface_path))
        written_html_paths = []
        for html_path in html_paths:
            document = html_path.read_text(encoding="utf-8")
            document = _embed_server_reference(document, host, port)
            if html_path.resolve() == surface_path.resolve():
                document = set_state_marker(
                    document,
                    "server_launcher_generated",
                )
            _atomic_write_text(html_path, document)
            written_html_paths.append(str(html_path))

        context.set_parameter_value("surface_path", str(surface_path))
        self._surface.require_check(
            context,
            check_server_launcher_generated,
            "server_launcher_generated",
        )

        return {
            "resulting_state": (
                SurfaceGenerationProcessState.SERVER_LAUNCHER_GENERATED
            ),
            "launcher_path": str(launcher_path),
            "launcher_file": SERVER_LAUNCHER_FILENAME,
            "host": host,
            "port": port,
            "html_paths": written_html_paths,
        }

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)

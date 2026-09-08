"""Browser (Pyodide) Python runtime for the dDock Web presentation.

``ontobdc-web-dock`` receives Component Events raised by the Web
presentation and runs, in Python, the semantic decision of *event
promotion*: it reads ``view:promotesTo`` from the presentation-event
ontology and answers with every Shared Event a Component Event promotes
to.

It adds one new plugin type -- the **Listener** -- following OntoBDC's
existing plugin, statechart and ontology conventions, but implemented
against nothing but the standard library and ``rdflib`` so it installs
and runs inside Pyodide.
"""

from ontobdc_web_dock.bridge import WebDock, bootstrap, is_ready, promote

__version__: str = "0.1.0"

__all__ = ["WebDock", "bootstrap", "promote", "is_ready", "__version__"]

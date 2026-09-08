from ontobdc.cli.domain.port.machine import CliHealthProcessStatePort


class CliHealthProcessState(CliHealthProcessStatePort):
    """States of the ``ontobdc health`` system-health verification process.

    A linear pipeline: ``UNDEFINED`` is the entry point, each intermediate
    state runs one bootstrap capability (repair + validate), and
    ``BOOTSTRAP_HEALTHY`` is the verified end state once every capability
    has been executed. Further health dimensions (view runtime, NLP model,
    ...) get their own states before ``BOOTSTRAP_HEALTHY`` as they are
    added.
    """

    UNDEFINED = "__undefined__"
    ONTOBDC_DIRECTORY_READY = "__ontobdc_directory_ready__"
    ENGINE_READY = "__engine_ready__"
    STORAGE_INDEX_HEALTHY = "__storage_index_healthy__"
    EXECUTION_CONTEXT_HEALTHY = "__execution_context_healthy__"
    CONFIG_ADAPTER_READY = "__config_adapter_ready__"
    BOOTSTRAP_HEALTHY = "__bootstrap_healthy__"

    def label(self, lang: str = "en") -> str:
        labels = {
            "en": {
                self.UNDEFINED: "Undefined",
                self.ONTOBDC_DIRECTORY_READY: "OntoBDC Directory Ready",
                self.ENGINE_READY: "Engine Ready",
                self.STORAGE_INDEX_HEALTHY: "Storage Index Healthy",
                self.EXECUTION_CONTEXT_HEALTHY: "Execution Context Healthy",
                self.CONFIG_ADAPTER_READY: "Config Adapter Ready",
                self.BOOTSTRAP_HEALTHY: "Bootstrap Healthy",
            },
            "pt-br": {
                self.UNDEFINED: "Indefinido",
                self.ONTOBDC_DIRECTORY_READY: "Diretorio OntoBDC Pronto",
                self.ENGINE_READY: "Engine Pronto",
                self.STORAGE_INDEX_HEALTHY: "Indice de Storage Saudavel",
                self.EXECUTION_CONTEXT_HEALTHY: (
                    "Contexto de Execucao Saudavel"
                ),
                self.CONFIG_ADAPTER_READY: "Adapter de Config Pronto",
                self.BOOTSTRAP_HEALTHY: "Bootstrap Saudavel",
            },
        }
        return labels.get(lang, labels["en"]).get(self, self.value)

    def description(self, lang: str = "en") -> str:
        descriptions = {
            "en": {
                self.UNDEFINED: (
                    "Initial state before any health check has run."
                ),
                self.ONTOBDC_DIRECTORY_READY: (
                    "The .__ontobdc__ directory exists in the target path."
                ),
                self.ENGINE_READY: (
                    "The engine entry is present and valid in the "
                    "bootstrap configuration."
                ),
                self.STORAGE_INDEX_HEALTHY: (
                    "storage.ttl exists and conforms to the bootstrap "
                    "checks."
                ),
                self.EXECUTION_CONTEXT_HEALTHY: (
                    "context.ttl exists and conforms to the bootstrap "
                    "checks."
                ),
                self.CONFIG_ADAPTER_READY: (
                    "config.yaml exists and conforms to the bootstrap "
                    "config contract."
                ),
                self.BOOTSTRAP_HEALTHY: (
                    "Every CLI bootstrap capability has been executed "
                    "and the system is healthy."
                ),
            },
            "pt-br": {
                self.UNDEFINED: (
                    "Estado inicial antes da execucao de qualquer "
                    "verificacao de saude."
                ),
                self.ONTOBDC_DIRECTORY_READY: (
                    "O diretorio .__ontobdc__ existe no caminho alvo."
                ),
                self.ENGINE_READY: (
                    "A entrada de engine esta presente e valida na "
                    "configuracao de bootstrap."
                ),
                self.STORAGE_INDEX_HEALTHY: (
                    "O storage.ttl existe e esta conforme os checks de "
                    "bootstrap."
                ),
                self.EXECUTION_CONTEXT_HEALTHY: (
                    "O context.ttl existe e esta conforme os checks de "
                    "bootstrap."
                ),
                self.CONFIG_ADAPTER_READY: (
                    "O config.yaml existe e esta conforme o contrato de "
                    "bootstrap de config."
                ),
                self.BOOTSTRAP_HEALTHY: (
                    "Todas as capabilities de bootstrap da CLI foram "
                    "executadas e o sistema esta saudavel."
                ),
            },
        }
        return descriptions.get(lang, descriptions["en"]).get(self, "")

    @staticmethod
    def get_state(state: str) -> "CliHealthProcessState":
        return getattr(CliHealthProcessState, state.upper())

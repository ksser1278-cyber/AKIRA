# src/akira_engine/corpus_intelligence/hooks/__init__.py

from .mod import (
    build_hook_bank_index,
    generate_hook_blueprint,
)
from .schema import (
    HookGrammar,
    HookGrammarBank,
    RhymePattern,
)
from .analyzer import (
    MoraCounter,
    RhymeAnalyzer,
    RepetitionMiner,
)

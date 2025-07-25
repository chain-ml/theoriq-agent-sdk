from .command_items import UnknownCommandData
from .dialog import *
from .block import *

# Import all items from their respective logical files
from .code_items import CodeData, CodeBlock
from .data_items import DataItem, DataBlock
from .error_items import ErrorData, ErrorBlock
from .metrics_items import MetricItem, MetricsData, MetricsBlock
from .router_items import RouterItem, RouterData, RouterBlock
from .suggestions_items import SuggestionItem, SuggestionsData, SuggestionsBlock
from .text_items import TextData, TextBlock
from .web3_items import Web3ProposedTxData, Web3ProposedTxBlock, Web3SignedTxData, Web3SignedTxBlock

# Re-export all classes for backward compatibility
__all__ = [
    # BlockBase
    "BlockBase",
    "UnknownBlock",
    # Code items
    "CodeData",
    "CodeBlock",
    # Command items
    "CommandBlock",
    "UnknownCommandData",
    # Data items
    "DataItem",
    "DataBlock",
    # Dialog items
    "Dialog",
    "DialogItem",
    # Error items
    "ErrorData",
    "ErrorBlock",
    # Metrics items
    "MetricItem",
    "MetricsData",
    "MetricsBlock",
    # Router items
    "RouterItem",
    "RouterData",
    "RouterBlock",
    # Suggestions items
    "SuggestionItem",
    "SuggestionsData",
    "SuggestionsBlock",
    # Text items
    "TextData",
    "TextBlock",
    # Web3 items
    "Web3ProposedTxData",
    "Web3ProposedTxBlock",
    "Web3SignedTxData",
    "Web3SignedTxBlock",
]

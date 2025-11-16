"""Pre-defined tree-sitter queries for common Python patterns.

These queries provide convenient patterns for matching common Python
constructs. They will be used extensively in CORE-414 for keyword translation.
"""

# Query for all function definitions
# Captures: @function (the full function_definition node),
#           @function_name (the identifier node for the function name),
#           @params (the parameters node)
# Validation: Matches both regular and async function definitions
FUNCTION_DEFINITIONS = """
(function_definition
  name: (identifier) @function_name
  parameters: (parameters) @params
) @function
"""

# Query for all class definitions
# Captures: @class (the full class_definition node),
#           @class_name (the identifier node for the class name)
# Validation: Matches class definitions with or without inheritance
CLASS_DEFINITIONS = """
(class_definition
  name: (identifier) @class_name
) @class
"""

# Query for all Python keywords (for translation in CORE-414)
# Captures: @keyword (each keyword token individually)
# Validation: Uses tree-sitter's string literal matching to identify exact keywords
# Note: True, False, None are keyword constants in Python, not just identifiers.
#       This pattern ensures we match them as keywords, not as variable names.
#       The query deliberately uses exact string matching [literals] instead of
#       named node types, which is tree-sitter's recommended pattern for keywords.
# TODO: Consider generating this dynamically from legesher_i18n.scripts.translate.term_classifier
#       Currently missing Python 3.11+ (except*) and 3.12+ (type) keywords
KEYWORDS_QUERY = """
[
  "def" "class" "if" "elif" "else"
  "for" "while" "return" "yield"
  "import" "from" "as" "pass"
  "break" "continue" "raise" "try"
  "except" "finally" "with" "assert"
  "lambda" "and" "or" "not" "is"
  "in" "True" "False" "None"
  "async" "await" "global" "nonlocal"
  "del" "match" "case"
] @keyword
"""

# Query for import statements
# Captures: @import (import ... statements),
#           @import_from (from ... import statements)
# Validation: Matches both "import x" and "from x import y" forms
IMPORT_STATEMENTS = """
[
  (import_statement) @import
  (import_from_statement) @import_from
]
"""

# Query for all control flow structures
# Captures: @if, @for, @while, @try, @with, @match (individual control flow nodes),
#           @control_flow (parent aggregate for any control flow statement)
# Validation: Matches all Python control flow statements (if, for, while, try, with, match)
#             Note: match_statement requires Python 3.10+
CONTROL_FLOW = """
[
  (if_statement) @if
  (for_statement) @for
  (while_statement) @while
  (try_statement) @try
  (with_statement) @with
  (match_statement) @match
] @control_flow
"""

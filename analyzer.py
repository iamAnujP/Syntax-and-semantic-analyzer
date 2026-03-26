from lexical  import lexical_analyze
from syntax   import syntax_analyze
from semantic import semantic_analyze


def analyze_code(code):
    tokens, lex_errors = lexical_analyze(code)
    syntax_errors      = syntax_analyze(tokens)   if not lex_errors    else []
    semantic_errors    = semantic_analyze(tokens)  if not syntax_errors else []

    all_errors = lex_errors + syntax_errors + semantic_errors
    has_errors = bool(all_errors)
    count      = len(all_errors)
    summary    = (f"{count} error{'s' if count != 1 else ''} found"
                  if has_errors else "No errors found! Code looks clean.")

    return {
        "tokens":     tokens,
        "errors":     all_errors,
        "has_errors": has_errors,
        "summary":    summary,
    }
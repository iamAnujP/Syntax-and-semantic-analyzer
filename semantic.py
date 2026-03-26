PURE_TYPES  = {"int","char","float","double","void","long","short","unsigned","signed"}
QUALIFIERS  = {"const","static","extern","auto","register","volatile","inline"}
INT_TYPES   = {"int","short","long","unsigned","signed","char"}
FLOAT_TYPES = {"float","double"}
C_KEYWORDS  = {
    "auto","break","case","char","const","continue","default","do",
    "double","else","enum","extern","float","for","goto","if","inline",
    "int","long","register","return","short","signed","sizeof","static",
    "struct","switch","typedef","union","unsigned","void","volatile","while"
}
BUILTINS = {
    "printf","scanf","malloc","free","exit","NULL","EOF","stdin","stdout",
    "stderr","sizeof","strlen","strcpy","strcat","strcmp","atoi","atof",
    "abs","pow","sqrt","rand","srand","time","fopen","fclose","fprintf",
    "fscanf","fgets","fputs","assert","memcpy","memset","memmove","main"
}


def semantic_analyze(tokens):
    errors = []
    scope_stack = [{}]

    def current_scope():
        return scope_stack[-1]

    def lookup(name):
        for scope in reversed(scope_stack):
            if name in scope:
                return scope[name]
        return None

    def declare(name, entry):
        scope = current_scope()
        if name in scope and len(scope_stack) > 1:
            errors.append({"phase":"semantic","line":entry["line"],"column":entry["column"],
                           "message":f"Duplicate declaration of '{name}' — already declared at line {scope[name]['line']}",
                           "token":name})
        else:
            scope[name] = entry

    i = 0
    while i < len(tokens):
        tok  = tokens[i]
        nxt  = tokens[i+1] if i+1 < len(tokens) else None
        prev = tokens[i-1] if i > 0 else None

        # Scope management
        if tok["value"] == '{':
            scope_stack.append({})
            i += 1; continue
        if tok["value"] == '}':
            if len(scope_stack) > 1:
                scope_stack.pop()
            i += 1; continue

        # Variable / function declaration
        is_qual  = tok["value"] in QUALIFIERS
        type_tok = tokens[i+1] if is_qual and i+1 < len(tokens) else tok
        off      = 1 if is_qual else 0

        if type_tok and type_tok["value"] in PURE_TYPES:
            name_idx = i + 1 + off
            name_tok = tokens[name_idx] if name_idx < len(tokens) else None

            if name_tok and name_tok["type"] == "IDENTIFIER":
                after_idx = i + 2 + off
                after     = tokens[after_idx] if after_idx < len(tokens) else None

                if after and after["value"] == '(':
                    # Function declaration — register and parse parameters
                    declare(name_tok["value"], {
                        "name": name_tok["value"], "type": type_tok["value"],
                        "line": name_tok["line"],  "column": name_tok["column"], "kind": "function"
                    })
                    j = i + 3 + off
                    while j < len(tokens) and tokens[j]["value"] != ')':
                        if tokens[j]["value"] in PURE_TYPES and j+1 < len(tokens) and tokens[j+1]["type"] == "IDENTIFIER":
                            declare(tokens[j+1]["value"], {
                                "name": tokens[j+1]["value"], "type": tokens[j]["value"],
                                "line": tokens[j+1]["line"], "column": tokens[j+1]["column"], "kind": "parameter"
                            })
                            j += 2
                        else:
                            j += 1
                        if j < len(tokens) and tokens[j]["value"] == ',':
                            j += 1
                    i = j + 1; continue
                else:
                    # Variable declaration
                    declare(name_tok["value"], {
                        "name": name_tok["value"], "type": type_tok["value"],
                        "line": name_tok["line"],  "column": name_tok["column"], "kind": "variable"
                    })
            i += 1; continue

        # Identifier usage — check declared
        if tok["type"] == "IDENTIFIER":
            is_decl = prev and (
                prev["value"] in PURE_TYPES or
                prev["value"] in QUALIFIERS or
                prev["value"] == ','
            )
            if not is_decl and tok["value"] not in BUILTINS and tok["value"] not in C_KEYWORDS:
                if not lookup(tok["value"]):
                    msg = (f"Call to undeclared function '{tok['value']}'"
                           if nxt and nxt["value"] == '('
                           else f"Use of undeclared identifier '{tok['value']}'")
                    errors.append({"phase":"semantic","line":tok["line"],"column":tok["column"],
                                   "message":msg,"token":tok["value"]})

        # Assignment type-checking
        if tok["value"] == '=':
            lhs = tokens[i-1] if i > 0 else None
            rhs = tokens[i+1] if i+1 < len(tokens) else None
            if lhs and rhs:
                entry = lookup(lhs["value"])
                if entry:
                    if entry["type"] in INT_TYPES and rhs["type"] == "FLOAT_LITERAL":
                        errors.append({"phase":"semantic","line":rhs["line"],"column":rhs["column"],
                                       "message":f"Type mismatch: assigning float '{rhs['value']}' to integer '{lhs['value']}' (data loss)",
                                       "token":rhs["value"]})
                    if entry["type"] in (INT_TYPES | FLOAT_TYPES) and rhs["type"] == "STRING_LITERAL":
                        errors.append({"phase":"semantic","line":rhs["line"],"column":rhs["column"],
                                       "message":f"Type mismatch: cannot assign string to numeric variable '{lhs['value']}'",
                                       "token":rhs["value"]})

        i += 1

    return errors
C_TYPES = {
    "int","char","float","double","void","long","short",
    "unsigned","signed","const","static","extern","auto"
}


def syntax_analyze(tokens):
    errors = []
    braces, parens, brackets = [], [], []

    # Bracket matching pass
    for tok in tokens:
        if tok["type"] != "PUNCTUATION":
            continue
        if tok["value"] == '{':
            braces.append(tok)
        elif tok["value"] == '}':
            if not braces:
                errors.append({"phase":"syntax","line":tok["line"],"column":tok["column"],
                               "message":"Unexpected '}' — no matching '{'","token":"}"})
            else:
                braces.pop()
        if tok["value"] == '(':
            parens.append(tok)
        elif tok["value"] == ')':
            if not parens:
                errors.append({"phase":"syntax","line":tok["line"],"column":tok["column"],
                               "message":"Unexpected ')' — no matching '('","token":")"})
            else:
                parens.pop()
        if tok["value"] == '[':
            brackets.append(tok)
        elif tok["value"] == ']':
            if not brackets:
                errors.append({"phase":"syntax","line":tok["line"],"column":tok["column"],
                               "message":"Unexpected ']' — no matching '['","token":"]"})
            else:
                brackets.pop()

    # Report unclosed brackets
    for b  in braces:
        errors.append({"phase":"syntax","line":b["line"],"column":b["column"],
                       "message":"Unclosed '{' — missing matching '}'","token":"{"})
    for p  in parens:
        errors.append({"phase":"syntax","line":p["line"],"column":p["column"],
                       "message":"Unclosed '(' — missing matching ')'","token":"("})
    for br in brackets:
        errors.append({"phase":"syntax","line":br["line"],"column":br["column"],
                       "message":"Unclosed '[' — missing matching ']'","token":"["})

    # Statement-level checks
    for i, tok in enumerate(tokens):
        nxt  = tokens[i+1] if i+1 < len(tokens) else None
        prev = tokens[i-1] if i > 0 else None

        # if / while / for must be followed by (
        if tok["value"] in ("if", "while", "for"):
            if not nxt or nxt["value"] != '(':
                errors.append({"phase":"syntax","line":tok["line"],"column":tok["column"],
                               "message":f"'{tok['value']}' must be followed by '('","token":tok["value"]})

        # return must end with ;
        if tok["value"] == "return":
            j = i + 1
            while j < len(tokens) and tokens[j]["value"] not in (";", "{", "}"):
                j += 1
            if j >= len(tokens) or tokens[j]["value"] != ";":
                errors.append({"phase":"syntax","line":tok["line"],"column":tok["column"],
                               "message":"Missing semicolon after 'return' statement","token":"return"})

        # Missing semicolon between consecutive statements
        if tok["type"] in ("IDENTIFIER", "INTEGER_LITERAL", "FLOAT_LITERAL") and \
           nxt and nxt["value"] in C_TYPES and tok["line"] < nxt["line"] and \
           (not prev or prev["value"] not in (")", "{", "}", ";", ",")):
            errors.append({"phase":"syntax","line":tok["line"],"column":tok["column"] + len(tok["value"]),
                           "message":f"Missing semicolon after '{tok['value']}'","token":tok["value"]})

    return errors
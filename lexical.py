C_KEYWORDS = {
    "auto","break","case","char","const","continue","default","do",
    "double","else","enum","extern","float","for","goto","if","inline",
    "int","long","register","return","short","signed","sizeof","static",
    "struct","switch","typedef","union","unsigned","void","volatile","while"
}
TWO_OPS = {"++","--","+=","-=","*=","/=","%=","==","!=","<=",">=","&&","||","<<",">>","->"}
ONE_OPS = set("+-*/%=<>!&|^~.")


def lexical_analyze(code):
    tokens, errors = [], []
    i, line, line_start = 0, 1, 0

    while i < len(code):
        col = i - line_start + 1
        ch  = code[i]

        if ch == '\n':
            line += 1; line_start = i + 1; i += 1; continue

        if ch.isspace():
            i += 1; continue

        # Single-line comment
        if code[i:i+2] == '//':
            while i < len(code) and code[i] != '\n':
                i += 1
            continue

        # Block comment
        if code[i:i+2] == '/*':
            i += 2
            while i < len(code) - 1 and code[i:i+2] != '*/':
                if code[i] == '\n':
                    line += 1
                    line_start = i + 1
                i += 1
            if code[i:i+2] == '*/':
                i += 2
            else:
                errors.append({"phase":"lexical","line":line,"column":col,"message":"Unterminated block comment","token":"/*"})
            continue

        # String literal
        if ch == '"':
            s = '"'; i += 1; closed = False
            while i < len(code):
                if code[i] == '\\':
                    s += code[i] + (code[i+1] if i+1 < len(code) else '')
                    i += 2; continue
                if code[i] == '"':
                    s += '"'; i += 1; closed = True; break
                if code[i] == '\n':
                    break
                s += code[i]; i += 1
            if not closed:
                errors.append({"phase":"lexical","line":line,"column":col,"message":"Unterminated string literal","token":s})
            else:
                tokens.append({"type":"STRING_LITERAL","value":s,"line":line,"column":col})
            continue

        # Char literal
        if ch == "'":
            c = "'"; i += 1; closed = False
            while i < len(code):
                if code[i] == '\\':
                    c += code[i] + (code[i+1] if i+1 < len(code) else '')
                    i += 2; continue
                if code[i] == "'":
                    c += "'"; i += 1; closed = True; break
                if code[i] == '\n':
                    break
                c += code[i]; i += 1
            if not closed:
                errors.append({"phase":"lexical","line":line,"column":col,"message":"Unterminated character literal","token":c})
            else:
                tokens.append({"type":"CHAR_LITERAL","value":c,"line":line,"column":col})
            continue

        # Number literal
        if ch.isdigit() or (ch == '.' and i+1 < len(code) and code[i+1].isdigit()):
            num = ''; is_float = False
            while i < len(code) and (code[i].isdigit() or code[i] in '._xXabcdefABCDEF'):
                if code[i] == '.':
                    is_float = True
                num += code[i]; i += 1
            if i < len(code) and code[i] in 'fF':
                num += code[i]; i += 1; is_float = True
            tokens.append({"type":"FLOAT_LITERAL" if is_float else "INTEGER_LITERAL","value":num,"line":line,"column":col})
            continue

        # Identifier or keyword
        if ch.isalpha() or ch == '_':
            ident = ''
            while i < len(code) and (code[i].isalnum() or code[i] == '_'):
                ident += code[i]; i += 1
            tok_type = "KEYWORD" if ident in C_KEYWORDS else "IDENTIFIER"
            tokens.append({"type":tok_type,"value":ident,"line":line,"column":col})
            continue

        # Two-char operators
        two = code[i:i+2]
        if two in TWO_OPS:
            tokens.append({"type":"OPERATOR","value":two,"line":line,"column":col})
            i += 2; continue

        # One-char operators
        if ch in ONE_OPS:
            tokens.append({"type":"OPERATOR","value":ch,"line":line,"column":col})
            i += 1; continue

        # Punctuation
        if ch in '{}()[];,#':
            tokens.append({"type":"PUNCTUATION","value":ch,"line":line,"column":col})
            i += 1; continue

        # Unknown
        errors.append({"phase":"lexical","line":line,"column":col,"message":f"Unrecognized character '{ch}'","token":ch})
        i += 1

    return tokens, errors
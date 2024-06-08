"""Parse a string that contains climb log entries.

An example of a log entry string is below:

 Armed, Obi (AS); Jedi Mind Tricks * 2 (TA working moves).

A log entry string is a series of climb entries separated by semicolons, commas or
periods. Each climb entry has a climb name and possibly a comment in parentheses.

The output should be a list of dictionaries, one for each climb entry. Each dictionary
should have a "name" key and a "comment" key.

For the example above, the output would be:

[
    {"name": "Armed", "comment": ""},
    {"name": "Obi", "comment": "(AS)"},
    {"name": "Jedi Mind Tricks * 2", "comment": "TA working moves"}
]

Use the PLY package to parse the string by defining the tokens and grammar rules.
"""
import ply.lex as lex
import ply.yacc as yacc

# Token definitions for the lexer
tokens = (
    'NAME',
    'COMMENT',
#    'SEPARATOR'
)

# Regular expression rules for tokens
def t_COMMENT(t):
    r'\(.*?\)'
    return t

def t_NAME(t):
    r'[^,;.()]+'
    t.value = t.value.strip()
    return t

def t_SEPARATOR(t):
    r'[;,\.]+'
    pass  # Ignore separators

# Ignored characters (spaces and tabs)
t_ignore = ' \t'

# Error handling rule
def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

# Grammar rules for the parser
def p_log(p):
    '''log : entry_list'''
    p[0] = p[1]

def p_entry_list(p):
    '''entry_list : entry_list entry
                  | entry'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_entry(p):
    '''entry : NAME opt_comment
             | COMMENT'''
    if len(p) == 3:
        p[0] = {"name": p[1], "comment": p[2][1:-1]}  # Remove parentheses
    else:
        p[0] = {"name": "", "comment": p[1][1:-1]}  # Remove parentheses

def p_opt_comment(p):
    '''opt_comment : COMMENT
                   | empty'''
    if len(p) == 2 and p[1] is not None:
        p[0] = p[1]
    else:
        p[0] = ""

def p_empty(p):
    'empty :'
    pass

# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input!")

# Build the parser
parser = yacc.yacc()

# Example usage
log_entry = "Armed, Obi (AS); Jedi Mind Tricks * 2 (TA working moves)."
parsed_log = parser.parse(log_entry)

print(parsed_log)

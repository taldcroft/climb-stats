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
    "SEPARATOR",
)

# Regular expression rules for tokens
def t_COMMENT(t):
    r'\([^)]*\)'
    t.value = t.value[1:-1]  # Remove parentheses
    return t


def t_NAME(t):
    r'[^!,;.()]+'
    t.value = t.value.strip()
    return t

def t_SEPARATOR(t):
    r'[!;,\.]+'
    return t

# Ignored characters (spaces and tabs)
t_ignore = ' \t'

# Error handling rule
def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    print(t.lexer.lexdata)
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

# Grammar rules for the parser
def p_log(p):
    '''log : entry_list
           | entry_list SEPARATOR
    '''
    p[0] = p[1]

def p_entry_list(p):
    '''entry_list : entry_list SEPARATOR entry
                  | entry'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_entry(p):
    '''entry : NAME
             | NAME COMMENT'''
    if len(p) == 3:
        p[0] = {"name": p[1], "comment": p[2]}  # Remove parentheses
    else:
        p[0] = {"name": p[1], "comment": ""}

# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input!")
    # Print the entire input string
    raise ValueError(p)

# Build the parser
parser = yacc.yacc()

# # Example usage
# log_entry = "Armed, Obi (AS); lcimb (blah), Jedi Mind Tricks * 2 (TA working moves)."
# #log_entry = "Armed,, Obi *2 (AS)"
# parsed_log = parser.parse(log_entry)

# print(parsed_log)

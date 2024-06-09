from lark import Lark, Transformer

# Grammar definition for Lark
grammar = r"""
    start: entry (SEPARATOR entry)*

    entry: NAME COMMENT -> entry_with_comment
         | NAME -> name_only

    NAME: /[^,()]+/
    COMMENT: /\([^)]*\)/
    SEPARATOR: /,+/

    %ignore " "
    %ignore "\t"
"""

# Transformer to convert parse tree to desired output format
class ClimbingLogTransformer(Transformer):
    def entry_with_comment(self, items):
        name, comment = items
        return {"name": name.strip(), "comment": comment[1:-1]}  # Remove parentheses

    def name_only(self, items):
        name, = items
        return {"name": name.strip(), "comment": ""}

    def SEPARATOR(self, items):
        return

    def start(self, items):
        return items

# Initialize Lark parser
parser = Lark(grammar, start='start')

# Example usage
log_entry = "Armed, Obi (AS), Jedi Mind Tricks * 2 (TA working moves)"
parsed_log = parser.parse(log_entry)

print(parsed_log.pretty())
print()
print(ClimbingLogTransformer().transform(parsed_log))

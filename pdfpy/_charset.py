"""
MIT License

Copyright (c) 2019 Cristian Di Pietrantonio (cristiandipietrantonio@gmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


# Defines a constant for each relevant character
LINE_FEED = ord('\n')
HORIZONTAL_TAB = ord('\t')
FORM_FEED = ord('\f')
BACKSPACE = ord('\b')
CARRIAGE_RETURN = ord('\r')
OPEN_PARENTHESIS = ord('(')
CLOSE_PARENTHESIS = ord(')')
OPEN_ANGLE_BRACKET = ord('<')
CLOSE_ANGLE_BRACKET = ord('>')
OPEN_SQUARE_BRACKET = ord('[')
CLOSE_SQUARE_BRACKET = ord(']')
FORWARD_SLASH = ord('/')
BACK_SLASH = ord("\\")
OPEN_CURLY_BRACKET = ord('{')
CLOSE_CURLY_BRAKET = ord('}')
PERCENTAGE = ord('%')
POINT = ord('.')
PLUS = ord('+')
MINUS = ord('-')
KEYWORD_REFERENCE = ord('R')
FREE_ENTRY_KEYWORD = ord('f')
INUSE_ENTRY_KEYWORD = ord('n')
CHARACTER_X = ord('x')
NUMBER_SIGN = ord('#')


# singletons are lexemes composed by only one character.
SINGLETONS = {
    OPEN_CURLY_BRACKET, CLOSE_CURLY_BRAKET, OPEN_SQUARE_BRACKET, CLOSE_SQUARE_BRACKET, INUSE_ENTRY_KEYWORD,
    FREE_ENTRY_KEYWORD, KEYWORD_REFERENCE
}

# the order is important here! For example, you don't want "n" to comes before "null", otherwise the
# latter will never be matched.
KEYWORDS = [
   b"<<", b">>", b"endobj", b"obj", b"trailer", b"xref", b"null", b"startxref", b"endstream"
]


is_digit = lambda x : x >= 48 and x < 58
is_hex_digit = lambda x: (x >= 48 and x < 58) or (x >= 65 and x < 71) or (x >= 97 and x < 103)


def hex_to_number(x):
    if x >= 48 and x < 58:
        return x - 48
    elif x >= 65 and x < 71:
        return x - 55
    elif x >= 97 and x < 103:
        return x - 87
    else:
        raise ValueError("'{}' is not a hexadecimal string.".format(chr(x)))


STRING_ESCAPE_SEQUENCES = {
    ord("n") : LINE_FEED,
    ord("r") : CARRIAGE_RETURN,
    ord("b") : BACKSPACE,
    ord("t") : HORIZONTAL_TAB,
    ord("f") : FORM_FEED
}


BLANKS = {0x00, 0x09, 0x0A, 0x0C, 0x0D, 0x20}
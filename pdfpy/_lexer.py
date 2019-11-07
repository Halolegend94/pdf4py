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


from collections import namedtuple
import logging
from binascii import unhexlify
from ._charset import *



class PDFLexicalError(Exception):
    """
    Lexical error
    """

# ------------------------------------------------------------------------------------
# Lexeme classes
# Here are defined all the classes used to represent a valid lexeme in the pdf language
# that cannot otherwise be represented with standard python types.
# ------------------------------------------------------------------------------------

PDFName = namedtuple("PDFName", ["value"])
PDFKeyword = namedtuple("PDFKeyword", ["value"])
PDFHexString = namedtuple("PDFHexString", ["value"])
PDFSingleton = namedtuple("PDFSingleton", ["value"])


class Seekable:

    def __init__(self, obj):
        if not(isinstance(obj, bytes) or isinstance(obj, bytearray)):
            raise ValueError("'obj' must be 'bytes' or 'bytearray' type.")
        self.__source = memoryview(obj)
        self.__pos = 0
        self.__len = len(obj)
    

    def read(self, n = 0):
        if self.__pos == self.__len:
            return b''
        if n == 1:
            val = [self.__source[self.__pos]]
        else:
            if n <= 0:
                n = self.__len
            val = self.__source[self.__pos : self.__pos + n]
            n = len(val)
        self.__pos += n
        return val
    


    def seek(self, off, whence):
        if whence == 0:
            self.__pos = off
        elif whence == 1:
            self.__pos += off
        else:
            self.__pos = self.__len + off
        
        if self.__pos < 0:
            self.__pos = 0
        if self.__pos > self.__len:
            self.__pos = self.__len
    

    def tell(self):
        return self.__pos



class Lexer:

    def __init__(self, source, contextSize = 200):
        """
        Creates a new instance of a PDF lexical analyzer associated to the given character 
        stream source.

        Parameters:
        -----------
        source : TextIOWrapper or Seekable object.
            The source from where characters are read. The object must implement the 
            read, tell and seek protocol typical of a file handle.
        
        """
        if isinstance(source, bytes) or isinstance(source, bytearray):
            self.__source = Seekable(source)
        else:
            self.__source = source
        cpos = self.__source.tell()
        self.__source.seek(0, 2)
        self.__length = self.__source.tell()
        self.__source.seek(cpos, 0)
        self.__current = self.__source.read(1)[0]
        self.__lexemesBuffer = list()
        self.__movesHistory = list()
        self.__contextSize = contextSize
        self.__ended = False
        self.__currentLexeme = None
    

    @property
    def current_lexeme(self):
        if self.__ended:
            raise StopIteration()
        return self.__currentLexeme
    

    def seekable_rfind(self, keyword : 'bytes'):
        revKeyword = bytes(reversed(keyword))
        buff = bytearray()
        count = 1
        while bytes(buff) != revKeyword:
            buff.clear()
            while count <= self.__length:
                self.__source.seek(self.__length - count, 0)
                c = self.__source.read(1)
                count += 1
                if c[0] not in [CARRIAGE_RETURN, LINE_FEED]:
                    buff.extend(c)
                else:
                    break
            if count > self.__length and c[0] not in [CARRIAGE_RETURN, LINE_FEED]:
                return -1
        pos = self.__source.tell()
        self.__advance()
        self.__next__()
        return pos


    def get_context(self):
        """
        Returns the bytes near the Lexer's current head position.

        Description
        -----------
        Given a context size of `C` bytes, and the current head position `P`, the 
        function returns the bytes sequence starting from the byte at position
        `max(P - C // 2, 0)` whose length is at most `C`.
        """
        # collect the context in which the error occurred
        # collect the context in which the error occurred
        errorPosition = self.__source.tell()
        contextSideSize = self.__contextSize // 2
        contextStart = errorPosition - contextSideSize
        if contextStart < 0:
            contextSideSize = contextSideSize + contextStart
            contextStart = 0
        self.__source.seek(contextStart, 0)
        context = self.__source.read(self.__contextSize)
        if isinstance(context, memoryview):
            context = bytes(context)
        # escaped occurrences occupy 2 spaces instead of one, when printed as bytes.
        escapedOccurrences = sum(context[:contextSideSize].count(x) for x in STRING_ESCAPE_SEQUENCES.values())
        errorRelativePosition = contextSideSize + escapedOccurrences + 1
        self.__source.seek(errorPosition, 0)
        return context, errorPosition, errorRelativePosition

        
    def __raise_lexer_error(self, msg):
        """
        Called when a lexical error is encountered during the input tokenization,
        for example when an unrecognised character is found.

        Description:
        ------------
        This function collects also the input sequence around the position where the error
        happened, enriching the original error message given as input, so that the exception
        carries a more informative error message for the user.

        Parameters:
        -----------
        msg : str
            A description of the lexical error.
        
        Raise:
        ------
        PDFLexicalError
        """
        # collect the context in which the error occurred
        context, errorPosition, relativeErrorPosition = self.get_context()
        finalMsg = "{}\n\nPosition {}, context:\n\t{}\n\t{}^".format(msg, errorPosition, context, " "*relativeErrorPosition)
        raise PDFLexicalError(finalMsg)


    def move_at_position(self, pos):
        previousLexeme = self.current_lexeme
        previousPosition = self.__source.tell()
        self.__movesHistory.append((previousLexeme, previousPosition))
        self.__source.seek(pos, 0)
        self.__advance()
        return self.__next__()


    def move_back(self):
        if len(self.__movesHistory) == 0:
            raise Exception("No move in history")
        prevLex, prevPos = self.__movesHistory.pop()
        self.__currentLexeme = prevLex
        self.__source.seek(prevPos - 1, 0)
        self.__advance()


    def __advance(self):
        if self.__ended:
            raise StopIteration()
        self.__current = self.__source.read(1)
        if self.__current == b'':
            self.__current = b' '[0]
            self.__ended = True
        else:
            self.__current = self.__current[0]
        

    def __read_chunk(self, size):
        if self.__ended:
            raise StopIteration()
        endPos = self.__source.tell() + size
        if endPos <= self.__length:
            data = self.__source.read(size)
            return data
        else:
            return None


    def __remove_blanks(self):
        while True:
            if self.__current in BLANKS:
                self.__advance()
            elif self.__current == PERCENTAGE: # comment starts
                while self.__current != LINE_FEED:
                    self.__advance()
                self.__advance()
            else:
                break


    def __peek(self, k = 1):
        k -= 1
        currentPos = self.__source.tell()
        if currentPos + k >= self.__length:
            return None
        else:
            self.__source.seek(k, 1)
            v = self.__source.read(1)
            self.__source.seek(currentPos, 0)
            return v[0]
    

    def __parse_string_literal(self):
        self.__advance()
        openParentheses = 1
        buffer = bytearray()
        while openParentheses > 0:
            if self.__current == OPEN_PARENTHESIS:
                openParentheses += 1
            elif self.__current == CLOSE_PARENTHESIS:
                openParentheses -= 1
            elif self.__current == BACK_SLASH:
                # parse special content (escaped sequence)
                self.__advance()
                if not is_digit(self.__current):
                    # then it must be one of the blanks like: \n, \r, \t etc..
                    buffer.append(STRING_ESCAPE_SEQUENCES.get(self.__current, self.__current))
                    self.__advance()
                    continue
                else:
                    # otherwise it is an octal number
                    digits = bytearray()
                    while is_digit(self.__current) and len(digits) < 3:
                        digits.append(self.__current)
                        self.__advance()
                    charCode = sum(int(x) << 3*(len(digits) -i - 1) for i, x in enumerate(digits.decode('ascii')))
                    buffer.append(charCode)
                    continue
            buffer.append(self.__current)
            self.__advance()
        buffer.pop()

        try:
            return buffer.decode(encoding='utf-8')
        except UnicodeDecodeError:
            return buffer.decode(encoding='cp1252')
    

    def __parse_hexadecimal_string(self):
        """
        Parse a hexadecimal digits sequence
        """
        self.__advance()
        buffer = bytearray()
        while True:
            if self.__current in BLANKS:
                self.__advance()
                continue
            if not is_hex_digit(self.__current):
                break
            buffer.append(self.__current)
            self.__advance()
        if self.__current != CLOSE_ANGLE_BRACKET:
            self.__raise_lexer_error("Expected '>' to end hexadecimal string.")
        self.__advance()
        return PDFHexString(buffer)

            

    def __parse_name(self):
        """
        Parse a PDF name token.
        """
        buffer = bytearray()
        self.__advance()
        while ord('!') <= self.__current and self.__current <= ord('~'):
            if self.__current == NUMBER_SIGN:
                self.__advance()
                try:
                    hexDigit1 = hex_to_number(self.__current)
                    self.__advance()
                    hexDigit2 = hex_to_number(self.__current)
                    hexNum = (hexDigit1 << 4) + hexDigit2
                    buffer.append(hexNum)
                except ValueError:
                    self.__raise_lexer_error("'{}' is not an hexadecimal digit.".format(self.__current))
            else:
                buffer.append(self.__current)
            self.__advance()
        return PDFName(buffer.decode('ascii'))


    def __parse_number(self):
        """
        Parse an integer or real value from the input stream.
        """
        buff = bytearray()
        if self.__current == PLUS or self.__current == MINUS:
            buff.append(self.__current)
            self.__advance()
        
        while is_digit(self.__current):
            buff.append(self.__current)
            self.__advance()
        
        if self.__current == POINT:
            buff.append(POINT)
            self.__advance()
        else:
            return int(buff.decode('utf-8'))
        
        while is_digit(self.__current):
            buff.append(self.__current)
            self.__advance()

        return float(buff.decode('utf-8'))

    
    def __parse_literal(self, lit):
        diff = False
        for i, l in enumerate(lit):
            p = self.__peek(i)
            if p != l:
                diff = True
                break
        if not diff:
            # ok, we matched it
            for i in range(len(lit)):
                self.__advance()
            return True
        else:
            return False


    def __match_keyword(self):
        for k in KEYWORDS:
            if self.__parse_literal(k):
                self.__currentLexeme = PDFKeyword(k)
                return True
        else:
            return False


    def put_back(self, current, lexeme):
        self.__lexemesBuffer.append(lexeme)
        self.__currentLexeme = current


    def __iter__(self):
        """
        Makes a Lexer Analyzer instance an iterable object.

        Usually this is a bad idea, but here can be ok.
        """
        return self
    

    def __next__(self):
        """
        Returns the next lexeme in the input bytes sequence. Also, set current_lexeme property 
        to the returned value.

        Description
        -----------
        The Lexical Analyzer is an iterator over the sequence of lexemes present in the input
        bytes sequence. For this reason the user can use the built-in `next` function to get
        the next lexeme in the sequence. When the end of the bytes sequence is reached,
        StopIteration is raised.


        Returns:
        --------
        An object that can be instance of: str, int, float, bool, function, PDFName, PDFKeyword,
        PDFHexString, PDFSingleton.


        Raises:
        -------
        StopIteration on End-Of-Sequence, PDFLexicalError when an unexpected input byte is
        encountered.
        """

        if len(self.__lexemesBuffer) > 0:
            self.__currentLexeme = self.__lexemesBuffer.pop()
            return self.__currentLexeme

        self.__remove_blanks()
        # now try to parse lexical entities
        if self.__current == OPEN_PARENTHESIS:
            self.__currentLexeme = self.__parse_string_literal()
    
        elif self.__current == OPEN_ANGLE_BRACKET and self.__peek() != OPEN_ANGLE_BRACKET:
            # If the next bytes had been another OPEN_ANGLE_BRACKET then we would have gotten
            # a "dictionary starts here" mark 
            self.__currentLexeme = self.__parse_hexadecimal_string()

        elif self.__current == FORWARD_SLASH:
            self.__currentLexeme = self.__parse_name()
        
        elif is_digit(self.__current) or self.__current in [PLUS, MINUS, POINT]:
            self.__currentLexeme = self.__parse_number()

        elif self.__parse_literal(b"true"):
            self.__currentLexeme = True
        
        elif self.__parse_literal(b"false"):
            self.__currentLexeme = False
        
        elif self.__parse_literal(b"stream"):
            # check whether there are the optional \r\n
            if self.__current == CARRIAGE_RETURN:
                self.__advance()
                if self.__current != LINE_FEED:
                    self.__raise_lexer_error("Carriage return not followed by a line feed after 'stream' keyword.")
            
            streamPos = self.__source.tell()
            # build a closure to read the stream later
            def read_stream(length):
                oldPos = self.__source.tell()
                self.__source.seek(streamPos, 0)
                data = self.__source.read(length)
                self.__advance()
                # now need to match endstream, or line feed + endstream
                if self.__current == LINE_FEED:
                    self.__advance()
                self.__source.seek(oldPos, 0)
                return data
            self.__currentLexeme = read_stream

        elif self.__match_keyword():
            # self.__currentLexeme is set inside the called function
            pass
        
        elif self.__current in SINGLETONS:
            self.__currentLexeme = PDFSingleton(self.__current)
            self.__advance()
        else:
            # If the input bytes sequence prefix doesn't match anything known, then...
            raise self.__raise_lexer_error("Invalid characters sequence in input stream.")

        return self.__currentLexeme
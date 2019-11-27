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


import unittest
from .context import *
from binascii import unhexlify

# array of pdf sentences used to test the Lexer class
pdfParts = [
    b"% comment ( /% ) blah blah blah", # this is just a comment
    b"346% comment ( /% ) blah blah blah\n123", # corresponds to tokens "abc" and "123"
    b"                                       ~", # Invalid string
    b"true false", # booleans
    b"123 43445 +17 -98 0", # Integers
    b"34.5 -3.62 +123.6 4. -.002 0.0", # floats
    b"""
    ( This is a string )
    (Strings may contain newlines\n and such.)
    (Strings may contain balanced parentheses ( ) and\n special characters ( * ! & } ^ % and so on).)
    (The following is an empty string.)
    ()
    (It has zero (0) length.)
    """, # string examples 1
    b"(These \\ntwo strings \\nare the same.) (These \ntwo strings \nare the same.)", # strings with back slash
    rb"(\a backslash is ignored)",  
    rb"(This string contains \245two octal characters\307.)", # test octal strings
    rb"(\0053) (\053) (\53)", # test octal strings 2
    rb"<4 E6F762073686D 6F7A206B6120706F702E>", # hex string
]


validNames = {
    b"/Name1" :  "Name1",
    b"/ASomewhatLongerName" : "ASomewhatLongerName",
    b"/A;Name_With-Various***Characters?" : "A;Name_With-Various***Characters?",
    b"/1.2" : "1.2",
    b"/$$" : "$$",
    b"/@pattern" : "@pattern",
    b"/.notdef" : ".notdef",
    b"/Lime#20Green" : "Lime Green",
    b"/paired#28#29parentheses" : "paired()parentheses",
    b"/The_Key_of_F#23_Minor" : "The_Key_of_F#_Minor",
    b"/A#42" : "AB",
    b"/ " : ""
}


class LexerUnitTest(unittest.TestCase):
    """
    Tests the Lexer class.
    """

    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_lexer_creation(self):
        with open(os.path.join(PDFS_FOLDER, "0000.pdf"), "rb") as fp:
            lex = lexpkg.Lexer(fp)
            self.assertIs(lex.current_lexeme, None)



    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_read_only_comment_source(self):
        lex = lexpkg.Lexer(pdfParts[0])
        try:
            a = next(lex)
        except StopIteration:
            """
            Ok, comments are properly skipped and EOF is reached.
            """
    

    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_tokens_mixed_with_comment(self):
        lex = lexpkg.Lexer(pdfParts[1])
        a = next(lex)
        self.assertEqual(a, 346)
        b = next(lex)
        self.assertEqual(b, 123)
    
    
    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_invalid_input_and_context_print(self):
        lex = lexpkg.Lexer(pdfParts[2], 31)
        try:
            a = next(lex)
        except lexpkg.PDFLexicalError as e:
            msg = str(e)
            self.assertIn("40", msg)
    

    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_boolean_parsing(self):
        lex = lexpkg.Lexer(pdfParts[3], 31)
        t, f = next(lex), next(lex)
        self.assertEqual(t, True)
        self.assertEqual(f, False)


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_integer_parsing(self):
        lex = lexpkg.Lexer(pdfParts[4])
        self.assertEqual([123, 43445, +17, -98, 0], list(lex))


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_real_parsing(self):
        lex = lexpkg.Lexer(pdfParts[5])
        self.assertEqual([34.5, -3.62, +123.6, 4., -.002, 0.0], list(lex))


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_parse_string_literal(self):
        lex = lexpkg.Lexer(pdfParts[6])
        strings = [" This is a string ",
            "Strings may contain newlines\n and such.",
            "Strings may contain balanced parentheses ( ) and\n special characters ( * ! & } ^ % and so on).",
            "The following is an empty string.",
            "",
            "It has zero (0) length."]
        self.assertEqual(strings, list(lex))
        # Test backslashes
        lex = lexpkg.Lexer(pdfParts[7])
        a, b = next(lex), next(lex)
        self.assertEqual(a, b)
        lex = lexpkg.Lexer(pdfParts[8])
        self.assertEqual("a backslash is ignored", next(lex))
        # Test octal characters
        lex = lexpkg.Lexer(pdfParts[9])
        self.assertEqual('This string contains ¥two octal charactersÇ.', next(lex))
        lex = lexpkg.Lexer(pdfParts[10])
        self.assertEqual('\0053', next(lex))
        self.assertEqual(next(lex), next(lex))
        
    
    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_parse_hex_string(self):
        
        lex = lexpkg.Lexer(pdfParts[11])
        item = next(lex)
        self.assertIsInstance(item, lexpkg.PDFHexString)
        self.assertEqual(unhexlify(b"4E6F762073686D6F7A206B6120706F702E"), unhexlify(item.value))
 

    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_parse_name(self):
        for x in validNames:
            lex = lexpkg.Lexer(x)
            tok = next(lex)
            self.assertIsInstance(tok, lexpkg.PDFName)
            self.assertEqual(tok.value, validNames[x])
    

    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_parse_keywords(self):
        istream = b"R n null n false f << endobj obj >> trailer xref startxref { } [ ]"
        checkVals = [lexpkg.KEYWORD_REFERENCE, lexpkg.INUSE_ENTRY_KEYWORD, b"null", 
            lexpkg.INUSE_ENTRY_KEYWORD, False, lexpkg.FREE_ENTRY_KEYWORD, b"<<",
            b"endobj", b"obj", b">>", b"trailer", b"xref", b"startxref", 
            lexpkg.OPEN_CURLY_BRACKET, lexpkg.CLOSE_CURLY_BRAKET,
            lexpkg.OPEN_SQUARE_BRACKET, lexpkg.CLOSE_SQUARE_BRACKET]
        
        lex = lexpkg.Lexer(istream)     
        self.assertEqual([x if isinstance(x, bool) else x.value for x in list(lex)], checkVals)



class SeekableTestCase(unittest.TestCase):


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_seekable_class(self):
        aSequenceOfBytes = b"This is a sequence of bytes."

        # Tests that Seekable does not accept wrong objects.
        with self.assertRaises(ValueError):
            lexpkg.Seekable(5)
        
        # Now creates a valid Seekable instance.
        sk = lexpkg.Seekable(aSequenceOfBytes)
        # moves at the end of the stream
        sk.seek(0, 2)
        # gets the size of the stream
        self.assertEqual(sk.tell(), len(aSequenceOfBytes))
        # now moves to position 3
        sk.seek(3, 0)
        v = sk.read(1)
        self.assertIsInstance(v, list)
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0], aSequenceOfBytes[3])
        # makes a read bigger than the available bytes
        sk.seek(-3, 2)
        v = sk.read(4)
        self.assertEqual(v, aSequenceOfBytes[-3:])



class BasicParserTestCase(unittest.TestCase):


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_parse_simple_sequence(self):
        sequence = b"\n".join(pdfParts[:2] + pdfParts[3:])
        par = parpkg.BasicParser(sequence)
        lpar = list(par)
        self.assertEqual(lpar, [346, 123, True, False, 123, 43445, 17, -98, 0,
            34.5, -3.62, 123.6, 4.0, -0.002, 0.0, " This is a string ", """Strings may contain newlines
 and such.""", """Strings may contain balanced parentheses ( ) and\n special characters ( * ! & } ^ % and so on).""",
"The following is an empty string.", "", "It has zero (0) length.", "These \ntwo strings \nare the same.", 
"These \ntwo strings \nare the same.", "a backslash is ignored", "This string contains ¥two octal charactersÇ.","\0053",
"+", "+", lexpkg.PDFHexString(value=bytearray(b'4E6F762073686D6F7A206B6120706F702E'))])


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_parse_dictionary(self):

        dictExample = b"""
        << /Type /Example
            /Subtype /DictionaryExample
            /Version 0.01
            /IntegerItem 12
            /StringItem (a string)
            /Subdictionary << /Item1 0.4
                /Item2 true
                /LastItem (not!)
                /VeryLastItem (OK)
            >>
        >>"""

        dictCorrectParsed = {
            "Type" : lexpkg.PDFName("Example"),
            "Subtype" : lexpkg.PDFName("DictionaryExample"),
            "Version" : 0.01,
            "IntegerItem" : 12,
            "StringItem" : "a string",
            "Subdictionary" : {
                "Item1" : 0.4, "Item2" : True, "LastItem" :"not!", "VeryLastItem" : "OK"
            }
        }

        par = parpkg.BasicParser(dictExample)
        item = next(par)
        self.assertEqual(item, dictCorrectParsed)


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_parse_indirect_object_and_indirect_reference(self):
        data = b"12 0 obj ( Brillig ) endobj 12 0 R"
        par = parpkg.BasicParser(data)
        item1 = next(par)
        item2 = par.parse_object()
        self.assertIsInstance(item1, parpkg.PDFIndirectObject)
        self.assertEqual(item1.value, " Brillig ")
        self.assertIsInstance(item2, parpkg.PDFReference)


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_parse_stream(self):
        sourceStream = b"""28 0 obj
<<
/Length 34
>>
stream
this is the content of the stream.
endstream
endobj
"""
        par = parpkg.BasicParser(sourceStream, lambda D, read : (D["Length"], lambda : read(D["Length"])))
        item = next(par)
        val = bytes(item.value.stream())
        self.assertEqual(val, b"this is the content of the stream.")


    def test_parse_empty_input(self):
        par = parpkg.BasicParser(b"")
        with self.assertRaises(StopIteration):
            next(par)




class ParserTestCase(unittest.TestCase):


    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_parse_xref_section(self):
        sample = b"""xref
0 7
0000000000 65535 f
0000000009 00000 n
0000000074 00000 n
0000000120 00000 n
0000000179 00000 n
0000000300 00000 n
0000000384 00000 n

trailer
    << /Size 7
        /Root 1 0 R
    >>
startxref
0
%%EOF"""
        parser = parpkg.Parser(sample)
        parsedObjects = [(x.object_number, x.generation_number) for x in parser.xRefTable]
        self.assertEqual(parsedObjects, [(1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0)])




class DocumentTestCase(unittest.TestCase):

    @unittest.skipUnless(RUN_ALL_TESTS, "debug_purposes")
    def test_document_catalog(self):
        with open(os.path.join(PDFS_FOLDER, "0000.pdf"), "rb") as fp:
            myPdfDoc = docpkg.Document(fp)
            self.assertIn("Pages", myPdfDoc.catalog)
    
    
if __name__ == "__main__":
    unittest.main()



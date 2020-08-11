#!python
#-*- coding: utf-8 -*-
"""
    String Tokenizer for Human Formatter

    This module defines the class Token, which is used to identify, classify and
    handle the Human Formatter formatting substrings (named {tokens}).

    Functions
    ---------
    dict_join() -> dict
        Auxiliar functions that joins two dictionaries in a way that keys that
        appear in both are not overriden in on of them, but joined, generally,
        applying operator '+'.

    Classes
    -------
    Token
        Main class. Given any string, it identifies all its tokens (substrings
        that appear between keys {}); and creates a Token for them, which at
        the same time identifies nested tokens inside them. It keeps a track
        of each 'parent' and 'child' token, and has methods to list all the
        tokens and translate them into their HF conversion.


    Created:        08 Ago 2020
    Last modified:  08 Ago 2020
"""

#
# Errors
#
ERR_MISSING_OPENING_KEY = "HFormat Token Error: Closing key '}' found without"\
                          " opening key '{' at position {}."
ERR_CHILD_NO_CONVERSION = "HFormat Token Error: Token {!r} unable to replace"\
                          " childs conversions as child token {!r} does not"\
                          " have one."


#
# Functions
#
def dict_join (left, right, *args, **kwargs):
    """Joins two or more dictionaries into one without losing information.

    It acts just like *dict.update(dict)*, but, instead of overriding the values
    of the keys that appear in both dicts, it "joins" them. In order to do that,
    it uses the add operator (+); but another function can be given using the
    *key* keyword.

    """
    listed = [left, right] + list(args)
    finale = dict()
    for di in listed:
        for key, value in di.items():
            if key not in finale.keys():
                finale[key] = value
            else:
                try:
                    fkey = kwargs.get('key')
                    if fkey and callable(fkey):
                        finale[key] = fkey(finale[key], value)
                    else:
                        finale[key] += value    # '+' operator applies.
                except Exception as err:
                    raise(err)
    return finale


#
# Classes
#
class Token (object):
    """Token Class

    Given a string, this class identifies every token in them, and, also, all
    the 'child' tokens from those ones, keeping an organised track of all of
    them so the HF parsing and conversion can be done with no problem.

    For example, if the given string looks like this: "hello {john {surname}}",
    the Token object resultant will have the following format:

        Token object gen 1 - "hello {john {surname}}"
        - Token object gen 2 - "john {surname}"
        - - Token object gen 3 - "surname"

    So all tokens can be accesed, no matters how deep or nested it is. Thanks
    to that, parsing and conversion can be done in each token ensuring that all
    inner tokens have been previously translated.

    Public attributes:
        token (str): Given token (always without keys)
        conversion (str): Result after HF parsing and conversion. If conversion
            has not been done yet, it will value 'None'.
        parent (Token): Parent of this token, or None, if it is the original.
        childs (list[Token]): List of childs - inner tokens.
        gen (int): Generation, or token depth. Original string will be 0.

    Public methods:
        list() -> dict[list[Token]]: Organizes all the tokens in a dictionary
            where each key is an integer identifying the generation, and the
            value is a list of all the tokens from this generation.
        replace_child_conversions() -> str: Replaces the current token inner
            tokens (childs) with their conversion (child.conversion). If any
            child has no conversion yet, it will raise an exception.
        __str__() -> str: Returns a printable representation of the initial
            token, and all its childs, in a tree-view.
        __repr__() -> str: Returns an object representation of this token only.

    Raises:
        SyntaxError: if there are any problems during tokens identification.

    """

    def __init__ (self, token, gen = 0):
        """Builds the token for the given string, and identifies its childs."""
        self.token = token
        self.conversion = None
        self.parent = None
        self.childs = list()
        self.gen = gen      # Generation, depth level

        stack = list()
        raw_childs = list()     # Possible childs before tokenizing them
        for i, char in enumerate(self.token):
            if char == '{':
                stack.append(i)
            elif char == '}':
                if stack:
                    start = stack.pop()
                    if len(stack) == 0:
                        raw_childs.append(self.token[start+1:i])
                else:
                    raise SyntaxError(ERR_MISSING_OPENING_KEY.format(i))

        for child in raw_childs:
            self.childs.append(Token(child, self.gen + 1))
            self.childs[-1].parent = self


    def list (self):
        """Returns a list of all tokens from this one, organized with format:

            <gen>: [<list of same gen tokens>]

        """
        back = {self.gen: [self]}
        for child in self.childs:
            back = dict_join(back, child.list())
        return back


    def replace_child_conversions (self):
        """Replaces its nested tokens with the translations from its childs.

        Returns the replaced result; or raises an exception if a child has no
        translation yet.

        """
        out = self.token
        for child in self.childs:
            if child.conversion is None:
                raise RuntimeError(ERR_CHILD_NO_CONVERSION.format(self, child))
            else:
                out = out.replace('{'+child.token+'}', child.conversion, 1)
        return out


    def __str__ (self):
        s = "{indent}{gen}. {token}\n".format(indent = '  '*self.gen,
                                              gen = self.gen,
                                              token = self.token)
        for child in self.childs:
            s += str(child)
        return s


    def __repr__ (self):
        return "Token Object for {token!r} at <{id}>".format(token = self.token,
                                                             id = id(self))


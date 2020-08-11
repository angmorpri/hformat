#!python
#-*- coding: utf-8 -*-
"""
    Human Formatter Main Module

    This module defines all the components that conform the Human Formatter,
    which provides a string formatter system with a custom language that
    resembles more like Python, so it does not use the original mini-language.
    It also adds some extra features, such as string wrapping or realtive field
    width.

    It is compatible with both Python 2 and 3.

    For example, let's say we want to print the result of 3/11 as a float with
    three decimals, aligned to the center and filled by dashes. That would be:

    In Python 2.x:      print("{:-^10.3f}".format(3/11))
    In Python 3.x:      print(f"{3/11:-^10.3f}")
    With HF in 2.x/3.x: hfprint("{3/11:width(10), fill(-), float(3), center")

    As you can see, although with HF the result is way larger, the syntax is
    clear, and you can tell what it is going to do without having any under-
    standing of the Python's format mini-language. You can even improve the
    length of the formatting string by using some of the custom functions:

        hfprint("{3/11:field(10, -, center), float(3)}")

    In all cases, it will output: '--0.273---'.


    Functions
    ---------
    hformat() -> str
        Main function. Given a hformatted string, returns its conversion.

    hfprint() -> str
        Same as 'hformat()', but prints the string before returning it.

    Classes
    -------
    HumanFormatter
        Main engine for the Human Formatter. Does all the format, parse and
        conversion. Based on Python's str.Formatter.

    FunctionObject
        Dataclass that stores info about the Human Formatter functions in the
        given string, so its handling is easier. It also checks for syntax and
        type errors in the functions.


    Created:        06 Ago 2020
    Last modified:  11 Ago 2020
        + 'width' is now checked just before formatting, so relative width can
        work properly even with separators and trimming modifications.
    TODO:
        + [Prop] Make the use of extra features optional.
        + Include more f-strings features (such as !s !r or =)
        + [Doc] Limitations and differences with f-strings
        + [Prop] Allow to use locals and globals optionally.

"""
import sys
if sys.version_info[0] < 3:
    from itertools import izip_longest as zip_longest
else:
    from itertools import zip_longest
import yaml

from placeholder import PlaceholderHandler
from tokenizer import Token


#
# Definitions
#
_FDEFS_FILE = "functions.yml"
_CANVAS_FILL_PLACEHOLDER = chr(5)
_MISC_PLACEHOLDER = chr(6)
_MULTICHAR_FILL_PLACEHOLDER = chr(7)
ESCAPE_CHAR = '!'


#
# Errors
#
ERR_FUNC_DOESNT_EXIST = "HFormat Error: Function {!r} is not defined."
ERR_TOO_MANY_ARGS = "HFormat Error: {0!r} takes {1} args, but {2} were given."
ERR_TOO_FEW_ARGS = "HFormat Error: {0!r} expects {1} args, but {2} were given."


#
# Functions
#
def hformat (format_string__, *args, **kwargs):
    """Main function. Formats the given string and returns the result.

    Copies the Python's str.format(): format_string__.format(*args, **kwargs)

    """
    hf = HumanFormatter()
    return hf.format(format_string__, *args, **kwargs)

def hfprint (string, *args, **kwargs):
    """Same as *hformat*, but prints the result before returning it."""
    hf = HumanFormatter()
    result = hf.format(string, *args, **kwargs)
    print(result)
    return result


#
# Classes
#
class HumanFormatter (object):
    """Human Formatter Class

    This class allows to use the functionalities of Python's str.format() but
    using an specification language that resembles more to Python syntax. It
    also brings some f-string features, such as expressions evaluating; and adds
    some brand-new ones, like relative field width, or wrapping.

    You can use this class via extern function 'hformat()', or using the method
    'format' in any object of this class.

    Public attributes:
        original (str): Original string
        final (str): Final string (after conversion)
        given_args (list): List of arguments given along with the original str.

    Methods:
        format() -> str: Given a formatting string and the arguments involved,
            returns the formatted conversion, such as using str.format().
        parse() -> tuple: Parses a given token (formatting substring) and returns
            a tuple with (expression, function_list), where 'expression' is the
            part that will be outputted, and the 'function_list' is the list
            with all the FunctionObjects created for the specifications (specs).
        convert() -> str: Given the 'parse()' tuple output, identifies and
            interpretes all the functions from this token and builds the final
            string, returning it.

    """
    def __init__ (self):
        """Initializes some private properties."""
        self.original = ''
        self.final = ''
        self.given_args = list()
        self._positional_args_index = 0


    def format (self__, format_string, *args, **kwargs):
        """Primary API method.

        Takes the formatted string and the arguments necessary and returns the
        final form string, with all its fields completed and converted.

        """
        self__.original = format_string
        self__.given_args = kwargs
        self__.given_args['__args__'] = args  # Simplifies the args check.

        # Identify every sub-string to be formatted (each 'token'):
        main_token = Token(format_string)
        tokens_list = main_token.list()
        # Tokens are divided by levels, being the highest levels the deeper
        # tokens. This means that those tokens ('childs') are inside another
        # token ('parent'), and those lasts need the first to be converted
        # before they themselves can be finally converted.
        tokens_sorted = sorted(tokens_list.items(), key=lambda i: i[0],
                               reverse=True)
        for level, tokens in tokens_sorted:
            # Each level stores a tuple with all the same-level tokens, which
            # can be converted at the same time as they won't affect each other.
            # The level 0 is the original string, which is not converted, but
            # has its tokens replaced when all are translated.
            if level == 0:
                final = tokens[0].replace_child_conversions()
            else:
                for token in tokens:
                    parsed_token = self__.parse(token.replace_child_conversions())
                    final = self__.convert(parsed_token)
                    token.conversion = final

        return final


    def parse (self, token):
        """Parsing function.

        The tasklist of this function and its behavior is the following:
        1. Placehold every special char or substring, such as literals.
        2. Separate *expression* from *specs*.
        3. Identify each function in the specs, and create a list of "function
        objects", which store all important info.
        4. Un-placehold every placeholders and return a tuple (expr, list).

        """
        phhandler = PlaceholderHandler()
        # Placeholding will save chars and substring following the rules:
        #   - Chars after escape char !
        #   - Substrings between quotes. The quote char will be chosen in
        #   runtime, selecting the one that appears the most between ' and ".
        safe_string = phhandler.after(token, ESCAPE_CHAR, 1)
        quote_char = "'" if token.count("'") >= token.count('"') else '"'
        safe_string = phhandler.between(safe_string, quote_char)

        # Separating expression from specs. Format is '{expression[:specs]}'
        expression = specs = ''
        if ':' in safe_string:
            expression, specs = safe_string.split(':')
            expression, specs = expression.strip(), specs.strip()
        else:
            expression = safe_string

        expression = phhandler.revert(expression)

        functions = list()  # List for FunctionObjects.
        if specs:
            # Format is 'function[([arg1, arg2, ..., argN])][, function...]'
            # The functions separator can be the comma (,) or the semicolon (;).
            safe_specs = phhandler.between(specs, '(', ')')
            funcs_sep = ',' if safe_specs.count(',') >= safe_specs.count(';') \
                       else ';'
            raw_funcs = safe_specs.split(funcs_sep)

            for raw_func in raw_funcs:
                raw_func = raw_func.strip()
                raw_func = phhandler.revert_last(raw_func)  # Arguments back.
                if '(' in raw_func:
                    func_name, raw_func_args = raw_func.split('(')
                else:
                    func_name = raw_func
                    raw_func_args = None
                func_args = list()
                if raw_func_args:
                    raw_func_args = raw_func_args[:-1]   # Delete closing ')'
                    for arg in raw_func_args.split(','):
                        arg = arg.strip()
                        func_args.append(phhandler.revert(arg, True))
                # Now, with both function name and arguments, the FunctionObject
                # is created.
                functions.append(FunctionObject(func_name, func_args))

        # The tuple (expression, functions) is returned
        return (expression, functions)


    def convert (self, parsed_token):
        """Conversion function.

        Given a parsed token, this method interpretes the expression and each
        formatter function and creates the resultant string.

        Mainly it translates from HumanFormatter system to Python's one, and
        applies a generic str.format() when this translation is done; but the
        HumanFormatter also allows some extra functionalities, and those are
        handled in many different ways.

        """
        expression, functions = parsed_token

        # A. Expression
        # Positional arguments reference is replaced with keyword '__args__[]',
        # so evaluation is still posible.
        if not expression:
            # Empty expression will mean 'next positional argument'; so the
            # private attribute is used to follow which is the next.
            expression = '_' + str(self._positional_args_index) + '_'
            self._positional_args_index += 1


        if sys.version_info[0] < 3:
            uexpr = unicode(expression)     # For Python2 compatibility.
            if uexpr.isnumeric():
                expression = '_' + expression + '_'
        else:
            if expression.isnumeric():
                expression = '_' + expression + '_'

        # Some translations are made in order to allow positional arguments
        # evaluation:
        fake_expr = expression
        for index in range(len(self.given_args['__args__'])):
            fake_expr = fake_expr.replace("{}.".format(index),
                                          "__args__[{}].".format(index))
            fake_expr = fake_expr.replace("{}[".format(index),
                                          "__args__[{}][".format(index))
            fake_expr = fake_expr.replace("_{}_".format(index),
                                          "__args__[{}]".format(index))

        # The expression is evaluated. If it raises an error while evaluating (
        # but not if the expression fails), it will treat it as a literal string
        try:
            final_expr = eval(fake_expr, None, self.given_args)
        except NameError:
            final_expr = expression


        # B. Functions.
        # Each function may modify one of the variables that will end up forming
        # the Python-like specs:
        #   [[fill]align][sign][alter][zero][width][comma][.precision][ptype]

        # Function that searches for a FunctionObject given various posible
        # names. If it finds it, will return True, and store the object in
        # local property '_func'. Else, it will return False, and store None.
        def get_func (*names):
            self._func = None
            for name in names:
                for fobj in functions:
                    if fobj.name == name:
                        self._func = fobj
                        return True
            return False

        # Control variables, generally for extra features
        _decsep = ''

        # Fill
        #   Will also define 'align', in case it is not given.
        #   Can be set from functions 'fill', 'field' and 'canvas'.
        fill = align = wrapper = ''
        if get_func('fill', 'field', 'canvas'):
            align = '<'     # Default aligning.
            fill = self._func.args.get('fillchar', '')

            if self._func.name == 'canvas':
                # Canvas filling behave differently depending on the format:
                if len(fill) % 2:
                    # Odd: mid char is the fill char, and the others are wrappers.
                    wrapper = fill[:len(fill)//2] + fill[len(fill)//2+1:]
                    fill = fill[len(fill)//2]
                else:
                    # Even: half fills before the string, and half after.
                    wrapper = fill[:len(fill)//2] + fill[len(fill)//2:]
                    fill = _CANVAS_FILL_PLACEHOLDER

            if len(fill) > 1:
                # Multicharacter filling, handled after Python str.format().
                multifill = fill
                fill = _MULTICHAR_FILL_PLACEHOLDER

        # Align
        #   Can be set from functions 'align', 'left', 'right', 'center',
        #   'field' and 'canvas'.
        raw_align = ''
        if get_func('align', 'field', 'canvas'):
            raw_align = self._func.args.get('align', '<')
        if get_func('left') or raw_align in ('left', '<'):
            align = '<'
        elif get_func('right') or raw_align in ('right', '>'):
            align = '>'
        elif get_func('center') or raw_align in ('center', '^'):
            align = '^'
        elif raw_align in ('sign', '='):
            align = '='

        # Sign
        #   Can be obtained from 'sign'.
        sign = ''
        if get_func('sign'):
            sign = self._func.args.get(0, '+') or '+'

        # Precision
        #   Can be set with 'precision' and 'float'.
        precision = ''
        if get_func('precision', 'float'):
            aux = self._func.args.get('prec', '')
            precision = '.'+aux if aux else ''

        # Type (ptype)
        ptype = alter = ''
        _ptype_dict = {
            'string': '',
            'bin': 'b',
            'rawbin': 'b',
            'char': 'c',
            'decimal': 'd',
            'octal': 'o',
            'rawoctal': 'o',
            'hex': 'x',
            'Hex': 'X',
            'rawhex': 'x',
            'rawHex': 'X',
            'number': 'n',
            'exp': 'e',
            'Exp': 'E',
            'float': 'f',
            'Float': 'F',
            'general': 'g',
            'General': 'G',
            'percentage': '%'
        }
        if get_func(*_ptype_dict.keys()):
            ptype = _ptype_dict[self._func.name]
            if self._func.name in ('bin', 'octal', 'hex', 'Hex'):
                alter = '#'

        # Pre-format functions
        # Some functions may need to pre-format the string only with some specs,
        # and then use the result (as a string) with the rest of them.
        # This happens with 'trim', 'milesep' and 'decsep'. 'width' also may
        # need to know the final result of the string, for the relative width
        # option.

        # Comma - Miles & Decimals separator
        #   Can be set with 'milesep' (for miles) and 'decsep' (for decimals).
        comma = ''
        if get_func('milesep'):
            comma = self._func.args.get(0, ',') or ','
        if get_func('floatsep'):
            _decsep = self._func.args.get(0, '.') or '.'
        if comma or _decsep:
            # Output will have the miles separator default char comma and the
            # decimals separator default point replaced with user given chars,
            # if any.
            comma = comma or ','
            _decsep = _decsep or '.'
            preformat = "{0:{1},{2}{3}}".format(final_expr, alter, precision,
                                                ptype)
            # , --> \2046
            preformat = preformat.replace(',', _MISC_PLACEHOLDER)
            # . --> _decsep
            preformat = preformat.replace('.', _decsep)
            # \2046 --> comma
            preformat = preformat.replace(_MISC_PLACEHOLDER, comma)
            alter = precision = ptype = comma = ''
            final_expr = preformat

        # Trim (extra)
        #   Can be set with 'trim'.
        if get_func('trim'):
            limit = int(self._func.args.get(0, 100))
            stopchar = self._func.args.get(1, None)
            preformat = "{0:{1}{2}{3}}".format(final_expr, alter, precision,
                                               ptype)
            if stopchar:
                final_expr = preformat[:limit-len(stopchar)] + stopchar
            else:
                final_expr = preformat[:limit]
            alter = precision = ptype = ''  # Reset, as they won't be used.

        # Width
        #   Can be obtained from 'width', 'zwidth', 'field' and 'canvas'.
        width = zero = ''
        if get_func('width', 'field', 'canvas', 'zwidth'):
            width = self._func.args['size']

            if self._func.name == 'zwidth':
                zero = '0'

            if width.startswith('+'):
                # Relative width, needs to know which will be the final length
                # of the string.
                # Ignores *trim* function.
                width = str(int(width[1:]) \
                            + len("{0:{1}{2}{3}}".format(final_expr, alter,
                                                          precision, ptype)))


        # Once all Python-original specs are completed, the conversion is made:
        python_specs = fill+align+sign+alter+zero+width+comma+precision+ptype
        #print(python_specs)
        conversion = "{0:{1}}".format(final_expr, python_specs)


        # Then, some after-conversion alterations may take part:
        # Multichar filling (extra)
        if fill == _MULTICHAR_FILL_PLACEHOLDER:
            # The current filling char is an special non-representable char that
            # now will be replaced with the correct chars in the correct order.
            for i in range(conversion.count(_MULTICHAR_FILL_PLACEHOLDER)):
                conversion = conversion.replace(_MULTICHAR_FILL_PLACEHOLDER,
                                                multifill[i%len(multifill)], 1)

        # Canvas filling (extra)
        if fill == _CANVAS_FILL_PLACEHOLDER:
            # The current filling char is an special non-representable char.
            # Those before the string will be replaced with the opening part
            # of the wrapper, and so will the other half with the closing part.
            open_chars = wrapper[:len(wrapper)//2]
            close_chars = wrapper[len(wrapper)//2:]
            n_chars = len(open_chars)

            total = conversion.count(_CANVAS_FILL_PLACEHOLDER)
            after = before = 0  # Chars to replace *after* and *before*.
            for char in conversion:
                if char != _CANVAS_FILL_PLACEHOLDER:
                    break
                else:
                    before += 1
            after = total - before

            for i in range(before):
                conversion = conversion.replace(_CANVAS_FILL_PLACEHOLDER,
                                                open_chars[i%n_chars], 1)
            for i in range(after):
                conversion = conversion.replace(_CANVAS_FILL_PLACEHOLDER,
                                                close_chars[i%n_chars], 1)

        # Wrapping (extra)
        #   Can be set with function 'wrap' and with 'canvas' arguments.
        if wrapper or get_func('wrap'):
            wrapper = wrapper or self._func.args.get(0, '')
            open_chars = wrapper[:len(wrapper)//2]
            close_chars = wrapper[len(wrapper)//2:]
            conversion = open_chars + conversion + close_chars

        # Returning the final string
        self.final = conversion
        return conversion



class FunctionObject (object):
    """FunctionObject Class

    This class acts like a dataclass for the information gathered from each
    functions of a given token. Along with storing the information, it checks
    the functions, ensuring they are correct (exist) and have the correct args,
    as defined in the Functions Definitions File ('functions.yaml'). After that,
    the object can be used by its two public attributes: name and args.

    Public attributes:
        name (str): Identification name of the function. Note that this may not
            be the name the user put, as some functions can have different names
            but be identified by the same 'main name', which will be the one
            stored here.
        args (dict): Dictionary with all the arguments for this function. Each
            argument given will be stored in two ways: with its defined name as
            a keyword, but also with its position as a dict-key.
            Note that all the arguments defined for the function will be stored,
            even the ones that the user gave no value. Those will have 'None' as
            their value.

    Private methods:
        _build() -> None: Actually creates the object.

    Raises:
        NameError: If it does not find a given function name in the defs.
        TypeError: Whenever there is an error in the arguments given.

    """

    _fdefs = None      # Dict of functions definitions, obtained from YAML.

    def __init__ (self, name, args):
        self.name = name
        self.args = args
        self._build(name, args)


    def _build (self, given_name, given_args):
        """Builds the object.

        Takes the given function name and its arguments, searches for them in
        the functions definitions (YAML) and if everything is correct, the
        object is created. Else, it would raise an error.

        """
        if FunctionObject._fdefs is None:
            # Functions definitions dict is created from YAML just once.
            FunctionObject._fdefs = dict()
            if sys.version_info[0] < 3:
                raw_def = yaml.load(open(_FDEFS_FILE))
            else:
                raw_def = yaml.load(open(_FDEFS_FILE), yaml.FullLoader)
            for raw_group in raw_def:
                group_names = raw_group['name']
                group_args = raw_group.get('args', list())

                # Args parsing
                args = list()
                for raw_arg in group_args:
                    args.append([a.strip() for a in raw_arg.split(',')])

                # Functions name parsing
                if not isinstance(group_names, list):
                    group_names = [group_names]
                for raw_name in group_names:
                    allowed_names = [n.strip() for n in raw_name.split(',')]
                    main_name = allowed_names[0]
                    for func_name in allowed_names:
                        FunctionObject._fdefs[func_name] = {
                            'id': main_name,
                            'args': args
                        }

        # Building the object
        try:
            func_def = FunctionObject._fdefs[given_name]
        except KeyError:
            raise NameError(ERR_FUNC_DOESNT_EXIST.format(given_name))

        self.name = func_def['id']      # Name needs no check.
        # But args do:
        # - Checking number of arguments given / needed:
        n_given_args = len(given_args)
        total_allowed_args = len(func_def['args'])
        min_man_args = len([m for m in func_def['args'] if m[1] == 'man'])
        if n_given_args > total_allowed_args:
            # More arguments than needed.
            raise TypeError(ERR_TOO_MANY_ARGS.format(self.name,
                                                     total_allowed_args,
                                                     n_given_args))
        if n_given_args < min_man_args:
            # Less arguments than needed.
            raise TypeError(ERR_TOO_FEW_ARGS.format(self.name,
                                                    min_man_args,
                                                    n_given_args))
        # If success, the given arguments are mapped to their definition args.
        self.args = dict()
        for index, combo in enumerate(zip_longest(func_def['args'], given_args)):
            # Arguments are stored in the dict both with their position and
            # their definition name.
            def_arg, given_arg = combo
            self.args[def_arg[0]] = given_arg
            self.args[index] = given_arg


    def __str__ (self):
        """For debug printing"""
        out = "Function Name: {}\n".format(self.name)
        out += "Function Args: \n"
        for key, value in self.args.items():
            if not isinstance(key, int):
                out += " - {0}: {1}\n".format(key, value)
        return out

#!python
#-*- coding: utf-8 -*-
"""
    Universal String Placeholder

    This module allows to safely secure substrings of a string by replacing them
    with random placeholders that can then be brought back easily; so the string
    can be manipulated without having those substring interfering or changing.

    Classes
    -------
    PlaceholdHandler
        Handles all the placeholders made for a string. The same object must be
        used for the same string. Defines all the methods used for creating
        placeholders for different substrings, and to bring back them in the
        correct way or order.

    Created:       27 Jul 2020
    Last modified: 09 Ago 2020
        - Now resets the secure chars index when it reaches the maximum.

"""
import random

#
# Definitions
#
_SECURE_CHARS = list(range(48, 57)) + list(range(65, 90)) + list(range(97, 122))
DEFAULT_SAFE_CHARS = '$_'


# Singleton definition (unused)
class Singleton (type):
    _instances = dict()
    def __call__ (cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

#
# Class definition
#
class PlaceholderHandler (object):
    """PlaceholderHandler Handler Class

    Defines all the methods to handle placeholding, used to protect some chars
    or substrings of a string, so manipulating it won't affect the protected
    chars, and can be brought back easily.

    Only one handler must be created for the same string, but one handler can
    be used for multiple strings at the same time.

    Placeholders are random. By default, they will be made with one printable
    char, surrounded by 8 random chars obtained from public attribute safe_chars,
    which by default is compound of '$_' but can be set to whatever the user
    wants. It is recommended that the chars used for placeholding are not
    important in the string.

    Because of the fact that it uses printable chars as a part of the placeholding
    in order to avoid repeatition (even randomly generated), the maximum amount
    of placeholders that it can create are 59. After this point it will reuse
    the old ones, trying to use those who are unused in the moment; but it
    could cause an error at some point.

    Each time a placeholder and some substring is replaced, it returns the
    resultant string, and saves the placeholder with the substring and an
    identifying group number. This number can be used to bring back specific
    placeholders, instead of bringing all back at the same time, which is the
    standard way.

    Public attributes:
        safe_chars (str): String of any length with chars that can be used as a
            part of the placeholders. By default, it is '$_'.

    Private methods:
        _get_new_placeholder() -> str: Creates a new placeholder, pseudo-randomly.
        _revert_group() -> str: Reverts the selected groups of placeholders.

    Public methods:
    Placeholding methods:
        All placeholding methods receive the string where the placehold must
        take part, and return the string with the replacement done. They all
        can also have the keyword arg 'return_group_id' set to True in order to
        return a tuple (string, group_id).

        substr() -> str: Receives a substring and placeholds ALL the occurrences
            of the substring.
        after() -> str: Placeholds substrings after a given char. The stop point
            can be set in many different ways.
        between() -> str: Placeholds substrings between one (or two) given chars.

    Reverting methods:
        All reverting methods receive the string with the placeholders, and
        return the string with the specific placeholders asked replaced. They
        all can have also the keyword arg 'ignore_identifiers' set to True in
        order to not include in the replacement the original indentification
        chars (for example, if the placehold is donde 'after char !', the char
        ! will be included normally, unless this keyword is set).

        revert() -> str: Reverts all the placeholders.
        revert_last() -> str: Reverts the last placeholder made.
        revert_group() -> str: Reverts the placeholders identified by the given
            group id.

    """
    def __init__ (self):
        self._current_placeholders = list()
        self.safe_chars = DEFAULT_SAFE_CHARS
        self._secure_index = 0


    # Privates
    def _get_new_placeholder (self):
        """Returns a new placeholder"""
        if self._secure_index >= len(_SECURE_CHARS):
            self._secure_index = 0
        secure_char = chr(_SECURE_CHARS[self._secure_index])
        self._secure_index += 1
        random_chars = [random.choice(self.safe_chars) for _ in range(8)]
        placeholder = ''.join(random_chars[0:4]) \
                      + secure_char \
                      + ''.join(random_chars[4:8])
        return placeholder


    def _revert_groups (self, string, group_list, ignore):
        """Reverts all the placeholds made for the groups in *group_list*"""
        for ph in self._current_placeholders:
            if ph['group'] in group_list and ph['name'] in string:
                back = ph['hidden']
                if not ignore:
                    if ph['type'] == 'between':
                        back = ph['identifier'][0] + back + ph['identifier'][1]
                    elif ph['type'] == 'after':
                        back = ph['identifier'] + back
                string = string.replace(ph['name'], back)
        return string


    # Publics
    def revert (self, string, ignore_identifiers=False):
        """Reverts all the placeholders in the given string."""
        if len(self._current_placeholders) > 0:
            last_ph_group = self._current_placeholders[-1]['group']
            return self._revert_groups(string, list(range(0, last_ph_group+1)),
                                       ignore_identifiers)
        else:
            return string


    def revert_last (self, string, ignore_identifiers=False):
        """Reverts the last group placeholding made in the given string."""
        if len(self._current_placeholders) > 0:
            last_ph_group = self._current_placeholders[-1]['group']
            return self._revert_groups(string, [last_ph_group], ignore_identifiers)
        else:
            return string


    def revert_group (self, string, group, ignore_identifiers=False):
        """Reverts the placeholds given for the group given, in the string."""
        return self._revert_groups(string, [group], ignore_identifiers)


    def substr (self, string, substr, return_group_id=False):
        """Placeholds all occurrences of *substr* in *string*."""
        group = self._secure_index
        ph = self._get_new_placeholder()
        self._current_placeholders.append({'group': group,
                                          'name': ph,
                                          'hidden': substr,
                                          'type': 'substr',
                                          'identifier': None})
        if return_group_id:
            return string.replace(substr, ph), group
        else:
            return string.replace(substr, ph)


    def after (self, string, idchar, stop=' \n\t', return_group_id=False):
        """Placeholds everything after *idchar*.

        It will placehold everything until *stop*, which can be:
            A char, or a group of chars: Will stop when it finds any of those
                chars. Won't include that char in the placehold.
            An integer: Will stop after that number of chars.
            A tuple of (char[s], int): Will stop after whatever happens first.

        By default, the stop will be any whitespace char (' \t\n').

        """
        group = self._secure_index

        stop_chars = list()
        stop_after = 1000
        if isinstance(stop, str):
            stop_chars = stop
        elif isinstance(stop, int):
            stop_after = stop
        elif isinstance(stop, tuple):
            stop_chars = stop[0]
            stop_after = stop[1]

        to_placehold = list()
        new = False
        plh = ''
        count = 0
        for char in string:
            if new:
                count += 1
                if (char in stop_chars) or (count > stop_after):
                    new = False
                    to_placehold.append(plh)
                    plh = ''
                    count = 0
                else:
                    plh += char
            elif char == idchar:
                new = True

        # Adds the last one if the string ended while on 'new=True'
        if new:
            to_placehold.append(plh)

        for substr in to_placehold:
            placeholder = self._get_new_placeholder()
            string = string.replace(idchar + substr, placeholder)
            self._current_placeholders.append({'group': group,
                                               'name': placeholder,
                                               'hidden': substr,
                                               'type': 'after',
                                               'identifier': idchar})
        if return_group_id:
            return string, group
        else:
            return string


    def between (self, string, open_char, close_char=None, return_group_id=False):
        """Placeholds everything between *start* and *end*, wich must be chars.

        If *end* is not given, would be the same as *start*.

        Does not handle inner substrings.

        """
        group = self._secure_index
        close_char = close_char or open_char

        stack = list()
        copy = string
        for i, char in enumerate(copy):
            if not stack and char == open_char:
                stack.append(i)
            elif stack and char == close_char:
                start = stack.pop()
                hidden = copy[start+1:i]
                placeholder = self._get_new_placeholder()
                string = string.replace(open_char+hidden+close_char, placeholder)
                self._current_placeholders.append({'group': group,
                                            'name': placeholder,
                                            'hidden': hidden,
                                            'type': 'between',
                                            'identifier': open_char+close_char})

        if return_group_id:
            return string, group
        else:
            return string



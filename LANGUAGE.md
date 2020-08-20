# HFormat Language [WIP]
## Introduction
HFormat implements a function-based syntax in order to use all its functionalities. If in the standard way we had something like this:

	"{"field_name[:[[fill]align][sign][alter][zero][width][grouping_option][.precision][type]]"}"

The HFormat way presents the following syntax:

	"{"field_name[:[func_name[([func_args, ...])]], ...]"}"

The `field_name` part remains just the same, but the *specs* part (everything after the colon) proposes a simple pythonic way that just uses a list of functions. And, more important, it is *way* more clear than `str.format()` approach. For example:

	{var+1 : fill(' '), width(20), center}

It is pretty clear that it will print whatever is inside `var` plus one, and that it will center it in a field of 20 whitespace.

___

## Keyword chars
As HFormat allows the user to use a more simple and readable language, it needs to use more keyword chars. Those characters cannot be used freely, as they would cause conflict with the defined syntax. Those are:

* The colon (':'), used to separate *field* from *specs*.
* The comma (','), used to separate both functions and function arguments.
* The semicolon (';'), an alternate char to separate functions.
* Both parentheses ('(', ')'), which are used to assign parameters to a function.
* One of the string quotes (' or "), which will be used to identify strings *in* the formatting substring.

In order to allow the user to use those chars without trouble, two "escaping" mechanisms are given:

* First, everything between string quotes (' or ") will be ignored. Only one of the two possible quotes will be used to define strings, and the other will remain as an unused char (so it could be used anywhere without escaping needed). The program automatically assigns the quote by choosing the one that appears the most in the formatting substring.
* Second, the syntax provides the escaping char '!', which works such like Python's '\\' escape char. Every char *before* the exclamation sign won't be evaluated, and will be treated as a literal.

**WARNING**: By now, key brackets ('{' and '}') are always interpreted as formatting substring definitors, which means they can't be used as literals, even if they are escaped. This will be fixed soon.

___

## Field
The field is the part that appears *before* the colon. In Python versions before 3.6, it must be a parameter given in the arguments of `str.format()`; in Python >=3.6, with the addition of f-strings, it can be any expression, which will be evaluated at runtime. HFormat allows a mixed system that works in *every* Python version, although it is not as powerful as f-strings.

HFormat field allows any expression that can be evaluated with the `eval()` function, using the arguments given to `hformat` as local variables for the expression. This means that something like the following can be done:

```python
hformat("Example {3 + arg[2] : float}.", arg = [1,2,3,4])
```

But this not:

```python
arg = [1,2,3,4]
hformat("Example {3 + arg[2] : float}.")
```

Which could be achieved using f-strings. That is because [PEP 498](https://www.python.org/dev/peps/pep-0498/#no-use-of-globals-or-locals) discourages the use of `locals()` and `globals()`, which would be necessary in order to get the user's defined variables. In any case, this feature may be added in a future as an optional element.

The combination of `str.format()` fields and expression evaluation leads to some conflicts. For example, in this case:

```python
hformat("Result: {0}", 19)
```

With `str.format()`, the result should be 19, as it is the value of the first \*arg; but, with f-strings, the value should be 0, as f-strings does not know about extra arguments, and evaluates the field expression. In order to provide both behaviors with `hformat`, it defines the following approach:

```python
hformat("Result: {0}", 19)
# Will output '0'

hformat("Result: {_0_}", 19)
# Will output '19'

hformat("Result: {}", 19)
# Will also output '19'
```

Keep in mind that this `_<pos>_` representation is only needed when you have to use the *raw* variable. If you attempt to access the content of a positional argument using indexes or attributes, it will work without underscores required:

```python
obj.elem = 1
hformat("Result: {0.elem + 1[2] + 3['a']}", obj, [1,2,3], {'a':3, 'b':5})
# Will output '7'
```

Finally, if an error related to the expression interpretation occurs during the evaluation (for example, a not defined variable), it won't raise an exception, but interpret the field as a string literal.

___

## Specs
The specs part goes after the colon. It is where all the text modifications occurs. With HFormat, this is done by using functions, which have an easy Python format:

	func_name[([arg1[, arg2[, ...]]])][, func_name...]
    
Different functions are concatenated using a comma or a semicolon (but not both of them). 
Each function may have arguments, in which case, the parentheses are used to identify those. Unlike standard functions, HFormat ones do not need to add the parentheses if no arguments will be given.
The arguments inside a function must be separated with commas, they can't be keyword style args, and **all** of them are interpreted as string literals, which means the do not need to be surrounded with quotes (although they can, for example, for escaping chars), and that you can't use variables inside them. For a quick summary, take a look at the following examples:

```python

# Concatenated functions using commas and semicolons are allowed:
hformat("Example: { : fill(x), width(10), center}", 10)
hformat("Example: { : fill(x); width(10), center}", 10)
# >>> "Example: xxxx10xxxx"

# Arguments may or may not be given, and parentheses are optional:
hformat("Example: { : field(10, x, center), float", 10)
#                            |                   |
#				             |                   +--- No args, no parentheses.
#	                         +------------------------Uses parentheses and have its arguments separated by commas.
# >>> "Example: 10.000000x"

# Arguments are interpreted as string literals, so no variables are allowed, and no quotes are needed.
# Both following examples will output the same:
hformat("Example: { : fill('x'), width('10'), align('center')}", 10)
hformat("Example: { : fill(x), width(10), align(center)}", 10)
# >>> "Example: xxxx10xxxx"

# If you would like to use variables inside HFormat functions, you could nest an inner formatting substring:
hformat("Example: { : fill({x}), width({y}), align({z})}", 10, x='$', y=8, z='left')
# >>> "Example: 10$$$$$$"

```

### Functions
HFormat defines a bunch of functions that allows not only to reply the standard `str.format()` system, but also improves it with more functionalities. In this paragraph, all those functions will be listed and explained:

#### Field functions:

* **fill ( [fillchar] )**, chooses a filling char for the field where the text will be outputted. It allows every type of string, even with multiple chars, in which case those will be used, in recursive order, to fill the spaces. If no argument is given, the default filling char is the whitespace (' ').

* **width ( size )**, sets the width of the text field. Its argument can be either an integer, in which case the width size will be absolute; or a string with the format '`+NN`', where `NN` can be any integer, and the size will be relative to the text size. Check the following example:

```python
hformat("{'Hello world': width(17), fill(_), center}")
hformat("{'Hello world': width(+6), fill(_), center}")
# >>> "___Hello world___"
```

* **zwidth ( size )**, it acts just like `width`, but performs what is called *zero-padding*; it places 0s between the digit sign and the numbers.

* **align ( align )**, sets the alignment of the text in the field. The possibilities are: '*center*' or '*^*', '*left*' or '*<*', '*right*' or '*>*' and '*=*'.
* **center**, same as `align(center)`.
* **left**, same as `align(left)`.
* **right**, same as `align(right)`.

* **field ( size, fillchar, align )**, a grouped format for `width`, `fill` and `align`, as they are commonly used together. Following the previous example:

```python
hformat("{'Hello world': width(+6), fill(_), center}")
hformat("{'Hello world': field(+6, _, center)}")
# >>> "___Hello world___"
```

* **wrap ( wrapper )**, sets a group of chars that will wrap the output textfield. The first half of them will open the text, and the other half will close it.

```python
hformat("{'Hello world': field(+6, _, center), wrap('()')}")	# Look how quotes are used to escape argument parentheses.
# >>> "(___Hello world___)"

hformat("{'Hello world': field(+6, _, center), wrap('(.)')}")
# >>> "(___Hello world___.)"	# If odd number of chars, the closing half will get the center char.
```

* **canvas ( size, fillchar, align )**, combines both `field` and `wrap`, and provides an unique way of defining the textfield. Both `size` and `align` arguments work the same as with `field`, but the `fillchar` one changes. Depending on the number of chars given, it will do one thing or another:

```python
# If 'fillchar' has an odd number of chars, it fills with the center char, and wraps with the others.
hformat("{'Hello world': canvas(+6, '(_)', center)}")
# >>> "(___Hello world___)"

# If 'fillchar' has an even number of chars, each half will be used to fill completely each half of the text, and also to wrap it.
hformat("{'Hello world': canvas(+6, '()', center)}")
# >>> "((((Hello world))))"
```

#### String functions

* **trim ( limit, [stopchar] )**, trims the raw outputted text to a `limit` amount of characters. Keep in mind that this acts *after* float precision stuff is done, but *before* any field modifications. See the example below. If a `stopchar` string is given, it will be putted after the string, and it changes the limit size to `(limit - len(stopchar))`.

```python
# Trimming a normal string without modifications:
hformat("{'Hello world': trim(7)}")
# >>> "Hello w"

# Trimming a string with field modifications:
hformat("{'Hello world': field(+6, _, center), trim(7)}")
# >>> "___Hello w___"

# Trimming a floating number with no precission:
hformat("{11/7: trim(7)}")
# >>> "1.57142"

# Trimming a floating number with precission:
hformat("{11/7: trim(3), float(7)}")	# (the argument of float sets the decimal precision, see below) 
# >>> "1.5"

# Trimming a string and using a stop char:
hformat("{'Hello world': trim(7, |)}")
# >>> "Hello |"

# Trimming a string and using a stop string:
hformat("{'Hello world': trim(7, ...)}")
# >>> "Hell..."
```


#### Number functions

* **sign ( [which] )**, determines the signing style for a number. It uses the Python system, so the allowed arguments are '*+*' (default), used for both plus and minus sign; '*-*', used only for negative numbers; or the whitespace ' ', which uses a minus sign for negative numbers, and a whitespace for positive ones.

* **precision ( prec )**, sets the number of decimals a floating number must have. It rounds up if possible. Alternate name `prec` can be used.

* **float ( [prec] )**, casts the content of the text to a floating point. If the argument `prec` is given, it works just like `precision(prec)`. Alternate name `f` can be used.

* **floatsep ( char )**, changes the floating point separator char, from default point, to `char`.

* **milesep ( [char] )**, changes the miles separator char, from none, to `char`. If no `char` given, it uses the comma.


#### Casting functions
Casting functions work just like presentation types in `str.format()`. There is at least one for each Python type representation, and they do just the same. None of them use arguments, and they have more than one name, each separated with a vertical bar (|).

* **string | str | s**
* **bin | xb**, casts to a binary with 0bN format.
* **rawbin | rbin | b**, casts to a binary without format.
* **char | c**, casts an integer to a char.
* **decimal | dec | d**, casts to an integer.
* **octal | oct | xo**, casts to an octal with 0oN format.
* **rawoctal | rawoct | o**, casts to an octal without format.
* **hex | xx**, casts to a hexadecimal with 0xN format.
* **rawhex | rhex | x**, casts to a hexadecimal without format.
* **number | n**, casts to a number.
* **exp**, casts to an exponential expression.
* **general | gen | g**, casts to a general number.
* **percentage | %**, casts to a percentage format.


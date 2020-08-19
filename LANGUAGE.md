# HFormat Language [WIP]
___

## Introduction
HFormat implements a function-based syntax in order to use all its functionalities. If in the standard way we had something like this:

	"{"field_name[:[[fill]align][sign][alter][zero][width][grouping_option][.precision][type]]"}"

The HFormat way presents the following system:

	"{"field_name[:[func_name[([func_args, ...])]], ...]"}"

The `field_name` part remains just the same, but the *specs* part (everything after the colon) proposes a simple pythonic way that just uses a list of functions. And, more important, it is *way* more clear than `str.format()` approach. For example:

	{var+1 : fill(' '), width(20), center}

It is pretty clear that it will print whatever is inside `var` plus one, and that it will center it in a field of 20 whitespaces.



## Keyword chars
As HFormat allows the user to use a more simple and readable language, it needs to use way more keyword chars. Those characters cannot be used freely, as they would cause conflict with the defined syntax. Those are:

* The colon (':'), used to separate *field* from *specs*.
* The comma (','), used to separate both functions and function arguments.
* The semicolon (';'), an alternate char to separate functions.
* Both parentheses ('(', ')'), which are used to assign parameters to a function.
* One of the string quotes (' or "), which will be used to identify strings *in* the formatting substring.

In order to allow the user to use those chars without trouble, two "escaping" mechanisms are given:

* First, everything between string quotes (' or ") will be ignored. Only one of the two possible quotes will be used to define strings, and the other will remain as an unused char (so it could be used anywhere without escaping needed). The program automatically assigns the quote by choosing the one that appears the most in the formatting substring.
* Second, the syntax provides the escaping char '!', which works such like Python's '\\' escape char. Every char *before* the exclamation sign won't be evaluated, and will be treated as a literal.

**WARNING**: By now, key brackets ('{' and '}') are always interpreted as formatting substring definitors, which mean they can't be used as literals, even if they are escaped. This will be fixed soon.



## Field
The field is the part that appears *before* the colon. In Python <3.6, it must be a parameter given in the arguments of `str.format()`; in Python >=3.6, with the addition of f-strings, it can be any expression, which will be evaluated at runtime. HFormat allows a mixed system that works in *every* Python version, although it is not as powerful as f-strings.

HFormat field allows any expression that can be evaluated with the `eval()` function, using the arguments given to `hformat` as local variables for the expression. This means that something like the following can be done:

```python

	hformat("Example {3 + arg[2] : float}.", arg = [1,2,3,4])

```

But this won't:

```python

	arg = [1,2,3,4]
	hformat("Example {3 + arg[2] : float}.")

```

Which could be achieved using f-strings. That is because [PEP 498](https://www.python.org/dev/peps/pep-0498/#no-use-of-globals-or-locals) discourages the use of `locals()` and `globals()`, which would be necessary in order to get the user's defined variables. In any case, this feature may be added in a future as an optional element.

The combination of `str.format()` fields and expression evaluation leads to some issues. For example, in this case:

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

Keep in mind that this `_<pos>_` representation is only needed when you need to use the *raw* variable. If you attempt to access the content of a positional argument using indeces or attributes, it will work without underscores required:

```python

	obj.elem = 1
	hformat("Result: {0.elem + 1[2] + 3['a']}", obj, [1,2,3], {'a':3, 'b':5})
	# Will output '7'

```

Finally, if an error related to the expression interpretation occurs during the evaluation (for example, a not defined variable), it won't raise an error, but interprete the field as a string literal.


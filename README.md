# Human Formatter
___
This module provides an alternative way of formatting Python strings. It's idea is to avoid using the confusing and arbitrary `str.format()` minilanguage, substituting it with a Python-like, legible and simple language which allows to perform the same actions, and even more.

As an example, let's see the following code:

```python

	# In Python <3.6
	"{0:.^15,.3f}".format(10000/7)

	# In Python >=3.6
	f"{10000/7:.^15,.3f}"

	# In Python >=2.7 with hformat
	hformat("{10000/7 : field(15, ., center), milesep, float(3)}")

```

All those options print the same:

	>>> <...1,428.571...>

Is easy to see that the `hfprint()` option requires a larger string, and more writting. But see both `str.format()` and f-string specification. You can't tell me you understand anything. The Human Formatter tries to overcome that issue. It does take longer to get the same result, but it is also *lot easier to remember* than original Python way. 

And, you can do *a lot more* with the Human Formatter. Let's say we want to change the comma that separates the miles, and the point that separates the decimal part. Also, we only want to have three filling characters in both sides of the number, but we don't know how many chars it will be in the end. Finally, we want to wrap everything between '<...>'. Let's see how we could do it:

```python

	hformat("{10000/7 : canvas(+6, <.>, center), milesep(.), decsep('), float(3)}")

```

The output would be:

	>>> <...1.428'571...>

Which is something that won't be that easy to achieve using standard Python way.


It includes the following functions:

* `hformat(line, *args, **kwargs)`: Main function, acts like str.format().
* `hfprint(line, *args, **kwargs)`: A simplification of `print(hformat(...))`.

And, following Python's str.Formatter, the class:

* `HumanFormatter`: Performs all the formatting operation, from parsing to interpreting.



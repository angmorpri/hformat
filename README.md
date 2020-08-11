# Human Formatter
___
This module provides an alternative way of formatting Python strings. It's idea is to avoid using the confusing and arbitrary str.format() minilanguage, substituting it with a Python-like, legible and simple language which allows to perform the same actions, and even more.

As an example, let's say we want to print the following lines:


	Name:  Ben Hanscom
	Age:   11
	City:  Derry

And we have the object `person` who has all those values as attributes. With the standard Python way, we would do something like this:


```python
	# If Python < 3.6
	print("Name: {0.name: <3}\n".format(person))

	# If Python >= 3.6
```


It includes the following functions:

* `hformat(line, *args, **kwargs)`: Main function, acts like str.format().
* `hfprint(line, *args, **kwargs)`: A simplification of `print(hformat(...))`.

And, following Python's str.Formatter, the class:

* `HumanFormatter`: Performs all the formatting operation, from parsing to interpreting.



# Quick Python Reference
## Slicing
*Works for Str, List*
### Notation
```python
iterable_obj[start:stop:step]
```
*lists are muteable, strings are not. If you use* `[:]` *(slicing notation) you always work with a copy*
### Examples
#### half lower half upper string
```python
def half_lower_half_upper(word):
    middle = len(word) // 2
    return word[:middle].lower() + word[middle:].upper()
```
#### reverse even indexes
```python
def revers_even(iterable):
    if len(iterable) % 2:
        return iterable[::-2]
    else:
        return iterable[-2::-2]
```

## Convenient Type Checks
### Example
```python
for item in collection:
    if type(item) in [str, bool, list]:
        # do something
```

## Packing and Unpacking Dictionaries
### Unpacking
```python
my_dict = {'first_name': 'Kenneth', 'last_name': "Leverage"}
print("Hello {first_name} {last_name}!".format(**my_dict)
```
### Packing
```python
def packing(**kwargs):
    return len(kwargs)
packing(first="a", second="b", third="c")
#>> 3
```

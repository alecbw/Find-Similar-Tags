# Find-Similar-Tags
# GPT3-Create-Glossary-Definitions

A wrapper with interactive CLI that provides a way to replace duplicate, variation, and misspelled permutations of tags with the correct tags



### Setup

Install pip (if necessary)
```py
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python get-pip.py
```
Install the rapidfuzz library and a CLI helper library
```py
pip install rapidfuzz inquirer
```

### Usage

You'll need a CSV of terms with the following headers:
* Tag
* Count

Start the execution with
```py
python3 local_fuzzing_find_similar_tags.py
```

The script will find pairings among the provided tags and give you the option via the prompt to pick which tag should apply to both

There are a set of characters that correspond to each choice. They were picked by ergonomic convenience, not because the letters mean anything:

* ["No", "no", "N", "n", "M", "m"] - apply neither tag
* ["k", "K", "l", "L"] - apply the less frequent (second) tag to both
* literally anything else, including enter - apply the more frequent (first) tag to both)

```text
[?] ecommerce (5 instances) for ekommerc (1 instance): l
>> ekommerc will be applied to both
[?] ecommerce (5 instances) for ekommerc (1 instance): m
>> nothing will be applied to either; both remain in pool of potential pairings
[?] ecommerce (5 instances) for ekommerc (1 instance): (hit enter, or any key that doesn't match the others)
>> ecommerce will be applied to both

[then it will iterate through the full file, saving output to CSV every 25 rows]
```

The script keeps track of which tags have been discarded, so you won't be prompted again to re-label them

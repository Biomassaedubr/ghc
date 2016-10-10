
import nose.tools as nt
import ghc

def test_title_to_link():
    assert ghc.title_to_link('Some Thing') == 'some-thing'


text='''

# A Title Here?

This is the introduction.

Stuff here is ignored.

## Part One

A bunch of stuff here.

> This should be ignored
> Concepts: one, two ish  , Three !

## Part Two   
Empty here
> Concepts:
> two ish,
>   Three !

-------
Footer

'''

'''
def test_load_course():
    should = {
        'title': '',
    }
    course = ghc.load_course('test_course')
    nt.assert_dict_equal(course, should)
'''
'''
def test_parse():
    should = {
        'title': 'A Title Here?',
        'parts': {
            'part-one': {
                'short': 'part-one',
                'title': 'Part One',
                'concepts': ['one', 'two ish', 'Three !']
                },
            'part-two': {
                'short': 'part-two',
                'title': 'Part Two',
                'concepts': ['two ish', 'Three !']
            }
        } 
    }
    nt.assert_dict_equal(ghc.parse(text), should)
'''

def test_unmdlink():
    assert ghc.unmdlink("[something here][a link]") == "something here"

def test_h1link():
    assert ghc.h1link('# Something Here','#blah') == '# [Something Here](#blah)'



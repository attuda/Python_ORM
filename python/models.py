from entity import *

class Section(Entity):
    _fields  = ['title']
    _parents  = []
    _children = {'categories': 'Category'}
    _siblings = {}

class Category(Entity):
    _fields  = ['title']
    _parents  = ['section']
    _children = {'posts': 'Post'}
    _siblings = {}

class Post(Entity):
    _fields  = ['content', 'title']
    _parents  = ['category']
    _children = {'comments': 'Comment'}
    _siblings = {'tags': 'Tag'}

class Comment(Entity):
    _fields  = ['text']
    _parents  = ['post', 'user']
    _children = {}
    _siblings = {}

class Tag(Entity):
    _fields  = ['name']
    _parents  = []
    _children = {}
    _siblings = {'posts': 'Post'}

class User(Entity):
    _fields  = ['name', 'email', 'age']
    _parents  = []
    _children = {'comments': 'Comment'}
    _siblings = {}


if __name__ == "__main__":
    section = Section()
    section.title = "zzz"
    section.save()

    for section in Section.all():
        print section.title

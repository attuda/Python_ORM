# import psycopg2

from models import *
# post.db.set_isolation_level(0)

# post = Post(1) # select from post where post_id=?
# print(post.title)
# print(post.content)

# print(post.nosuchfield) # raise AttributeError

# post.title = 'Very New title 1'
# post.save() # update article set article_title=? where article_id = ?

# article = Post(3)
# article.title = 'Another title'
# article.content = 'Very interesting content'
# article.save() # update article set article_title=?, article_text=? where article_id = ?

# article = Post(4)
# article.title = 'Third title'
# article.content = 'Very interesting content with some freakin\' "quotes"'
# article.save() # update article set article_title=?, article_text=? where article_id = ?

post = Post(1) 
post.title = 'qqqNew title'
post.tags = Tag.all()
for tag in post.tags: # select * from tag natural join article_tag where article_id=?
   print(tag.name)
post.save() # insert into article (article_title) values (?)
print 'xxx'
# for post in Post.all():
   # print(post.title, post.content)

# article = Post(1)
# print(article.title)  # select * from article where article_id=?
# print(article.category.title)  # select * from category where category_id=?


# cat = Category(2)
# article.category = cat
# article.save()
# for post in cat.posts: # select * from article where category_id=?
   # print(post.title)

# a = [a for a in Post.all() if a.id == 10]
# a = a[0]
# print a.title
article = Post(10)
# print article.title
# a.title = 'bla-bla'
# print a.title
# print article.title
# c = article.tags
for tag in article.tags: # select * from tag natural join article_tag where article_id=?
   print(tag.name)

new_tag = Tag(5)
article.tags += [new_tag]
print
for tag in article.tags: # select * from tag natural join article_tag where article_id=?
   print(tag.name)
article.save()
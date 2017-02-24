import psycopg2
import psycopg2.extras
# from models2 import *

try:
    conn = psycopg2.connect("dbname='ORM' user='postgres' host='localhost' password='cvtyfcbvdjk'")
except:
    print "I am unable to connect to the database"
conn.set_isolation_level(0)

cur = conn.cursor(
            cursor_factory=psycopg2.extras.DictCursor
        )
# cur.execute("SELECT * FROM products;")
# cur.execute("""SELECT datname from pg_database""")
# rows = cur.fetchall()
# cur.fetchone()
# print "\nShow me the databases:\n"
# for row in rows:
    # print "   ", row[0]
cur.execute("""Select table_name FROM information_schema.tables WHERE table_schema = 'public'""")
rows = cur.fetchall()
print "\nShow me the tables in ORM db:\n"
print rows
for row in rows:
    print "   ", row[0]
__select_query    = 'SELECT * FROM "{table}" WHERE {table}_id=%s'
query = __select_query.format( table = 'post' )
cur.execute(query, [1])
fields = cur.fetchone()
print fields
cur.execute("""UPDATE "post" SET post_title='NNN' WHERE post_id=%s""", (1, ))
# fields = cur.fetchone()
# print fields
# colnames = [desc[0] for desc in cur.description]
# fields = zip(colnames,rows[0])
# print fields
# for field, row in fields:
    # print field, row
# cur.fetchone()
# print "\nShow me the units:\n"
# print rows
import psycopg2
import psycopg2.extras

class DatabaseError(Exception):
    pass
class NotFoundError(Exception):
    pass
class ItemWasNotCreatedError(Exception):
    pass

def diff(a, b):
    b = set(b)
    return [aa for aa in a if aa not in b]

class Entity(object):
    # db = None
    db = psycopg2.connect("dbname='ORM' user='postgres' host='localhost' password='cvtyfcbvdjk'")
    db.set_isolation_level(0)
    # ORM part 1
    __delete_query    = 'DELETE FROM "{table}" WHERE {table}_id=%s'
    __insert_query    = 'INSERT INTO "{table}" ({columns}) VALUES ({placeholders}) RETURNING "{table}_id"'
    __insert_query_tmp    = 'INSERT INTO "{table}" ({columns}, category_id) VALUES ({placeholders}, 1) RETURNING "{table}_id"'
    __list_query      = 'SELECT * FROM "{table}"'
    __select_query    = 'SELECT * FROM "{table}" WHERE {table}_id=%s'
    __update_query    = 'UPDATE "{table}" SET {columns} WHERE {table}_id=%s'

    # ORM part 2
    __parent_query    = 'SELECT * FROM "{table}" WHERE {parent}_id=%s'
    __sibling_query   = 'SELECT * FROM "{sibling}" NATURAL JOIN "{join_table}" WHERE {table}_id=%s'
    __update_children = 'UPDATE "{table}" SET {parent}_id=%s WHERE {table}_id IN ({children})'
    __loaded_items = {}
    
    def __init__(self, id=None):
        if self.__class__.db is None:
            raise DatabaseError()
        if not self.__class__.__name__ in self.__class__.__loaded_items.keys():
            self.__class__.__loaded_items[self.__class__.__name__] = {}
        if id in self.__class__.__loaded_items[self.__class__.__name__].keys():
            # print '!!! already have object ', self.__class__.__name__, ' with id ', id,
            self.__dict__ =  self.__class__.__loaded_items[self.__class__.__name__][id].__dict__
        else:
            self.__cursor   = self.__class__.db.cursor(
                cursor_factory=psycopg2.extras.DictCursor
            )
            
            self.__fields   = {}
            self.__id       = id
            self.__loaded   = False
            self.__modified = False
            self.__table    = self.__class__.__name__.lower()
            
            self._siblings_join_tables = {}
            self._initial_siblings = set()
            if not id is None:
                # self.__load()
                self.__class__.__loaded_items[self.__class__.__name__][id] = self
            # print 'Loaded ', self.__class__.__name__, ' with id ', id,
        # print self, self.__table

    def __getattr__(self, name):
        # check, if instance is modified and throw an exception
        # get corresponding data from database if needed
        # check, if requested property name is in current class
        #    columns, parents, children or siblings and call corresponding
        #    getter with name as an argument
        # throw an exception, if attribute is unrecognized
        if self.__modified:
            raise DatabaseError()
        if not self.__loaded and not self.__id is None:
            self.__load()
        if name in self._fields:
            return self._get_column(name)
        elif name in self._parents:
            return self._get_parent(name)
        elif name in self._children:
            return self._get_children(name)
        elif name in self._siblings:
            initial_name = 'initial_{}'.format(name)
            initial_siblings_list = self._get_siblings(name)
            object.__setattr__(self, name, initial_siblings_list)    
            object.__setattr__(self, initial_name, list(initial_siblings_list))  
            self._initial_siblings.add(initial_name)
            return self.__dict__[name]
        else:
            # print self, "has no attr:", name
            raise AttributeError()

    def __setattr__(self, name, value):
        # check, if requested property name is in current class
        #    columns, parents, children or siblings and call corresponding
        #    setter with name and value as arguments or use default implementation
        
        if name in self._fields:
            self._set_column(name, value)
            # self.__modified = True
        elif name in self._parents:
            self._set_parent(name, value)
        elif name in self._children:
            pass
        elif name in self._siblings:
            if not self.__id is None:
                initial_name = 'initial_{}'.format(name)
                if not initial_name in self._initial_siblings:
                    initial_siblings_list = self._get_siblings(name)
                    object.__setattr__(self, initial_name, list(initial_siblings_list))
                    self._initial_siblings.add(initial_name)
            object.__setattr__(self, name, value)        
        else:
            object.__setattr__(self, name, value)

    def __execute_query(self, query, args):
        # execute an sql statement and handle exceptions together with transactions

        try:
            self.__cursor.execute(query, args)
        except psycopg2.Error as error:
            print error.pgerror
            pass

    def __insert(self):
        # generate an insert query string from fields keys and values and execute it
        # use prepared statements
        # save an insert id
        
        columns_list = self.__fields.keys()
        arg_list = [self.__fields[column] for column in columns_list]
        columns_string = ', '.join(columns_list)
        param_list = ['%s'] * len(self.__fields)
        param_string = ', '.join(param_list)
        insert_query = self.__insert_query_tmp.format(table = self.__table, columns = columns_string, placeholders = param_string)
        self.__execute_query(insert_query, arg_list)
        result = self.__cursor.fetchone()
        self.id = result
        self.__class__.__loaded_items[self.__class__.__name__][id] = self
        # print self.id

    def __load(self):
        # if current instance is not loaded yet -
        # execute select statement and store it's result 
        # as an associative array (fields), 
        # where column names used as keys
        if not self.__loaded :
            load_query = self.__select_query.format(table = self.__table)
            self.__execute_query(load_query, (self.__id,))
            result = self.__cursor.fetchone()
            if not result is None:
                self.__fields   = result
                self.__loaded   = True

    def __update(self):
        # generate an update query string from fields keys and values and execute it
        # use prepared statements
        if not self.__loaded:
            columns_list = ['{}=%s'.format(field) for field in self.__fields]
            arg_list = [self.__fields['{}'.format(column)] for column in self.__fields]
        else:
            columns_list = ['{}_{}=%s'.format(self.__table, field) for field in self._fields]
            columns_list += ['{}_id=%s'.format(field) for field in self._parents]
            arg_list = [self.__fields['{}_{}'.format(self.__table, column)] for column in self._fields]
            arg_list += [self.__fields['{}_id'.format(column)] for column in self._parents]
        columns_string = ', '.join(columns_list)
        arg_list.append(self.__id)
        update_query = self.__update_query.format(table = self.__table, columns = columns_string)
        self.__execute_query(update_query, arg_list)
        self.__update_siblings()
        
    def __update_siblings(self):
        for initial_name in self._initial_siblings:
            initial_list = getattr(self, initial_name)
            print 'initial_list:'
            print initial_list
            sibling_name = initial_name[8:]
            current_list = getattr(self, sibling_name)
            print 'current_list:'
            print current_list
            for tag in initial_list:
                print (tag.name),
            print
            for tag in current_list:
                print (tag.name),
            print
            sib_to_del = diff(initial_list, current_list)
            self.__delete_siblings(sibling_name, sib_to_del)
            print "Del: ", sib_to_del
            sib_to_ins = diff(current_list, initial_list)
            self.__insert_siblings(sibling_name, sib_to_ins)
            print "Ins:", sib_to_ins
        # # print self._initial_siblings

    def _get_children(self, name):
        # return an array of child entity instances
        # each child instance must have an id and be filled with data
        child_class_name = self._children[name]
        child_table = child_class_name.lower()
        children_query = """select * from {table} where {parent}_id=%s""".format(table = child_table, parent = self.__table)
        self.__execute_query(children_query, (self.__id, ))
        models = __import__('models')
        child_class = getattr( models, child_class_name )
        item_id_string = '{}_id'.format(child_table)
        all_items = self.__cursor.fetchall()
        entities = []
        for item in all_items:
            entity = child_class(item[item_id_string])
            entity.__fields   = item
            entity.__loaded   = True
            entities.append(entity)
        return entities

    def _get_column(self, name):
        # return value from fields array by <table>_<name> as a key
        field = '{}_{}'.format(self.__table, name)
        return self.__fields[field]

    def _get_parent(self, name):
        # ORM part 2
        # get parent id from fields with <name>_id as a key
        # return an instance of parent entity class with an appropriate id
        parent_class_name = name.capitalize()
        models = __import__('models')
        parent_class = getattr( models, parent_class_name )
        instance = parent_class(self.__fields['{}_id'.format(name)])
        return instance
        

    def _get_siblings(self, name):
        # ORM part 2
        # get parent id from fields with <name>_id as a key
        # return an array of sibling entity instances
        # each sibling instance must have an id and be filled with data
        sibling_class_name = self._siblings[name]
        sibling_table = sibling_class_name.lower()
        if name not in self._siblings_join_tables.keys():
            self._get_sibling_join_table(name, sibling_table)
        query = self.__sibling_query.format(sibling = sibling_table, join_table = self._siblings_join_tables[name], table = self.__table)
        self.__execute_query(query, (self.__id, ))
        models = __import__('models')
        sibling_class = getattr( models, sibling_class_name )
        item_id_string = '{}_id'.format(sibling_table)
        all_items = self.__cursor.fetchall()
        entities = []
        for item in all_items:
            id = item[item_id_string]
            # if not sibling_class_name in sibling_class.__loaded_items.keys():
                # sibling_class.__loaded_items[sibling_class_name] = {}
            # if id in sibling_class.__loaded_items[sibling_class_name].keys():
                # print 'already have object ', sibling_class_name, ' with id ', id
                # entity = sibling_class.__loaded_items[sibling_class_name][id]
            # else:
            entity = sibling_class(id)
            entity.__fields   = item
            entity.__loaded   = True
            entities.append(entity)
        return entities

    def _set_column(self, name, value):
        # put new value into fields array with <table>_<name> as a key
        field = '{}_{}'.format(self.__table, name)
        self.__fields[field] = value
        self.__modified = True

    def _set_parent(self, name, value):
        # ORM part 2
        # put new value into fields array with <name>_id as a key
        # value can be a number or an instance of Entity subclass
        field = '{}_id'.format(name)
        if isinstance(value, Entity):
            value = value.id
        self.__fields[field] = value
        self.__modified = True
    
    def __insert_siblings(self, name, value_list):
        sibling_class_name = self._siblings[name]
        sibling_table = sibling_class_name.lower()
        if name not in self._siblings_join_tables.keys():
            self._get_sibling_join_table(name, sibling_table)
        if not isinstance(value_list, list):
            value_list = [value_list]
        columns_string = '{}_id, {}_id'.format(self.__table, sibling_table)
        insert_siblings_query = 'INSERT INTO "{table}" ({columns}) VALUES (%s, %s)'.format(table = self._siblings_join_tables[name], columns = columns_string)
        for value in value_list:
            self.__execute_query(insert_siblings_query, (self.__id, value.id))

    def __delete_siblings(self, name, value_list):
        sibling_class_name = self._siblings[name]
        sibling_table = sibling_class_name.lower()
        if name not in self._siblings_join_tables.keys():
            self._get_sibling_join_table(name, sibling_table)
        if not isinstance(value_list, list):
            value_list = [value_list]
        delete_siblings_query = 'DELETE FROM "{table}" WHERE {column1}=%s AND {column2}=%s'.format(table = self._siblings_join_tables[name], column1 = '{}_id'.format(self.__table), column2 = '{}_id'.format(sibling_table))
        for value in value_list:
            self.__execute_query(delete_siblings_query, (self.__id, value.id))
            
    def _get_sibling_join_table(self, name, sibling_table):
        self.__execute_query("""Select table_name FROM information_schema.tables WHERE table_schema = 'public'""", ())
        table_names = [ x[0] for x in self.__cursor.fetchall() ]
        join_table_variants = ['{0}_{1}', '{1}_{0}', '{0}__{1}', '{1}__{0}']
        for variant in join_table_variants:
            name_var = variant.format(self.__table, sibling_table)
            if name_var in table_names:
                self._siblings_join_tables[name] = name_var

    @classmethod
    def all(cls):
        # get ALL rows with ALL columns from corrensponding table
        # for each row create an instance of appropriate class
        # each instance must be filled with column data, a correct id and MUST NOT query a database for own fields any more
        # return an array of istances
        table_name = cls.__name__.lower()
        list_query = cls.__list_query.format(table = table_name)
        cursor   = cls.db.cursor(
            cursor_factory=psycopg2.extras.DictCursor
        )
        cursor.execute(list_query, )
        all_items = cursor.fetchall()
        entities = []
        for item in all_items:
            id = item['{}_id'.format(table_name)]
            # if not cls.__name__ in cls.__loaded_items.keys():
                # cls.__loaded_items[cls.__name__] = {}
            # if id in cls.__loaded_items[cls.__name__].keys():
                # print 'already have object ', cls.__name__, ' with id ', id
                # entity = cls.__loaded_items[cls.__name__][id]
            # else:
            entity = cls(id)
            entity.__fields   = item
            entity.__loaded   = True
            entities.append(entity)
        return entities
            

    def delete(self):
        # execute delete query with appropriate id
        if self.created:
            delete_query = self.__delete_query.format(table = self.__table)
            self.__execute_query(delete_query, (self.__id,))
        else:
            raise ItemWasNotCreatedError()
            

    @property
    def id(self):
        # try to guess yourself
        return self.__id
    
    @id.setter
    def id(self, value):
        self.__id = value

    @property
    def created(self):
        # try to guess yourself
        if self.__id is None:
            return False
        else:
            return True
    
    
    @property
    def updated(self):
        # try to guess yourself
        if not self.id is None:
            if not self.__loaded:
                self.__load()
            return self.__fields['{}_updated'.format(self.__table)]

    def save(self):
        # execute either insert or update query, depending on instance id
        if not self.created:
            self.__insert()
        else:
            self.__update()
        self.__modified = False

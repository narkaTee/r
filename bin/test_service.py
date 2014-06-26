import os


class Service(object):
    def __init__(self, stanzas=None):
        if not stanzas:
            stanzas = []
        self.confs = Confs(stanzas)
        #self.indexes = {
        #    'r': Index('r')
        #}


#class Index(object):
#
#    def __init__(self, name):
#        self.name = name
#        self.service = IndexService()


#class IndexService(object):
#
#    def __init__(self):
#        #self.posts = []
#        pass
#
#    def post(self, path_segment="", **query):
#        self.posts.append({
#            'path_segment': path_segment,
#            'query': query
#        })


class Confs(object):
    r_file = None

    def __init__(self, stanzas):
        self.stanzas = stanzas

    def create(self, name):
        if name != 'r':
            raise Exception('invalid config name: %s' % name)
        if not self.r_file:
            self.r_file = File(self.stanzas)
        return self.r_file


class File(object):
    def __init__(self, stanzas):
        self.stanzas = [
            Stanza('paths', {
                'r': os.environ['R_PATH']
            })
        ]
        for s in stanzas:
            self.stanzas.append(s)

    def list(self):
        r = []
        for s in self.stanzas:
            if not s.deleted:
                r.append(s)
        return r

    def create(self, name):
        stanza = Stanza(name, {
        })
        self.stanzas.append(stanza)
        return stanza


class Stanza(object):
    def __init__(self, name, data):
        self.deleted = False
        self.name = name
        self.data = data

    def __getattr__(self, key):
        # Called when an attribute was not found by the normal method. In this
        # case we try to find it in self.content and then self.defaults.
        if key in self.data:
            return self.data[key]
        else:
            raise AttributeError(key)

    def __getitem__(self, key):
        # getattr attempts to find a field on the object in the normal way,
        # then calls __getattr__ if it cannot.
        return getattr(self, key)

    def delete(self):
        self.deleted = True

    def submit(self, attr):
        for k in attr:
            self.data[k] = attr[k]
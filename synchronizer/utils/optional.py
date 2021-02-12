class Optional(object):

    def __init__(self, obj_value):
        self.obj_value = obj_value

    def map(self, func):
        self.obj_value = func(self.obj_value) if self.obj_value else None
        return self

    def if_exists(self, func, else_value=None):
        return func(self.obj_value) if self.obj_value else else_value

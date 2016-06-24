class TresorerieRouter(object):
    """
    A router to control all database operations on models in the
    tresorerie application.
    """
    def db_for_read(self, model, **hints):
        """
        Attempts to read tresorerie models go to admin db
        """
        if model._meta.app_label == 'tresorerie':
            return 'admin'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write tresorerie models go to admin db
        """
        if model._meta.app_label == 'tresorerie':
            return 'admin'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the tresorerie app is involved
        """
        if obj1._meta.app_label == 'tresorerie' or \
           obj2._meta.app_label == 'tresorerie':
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the tresorerie app only appears in the 'admin'
        database.
        """
        if app_label == 'tresorerie':
            return db == 'admin'
        return None
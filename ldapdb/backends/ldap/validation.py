# -*- coding: utf-8 -*-
# This software is distributed under the two-clause BSD license.
# Copyright (c) Loïc Carr
#
# This file was created as a hack
# TODO: implement something useful

from django.db.backends.base.validation import BaseDatabaseValidation


class DatabaseValidation(BaseDatabaseValidation):
    def check(self, **kwargs):
        issues = super(DatabaseValidation, self).check(**kwargs)
        return issues

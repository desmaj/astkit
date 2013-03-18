# 
# Copyright (C) 2012  Jason Michalski

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
import inspect

def exec_f(object_, globals_=None, locals_=None):
    if not globals_ and not locals_:
       frame = inspect.stack()[1][0]
       globals_ = frame.f_globals
       locals_ = frame.f_locals
    elif globals_ and not locals_:
        locals_ = globals_
    exec object_ in globals_, locals_

execfile = execfile

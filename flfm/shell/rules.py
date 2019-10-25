"""
    Rules and Permissions
    ~~~~~~~~~~~~~~~~~~~~~

    Objects pertaining to the rules and permissions controlling FLFM.

"""
import collections.abc
import copy
import os
import re
from functools import wraps
from werkzeug.datastructures import MultiDict
from flask import current_app, g, flash, abort
from .paths import ShellDirectory

def read_rules_file(rule_file):
    """Generate (key, value) tuples from the rules file.

    :param rule_file: The ``rules`` file to read from.
    :type rule_file: str
    """
    lines = rule_file.readlines()
    good_lines = list(filter(lambda line: len(line) > 2, lines))
    sorted_lines = sorted(good_lines,
                          key=lambda line: re.match(r"^(\w+)\=", line).group(1))
    for line in sorted_lines:
        pair = re.search(r"(\w*)\=([/\.\w]*)", line)
        yield (pair.group(1), pair.group(2))

def enforce_mapped(mapped_dirs, requested_path, for_upload=False):
    """Enforce the rules from the rules file on requested_path.

    :param mapped_dirs: A collection of mapped directories.
    :type mapped_dirs: An instance of :class:`MappedDirectories`.
    :param requested_path: The path of the directory to check permissions of.
    :type requested_path: str
    :param for_upload: Whether or not to enforce for an upload. **Default: False**
    :type for_upload: bool
    """
    requested_md = mapped_dirs.get_mapped_dir(requested_path)
    for mapped_dir in mapped_dirs:
        if for_upload:
            if requested_md == mapped_dir:
                if not mapped_dir.dir_allowuploads:
                    break
                return
        else:
            if requested_md == mapped_dir:
                if not mapped_dir.dir_allowed:
                    break
                return
    # Can't find a damn thing? Abort!
    abort(403)


def needs_rules(needing_method):
    """A decorator to wrap around ``routes`` requiring rules.
    """
    @wraps(needing_method)
    def load_rules(*args, **kwargs):
        rules_file = current_app.config['RULES_FILE']
        if not hasattr(g, 'fm_rules'):
            g.fm_rules = Rules(rules_file)
        if rules_file is None or g.fm_rules.num_rules == 0:
            flash('Please properly configure Flask FM before using.', 'danger')

        return needing_method(*args, **kwargs)

    return load_rules

class Rules:
    """Class representing the ``rules`` file.

    :param rule_file: Path to the ``rules`` file
    :type rule_file: str
    """
    def __init__(self, rule_file):
        try:
            if rule_file is not None:
                with open(rule_file, 'r') as f:
                    self._rules = MultiDict(read_rules_file(f))
            else:
                self._rules = MultiDict()
        except FileNotFoundError:
            self._rules = MultiDict()

    @property
    def rules(self):
        """A *werkzeug* **MultiDict** of rules.
        """
        return self._rules

    @property
    def num_rules(self):
        """The number of rules in the ``rules`` file.
        """
        rule_keys = ('Allowed', 'AllowUpload', 'AllowUploads', 'Disallowed',
                     'DisAllowed')
        count_o_rules = 0

        for key, count_us in self._rules.lists():
            if key in rule_keys:
                count_o_rules += len(count_us)

        return count_o_rules

# C'mon pylint VirtualRules derives from Rules
# Derived classes get them juicy protecteds
# pylint: disable=protected-access

class VirtualRules(Rules):
    """Mutable version of :class:`Rules`.

    Construction from a file in this derivation is handled by ``template`` param.
    To copy from a :class:`Rules` use :meth:`make_virtual`.

    :param template: Identical to the ``rule_file`` param in :class:`Rules`.
    :type template: str
    """
    def __init__(self, template=None):
        Rules.__init__(self, template)

    def _remove_item(self, key, value):
        value_list = self._rules.poplist(key)

        if not value_list:
            return

        for val in value_list:
            if val == value:
                continue
            self._rules.add(key, val)

    @classmethod
    def make_virtual(cls, rules_class):
        """Converts an immutable :class:`Rules` into a mutable :class:`VirtualRules`.

        :param rules_class: What to convert.
        :type rules_class: Instance of :class:`Rules`
        """
        now_virtual = cls(None)
        now_virtual._rules = copy.copy(rules_class._rules)
        return now_virtual

    def allowed(self, directory, remove=False):
        """Add or remove an *Allowed* rule for ``directory``.

        :param directory: The directory to create this rule for.
        :type directory: str
        :param remove: Remove this rule for ``directory``. **Default:** *False*.
        :type remove: bool
        """
        if remove:
            self._remove_item('Allowed', directory)
            return
        self._rules.add('Allowed', directory)

    def allow_uploads(self, directory, remove=False):
        """Add or remove an *Allowed* rule for ``directory``.

        :param directory: The directory to create this rule for.
        :type directory: str
        :param remove: Remove this rule for ``directory``. **Default:** *False*.
        :type remove: bool
        """
        if remove:
            self._remove_item('AllowUploads', directory)
            return
        self._rules.add('AllowUploads', directory)

    def disallowed(self, directory, remove=False):
        """Add or remove an *Allowed* rule for ``directory``.

        :param directory: The directory to create this rule for.
        :type directory: str
        :param remove: Remove this rule for ``directory``. **Default:** *False*.
        :type remove: bool
        """
        if remove:
            self._remove_item('Disallowed', directory)
            return
        self._rules.add('Disallowed', directory)

class MappedDirectory:
    """Represents a directory that is in the rules file, having rules.

    :param dir_path: Path of the directory.
    :type dir_path: str
    :param dir_allowed: Whether or not to allow access.
    :type dir_allowed: bool
    :param dir_allowuploads: Whether or not to allow uploads.
    :type dir_allowuploads: bool
    """
    def __init__(self, dir_path, dir_allowed, dir_allowuploads):
        self._dir_path = dir_path
        self._dir_allowed = dir_allowed
        self._dir_allowuploads = dir_allowuploads

    @classmethod
    def create_from_mapping(cls, mapping, path_key):
        """Instantiate a :class:`MappedDirectory` from a path corresponding to an
        entry within :class:`MappedDirectories`.

        :param mapping: The container to operate on.
        :type mapping: An instance of :class:`MappedDirectories`
        :param path_key: The path of the directory; It will be within **mapping**.
        :type path_key: str
        """
        try:
            allowed, allowuploads = mapping.get(path_key)
        except TypeError:
            allowed, allowuploads = False, False

        return cls(path_key, allowed, allowuploads)

    @property
    def dir_path(self):
        """The path of this :class:`MappedDirectory`.
        """
        return self._dir_path

    @property
    def dir_allowed(self):
        """Whether or not FLFM is allowed in this :class:`MappedDirectory`.
        """
        return self._dir_allowed

    @property
    def dir_allowuploads(self):
        """Whether or not uploads are allowed in this :class:`MappedDirectory`.
        """
        return self._dir_allowuploads

    def __repr__(self):
        return '<MappedDirectory \'{}\': {}>'.format(self.dir_path, self.__dict__)

    def __eq__(self, other):
        total_equates = 3
        equates = 0

        if self.dir_path == other.dir_path:
            equates += 1
        if self.dir_allowed == other.dir_allowed:
            equates += 1
        if self.dir_allowuploads == other.dir_allowuploads:
            equates += 1

        return equates is total_equates

    def is_in_tree(self, check_path):
        """Is a path denoted in ``check_path`` a subdirectory or in tree??

        :param check_path: The path to check against.
        :type check_path: str
        :returns: bool
        """
        common_path = os.path.commonpath([self.dir_path, check_path])
        if common_path.count('\\') > 0:
            common_path = common_path.replace('\\', '/')
        if common_path == self.dir_path:
            return True
        return False

    def as_shell(self):
        """Convert this :class:`MappedDirectory` into a
        :class:`~flfm.shell.paths.ShellPath`.

        :returns: A :class:`~flfm.shell.paths.ShellPath` representing this directory.
        """
        return ShellDirectory.from_str_loc(self.dir_path)

# `D` is an inherited property
# pylint: disable=invalid-name

# MappedDirectories' __iter__ must use yield
# pylint: disable=stop-iteration-return

class MappedDirectories(collections.abc.Mapping):
    """A mapping, `collections.abc.Mapping <https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping>`_,
    of :class:`MappedDirectory`'s.
    Internally, the mapped directories are a dictionary of *Path*, *tuple*.

    :param some_dict: A dictionary to populate this :class:`MappedDirectories`.
    :type some_dict: dict
    """
    def __init__(self, some_dict):
        self.D = some_dict

    @classmethod
    def from_rules(cls, rules):
        """Create from a :class:`Rules`.

        :param rules: The rules to create this mapping from.
        :type rules: A :class:`Rules` instance.
        """
        rule_dict = dict()

        if rules.num_rules > 0:
            # Tuple entries are as such:
            # (ALLOWED??, UPLOAD_ALLOWED??)
            for k, v in rules.rules.items(True):
                if 'Allowed' in k:
                    current = rule_dict.get(v, None)
                    if current is None:
                        rule_dict[v] = (True, False)
                    else:
                        rule_dict[v] = (True, current[1])
                elif 'Disallowed' in k or 'DisAllowed' in k:
                    # what is the point of other properties in a disallow??
                    # just overwrite
                    rule_dict[v] = (False, False)
                elif 'AllowUploads' in k or 'AllowUpload' in k:
                    current = rule_dict.get(v, None)
                    if current is None:
                        # Mark as allowed also since not in dict
                        rule_dict[v] = (True, True)
                    else:
                        rule_dict[v] = (current[0], True)
                else:
                    continue

        return cls(rule_dict)

    @classmethod
    def from_shell_path(cls, shell_path):
        """Create from a :class:`~flfm.shell.paths.ShellPath`

        :param shell_path: Create this mapping, without permission, from this.
        :type shell_path: A :class:`~flfm.shell.paths.ShellPath` instance.
        """
        the_dict = dict()
        default_tuple = (False, False)
        current_dir_path = shell_path.str_path

        the_dict[current_dir_path] = default_tuple
        for subdir in shell_path.directories:
            the_dict[subdir.path] = default_tuple

        return cls(the_dict)

    def __getitem__(self, key):
        return self.D.get(key)

    def __setitem__(self, key, item):
        if isinstance(item, MappedDirectory):
            new_item = (item.dir_allowed, item.dir_allowuploads)
            self.D[key] = new_item
            return
        self.D[key] = item

    def __len__(self):
        return len(self.D)

    def __iter__(self):
        num_yielded = 0
        iterator = iter(self.D)
        while True:
            if num_yielded >= len(self):
                break
            mapped_dir = next(iterator)
            num_yielded += 1
            yield MappedDirectory(mapped_dir, self.D[mapped_dir][0],
                                  self.D[mapped_dir][1])

    def __contains__(self, value):
        if isinstance(value, MappedDirectory):
            return value.dir_path in self.D
        return super().__contains__(value)

    def get_mapped_dir(self, dir_path):
        """Select a specific mapped directory from within this container.

        :param dir_path: The path to select.
        :type dir_path: str
        :returns: A :class:`MappedDirectory`.

        .. note::
            If ``_dir_path`` does not exist, the returned :class:`MappedDirectory`
            will have no permissions assigned. They will all be ``False``.

        """
        return MappedDirectory.create_from_mapping(self, dir_path)

    def apply_rule_map(self, rule_map):
        """Merge the rules of this :class:`MappedDirectories` and another.

        :param rule_map: Another rule/directories map.
        :type rule_map: Another :class:`MappedDirectories`
        :returns: ``self``, this instance but updated.
        """
        def length_paths(other_map):
            for md in other_map:
                yield len(md.dir_path)
        def difference_length(my_length, all_lengths):
            for length in all_lengths:
                yield abs(length-my_length)

        # the length of each path in the rule mapping
        rule_map_lens = list(length_paths(rule_map))

        for my_dir in self:
            # apply rule directly on top
            # iterate, because it's been explicitly set
            if my_dir in rule_map:
                self[my_dir.dir_path] = rule_map.get_mapped_dir(my_dir.dir_path)
                continue
            for rule_dir in rule_map:
                # are we in the tree of a ruled directory?
                if rule_dir.is_in_tree(my_dir.dir_path):
                    # we are in a tree of a disallowed directory
                    # prevent overwriting permissions
                    if not rule_dir.dir_allowed:
                        self[my_dir.dir_path] = rule_dir
                        break
                    my_length = len(my_dir.dir_path)
                    rd_length = len(rule_dir.dir_path)
                    # only lengths of what's in tree
                    rule_map_lens = list(filter(lambda x, l=rd_length: x <= l,
                                                rule_map_lens))
                    # apply rules to subdirectories of a ruled directory
                    # the most-common parent path from the rule mapping is the
                    # # one whose permissions shall be applied to the subdirectory
                    if my_length == min(difference_length(my_length, rule_map_lens))+rd_length:
                        self[my_dir.dir_path] = rule_dir
            # reset for next iteration
            rule_map_lens = list(length_paths(rule_map))

        return self

    @property
    def num_allowed(self):
        """Number of mapped directories that are allowed.
        """
        count_allowed = 0
        for md in self:
            count_allowed += 1 if md.dir_allowed else 0
        return count_allowed

    @property
    def num_disallowed(self):
        """Number of mapped directories that are disallowed.
        """
        count_disallowed = 0
        for md in self:
            count_disallowed += 1 if not md.dir_allowed else 0
        return count_disallowed

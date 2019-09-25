import collections.abc
import os
import re
from functools import wraps
from werkzeug.datastructures import MultiDict
from flask import current_app, g, flash, abort
from .paths import ShellDirectory

# Generate (key, value) tuples from the rules file
def read_rules_file(rule_file):
    lines = rule_file.readlines()
    good_lines = list(filter(lambda line: len(line) > 2, lines))
    sorted_lines = sorted(good_lines,
                          key=lambda line: re.match(r"^(\w+)\=", line).group(1))
    for line in sorted_lines:
        pair = re.search(r"(\w*)\=([/\.\w]*)", line)
        yield (pair.group(1), pair.group(2))

# Enforce the rules from the rules file on requested_path
def enforce_mapped(mapped_dirs, requested_path, for_upload=False):
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
        return self._rules

    @property
    def num_rules(self):
        return len(self.rules)

class MappedDirectory:
    def __init__(self, dir_path, dir_allowed, dir_allowuploads):
        self._dir_path = dir_path
        self._dir_allowed = dir_allowed
        self._dir_allowuploads = dir_allowuploads

    @classmethod
    def create_from_mapping(cls, mapping, path_key):
        try:
            allowed, allowuploads = mapping.get(path_key)
        except TypeError:
            allowed, allowuploads = False, False

        return cls(path_key, allowed, allowuploads)

    @property
    def dir_path(self):
        return self._dir_path

    @property
    def dir_allowed(self):
        return self._dir_allowed

    @property
    def dir_allowuploads(self):
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
        common_path = os.path.commonpath([self.dir_path, check_path])
        if common_path.count('\\') > 0:
            common_path = common_path.replace('\\', '/')
        if common_path == self.dir_path:
            return True
        return False

    def as_shell(self):
        return ShellDirectory.from_str_loc(self.dir_path)

class MappedDirectories(collections.abc.Mapping):
    def __init__(self, some_dict):
        self.D = some_dict

    @classmethod
    def from_rules(cls, rules):
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
        return MappedDirectory.create_from_mapping(self, dir_path)

    def apply_rule_map(self, rule_map):
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
        count_allowed = 0
        for md in self:
            count_allowed += 1 if md.dir_allowed else 0
        return count_allowed

    @property
    def num_disallowed(self):
        count_disallowed = 0
        for md in self:
            count_disallowed += 1 if not md.dir_allowed else 0
        return count_disallowed

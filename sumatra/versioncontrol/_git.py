"""
Defines the Sumatra version control interface for Git.

Classes
-------

GitWorkingCopy
GitRepository


:copyright: Copyright 2006-2014 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""

import logging
import git
import os
import shutil
from ConfigParser import NoSectionError, NoOptionError
try:
    from git.errors import InvalidGitRepositoryError, NoSuchPathError
except:
    from git.exc import InvalidGitRepositoryError, NoSuchPathError
from base import Repository, WorkingCopy, VersionControlError
from ..core import registry


logger = logging.getLogger("Sumatra")


def check_version():
    if not hasattr(git, "Repo"):
        raise VersionControlError("GitPython not installed. There is a 'git' package, but it is not GitPython (https://pypi.python.org/pypi/GitPython/)")
    if int(git.__version__.split(".")[1]) < 2:
        raise VersionControlError("Your Git Python binding is too old. You require at least version 0.2.0-beta1.")


def findrepo(path):
    check_version()
    try:
        repo = git.Repo(path)
    except InvalidGitRepositoryError:
        return
    else:
        return os.path.dirname(repo.git_dir)


class GitWorkingCopy(WorkingCopy):
    """
    An object which allows various operations on a Git working copy.
    """
    name = "git"

    def __init__(self, path=None):
        check_version()
        WorkingCopy.__init__(self, path)
        self.path = findrepo(self.path)
        self.repository = GitRepository(self.path)

    @property
    def exists(self):
        return bool(self.path and findrepo(self.path))

    def current_version(self):
        head = self.repository._repository.head
        try:
            return head.commit.hexsha
        except AttributeError:
            return head.commit.sha

    def use_version(self, version):
        logger.debug("Using git version: %s" % version)
        if version is not 'master':
            assert not self.has_changed()
        g = git.Git(self.path)
        g.checkout(version)

    def use_latest_version(self):
        self.use_version('master')  # note that we are assuming all code is in the 'master' branch

    def status(self):
        raise NotImplementedError()

    def has_changed(self):
        return self.repository._repository.is_dirty()

    def diff(self):
        """Difference between working copy and repository."""
        g = git.Git(self.path)
        return g.diff('HEAD', color='never')

    def content(self, digest):
        repo = git.Repo(self.path)
        for item in repo.iter_commits('master'):
            if item.hexsha == digest:
                file_content = item.tree.blobs[0].data_stream.read()
        return file_content

    def contains(self, path):
        """Does the repository contain the file with the given path?"""
        return path in self.repository._repository.git.ls_files().split()

    def get_username(self):
        config = self.repository._repository.config_reader()
        try:
            username, email = (config.get('user', 'name'), config.get('user', 'email'))
        except (NoSectionError, NoOptionError):
            return ""
        return "%s <%s>" % (username, email)


def move_contents(src, dst):
    for file in os.listdir(src):
        src_path = os.path.join(src, file)
        if os.path.isdir(src_path):
            shutil.copytree(src_path, os.path.join(dst, file))
        else:
            shutil.copy2(src_path, dst)
    shutil.rmtree(src)


class GitRepository(Repository):
    name = "git"
    use_version_cmd = "git checkout"
    apply_patch_cmd = "git apply"

    def __init__(self, url, upstream=None):
        check_version()
        Repository.__init__(self, url, upstream)
        self.__repository = None
        self.upstream = self.upstream or self._get_upstream()

    @property
    def exists(self):
        try:
            self._repository
        except VersionControlError:
            pass
        return bool(self.__repository)

    @property
    def _repository(self):
        if self.__repository is None:
            try:
                self.__repository = git.Repo(self.url)
            except (InvalidGitRepositoryError, NoSuchPathError) as err:
                raise VersionControlError("Cannot access Git repository at %s: %s" % (self.url, err))
        return self.__repository

    def checkout(self, path="."):
        """Clone a repository."""
        path = os.path.abspath(path)
        g = git.Git(path)
        if self.url == path:
            # already have a repository in the working directory
            pass
        else:
            tmpdir = os.path.join(path, "tmp_git")
            g.clone(self.url, tmpdir)
            move_contents(tmpdir, path)
        self.__repository = git.Repo(path)

    def get_working_copy(self, path=None):
        return GitWorkingCopy(path)

    def _get_upstream(self):
        if self.exists:
            config = self._repository.config_reader()
            if config.has_option('remote "origin"', 'url'):
                return config.get('remote "origin"', 'url')

registry.register(GitRepository)
registry.register(GitWorkingCopy)

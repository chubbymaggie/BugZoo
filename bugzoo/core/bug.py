from typing import List, Iterator, Dict, Optional
import os
import copy
import textwrap

import yaml
import docker

import bugzoo
from .language import Language
from .tool import Tool
from .build import BuildInstructions
from ..container import Container
from ..compiler import Compiler
from ..testing import TestCase, TestOutcome, TestSuite
from ..coverage import ProjectLineCoverage, \
                       ProjectCoverageMap, \
                       Spectra


class Bug(object):
    """
    Bugs provide an immutable snapshot of a software system at a given
    point in time, allowing it to be empirically studied and inspected in a
    transparent and reproducible manner.

    Each bug is assigned a unique identifier, based on its name, and
    the name of the program, if any, and dataset to which it belongs. This
    identifier takes the form: `"SOURCE:[PROGRAM:]NAME"`. Bugs can be
    retrieved by using this name, as shown below.

    .. code-block:: python

        rbox = BugZoo()
        bug = rbox.bugs['manybugs:python:69223-69224']
    """
    @staticmethod
    def from_file(dataset: 'bugzoo.manager.Dataset',
                  fn: str) -> 'Bug':
        """
        Loads a bug from its YAML manifest file.
        """
        with open(fn, 'r') as f:
            yml = yaml.load(f)

        name = yml['bug']
        program = yml.get('program', None)

        # determine the languages used by the program
        if not 'languages' in yml:
            raise Exception('No "languages" property specified for bug: {}'.format(name))

        languages = yml['languages'] # TODO: validate
        if languages is []:
            raise Exception('No associated languages specified for bug: {}'.format(name))
        languages = [Language[l] for l in languages]

        # build the test harness
        harness = TestSuite.from_dict(yml['test-harness'])

        # source directory
        source_dir = yml['source-location']

        # compilation instructions
        if not 'compiler' in yml:
            raise Exception('No compiler provided for bug: {}'.format(name))
        compiler = \
            Compiler.from_dict(yml['compiler'])

        # docker build instructions
        # TODO: this is stupid
        build_instructions = {'build': yml['build']}
        build_instructions = \
            BuildInstructions.from_dict(dataset,
                                        os.path.dirname(fn),
                                        build_instructions)

        return Bug(dataset,
                        name,
                        program,
                        languages,
                        source_dir,
                        harness,
                        build_instructions,
                        compiler)

    def __init__(self,
                 dataset: 'Dataset',
                 name: str,
                 program: str,
                 languages: List[Language],
                 source_dir: str,
                 harness: TestSuite,
                 build_instructions: BuildInstructions,
                 compiler: Compiler
                 ) -> None:
        assert name != ""
        assert program != ""
        assert languages != []

        self.__name = name
        self.__program = program
        self.__languages = languages[:]
        self.__source_dir = source_dir
        self.__test_harness = harness
        self.__build_instructions = build_instructions
        self.__compiler = compiler
        self.__dataset = dataset

    def to_dict(self) -> dict:
        """
        Produces a dictionary-based description of this bug, ready to be
        serialised in a JSON or YAML format.
        """
        jsn = {
            'uid': self.uid,
            'program': self.program,
            'dataset': self.dataset.name if self.dataset else None,
            'languages': [l.name for l in self.__languages]
        }
        return jsn

    @property
    def source_dir(self) -> str:
        """
        The absolute path of the dataset directory (within the container) for
        this bug.
        """
        # TODO
        return self.__source_dir

    @property
    def languages(self) -> List[Language]:
        return self.__languages[:]

    @property
    def program(self) -> Optional[str]:
        """
        The name of the program to which this bug belongs, if specified. If
        no program is specified for this bug, None will be returned instead.
        """
        return self.__program

    @property
    def build_instructions(self) -> BuildInstructions:
        return self.__build_instructions

    @property
    def compiler(self) -> Compiler:
        return self.__compiler

    @property
    def harness(self) -> TestSuite:
        """
        The test harness used by this bug.
        """
        return self.__test_harness

    @property
    def tests(self):
        """
        The test suite used by this bug.
        """
        return self.__test_harness.tests

    @property
    def dataset(self) -> 'Dataset':
        """
        The dataset to which this bug belongs.
        """
        return self.__dataset

    @property
    def installation(self) -> 'BugZoo':
        """
        The installation associated with this bug.
        """
        return self.dataset.manager.installation

    @property
    def coverage(self) -> 'ProjectCoverageMap':
        """
        Provides coverage information for each test within the test suite
        for the program associated with this bug.
        """
        # determine the location of the coverage map on disk
        fn = os.path.join(self.installation.coverage_path,
                          "{}.coverage.yml".format(self.identifier))

        # is the coverage already cached? if so, load.
        if os.path.exists(fn):
            return ProjectCoverageMap.from_file(fn, self.harness)

        # if we don't have coverage information, compute it
        try:
            container = None
            container = self.provision()
            coverage = container.coverage()

            # save to disk
            with open(fn, 'w') as f:
                yaml.dump(coverage.to_dict(), f, default_flow_style=False)
        finally:
            if container:
                container.destroy()

        return coverage

    @property
    def spectra(self) -> Spectra:
        """
        Computes and returns the fault spectra for this bug.
        """
        return Spectra.from_coverage(self.coverage)

    @property
    def image(self) -> str:
        """
        The name of the Docker image for this bug.
        """
        return self.__build_instructions.tag

    @property
    def identifier(self) -> str:
        """
        The fully-qualified name of this bug.
        """
        if self.__program:
            return "{}:{}:{}".format(self.__dataset.name, self.__program, self.__name)
        return "{}:{}".format(self.__dataset.name, self.__name)
    uid = identifier

    def provision(self,
                  volumes : Dict[str, str] = {},
                  tools : List[Tool] = [],
                  network_mode : str = 'bridge',
                  ports : dict = {},
                  tty : bool = False) -> 'Container':
        """
        Provisions a container for this bug.

        Parameters:
            network_mode:   the network mode that should be used by the
                provisioned container. Defaults to `bridge`. For more
                information, see the `documentation for Docker <https://docker-py.readthedocs.io/en/stable/containers.html>`_.
            tty:    a flag indicating whether a pseudo-TTY should be created
                for this container. By default, a pseudo-TTY is not created.
        """
        return Container(self, volumes=volumes, network_mode=network_mode, ports=ports, interactive=tty, tools=tools)
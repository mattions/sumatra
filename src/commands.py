from optparse import OptionParser
from textwrap import dedent

from programs import get_executable, Script
from datastore import FileSystemDataStore
from projects import SimProject, load_simulation_project
from launch import SerialLaunchMode

def setup(argv):
    """Set up a new simulation project in the current directory."""
    usage = "%prog setup [options] NAME MAINFILE"
    description = dedent("""\
      Set up a new simulation project in the current directory.

      NAME is the project name.

      MAINFILE is the name of the simulator script that would be supplied on the
      command line if running the simulator normally, e.g. init.hoc.
    """)
    parser = OptionParser(usage=usage,
                          description=description)
    parser.add_option('-d', '--datapath', metavar='PATH', default='./Data', help="set the path to the directory in which smt will search for datafiles generated by the simulation. Defaults to %default")
    parser.add_option('-s', '--simpath', metavar='PATH', help="set the path to the simulator executable. If this is not set, smt will try to infer the executable from MAINFILE, and will try to find the executable from the PATH environment variable, then by searching various likely locations on the filesystem.")
    parser.add_option('-r', '--repository', help="the URL of a Subversion or Mercurial repository containing the simulation code. This will be checked out/cloned into the current directory.")
    parser.add_option('-D', '--debug', action='store_true', help="print debugging information")
    (options, args) = parser.parse_args(argv)
    if len(args) != 2:
        parser.error('Both NAME and MAINFILE must be specified.')
    project_name, main_file = args
    
    global _debug
    _debug = options.debug
    
    script_code = Script(main_file=main_file, repository_url=options.repository)
    script_code.checkout() # worth doing now, to find any errors early
    executable = get_executable(path=options.simpath, script_file=main_file)
    
    project = SimProject(name=project_name,
                         default_executable=executable,
                         default_script=script_code,
                         default_launch_mode=SerialLaunchMode(),
                         data_store=FileSystemDataStore(options.datapath))
    
def info(argv):
    """Print information about the current simulation project."""
    usage = "%prog info"
    description = __doc__
    parser = OptionParser(usage=usage,
                          description=description)
    (options, args) = parser.parse_args(argv)
    if len(args) != 0:
        parser.error('info does not take any arguments')
    project = load_simulation_project()
    print project.info()
    
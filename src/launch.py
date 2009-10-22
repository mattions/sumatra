
import platform
import socket
import subprocess


class PlatformInformation(object):
    
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)
    #platform.mac_ver()
    #platform.win32_ver()
    #platform.dist()
    #platform.libc_ver()


class LaunchMode(object):
    """
    Launch serially or in parallel with MPI.
    If MPI store configuration (which nodes, etc)
    """
    
    def get_state(self):
        """
        Since each subclass has different attributes, we provide this method
        as a standard way of obtaining these attributes, for database storage,
        etc. Returns a dict.
        """
        return {}
    
    def pre_run(self, executable):
        #Run tasks before the simulation proper, e.g. nrnivmodl
        #should get the tasks to run from the Executable 
        pass

class SerialLaunchMode(LaunchMode):
    
    def __init__(self):
        LaunchMode.__init__(self)
        
    def __str__(self):
        return "serial"
    
    def run(self, executable, main_file, parameter_file):
        cmd = "%s %s %s" % (executable.default_executable_name, main_file, parameter_file)
        print "Sumatra is running the following command:", cmd
        #p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        p = subprocess.Popen(cmd, shell=True, stdout=None, stderr=None, close_fds=True)
        result = p.wait() 
        #self.errors = p.stderr.read()
        #self.output = p.stdout.read()
        #sys.stdout.write(self.output)
        #sys.stderr.write(self.errors)
        return result
    
    def get_platform_information(self):
        network_name = platform.node()
        bits, linkage = platform.architecture()
        return [PlatformInformation(architecture_bits=bits,
                                    architecture_linkage=linkage,
                                    machine=platform.machine(),
                                    network_name=network_name,
                                    ip_addr=socket.gethostbyname(network_name),
                                    processor=platform.processor(),
                                    release=platform.release(),
                                    system_name=platform.system(),
                                    version=platform.version())]
    
class DistributedLaunchMode(LaunchMode):
    
    def __init__(self, mpirun, hosts, n):
        LaunchMode.__init__(self)
        self.mpirun = os.path.abspath(mpirun)
        self.hosts = hosts
        self.n = n
        self.mpi_info = {}
    
    def run(self, executable, main_file, parameter_file):
        cmd = "%s -np %d -host %s %s %s %s" % (self.mpirun,
                                               self.n,
                                               ",".join(hosts),
                                               executable.default_executable_name,
                                               main_file,
                                               parameter_file)
        print "Sumatra is running the following command:", cmd
        p = subprocess.Popen(cmd, shell=True, stdout=None, stderr=None, close_fds=True)
        result = p.wait() 
        return result
    
    
    
    

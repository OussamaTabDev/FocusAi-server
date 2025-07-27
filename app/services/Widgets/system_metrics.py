import psutil as ps
import GPUtil

try:
    gpu_available = True
except ImportError:
    gpu_available = False

def get_gpu_usage():
    if not gpu_available:
        return "GPUtil not installed"
    


    gpus = GPUtil.getGPUs()
    if not gpus:
        return "No GPU found"
    
    usages = []
    for gpu in gpus:
        usages.append(f"GPU {gpu.id}: {gpu.load*100:.1f}% used, {gpu.memoryUsed}/{gpu.memoryTotal}MB")
    return "; ".join(usages) # %

def get_cpu_usge():
    return ps.cpu_percent(interval=1) # %

def get_ram_usge():
    ram = ps.virtual_memory()
    return  ram.percent , ram.used // (1024**2) , ram.total // (1024**2)  # % , Mb , Mb


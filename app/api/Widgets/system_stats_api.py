from ...services.Widgets.system_metrics import get_cpu_usge as gcu , get_gpu_usage as ggu , get_ram_usge as gru 
from . import widgets_bp 




#system_stats
@widgets_bp.route("system_stats", methods=["GET"])
def start_monitoring_loop():
    # while True:
    cpu = gcu()
    gpu = ggu()
    rpu , rsu , rst = gru()
    
    return {
        "CPU_Usage_Per": cpu, 
        "RAM_Usage_Per": rpu,
        "RAM_Usage": rsu ,
        "RAM_Total": rst,
        "GPU_Usage_Per": gpu
    }
        
"""
Utility methods for using browsermobproxy.
"""
import os
import signal
import psutil
from browsermobproxy import Server
from .promise import Promise


def bmp_proxy():
    """
    Creates a proxy and a server instance with browsermobproxy.
    Reference: http://browsermob-proxy-py.readthedocs.org/en/latest/index.html

    Returns:
        (proxy, server)
    """
    def create_proxy():
        """
        Try to create a proxy.
        """
        try:
            proxy = server.create_proxy()
        except:  # pylint: disable=bare-except
            return False, None
        return True, proxy

    port = int(os.environ.get('BROWSERMOB_PROXY_PORT', 8080))
    server = Server('browsermob-proxy', options={'port': port})

    try:
        # If anything in this block raises an exception, make sure we kill
        # the server process before exiting.
        server.start()

        # Using the promise module to wait for the server to be responsive.
        # The server.create_proxy function sometimes raises connection
        # refused errors if the server isn't ready yet.
        proxy = Promise(
            create_proxy, 'browsermobproxy is responsive', timeout=10
        ).fulfill()

        proxy_host = os.environ.get('BROWSERMOB_PROXY_HOST', '127.0.0.1')
        proxy.remap_hosts('localhost', proxy_host)
    except:  # pylint: disable=bare-except
        # Make sure that the server process is stopped.
        stop_server(server)
        raise

    return proxy, server


def kill_process(proc):
    """
    Kill the process `proc` created with `subprocess`.

    Args:
        process
    Returns:
        None
    """
    p1_group = psutil.Process(proc.pid)

    child_pids = p1_group.children(recursive=True)

    for child_pid in child_pids:
        os.kill(child_pid.pid, signal.SIGKILL)


def stop_server(server):
    """
    Stops the browsermobproxy server process and any child_pid
    processes.

    Args:
        server
    Returns:
        None
    """
    # Server.stop does not kill the child processes, but it needs to.
    # Do not remove this or the processes will not get killed.
    kill_process(server.process)
    server.stop()

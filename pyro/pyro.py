try:
    from zyre_pyzmq import Zyre as Pyre
except Exception as e:
    print("using Python native module", e)
    from pyre import Pyre

import zmq
import uuid
import json
from pyre import zhelper


class Pyro():
    def __init__(self, name, channel, headers):
        self.name = name
        self.channel = channel
        self.headers = headers
        self.commands = []
        self.swarm = {}

    def connect(self):
        def _chat_task(ctx, pipe):
            n = Pyre(self.name)
            for header_k, header_v in self.headers:
                n.set_header(header_k, header_v)
            n.join(self.channel)
            n.start()
            poller = zmq.Poller()
            poller.register(pipe, zmq.POLLIN)
            poller.register(n.socket(), zmq.POLLIN)
            while(True):
                items = dict(poller.poll())
                print(n.socket(), items)
                if pipe in items and items[pipe] == zmq.POLLIN:
                    message = pipe.recv()
                    # message to quit
                    if message.decode('utf-8') == "$$STOP":
                        break
                    # print("CHAT_TASK: %s" % message)
                    n.shouts(self.channel, message.decode('utf-8'))
                else:
                    cmds = n.recv()
                    msg_type = cmds.pop(0).decode('utf-8')
                    peer = uuid.UUID(bytes=cmds.pop(0))
                    name = cmds.pop(0).decode('utf-8')
                    msg_group = None
                    msg = None
                    if msg_type == "SHOUT":
                        msg_group = cmds.pop(0)
                    elif msg_type == "ENTER":
                        self.swarm['{}-{}'.format(name, peer)] = {
                            'peer': peer,
                            'name': name,
                            'headers': json.loads(cmds.pop(0).decode('utf-8'))
                        }
                    if cmds:
                        msg = cmds.pop(0).decode('utf-8')
                    self.commands.append([name, peer, msg_group, msg])
            n.stop()
        ctx = zmq.Context()
        chat_pipe = zhelper.zthread_fork(ctx, _chat_task)
        while True:
            try:
                msg = input()
                for c in self.commands:
                    print(c)
                print(self.swarm)
                chat_pipe.send(msg.encode('utf_8'))
            except (KeyboardInterrupt, SystemExit):
                break
        chat_pipe.send("$$STOP".encode('utf_8'))
        print("FINISHED")


if __name__ == '__main__':
    pyro = Pyro(name='pyro',
                channel='pyro_channel',
                headers=(("CHAT_Header1", "example header1"),))
    pyro.connect()

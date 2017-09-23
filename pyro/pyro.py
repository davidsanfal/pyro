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
        self.conected = False

    def _enter(self, cmds):
        cmds.pop(0).decode('utf-8')
        peer = uuid.UUID(bytes=cmds.pop(0))
        name = cmds.pop(0).decode('utf-8')
        self.swarm['{}-{}'.format(name, peer)] = {
            'peer': peer,
            'name': name,
            'headers': json.loads(cmds.pop(0).decode('utf-8'))
        }

    def _exit(self, cmds):
        cmds.pop(0).decode('utf-8')
        peer = uuid.UUID(bytes=cmds.pop(0))
        name = cmds.pop(0).decode('utf-8')
        self.swarm.pop('{}-{}'.format(name, peer))

    def _join(self, cmds):
        pass

    def _leave(self, cmds):
        pass

    def _whister(self, cmds):
        pass

    def _shout(self, cmds):
        cmds.pop(0)
        self.commands.append([uuid.UUID(bytes=cmds.pop(0)),
                              cmds.pop(0).decode('utf-8'),
                              cmds.pop(0).decode('utf-8'),
                              cmds.pop(0).decode('utf-8')])
        print(self.commands[-1])

    def connect(self):
        self.conected = True

        def _chat_task(ctx, pipe):
            n = Pyre(self.name)
            for header_k, header_v in self.headers:
                n.set_header(header_k, header_v)
            n.join(self.channel)
            n.start()
            poller = zmq.Poller()
            poller.register(pipe, zmq.POLLIN)
            poller.register(n.socket(), zmq.POLLIN)
            while self.conected:
                items = dict(poller.poll())
                # print(n.socket(), items)
                if pipe in items and items[pipe] == zmq.POLLIN:
                    message = pipe.recv()
                    n.shouts(self.channel, message.decode('utf-8'))
                else:
                    cmds = n.recv()
                    msg_type = cmds[0].decode('utf-8')
                    getattr(self, '_{}'.format(msg_type.lower()))(cmds)
            n.stop()
        ctx = zmq.Context()
        chat_pipe = zhelper.zthread_fork(ctx, _chat_task)
        while self.conected:
            try:
                msg = input()
                chat_pipe.send(msg.encode('utf_8'))
            except (KeyboardInterrupt, SystemExit):
                self.conected = False
                chat_pipe.send(''.encode('utf_8'))


if __name__ == '__main__':
    pyro = Pyro(name='pyro',
                channel='pyro_channel',
                headers=(("CHAT_Header1", "example header1"),))
    pyro.connect()

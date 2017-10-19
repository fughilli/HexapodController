import base64
import json

class ControlSocket(object):
    def __init__(self, sock):
        self.sock = sock

        self.partialbuffer = ''
        self.seenstart = False

        self.start_sentinel = '^'
        self.end_sentinel = '$'
    
    def transmitControl(self, control):
        sendbuf = '^%s$' % base64.b64encode(json.dumps(control))

        while(1):
            tx_bytes = self.sock.send(sendbuf)

            if tx_bytes == 0:
                raise Exception("Socket broken")

            sendbuf = sendbuf[tx_bytes:]

            if sendbuf == '':
                break

    def receiveControl(self):
        b64_buf = ''

        while(b64_buf == ''):
            # Receive 1024 characters
            rxbuf = self.sock.recv(128)

            # If we didn't get anything, the socket is broken
            if rxbuf == '':
                raise Exception("Socket broken")

            # Add the received data to the partial receive buffer
            self.partialbuffer += rxbuf

            while(1):
                # If the start sentinel is inside the partial receive buffer and we
                # have not seen it yet, then cut everything up to and including the
                # start sentinel and mark it seen
                if self.start_sentinel in self.partialbuffer and not self.seenstart:
                    self.partialbuffer = self.partialbuffer[
                        self.partialbuffer.find(self.start_sentinel) + 1:]
                    self.seenstart = True

                # If the end sentinel is inside the partial receive buffer, and we
                # have seen the start sentinel, then save everything up to the end
                # sentinel to b64_buf and cut everything up to and including the end
                # sentinel. Then mark the start sentinel as not seen
                if self.end_sentinel in self.partialbuffer and self.seenstart:
                    b64_buf = self.partialbuffer[
                        :self.partialbuffer.find(self.end_sentinel)]
                    self.partialbuffer = self.partialbuffer[len(b64_buf) + 1:]
                    self.seenstart = False

                    if self.end_sentinel in self.partialbuffer:
                        print self.partialbuffer
                        continue

                    break

        decoded_buf = base64.b64decode(b64_buf)
        return json.loads(decoded_buf)



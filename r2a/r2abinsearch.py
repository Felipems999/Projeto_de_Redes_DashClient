from r2a.ir2a import IR2A
from player.parser import *
import time


class R2ABinSearch(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.parsed_mpd = ''
        self.qi = []
        self.tput = 0
        self.time_req = 0
        self.index = int(10)

    def handle_xml_request(self, msg):

        self.time_req = time.time()

        self.send_down(msg)

    def handle_xml_response(self, msg):
        # getting qi list
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()

        var_time = time.time() - self.time_req

        self.time_req = var_time

        self.tput = msg.get_bit_length()/var_time

        print(f'\nThroughtput : {self.tput}')

        self.send_up(msg)

    def handle_segment_size_request(self, msg):

        self.index = self.busca_bin(
            0, int(self.qi.__len__()/2), self.qi.__len__() - 1)

        msg.add_quality_id(self.qi[self.index])
        print(f"\nqi[{self.qi[self.index]}]\n")

        self.time_req = time.time()

        self.send_down(msg)

    def handle_segment_size_response(self, msg):

        var_time = time.time() - self.time_req

        self.tput = msg.get_bit_length()/var_time
        print(f'\nThroughtput: {self.tput}\n')

        self.send_up(msg)

    def busca_bin(self, low, mid, hi):

        if (self.tput >= self.qi[hi]):
            return hi
        elif (self.tput <= self.qi[low]):
            return low

        while (low <= hi):
            if (self.tput == self.qi[mid]
                    or (self.tput > self.qi[mid] and self.tput < self.qi[mid + 1])):
                return int(mid)
            elif (self.tput < self.qi[mid] and self.tput >= self.qi[mid - 1]):
                return int(mid - 1)

            if (self.tput < self.qi[mid - 1]):
                hi = mid
                mid = int(hi / 2)
            elif (self.tput > self.qi[mid + 1]):
                low = mid + 1
                mid = int(((low + hi) / 2))

    def initialize(self):
        print('Iniciando\n')
        pass

    def finalization(self):
        print('Finalizando')
        pass

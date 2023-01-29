from r2a.ir2a import IR2A
from player.parser import *
import time
from statistics import mean as m, mode as mo
from json import *
from math import floor


class R2ABinSearch(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.parsed_mpd = ''  # Variável utilizada para obter a carga útil da mensagem
        self.qi = []  # Lista de qualidades
        self.tput = 0  # Valor da taxa de transferência(throughput)
        self.tput_list = []  # Lista de taxas de transferência
        self.time_req = 0  # Tempo de requisição
        self.buffer = 10  # Tamanho do buffer
        self.buffer_list = []  # Lista com os valores de tamanho de buffer
        self.index = 0  # Valor do indices da qualidade a ser selecionada na lista de qualidades
        self.index_list = []  # Lista dos indices que são selecionados em cada requisição

    def handle_xml_request(self, msg):

        self.time_req = time.perf_counter()

        self.send_down(msg)

    def handle_xml_response(self, msg):

        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()

        var_time = (time.perf_counter() - self.time_req)
        self.tput = msg.get_bit_length()/var_time
        print(f'\nThroughput : {self.tput}')
        self.tput_list.append(self.tput)

        self.buffer = self.whiteboard.get_amount_video_to_play()
        self.buffer_list.append(self.buffer)

        self.index = self.busca_bin_rec(
            0, floor(self.qi.__len__()/2), self.qi.__len__() - 1)
        self.index_list.append(self.index)

        self.send_up(msg)

    def handle_segment_size_request(self, msg):

        self.time_req = time.perf_counter()

        self.select_index()
        self.index = floor(mo(self.index_list))

        msg.add_quality_id(self.qi[self.index])
        print(f'\nqi[{self.qi[self.index]}]\n')

        self.send_down(msg)

    def handle_segment_size_response(self, msg):

        var_time = (time.perf_counter() - self.time_req)
        self.tput_list.append(msg.get_bit_length()/var_time)
        self.tput = m(self.tput_list)
        if (self.tput_list.__len__() == 5):
            self.tput_list.clear()
            self.tput_list.append(self.tput)

        print(f'\nThroughput: {self.tput}\n')

        self.buffer_list.append(self.whiteboard.get_amount_video_to_play())
        self.buffer = mo(self.buffer_list)
        if (self.buffer_list.__len__() == 30):
            self.buffer_list.clear()
            self.buffer_list.append(self.buffer)

        print(f'\n>>>>Buffer: {self.buffer}')

        self.send_up(msg)

    def select_index(self):
        if (self.buffer <= 10):
            self.index_list.append(self.busca_bin_rec(0, 1, 2))
        elif (self.buffer <= 20):
            hi = floor(self.qi.__len__() / 4)
            low = 0
            mid = floor((hi + low) / 2)
            self.index_list.append(self.busca_bin_rec(low, mid, hi))
        elif (self.buffer <= 30):
            hi = floor(self.qi.__len__() / 2)
            low = floor(hi / 2)
            mid = floor((hi + low) / 2)
            self.index_list.append(self.busca_bin_rec(low, mid, hi))
        elif (self.buffer > 30):
            hi = floor(self.qi.__len__() - 1)
            low = floor(hi / 2)
            mid = floor((hi + low) / 2)
            self.index_list.append(self.busca_bin_rec(low, mid, hi))

    # https://blog.pantuza.com/artigos/busca-binaria

    def busca_bin_rec(self, low, mid, hi):
        print(f'\nlow: {low}; mid: {mid}; hi: {hi}')
        if (self.tput >= self.qi[hi]):
            return hi
        elif (self.tput <= self.qi[low] or (low >= hi or mid == hi)):
            return low

        if (self.tput >= self.qi[mid] and self.tput < self.qi[mid + 1]):
            return floor(mid)
        elif (self.tput < self.qi[mid] and self.tput >= self.qi[mid - 1]):
            return floor(mid - 1)

        if (self.tput < self.qi[mid - 1]):
            hi = mid - 1
            mid = floor((hi + low) / 2)
            return floor(self.busca_bin_rec(low, mid, hi))
        elif (self.tput > self.qi[mid + 1]):
            low = mid + 1
            mid = floor((hi + low) / 2)
            return floor(self.busca_bin_rec(low, mid, hi))

    def initialize(self):
        print('Iniciando\n')
        pass

    def finalization(self):
        print('Finalizando')
        pass

####################################################################################################
        # if (self.buffer <= 10):
        #     hi = floor(self.qi.__len__() / 2)
        #     mid = floor(hi/2)
        #     self.index = self.busca_bin_rec(0, mid, hi)
        # elif (self.buffer > 10):
        #     hi = floor(self.qi.__len__() - 1)
        #     low = floor(self.qi.__len__()/2)
        #     mid = floor((hi + low) / 2)
        #     self.index = self.busca_bin_rec(low, mid, hi)

        # def busca_bin(self, low, mid, hi):

        # if (self.tput >= self.qi[hi]):
        #     return hi
        # elif (self.tput <= self.qi[low]):
        #     return low

        # while (low <= hi):
        #     if (self.tput >= self.qi[mid] and self.tput < self.qi[mid + 1]):
        #         return floor(mid)
        #     elif (self.tput < self.qi[mid] and self.tput >= self.qi[mid - 1]):
        #         return floor(mid - 1)

        #     if (self.tput < self.qi[mid - 1]):
        #         hi = mid
        #         mid = floor(hi / 2)
        #     elif (self.tput > self.qi[mid + 1]):
        #         low = mid + 1
        #         mid = floor((low + hi) / 2)

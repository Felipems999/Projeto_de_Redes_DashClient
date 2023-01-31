# Felipe Moura da Silva 16/0119740

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
        self.tput = 0  # Valor da média de taxas de transferência(throughput)
        self.tput_list = []  # Lista de taxas de transferência
        self.time_req = 0  # Tempo de requisição
        self.buffer = 10  # Tamanho do buffer
        self.buffer_list = []  # Lista com os valores de tamanho de buffer
        self.index = 0  # Valor do índices da qualidade a ser selecionada na lista de qualidades
        self.index_list = []  # Lista dos índices que são selecionados em cada requisição

    def handle_xml_request(self, msg):

        # Guarda o tempo em que a requeisição é enviada
        self.time_req = time.perf_counter()

        self.send_down(msg)

    def handle_xml_response(self, msg):

        # Carrega a carga útil da mensagem recebida
        self.parsed_mpd = parse_mpd(msg.get_payload())
        # Carrega a lista qi com os id's das qualidades disponíveis
        self.qi = self.parsed_mpd.get_qi()

        # Calcula a variação entre o momento da requisição e da resposta
        var_time = (time.perf_counter() - self.time_req)
        # Calcula a taxa de transferência em bits e armazena o valor na lista de taxas de transferência
        self.tput = msg.get_bit_length()/var_time
        print(f'\nThroughput : {self.tput}')
        self.tput_list.append(self.tput)

        # Salva o valor atula do buffer e armazena na lista de buffers
        self.buffer = self.whiteboard.get_amount_video_to_play()
        self.buffer_list.append(self.buffer)

        self.index = self.busca_bin_rec(
            0, floor(self.qi.__len__()/2), self.qi.__len__() - 1)  # Busca o primeiro índice com base apenas na 1ª taxa de transferência
        # Armazena o primeiro índice na lista de índices
        self.index_list.append(self.index)

        self.send_up(msg)

    def handle_segment_size_request(self, msg):

        # Guarda o tempo em que a requeisição é enviada
        self.time_req = time.perf_counter()

        # Chama a função que selecionará o índice da qualidade à ser requisitada
        self.select_index()
        # Escolhe o índice com base na moda da lista de índices
        self.index = floor(mo(self.index_list))

        # Adiciona a qualidade selecionada à mensagem
        msg.add_quality_id(self.qi[self.index])
        print(f'\nqi[{self.qi[self.index]}]\n')

        self.send_down(msg)

    def handle_segment_size_response(self, msg):

        # Calcula a variação entre o momento da requisição e da resposta
        var_time = (time.perf_counter() - self.time_req)
        # Calcula a taxa de transferência em bits e armazena o valor na lista de taxas de transferência
        self.tput_list.append(msg.get_bit_length()/var_time)
        # Calcula a média dos valores de taxa de tranferência e guarda na variável
        self.tput = m(self.tput_list)
        # Limpa a lista de taxas de transferência quando o tamanho é 5, salvando o valor da última média depois de limpá-la
        if (self.tput_list.__len__() == 5):
            self.tput_list.clear()
            self.tput_list.append(self.tput)

        print(f'\nThroughput: {self.tput}\n')

        # Guarda o tamanho atual do buffer na lista
        self.buffer_list.append(self.whiteboard.get_amount_video_to_play())
        # Armazena o valor da moda da lista de buffers
        self.buffer = mo(self.buffer_list)
        # Limpa a lista de buffers quando o tamanho é 30, salvando o valor da última moda depois de limpá-la
        if (self.buffer_list.__len__() == 30):
            self.buffer_list.clear()
            self.buffer_list.append(self.buffer)

        print(f'\n>>>>Buffer: {self.buffer}')

        self.send_up(msg)

    # Função que seleciona o índice da qualidade levando em consideração o comportamento dos últimos buffers
    def select_index(self):
        # Em caso de o buffer estar com tamanho bem limitado, se busca a melhor qualidade dentre as menores taxas de bits
        if (self.buffer <= 10):
            self.index_list.append(self.busca_bin_rec(0, 1, 2))
        elif (self.buffer <= 20):  # Em caso de um buffer de tamanho entre 10 e 21, se divide a lista em 4 partes e aplica a busca binária
            # na sub-lista com as menores taxas de bits
            hi = floor(self.qi.__len__() / 4)
            low = 0
            mid = floor((hi + low) / 2)
            self.index_list.append(self.busca_bin_rec(low, mid, hi))
        elif (self.buffer <= 30):  # Em caso de um buffer de tamanho entre 20 e 31, se divide a lista em 3 partes e aplica a busca binária
            # na sub-lista com as taxas de bits mais póximas da métade da lista, mas que sejam menores ou iguais ao valor mediano
            hi = floor(self.qi.__len__() / 2)
            low = floor(hi / 2)
            mid = floor((hi + low) / 2)
            self.index_list.append(self.busca_bin_rec(low, mid, hi))
        elif (self.buffer > 30):  # Em caso de um buffer de tamanho entre 20 e 31, se divide a lista em 2 partes e aplica a busca binária
            # na sub-lista com as taxas de bits maiores
            hi = floor(self.qi.__len__() - 1)
            low = floor(hi / 2)
            mid = floor((hi + low) / 2)
            self.index_list.append(self.busca_bin_rec(low, mid, hi))

    # Método que é uma variaçõa do algoritmo de busca binária recursiva, que recebe como parâmetros o índice dos itens promeiro, mediano
    # e último de uma lista ordenada decrescente
    def busca_bin_rec(self, low, mid, hi):
        # Verifica se o valor da média de taxa de transferência de bits é maior ou igual à qualidade com maior taxa
        # de bits disponível na lista de qualidades, senão, verifica se a média taxa de trasferência de bits é menor ou igual à
        # menor taxa de bits disponível, ou se a lista se tornou pequena demais para ser dividida, dando preferência para a menor taxa de bits
        if (self.tput >= self.qi[hi]):
            return hi
        elif (self.tput <= self.qi[low] or (low >= hi or mid == hi)):
            return low

        # Compara a média de taxas de tranferência se encontra entre o valor mediano e seus sucessor e antecessor;
        # em caso de estar entre o valor mediano e o sucessor, retorna o índice do valor mediano;
        # em caso de estar entre o valor mediano e o antecessor, retorna o índice do antecessor
        if (self.tput >= self.qi[mid] and self.tput < self.qi[mid + 1]):
            return floor(mid)
        elif (self.tput < self.qi[mid] and self.tput >= self.qi[mid - 1]):
            return floor(mid - 1)

        # Caso o valor não esteja entre o valor meidano e seu sucessor ou antecessor, aplica a recursividade em metade da lista
        # de acordo com o valor da média de taxas de transferência
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
